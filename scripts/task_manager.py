"""
Advanced task management utility for Manus API
View, search, analyze, and manage all your tasks
"""

import streamlit as st
from openai import OpenAI
from datetime import datetime, timedelta
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from typing import List, Dict, Optional
import json

st.set_page_config(
    page_title="Manus Task Manager",
    page_icon="📋",
    layout="wide"
)

# Custom CSS
st.markdown("""
<style>
    .task-card {
        padding: 1rem;
        border-radius: 0.5rem;
        border: 1px solid #e0e0e0;
        margin-bottom: 0.5rem;
    }
    .task-card:hover {
        box-shadow: 0 4px 6px rgba(0,0,0,0.1);
        border-color: #667eea;
    }
    .metric-container {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        padding: 1.5rem;
        border-radius: 0.5rem;
        color: white;
    }
    .status-completed { color: #28a745; }
    .status-running { color: #ffc107; }
    .status-error { color: #dc3545; }
    .status-pending { color: #17a2b8; }
</style>
""", unsafe_allow_html=True)

def get_manus_client(api_key: str) -> OpenAI:
    """Create and return Manus API client"""
    return OpenAI(
        base_url="https://api.manus.im",
        api_key="**",
        default_headers={"API_KEY": api_key},
    )

def fetch_tasks(client: OpenAI, status_filter: List[str], limit: int, search_query: str = "") -> List[Dict]:
    """Fetch tasks from Manus API"""
    try:
        url = f"/v1/tasks?limit={limit}"
        
        if status_filter:
            for status in status_filter:
                url += f"&status={status}"
        
        if search_query:
            url += f"&query={search_query}"
        
        response = client.get(url, cast_to=object)
        return response.get('data', [])
    except Exception as e:
        st.error(f"Error fetching tasks: {str(e)}")
        return []

def get_task_details(client: OpenAI, task_id: str) -> Optional[object]:
    """Get detailed information about a specific task"""
    try:
        return client.responses.retrieve(response_id=task_id)
    except Exception as e:
        st.error(f"Error fetching task details: {str(e)}")
        return None

def delete_task(client: OpenAI, task_id: str) -> bool:
    """Delete a specific task"""
    try:
        client.responses.delete(response_id=task_id)
        return True
    except Exception as e:
        st.error(f"Error deleting task: {str(e)}")
        return False

def analyze_tasks(tasks: List[Dict]) -> Dict:
    """Analyze tasks and return statistics"""
    if not tasks:
        return {}
    
    df = pd.DataFrame(tasks)
    
    analysis = {
        'total': len(tasks),
        'by_status': df['status'].value_counts().to_dict() if 'status' in df else {},
        'total_credits': 0,
        'avg_credits': 0,
        'tasks_by_date': []
    }
    
    # Calculate credits
    if 'metadata' in df.columns:
        credits = []
        for metadata in df['metadata']:
            if isinstance(metadata, dict) and 'credit_usage' in metadata:
                try:
                    credits.append(float(metadata['credit_usage']))
                except (ValueError, TypeError):
                    pass
        
        if credits:
            analysis['total_credits'] = sum(credits)
            analysis['avg_credits'] = sum(credits) / len(credits)
    
    # Tasks by date
    if 'created_at' in df.columns:
        df['date'] = pd.to_datetime(df['created_at'], unit='s').dt.date
        analysis['tasks_by_date'] = df.groupby('date').size().to_dict()
    
    return analysis

# Header
st.title("📋 Manus Task Manager")
st.caption("Comprehensive task monitoring and management dashboard")

# API Key Input
with st.sidebar:
    st.header("⚙️ Configuration")
    api_key = st.text_input("Manus API Key", type="password")
    
    if api_key:
        st.success("✓ API key configured")
    
    st.divider()
    
    st.header("📊 Filters")
    
    # Status filter
    status_filter = st.multiselect(
        "Task Status",
        ["completed", "running", "pending", "error"],
        default=["completed", "running"],
        help="Filter tasks by their current status"
    )
    
    # Limit
    limit = st.number_input(
        "Tasks to fetch",
        min_value=1,
        max_value=100,
        value=50,
        help="Maximum number of tasks to retrieve"
    )
    
    # Search
    search_query = st.text_input(
        "🔍 Search",
        placeholder="Search tasks...",
        help="Search in task titles and content"
    )
    
    st.divider()
    
    # View options
    st.header("👁️ Display Options")
    
    view_mode = st.radio(
        "View Mode",
        ["Cards", "Table", "Timeline"],
        help="Choose how to display tasks"
    )
    
    show_metadata = st.checkbox("Show metadata", value=True)
    show_analytics = st.checkbox("Show analytics", value=True)
    
    st.divider()
    
    # Bulk actions
    st.header("⚡ Bulk Actions")
    
    if st.button("🗑️ Delete All Completed", type="secondary"):
        st.warning("This action will delete all completed tasks. Use with caution!")

if not api_key:
    st.warning("⚠️ Please enter your Manus API key in the sidebar")
    st.info("""
    ### Getting Started
    1. Sign up at [manus.im](https://manus.im)
    2. Get your API key from the [dashboard](https://manus.im/app?show_settings=integrations&app_name=api)
    3. Enter it in the sidebar to view your tasks
    """)
    
else:
    # Fetch tasks button
    if st.button("🔄 Fetch Tasks", type="primary"):
        with st.spinner("Fetching tasks..."):
            client = get_manus_client(api_key)
            tasks = fetch_tasks(client, status_filter, limit, search_query)
            st.session_state.tasks = tasks
            st.session_state.last_fetch = datetime.now()
    
    # Display tasks if available
    if 'tasks' in st.session_state and st.session_state.tasks:
        tasks = st.session_state.tasks
        
        # Analytics Section
        if show_analytics:
            st.header("📊 Analytics")
            analysis = analyze_tasks(tasks)
            
            # Metrics row
            col1, col2, col3, col4 = st.columns(4)
            
            with col1:
                st.metric("Total Tasks", analysis.get('total', 0))
            
            with col2:
                st.metric("Total Credits", f"{analysis.get('total_credits', 0):.2f}")
            
            with col3:
                st.metric("Avg Credits/Task", f"{analysis.get('avg_credits', 0):.2f}")
            
            with col4:
                completed = analysis.get('by_status', {}).get('completed', 0)
                total = analysis.get('total', 1)
                st.metric("Success Rate", f"{(completed/total*100):.1f}%")
            
            # Charts
            col1, col2 = st.columns(2)
            
            with col1:
                # Status distribution
                status_data = analysis.get('by_status', {})
                if status_data:
                    fig = px.pie(
                        values=list(status_data.values()),
                        names=list(status_data.keys()),
                        title="Tasks by Status",
                        color_discrete_sequence=px.colors.qualitative.Set3
                    )
                    st.plotly_chart(fig, use_container_width=True)
            
            with col2:
                # Tasks over time
                tasks_by_date = analysis.get('tasks_by_date', {})
                if tasks_by_date:
                    dates = list(tasks_by_date.keys())
                    counts = list(tasks_by_date.values())
                    fig = px.line(
                        x=dates,
                        y=counts,
                        title="Tasks Over Time",
                        labels={'x': 'Date', 'y': 'Number of Tasks'}
                    )
                    st.plotly_chart(fig, use_container_width=True)
            
            st.divider()
        
        # Task Display Section
        st.header(f"📋 Tasks ({len(tasks)})")
        
        if view_mode == "Cards":
            # Card view
            for task in tasks:
                task_id = task.get('id', 'Unknown')
                status = task.get('status', 'Unknown')
                title = task.get('title', 'Untitled Task')
                created_at = datetime.fromtimestamp(int(task.get('created_at', 0))).strftime('%Y-%m-%d %H:%M:%S')
                
                # Status styling
                status_class = f"status-{status}"
                status_emoji = {
                    'completed': '✅',
                    'running': '⏳',
                    'pending': '⏸️',
                    'error': '❌'
                }.get(status, '❓')
                
                with st.container():
                    col1, col2 = st.columns([4, 1])
                    
                    with col1:
                        st.markdown(f"### {status_emoji} {title}")
                        st.caption(f"Created: {created_at}")
                        st.code(f"ID: {task_id}", language=None)
                        
                        if show_metadata and task.get('metadata'):
                            metadata = task['metadata']
                            
                            meta_col1, meta_col2 = st.columns(2)
                            
                            with meta_col1:
                                if 'credit_usage' in metadata:
                                    st.metric("Credits", metadata['credit_usage'])
                            
                            with meta_col2:
                                if 'task_url' in metadata:
                                    st.markdown(f"[🔗 Open in Manus]({metadata['task_url']})")
                    
                    with col2:
                        st.markdown(f"**Status**")
                        st.markdown(f"<span class='{status_class}'>{status.upper()}</span>", unsafe_allow_html=True)
                        
                        # Action buttons
                        if st.button("👁️ View", key=f"view_{task_id}", use_container_width=True):
                            with st.spinner("Loading details..."):
                                task_details = get_task_details(client, task_id)
                                if task_details:
                                    st.session_state[f"details_{task_id}"] = task_details
                        
                        if st.button("🗑️ Delete", key=f"delete_{task_id}", use_container_width=True):
                            if delete_task(client, task_id):
                                st.success("Deleted!")
                                st.rerun()
                        
                        if st.button("📋 Copy ID", key=f"copy_{task_id}", use_container_width=True):
                            st.code(task_id)
                    
                    # Show details if loaded
                    if f"details_{task_id}" in st.session_state:
                        with st.expander("📄 Full Task Details", expanded=True):
                            task_details = st.session_state[f"details_{task_id}"]
                            
                            # Display output
                            if hasattr(task_details, 'output'):
                                st.subheader("💬 Conversation")
                                for msg in task_details.output:
                                    with st.chat_message(msg.role):
                                        for content in msg.content:
                                            if hasattr(content, 'text') and content.text:
                                                st.markdown(content.text)
                                            elif hasattr(content, 'type') and content.type == 'output_file':
                                                st.info(f"📄 {content.fileName}")
                                                if content.fileUrl:
                                                    st.markdown(f"[Download]({content.fileUrl})")
                            
                            # Raw JSON
                            with st.expander("🔍 Raw JSON"):
                                st.json(task_details.model_dump())
                            
                            if st.button("✖️ Close Details", key=f"close_{task_id}"):
                                del st.session_state[f"details_{task_id}"]
                                st.rerun()
                    
                    st.divider()
        
        elif view_mode == "Table":
            # Table view
            table_data = []
            for task in tasks:
                row = {
                    'ID': task.get('id', '')[:12] + '...',
                    'Title': task.get('title', 'Untitled'),
                    'Status': task.get('status', 'Unknown'),
                    'Created': datetime.fromtimestamp(int(task.get('created_at', 0))).strftime('%Y-%m-%d %H:%M'),
                    'Credits': task.get('metadata', {}).get('credit_usage', 'N/A') if isinstance(task.get('metadata'), dict) else 'N/A'
                }
                table_data.append(row)
            
            df = pd.DataFrame(table_data)
            st.dataframe(df, use_container_width=True, hide_index=True)
        
        elif view_mode == "Timeline":
            # Timeline view
            st.info("Timeline view - showing tasks chronologically")
            
            sorted_tasks = sorted(tasks, key=lambda x: int(x.get('created_at', 0)), reverse=True)
            
            for task in sorted_tasks:
                created_at = datetime.fromtimestamp(int(task.get('created_at', 0)))
                time_ago = datetime.now() - created_at
                
                if time_ago.days > 0:
                    time_str = f"{time_ago.days}d ago"
                elif time_ago.seconds > 3600:
                    time_str = f"{time_ago.seconds // 3600}h ago"
                else:
                    time_str = f"{time_ago.seconds // 60}m ago"
                
                status_emoji = {
                    'completed': '✅',
                    'running': '⏳',
                    'pending': '⏸️',
                    'error': '❌'
                }.get(task.get('status'), '❓')
                
                st.markdown(f"**{time_str}** {status_emoji} {task.get('title', 'Untitled')}")
                st.caption(f"ID: {task.get('id', '')[:16]}... | Status: {task.get('status', 'Unknown')}")
                st.divider()
        
        # Export section
        st.divider()
        col1, col2, col3 = st.columns(3)
        
        with col1:
            if st.button("📥 Export as JSON"):
                json_data = json.dumps(tasks, indent=2)
                st.download_button(
                    "Download JSON",
                    json_data,
                    f"manus_tasks_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json",
                    "application/json"
                )
        
        with col2:
            if st.button("📥 Export as CSV"):
                df = pd.DataFrame(tasks)
                csv_data = df.to_csv(index=False)
                st.download_button(
                    "Download CSV",
                    csv_data,
                    f"manus_tasks_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
                    "text/csv"
                )
        
        with col3:
            st.caption(f"Last fetched: {st.session_state.get('last_fetch', 'Never').strftime('%H:%M:%S') if hasattr(st.session_state.get('last_fetch', None), 'strftime') else 'Never'}")
    
    elif 'tasks' in st.session_state:
        st.info("No tasks found matching your criteria. Try adjusting the filters.")
    else:
        st.info("Click 'Fetch Tasks' to load your tasks")

# Footer
st.divider()
st.caption("Built with Streamlit and Manus API | [Documentation](https://docs.manus.im)")
