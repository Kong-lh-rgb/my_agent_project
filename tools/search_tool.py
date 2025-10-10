from core import config
from langchain_core.tools import tool
from langchain_tavily import TavilySearch

search_tool = TavilySearch()