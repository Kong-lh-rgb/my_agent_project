from core import config
from langchain_core.tools import tool
import requests
from bs4 import BeautifulSoup


@tool(description="访问一个网页链接，返回网页的文本内容。输入应该是一个有效的URL。")
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
