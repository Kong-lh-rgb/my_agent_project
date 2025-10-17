from core import config
from langchain_core.tools import tool
from langchain_tavily import TavilySearch


search_tool = TavilySearch(max_results=3,description="使用Tavily搜索相关网页链接。输入应为查询关键词")
