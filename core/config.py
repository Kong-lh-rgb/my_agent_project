import os
from dotenv import load_dotenv
load_dotenv()

OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
JWT_SECRET_KEY = os.getenv("JWT_SECRET_KEY")
EASY_MODEL_NAME= "gpt-4o-mini"
SMART_MODEL_NAME = "gpt-4o"
EMBEDDING_MODEL_NAME = "text-embedding-3-small"
SEARCH_API_KEY = os.getenv("TAVILY_API_KEY")

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT_FILE_PATH = os.path.join(PROJECT_ROOT, "outputs")

DB_CONFIG = {
    'host':'localhost',
    'user':'root',
    'password':'abc123',
    'database':'agent_chat_db',
}