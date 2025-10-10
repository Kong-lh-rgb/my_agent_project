import os
from dotenv import load_dotenv
load_dotenv()

OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

EASY_MODEL_NAME= "gpt-4o-mini"
SMART_MODEL_NAME = "gpt-4o"

SEARCH_API_KEY = os.getenv("TAVILY_API_KEY")
