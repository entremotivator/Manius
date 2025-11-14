"""
Advanced file management utility for Manus API
Upload, organize, preview, and manage files with detailed analytics
"""

import streamlit as st
from openai import OpenAI
import requests
from datetime import datetime, timedelta
import pandas as pd
import plotly.express as px
from typing import List, Dict, Optional
import base64
from io import BytesIO

st.set_page_config(
    page_title="Manus File Manager",
    page_icon="📁",
    layout="wide"
)

# Custom CSS
st.markdown("""
<style>
    .file-card {
        padding: 1rem;
        border-radius: 0.5rem;
        border: 1px solid #e0e0e0;
        margin-bottom: 0.5rem;
        transition: all 0.3s;
    }
    .file-card:hover {
        box-shadow: 0 4px 6px rgba(0,0,0,0.1);
        border-color: #667eea;
    }
    .file-icon {
        font-size: 2rem;
        margin-bottom: 0.5rem;
    }
    .upload-zone {
        border: 2px dashed #667eea;
        border-radius: 0.5rem;
        padding: 2rem;
        text-align: center;
        background-color: #f8f9fa;
    }
</style>
""", unsafe_allow_html=True)

def get_manus_client(api_key: str) -> OpenAI:
    """Create and return Manus API client"""
    return OpenAI(
        base_url="https://api.manus.im",
        api_key="**",
        default_headers={"API_KEY": api_key},
    )

def upload_file_to_manus(client: OpenAI, file_data: bytes, filename: str) -> Optional[str]:
    """Upload a file to Manus and return file ID"""
    try:
        file_record = client.post(
            "/files",
            body={"filename": filename},
            cast_to=object
        )
        
        upload_response = requests.put(file_record['upload_url'], data=file_data)
        upload_response.raise_for_status()
        
        return file_record['id']
    except Exception as e:
        st.error(f"Error uploading {filename}: {str(e)}")
        return None

def get_file_icon(filename: str) -> str:
    """Return an emoji icon based on file extension"""
    ext = filename.split('.')[-1].lower()
    
    icon_map = {
        'pdf': '📕',
        'docx': '📘', 'doc': '📘',
        'txt': '📄', 'md': '📄',
        'csv': '📊', 'xlsx': '📊', 'xls': '📊',
        'json': '📋',
        'png': '🖼️', 'jpg': '🖼️', 'jpeg': '🖼️', 'gif': '🖼️', 'webp': '🖼️',
        'py': '🐍', 'js': '📜', 'html': '🌐', 'css': '🎨',
        'zip': '🗜️', 'tar': '🗜️', 'gz': '🗜️'
    }
    
    return icon_map.get(ext, '📎')

def format_file_size(bytes: int) -> str:
    """Format file size in human-readable format"""
    for unit in ['B', 'KB', 'MB', 'GB']:
        if bytes < 1024.0:
            return f"{bytes:.1f} {unit}"
        bytes /= 1024.0
    return f"{bytes:.1f} TB"

def analyze_files(files: List) -> Dict:
    """Analyze files and return statistics"""
    if not files:
        return {}
    
    analysis = {
        'total_files': len(files),
        'by_status': {},
        'by_type': {},
        'total_size': 0,
        'files_by_date': {}
    }
    
    for file in files:
        # Count by status
        status = getattr(file, 'status', 'unknown')
        analysis['by_status'][status] = analysis['by_status'].get(status, 0) + 1
        
        # Count by type
        ext = file.filename.split('.')[-1].lower() if '.' in file.filename else 'other'
        analysis['by_type'][ext] = analysis['by_type'].get(ext, 0) + 1
        
        # Files by date
        date = datetime.fromtimestamp(int(file.created_at)).date()
        analysis['files_by_date'][date] = analysis['files_by_date'].get(date, 0) + 1
    
    return analysis

# Initialize session state
if 'selected_files' not in st.session_state:
    st.session_state.selected_files = []
if 'upload_history' not in st.session_state:
    st.session_state.upload_history = []

# Header
st.title("📁 Manus File Manager")
st.caption("Upload, organize, and manage files for your Manus AI tasks")

# Sidebar
with st.sidebar:
    st.header("⚙️ Configuration")
    api_key = st.text_input("Manus API Key", type="password")
    
    if api_key:
        st.success("✓ API key configured")
    
    st.divider()
    
    st.header("📊 Filters & Sort")
    
    # Sort options
    sort_by = st.selectbox(
        "Sort by",
        ["Date (Newest)", "Date (Oldest)", "Name (A-Z)", "Name (Z-A)", "Size (Largest)", "Size (Smallest)"]
    )
    
    # Filter by status
    status_filter = st.multiselect(
        "File Status",
        ["uploaded", "processing", "ready", "error"],
        default=["uploaded", "ready"]
    )
    
    # Filter by type
    type_filter = st.multiselect(
        "File Type",
        ["pdf", "docx", "txt", "csv", "xlsx", "json", "images", "code"],
        help="Filter by file extension"
    )
    
    st.divider()
    
    st.header("⚡ Bulk Actions")
    
    if st.session_state.selected_files:
        st.info(f"{len(st.session_state.selected_files)} files selected")
        
        if st.button("🗑️ Delete Selected", type="secondary"):
            st.warning("Confirm bulk deletion")
    
    st.divider()
    
    st.header("ℹ️ Info")
    st.caption("Files are automatically deleted after 48 hours")
    st.caption("Max file size: 100MB")

if not api_key:
    st.warning("⚠️ Please enter your Manus API key in the sidebar")
    st.info("""
    ### Getting Started
    1. Sign up at [manus.im](https://manus.im)
    2. Get your API key from the [dashboard](https://manus.im/app?show_settings=integrations&app_name=api)
    3. Enter it in the sidebar to manage your files
    
    ### File Support
    - **Documents:** PDF, DOCX, TXT, MD
    - **Data:** CSV, XLSX, JSON
    - **Images:** PNG, JPG, GIF, WEBP
    - **Code:** PY, JS, HTML, CSS
    - **Archives:** ZIP, TAR, GZ
    """)
    
else:
    client = get_manus_client(api_key)
    
    # Create tabs
    tab1, tab2, tab3, tab4 = st.tabs(["📤 Upload", "📋 Manage Files", "📊 Analytics", "📚 Upload History"])
    
    # Upload Tab
    with tab1:
        st.header("📤 Upload Files")
        
        col1, col2 = st.columns([2, 1])
        
        with col1:
            uploaded_files = st.file_uploader(
                "Choose files to upload",
                accept_multiple_files=True,
                type=['pdf', 'docx', 'txt', 'md', 'csv', 'xlsx', 'json', 'png', 'jpg', 'jpeg', 'gif', 'webp', 'py', 'js', 'html', 'css', 'zip'],
                help="Select one or more files to upload to Manus"
            )
            
            if uploaded_files:
                st.success(f"✓ {len(uploaded_files)} file(s) selected")
                
                # File preview
                with st.expander("Preview selected files"):
                    for file in uploaded_files:
                        col_a, col_b, col_c = st.columns([1, 3, 2])
                        with col_a:
                            st.markdown(get_file_icon(file.name))
                        with col_b:
                            st.markdown(f"**{file.name}**")
                        with col_c:
                            st.caption(format_file_size(file.size))
                
                # Upload button
                upload_col1, upload_col2 = st.columns([1, 1])
                
                with upload_col1:
                    if st.button("📤 Upload All Files", type="primary", use_container_width=True):
                        progress_bar = st.progress(0)
                        status_text = st.empty()
                        
                        uploaded_count = 0
                        upload_results = []
                        
                        for idx, file in enumerate(uploaded_files):
                            status_text.text(f"Uploading {file.name}...")
                            
                            file_data = file.read()
                            file_id = upload_file_to_manus(client, file_data, file.name)
                            
                            if file_id:
                                uploaded_count += 1
                                upload_results.append({
                                    'filename': file.name,
                                    'file_id': file_id,
                                    'size': len(file_data),
                                    'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                                    'status': 'success'
                                })
                                st.success(f"✅ {file.name}")
                            else:
                                upload_results.append({
                                    'filename': file.name,
                                    'file_id': None,
                                    'size': len(file_data),
                                    'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                                    'status': 'failed'
                                })
                            
                            progress_bar.progress((idx + 1) / len(uploaded_files))
                        
                        status_text.success(f"✅ Uploaded {uploaded_count}/{len(uploaded_files)} files")
                        
                        # Save to history
                        st.session_state.upload_history.extend(upload_results)
                
                with upload_col2:
                    if st.button("🔄 Clear Selection", use_container_width=True):
                        st.rerun()
        
        with col2:
            st.markdown("### 💡 Tips")
            st.markdown("""
            - Upload multiple files at once
            - Supported: documents, images, code, data files
            - Max size: 100MB per file
            - Files expire after 48 hours
            - Use files in chat conversations
            """)
    
    # Manage Files Tab
    with tab2:
        st.header("📋 Your Files")
        
        col1, col2, col3 = st.columns([2, 1, 1])
        
        with col1:
            search_query = st.text_input("🔍 Search files", placeholder="Search by filename...")
        
        with col2:
            view_mode = st.selectbox("View", ["Grid", "List", "Detailed"])
        
        with col3:
            if st.button("🔄 Refresh Files", type="primary"):
                st.rerun()
        
        # Fetch files
        try:
            files_response = client.files.list()
            
            if files_response.data:
                files = files_response.data
                
                # Apply search filter
                if search_query:
                    files = [f for f in files if search_query.lower() in f.filename.lower()]
                
                # Apply status filter
                if status_filter:
                    files = [f for f in files if f.status in status_filter]
                
                # Apply type filter
                if type_filter:
                    filtered = []
                    for f in files:
                        ext = f.filename.split('.')[-1].lower() if '.' in f.filename else ''
                        if ext in type_filter or (ext in ['png', 'jpg', 'jpeg', 'gif', 'webp'] and 'images' in type_filter):
                            filtered.append(f)
                    files = filtered
                
                # Sort files
                if "Newest" in sort_by:
                    files = sorted(files, key=lambda x: int(x.created_at), reverse=True)
                elif "Oldest" in sort_by:
                    files = sorted(files, key=lambda x: int(x.created_at))
                elif "A-Z" in sort_by:
                    files = sorted(files, key=lambda x: x.filename)
                elif "Z-A" in sort_by:
                    files = sorted(files, key=lambda x: x.filename, reverse=True)
                
                st.success(f"Found {len(files)} file(s)")
                
                # Display files based on view mode
                if view_mode == "Grid":
                    # Grid view - 3 columns
                    cols = st.columns(3)
                    for idx, file in enumerate(files):
                        with cols[idx % 3]:
                            with st.container():
                                st.markdown(f"<div class='file-icon'>{get_file_icon(file.filename)}</div>", unsafe_allow_html=True)
                                st.markdown(f"**{file.filename}**")
                                st.caption(f"ID: {file.id[:12]}...")
                                st.caption(f"Status: {file.status}")
                                st.caption(datetime.fromtimestamp(int(file.created_at)).strftime('%Y-%m-%d %H:%M'))
                                
                                col_a, col_b = st.columns(2)
                                with col_a:
                                    if st.button("📋", key=f"copy_{file.id}", help="Copy ID"):
                                        st.code(file.id)
                                with col_b:
                                    if st.button("🗑️", key=f"del_{file.id}", help="Delete"):
                                        try:
                                            client.files.delete(file_id=file.id)
                                            st.success("Deleted!")
                                            st.rerun()
                                        except Exception as e:
                                            st.error(f"Error: {str(e)}")
                
                elif view_mode == "List":
                    # List view
                    for file in files:
                        col1, col2, col3, col4 = st.columns([1, 4, 2, 1])
                        
                        with col1:
                            st.markdown(get_file_icon(file.filename))
                        
                        with col2:
                            st.markdown(f"**{file.filename}**")
                            st.caption(f"ID: {file.id[:20]}...")
                        
                        with col3:
                            st.caption(f"Status: {file.status}")
                            st.caption(datetime.fromtimestamp(int(file.created_at)).strftime('%Y-%m-%d %H:%M'))
                        
                        with col4:
                            if st.button("🗑️", key=f"delete_{file.id}"):
                                try:
                                    client.files.delete(file_id=file.id)
                                    st.success("Deleted!")
                                    st.rerun()
                                except Exception as e:
                                    st.error(f"Error: {str(e)}")
                        
                        st.divider()
                
                elif view_mode == "Detailed":
                    # Detailed view
                    for file in files:
                        with st.expander(f"{get_file_icon(file.filename)} {file.filename}"):
                            col1, col2 = st.columns([3, 1])
                            
                            with col1:
                                st.markdown(f"**File ID:** `{file.id}`")
                                st.markdown(f"**Filename:** {file.filename}")
                                st.markdown(f"**Status:** {file.status}")
                                st.markdown(f"**Created:** {datetime.fromtimestamp(int(file.created_at)).strftime('%Y-%m-%d %H:%M:%S')}")
                                
                                # Calculate expiry
                                created = datetime.fromtimestamp(int(file.created_at))
                                expires = created + timedelta(hours=48)
                                time_left = expires - datetime.now()
                                
                                if time_left.total_seconds() > 0:
                                    hours_left = int(time_left.total_seconds() / 3600)
                                    st.markdown(f"**Expires in:** {hours_left} hours")
                                else:
                                    st.warning("⚠️ File expired")
                            
                            with col2:
                                if st.button("📋 Copy ID", key=f"copy_detailed_{file.id}", use_container_width=True):
                                    st.code(file.id)
                                
                                if st.button("🗑️ Delete", key=f"delete_detailed_{file.id}", use_container_width=True):
                                    try:
                                        client.files.delete(file_id=file.id)
                                        st.success("Deleted!")
                                        st.rerun()
                                    except Exception as e:
                                        st.error(f"Error: {str(e)}")
            else:
                st.info("No files found. Upload some files to get started!")
                
        except Exception as e:
            st.error(f"Error fetching files: {str(e)}")
    
    # Analytics Tab
    with tab3:
        st.header("📊 File Analytics")
        
        try:
            files_response = client.files.list()
            
            if files_response.data:
                analysis = analyze_files(files_response.data)
                
                # Metrics
                col1, col2, col3 = st.columns(3)
                
                with col1:
                    st.metric("Total Files", analysis['total_files'])
                
                with col2:
                    ready_files = analysis['by_status'].get('ready', 0)
                    st.metric("Ready Files", ready_files)
                
                with col3:
                    unique_types = len(analysis['by_type'])
                    st.metric("File Types", unique_types)
                
                # Charts
                col1, col2 = st.columns(2)
                
                with col1:
                    # Files by status
                    if analysis['by_status']:
                        fig = px.pie(
                            values=list(analysis['by_status'].values()),
                            names=list(analysis['by_status'].keys()),
                            title="Files by Status"
                        )
                        st.plotly_chart(fig, use_container_width=True)
                
                with col2:
                    # Files by type
                    if analysis['by_type']:
                        fig = px.bar(
                            x=list(analysis['by_type'].keys()),
                            y=list(analysis['by_type'].values()),
                            title="Files by Type",
                            labels={'x': 'File Type', 'y': 'Count'}
                        )
                        st.plotly_chart(fig, use_container_width=True)
                
                # Files over time
                if analysis['files_by_date']:
                    dates = sorted(analysis['files_by_date'].keys())
                    counts = [analysis['files_by_date'][d] for d in dates]
                    
                    fig = px.line(
                        x=dates,
                        y=counts,
                        title="Files Uploaded Over Time",
                        labels={'x': 'Date', 'y': 'Number of Files'}
                    )
                    st.plotly_chart(fig, use_container_width=True)
            else:
                st.info("No files to analyze. Upload some files first!")
                
        except Exception as e:
            st.error(f"Error generating analytics: {str(e)}")
    
    # Upload History Tab
    with tab4:
        st.header("📚 Upload History")
        
        if st.session_state.upload_history:
            st.success(f"{len(st.session_state.upload_history)} files in history")
            
            # Create dataframe
            df = pd.DataFrame(st.session_state.upload_history)
            
            # Display as table
            st.dataframe(
                df,
                use_container_width=True,
                hide_index=True,
                column_config={
                    "filename": "File Name",
                    "file_id": "File ID",
                    "size": st.column_config.NumberColumn("Size (bytes)", format="%d"),
                    "timestamp": "Upload Time",
                    "status": st.column_config.TextColumn("Status")
                }
            )
            
            # Export history
            col1, col2, col3 = st.columns(3)
            
            with col1:
                if st.button("📥 Export as CSV"):
                    csv = df.to_csv(index=False)
                    st.download_button(
                        "Download CSV",
                        csv,
                        f"upload_history_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
                        "text/csv"
                    )
            
            with col2:
                if st.button("🗑️ Clear History"):
                    st.session_state.upload_history = []
                    st.rerun()
        else:
            st.info("No upload history yet. Upload some files to see them here!")

# Footer
st.divider()
st.caption("Built with Streamlit and Manus API | [Documentation](https://docs.manus.im)")
