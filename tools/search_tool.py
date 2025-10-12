import textwrap

from core import config
from langchain_core.tools import tool
from langchain_tavily import TavilySearch
import requests
from bs4 import BeautifulSoup

# agent使用tavily工具搜索用户输入的相关网页链接，
# agent使用web_tool工具访问网页链接，清洗获得的文本内容
# 进入下一个结点rag存入chromedb，
# 进入检索生成结点，模型检索数据库生成content
# 进入writer结点大模型根据content输出报告到本地

search_tool = TavilySearch(max_results=3)


@tool
def web_tool(url: str):
    """
    使用requests库访问网页链接，返回网页的文本内容。
    """
    try:
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        }

        response = requests.get(url,headers=headers, timeout=10)
        response.raise_for_status()  # 确保请求成功

        response.encoding = response.apparent_encoding

        html_content = response.text

        soup = BeautifulSoup(html_content, 'html.parser')

        # 提取网页中的文本内容
        for script in soup(["script", "style"]):
            script.decompose()
        for tag in soup(['script', 'style', 'noscript', 'nav', 'footer', 'header', 'form', 'aside','ul','img','ol','li','video']):
            tag.decompose()
        text = soup.get_text(separator=' ',strip=True)
        return text

    except requests.RequestException as e:
        return f"无法访问该网页: {e}"

# res = web_tool("https://www.un.org/zh/global-issues/artificial-intelligence")
# formatted = textwrap.fill(res,80)
# print(formatted)
