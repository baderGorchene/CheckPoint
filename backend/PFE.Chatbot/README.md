# CheckPoint Chatbot

AI assistant for the CheckPoint workplace management system.  
Uses **Ollama** (gemma4) for reasoning and **MCP** (Model Context Protocol) for database access via function calling.

## Prerequisites

| Requirement | Version |
|---|---|
| Python | 3.10+ |
| Ollama | Running locally with `gemma4:e4b` model |
| SQL Server | CheckPoint_DB must exist (run the .NET app once) |
| ODBC Driver | ODBC Driver 18 for SQL Server |

## Setup

```bash
cd PFE.Chatbot

# Create virtual environment
python -m venv venv
venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt
```

## Usage

### 1. Seed mock data (run once)
```bash
python seed_data.py
```

### 2. Start the chatbot
```bash
python chatbot.py
```

### Example queries
- "How many employees are in each department?"
- "Show me all pending leave requests"
- "What events are coming up?"
- "Tell me about Fatima Zahra"
- "Are there any active announcements?"
- "What are the overall company statistics?"

## Architecture

```
You ──► chatbot.py ──► Ollama (gemma4:e4b) ──► tool_calls
                                                    │
                                          MCP Client (stdio)
                                                    │
                                          mcp_db_server.py
                                                    │
                                          SQL Server (CheckPoint_DB)
```

## MCP Tools Available

| Tool | Description |
|---|---|
| `get_departments` | List departments with employee counts |
| `get_employees` | List employees, filter by department |
| `get_employee_details` | Get details for a specific employee |
| `get_leave_requests` | Leave requests, filter by status |
| `get_events` | Upcoming company events |
| `get_rooms` | All rooms with type and capacity |
| `get_announcements` | Active company announcements |
| `get_general_requests` | Support requests, filter by status |
| `get_statistics` | Overall company dashboard stats |
