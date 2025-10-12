from core import config
from langchain_core.tools import tool
from langchain_tavily import TavilySearch

# agent使用tavily工具搜索用户输入的相关网页链接，
# agent使用web_tool工具访问网页链接，清洗获得的文本内容
# 进入下一个结点rag存入chromedb，
# 进入检索生成结点，模型检索数据库生成content
# 进入writer结点大模型根据content输出报告到本地

search_tool = TavilySearch(max_results=3,description="使用Tavily搜索相关网页链接。输入应为查询关键词")
