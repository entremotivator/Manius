import streamlit as st
import time
import base64
import requests
from openai import OpenAI
from datetime import datetime
import json
import pandas as pd
from typing import List, Dict, Optional

# Page configuration
st.set_page_config(
    page_title="Manus AI Assistant",
    page_icon="🤖",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS for better styling
st.markdown("""
<style>
    .stApp {
        max-width: 100%;
    }
    .chat-message {
        padding: 1.5rem;
        border-radius: 0.5rem;
        margin-bottom: 1rem;
        border: 1px solid #e0e0e0;
    }
    .user-message {
        background-color: #f0f2f6;
    }
    .assistant-message {
        background-color: #ffffff;
    }
    .task-stats {
        padding: 1rem;
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        border-radius: 0.5rem;
        color: white;
        margin-bottom: 1rem;
    }
    .file-badge {
        display: inline-block;
        padding: 0.25rem 0.75rem;
        background-color: #e3f2fd;
        border-radius: 1rem;
        margin: 0.25rem;
        font-size: 0.875rem;
    }
    .metric-card {
        background-color: #f8f9fa;
        padding: 1rem;
        border-radius: 0.5rem;
        border-left: 4px solid #667eea;
    }
    .status-badge {
        padding: 0.25rem 0.75rem;
        border-radius: 1rem;
        font-weight: 600;
        font-size: 0.875rem;
    }
    .status-completed {
        background-color: #d4edda;
        color: #155724;
    }
    .status-running {
        background-color: #fff3cd;
        color: #856404;
    }
    .status-error {
        background-color: #f8d7da;
        color: #721c24;
    }
</style>
""", unsafe_allow_html=True)

# Initialize session state
if 'messages' not in st.session_state:
    st.session_state.messages = []
if 'current_task_id' not in st.session_state:
    st.session_state.current_task_id = None
if 'uploaded_files' not in st.session_state:
    st.session_state.uploaded_files = []
if 'conversation_history' not in st.session_state:
    st.session_state.conversation_history = []
if 'total_credits_used' not in st.session_state:
    st.session_state.total_credits_used = 0
if 'task_count' not in st.session_state:
    st.session_state.task_count = 0
if 'api_key' not in st.session_state:
    st.session_state.api_key = ""

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
        st.error(f"Error uploading file {filename}: {str(e)}")
        return None

def create_task(
    client: OpenAI,
    user_input: str,
    uploaded_file_ids: Optional[List[str]] = None,
    image_url: Optional[str] = None,
    agent_profile: str = "quality",
    previous_task_id: Optional[str] = None,
    timeout_seconds: int = 300
):
    """Create a new task with Manus API"""
    content = [{"type": "input_text", "text": user_input}]
    
    if uploaded_file_ids:
        for file_id in uploaded_file_ids:
            content.append({"type": "input_file", "file_id": file_id})
    
    if image_url:
        content.append({"type": "input_image", "image_url": image_url})
    
    try:
        extra_body = {
            "task_mode": "agent",
            "agent_profile": agent_profile,
            "timeout_seconds": timeout_seconds,
        }
        
        if previous_task_id:
            extra_body["task_id"] = previous_task_id
        
        response = client.responses.create(
            input=[{"role": "user", "content": content}],
            extra_body=extra_body
        )
        
        return response
    except Exception as e:
        st.error(f"Error creating task: {str(e)}")
        return None

def poll_task_status(client: OpenAI, task_id: str, placeholder) -> Optional[object]:
    """Poll task status until completion with enhanced progress tracking"""
    with placeholder.container():
        col1, col2 = st.columns([3, 1])
        
        with col1:
            progress_bar = st.progress(0)
            status_text = st.empty()
        
        with col2:
            elapsed_time = st.empty()
        
        start_time = time.time()
        poll_count = 0
        
        while True:
            try:
                task_update = client.responses.retrieve(response_id=task_id)
                current_status = task_update.status
                
                elapsed = int(time.time() - start_time)
                elapsed_time.metric("Elapsed", f"{elapsed}s")
                
                if current_status == "completed":
                    progress_bar.progress(100)
                    status_text.success(f"✅ Task completed in {elapsed}s")
                    return task_update
                elif current_status == "error":
                    progress_bar.progress(100)
                    status_text.error("❌ Task encountered an error")
                    return task_update
                elif current_status == "pending":
                    progress_bar.progress(75)
                    status_text.warning("⏸️ Task pending user input")
                    return task_update
                else:
                    progress = min(50 + (poll_count * 2), 95)
                    progress_bar.progress(progress)
                    status_text.info(f"⏳ Processing... ({current_status})")
                
                poll_count += 1
                time.sleep(3)
                
            except Exception as e:
                status_text.error(f"Error checking status: {str(e)}")
                return None

def display_task_output(task_response, show_metadata: bool = True):
    """Display task output messages with enhanced formatting"""
    if not task_response or not hasattr(task_response, 'output'):
        return
    
    for message in task_response.output:
        if message.role == "assistant":
            with st.chat_message("assistant"):
                for content_item in message.content:
                    if hasattr(content_item, 'text') and content_item.text:
                        st.markdown(content_item.text)
                    elif hasattr(content_item, 'type') and content_item.type == 'output_file':
                        st.info(f"📄 **File Generated:** {content_item.fileName}")
                        if content_item.fileUrl:
                            st.markdown(f"[📥 Download {content_item.fileName}]({content_item.fileUrl})")
                
                if show_metadata and hasattr(task_response, 'metadata'):
                    with st.expander("📊 Task Details"):
                        col1, col2, col3 = st.columns(3)
                        with col1:
                            st.metric("Task ID", task_response.id[:12] + "...")
                        with col2:
                            credits = task_response.metadata.get('credit_usage', 'N/A')
                            st.metric("Credits Used", credits)
                        with col3:
                            st.metric("Status", task_response.status.upper())

def export_conversation_history(messages: List[Dict], format: str = "json") -> str:
    """Export conversation history in different formats"""
    if format == "json":
        return json.dumps(messages, indent=2)
    elif format == "markdown":
        md_content = "# Manus AI Conversation History\n\n"
        for msg in messages:
            role = msg['role'].upper()
            content = msg['content']
            timestamp = msg.get('timestamp', '')
            md_content += f"## {role}\n*{timestamp}*\n\n{content}\n\n---\n\n"
        return md_content
    elif format == "txt":
        txt_content = ""
        for msg in messages:
            txt_content += f"{msg['role'].upper()}: {msg['content']}\n\n"
        return txt_content
    return ""

def save_conversation_to_history():
    """Save current conversation to history"""
    if st.session_state.messages:
        conversation = {
            'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
            'messages': st.session_state.messages.copy(),
            'task_count': st.session_state.task_count,
            'credits_used': st.session_state.total_credits_used
        }
        st.session_state.conversation_history.append(conversation)

# Sidebar Configuration
with st.sidebar:
    st.title("⚙️ Configuration")
    
    # API Key input with save option
    col1, col2 = st.columns([3, 1])
    with col1:
        api_key = st.text_input(
            "Manus API Key",
            type="password",
            value=st.session_state.api_key,
            help="Enter your Manus API key from manus.im"
        )
    with col2:
        if st.button("💾", help="Save API key"):
            st.session_state.api_key = api_key
            st.success("Saved!")
    
    st.divider()
    
    # Session Statistics
    if api_key:
        st.markdown("### 📊 Session Stats")
        col1, col2 = st.columns(2)
        with col1:
            st.metric("Tasks", st.session_state.task_count)
        with col2:
            st.metric("Credits", st.session_state.total_credits_used)
    
    st.divider()
    
    # Agent Configuration
    st.subheader("🤖 Agent Settings")
    
    agent_profile = st.selectbox(
        "Profile",
        ["quality", "speed"],
        help="Quality: More thorough reasoning\nSpeed: Faster responses"
    )
    
    timeout_seconds = st.slider(
        "Timeout (seconds)",
        min_value=60,
        max_value=600,
        value=300,
        step=30,
        help="Maximum time to wait for task completion"
    )
    
    show_task_metadata = st.checkbox("Show task details", value=True)
    auto_scroll = st.checkbox("Auto-scroll to bottom", value=True)
    
    st.divider()
    
    # File Upload Section
    st.subheader("📎 Upload Files")
    
    uploaded_files = st.file_uploader(
        "Attach files to conversation",
        accept_multiple_files=True,
        type=['pdf', 'docx', 'txt', 'md', 'csv', 'xlsx', 'json', 'png', 'jpg', 'jpeg', 'gif', 'webp', 'py', 'js', 'html', 'css'],
        help="Upload documents, spreadsheets, images, or code files"
    )
    
    if uploaded_files and api_key:
        if st.button("📤 Process All Uploads", type="primary"):
            client = get_manus_client(api_key)
            st.session_state.uploaded_files = []
            
            progress_container = st.container()
            with progress_container:
                upload_progress = st.progress(0)
                for idx, file in enumerate(uploaded_files):
                    with st.spinner(f"Uploading {file.name}..."):
                        file_data = file.read()
                        file_id = upload_file_to_manus(client, file_data, file.name)
                        if file_id:
                            st.session_state.uploaded_files.append({
                                'id': file_id,
                                'name': file.name,
                                'size': len(file_data),
                                'type': file.type
                            })
                            st.success(f"✓ {file.name}")
                    upload_progress.progress((idx + 1) / len(uploaded_files))
    
    # Display uploaded files
    if st.session_state.uploaded_files:
        st.success(f"📁 {len(st.session_state.uploaded_files)} file(s) ready")
        with st.expander("View uploaded files"):
            for file in st.session_state.uploaded_files:
                st.markdown(f"**{file['name']}** ({file['size'] / 1024:.1f} KB)")
        
        if st.button("🗑️ Clear Files"):
            st.session_state.uploaded_files = []
            st.rerun()
    
    st.divider()
    
    # Conversation Management
    st.subheader("💬 Conversation")
    
    col1, col2 = st.columns(2)
    
    with col1:
        if st.button("🔄 New Chat", use_container_width=True):
            save_conversation_to_history()
            st.session_state.messages = []
            st.session_state.current_task_id = None
            st.session_state.uploaded_files = []
            st.rerun()
    
    with col2:
        if st.button("📥 Export", use_container_width=True):
            if st.session_state.messages:
                export_format = st.selectbox("Format", ["json", "markdown", "txt"])
                exported = export_conversation_history(st.session_state.messages, export_format)
                st.download_button(
                    "Download",
                    exported,
                    f"conversation_{datetime.now().strftime('%Y%m%d_%H%M%S')}.{export_format}",
                    f"application/{export_format}"
                )
    
    # Conversation History
    if st.session_state.conversation_history:
        st.divider()
        st.subheader("📚 History")
        st.caption(f"{len(st.session_state.conversation_history)} saved conversations")
        
        for idx, conv in enumerate(reversed(st.session_state.conversation_history)):
            with st.expander(f"💬 {conv['timestamp']}"):
                st.caption(f"Tasks: {conv['task_count']} | Credits: {conv['credits_used']}")
                if st.button("Load", key=f"load_{idx}"):
                    save_conversation_to_history()
                    st.session_state.messages = conv['messages']
                    st.rerun()

# Main Content Area
st.title("🤖 Manus AI Assistant")
st.caption("Advanced AI agent powered by Manus API for complex reasoning and multi-step tasks")

if not api_key:
    # Welcome screen
    st.markdown("""
    ### 👋 Welcome to Manus AI Assistant
    
    Manus is an advanced AI agent platform designed for complex reasoning tasks that require:
    - Multi-step problem solving
    - Document analysis and processing  
    - Code generation and review
    - Data analysis and visualization
    - Research and information synthesis
    
    #### Getting Started
    
    1. **Sign up** at [manus.im](https://manus.im)
    2. **Generate API key** from your [dashboard](https://manus.im/app?show_settings=integrations&app_name=api)
    3. **Enter API key** in the sidebar configuration
    4. **Start chatting** with the AI assistant
    
    #### Features
    
    - 📎 File upload support (documents, images, code, spreadsheets)
    - 🔄 Multi-turn conversations with context preservation
    - ⚡ Choice between quality and speed profiles
    - 📊 Real-time task monitoring and progress tracking
    - 💾 Conversation history and export capabilities
    - 📈 Credit usage tracking
    """)
    
    st.info("💡 **Tip:** Store your API key for quick access by clicking the save button in the sidebar")
    
else:
    # Display chat messages
    chat_container = st.container()
    
    with chat_container:
        for idx, message in enumerate(st.session_state.messages):
            with st.chat_message(message["role"]):
                st.markdown(message["content"])
                
                # Show file attachments
                if "files" in message and message["files"]:
                    st.caption("📎 Attached files:")
                    for file in message["files"]:
                        st.markdown(f"`{file}`")
                
                # Show task metadata
                if "task_url" in message:
                    with st.expander("🔗 Task Info"):
                        st.markdown(f"[Open in Manus Dashboard]({message['task_url']})")
                        if "credits" in message:
                            st.caption(f"Credits used: {message['credits']}")
                        if "timestamp" in message:
                            st.caption(f"Completed: {message['timestamp']}")
    
    # Chat input
    user_input = st.chat_input("Ask me anything...", key="chat_input")
    
    if user_input:
        # Add timestamp to message
        timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        
        # Display user message
        with st.chat_message("user"):
            st.markdown(user_input)
            if st.session_state.uploaded_files:
                st.caption(f"📎 {len(st.session_state.uploaded_files)} file(s) attached")
        
        # Store user message
        user_message = {
            "role": "user",
            "content": user_input,
            "timestamp": timestamp
        }
        
        if st.session_state.uploaded_files:
            user_message["files"] = [f['name'] for f in st.session_state.uploaded_files]
        
        st.session_state.messages.append(user_message)
        
        # Create and process task
        client = get_manus_client(api_key)
        
        with st.spinner("🚀 Creating task..."):
            file_ids = [f['id'] for f in st.session_state.uploaded_files]
            
            response = create_task(
                client,
                user_input,
                uploaded_file_ids=file_ids if file_ids else None,
                agent_profile=agent_profile,
                previous_task_id=st.session_state.current_task_id,
                timeout_seconds=timeout_seconds
            )
            
            if response:
                st.session_state.current_task_id = response.id
                st.session_state.task_count += 1
                task_url = response.metadata.get('task_url', '')
                
                # Poll for completion
                placeholder = st.empty()
                completed_task = poll_task_status(client, response.id, placeholder)
                placeholder.empty()
                
                if completed_task:
                    # Display assistant response
                    display_task_output(completed_task, show_metadata=show_task_metadata)
                    
                    # Extract response text
                    assistant_text = ""
                    output_files = []
                    
                    if hasattr(completed_task, 'output'):
                        for message in completed_task.output:
                            if message.role == "assistant":
                                for content_item in message.content:
                                    if hasattr(content_item, 'text') and content_item.text:
                                        assistant_text += content_item.text + "\n"
                                    elif hasattr(content_item, 'type') and content_item.type == 'output_file':
                                        output_files.append(content_item.fileName)
                    
                    # Track credits
                    credits_used = 0
                    if hasattr(completed_task, 'metadata'):
                        credits_used = completed_task.metadata.get('credit_usage', 0)
                        st.session_state.total_credits_used += credits_used
                    
                    # Store assistant message
                    assistant_message = {
                        "role": "assistant",
                        "content": assistant_text.strip() if assistant_text else "✅ Task completed successfully",
                        "task_url": task_url,
                        "credits": credits_used,
                        "timestamp": datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                    }
                    
                    if output_files:
                        assistant_message["output_files"] = output_files
                    
                    st.session_state.messages.append(assistant_message)
                    
                    # Clear uploaded files
                    st.session_state.uploaded_files = []
                    
                    st.rerun()

# Footer with quick tips
st.divider()

col1, col2, col3 = st.columns(3)

with col1:
    st.caption("📚 [Documentation](https://docs.manus.im)")

with col2:
    st.caption("💡 [API Reference](https://docs.manus.im/api-reference)")

with col3:
    st.caption("🐛 [Report Issue](https://github.com/manus-im)")

# Quick tips expander
with st.expander("💡 Quick Tips"):
    st.markdown("""
    **Effective Prompting:**
    - Be specific and provide context
    - Break complex tasks into steps
    - Upload relevant files for better analysis
    
    **File Support:**
    - Documents: PDF, DOCX, TXT, MD
    - Data: CSV, XLSX, JSON
    - Images: PNG, JPG, GIF, WEBP
    - Code: PY, JS, HTML, CSS
    
    **Best Practices:**
    - Use quality profile for complex reasoning tasks
    - Use speed profile for quick queries
    - Keep conversations focused on related topics
    - Export important conversations for future reference
    """)
