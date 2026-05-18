"""
Configuration for CheckPoint Chatbot.
Database and Ollama settings.
"""

# ── Database ──────────────────────────────────────────────
DB_SERVER = r"BUNSHEE\SQLEXPRESS"
DB_NAME = "CheckPoint_DB"
DB_DRIVER = "{ODBC Driver 18 for SQL Server}"

def get_connection_string() -> str:
    return (
        f"Driver={DB_DRIVER};"
        f"Server={DB_SERVER};"
        f"Database={DB_NAME};"
        f"Trusted_Connection=yes;"
        f"TrustServerCertificate=yes;"
    )

# ── Ollama ────────────────────────────────────────────────
OLLAMA_MODEL = "gemma4:e4b"
OLLAMA_HOST = "http://localhost:11434"
