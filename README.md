# Manus AI Streamlit Application

A comprehensive Streamlit application for interacting with the Manus API - an advanced AI agent platform for complex reasoning tasks, document analysis, and multi-step workflows.

## Features

- 🤖 **Interactive Chat Interface** - Natural conversation with Manus AI agents
- 📎 **File Upload Support** - Upload documents, spreadsheets, images, and code files
- 🔄 **Multi-turn Conversations** - Context-aware conversations across multiple requests
- 📋 **Task Management** - View, search, and manage all your tasks
- 📁 **File Management** - Upload, list, and delete files
- ⚙️ **Agent Profiles** - Choose between quality (thorough) or speed (fast) modes
- 💳 **Credit Tracking** - Monitor API credit usage per task

## Installation

1. Install Python 3.10 or higher

2. Install dependencies:
\`\`\`bash
pip install streamlit openai requests
\`\`\`

## Getting Started

1. **Get your API key:**
   - Sign up at [manus.im](https://manus.im)
   - Generate your API key from the [dashboard](https://manus.im/app?show_settings=integrations&app_name=api)

2. **Run the main application:**
\`\`\`bash
streamlit run app.py
\`\`\`

3. **Run additional utilities:**
\`\`\`bash
# Task Manager
streamlit run task_manager.py

# File Manager
streamlit run file_manager.py
\`\`\`

## Usage

### Main Chat Application

1. Enter your Manus API key in the sidebar
2. (Optional) Upload files you want to reference
3. Select your preferred agent profile (quality or speed)
4. Start chatting with the AI assistant
5. View task progress and results in real-time

### Task Manager

- View all your tasks with status filtering
- Search tasks by title or content
- Delete completed or unwanted tasks
- View detailed task information

### File Manager

- Upload files to reuse across multiple tasks
- View all uploaded files with status
- Delete files manually (auto-deleted after 48 hours)

## Supported File Types

**Documents:** PDF, DOCX, TXT, MD
**Spreadsheets:** CSV, XLSX
**Code:** JSON, YAML, Python, JavaScript, etc.
**Images:** PNG, JPEG, JPG, GIF, WebP

## Agent Profiles

- **Quality:** More thorough analysis and better results for complex tasks
- **Speed:** Faster responses for simpler queries

## Tips

- Use multi-turn conversations for complex workflows
- Upload files once and reference them across multiple tasks
- Monitor credit usage to manage costs
- Save important outputs before deleting tasks
- Files are automatically deleted after 48 hours

## API Documentation

For more details, visit the [Manus API Documentation](https://docs.manus.im)
\`\`\`

```text file="requirements.txt"
streamlit>=1.28.0
openai==1.100.2
requests>=2.31.0
