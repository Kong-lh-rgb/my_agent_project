from core import config
import io
import PyPDF2
from langchain_core.tools import tool
import requests
from bs4 import BeautifulSoup


@tool(description="访问一个网页链接，返回网页的文本内容。输入应该是一个有效的URL。")
def web_tool(url: str):
    """
    使用requests库访问网页链接，判断内容类型，返回网页的文本内容。
    """
    try:
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        }

        response = requests.get(url,headers=headers, timeout=10)
        response.raise_for_status()  # 确保请求成功

        content_type = response.headers.get('Content-Type', '').lower()
        if 'application/pdf' in content_type:
            # 使用 BytesIO 在内存中处理 PDF 内容，无需保存到本地
            pdf_file = io.BytesIO(response.content)
            reader = PyPDF2.PdfReader(pdf_file)
            text = ''
            for page in reader.pages:
                page_text = page.extract_text()
                if page_text:
                    text += page_text + '\n'
            return text.strip()

        # 如果不是PDF，则作为HTML处理
        else:
            response.encoding = response.apparent_encoding
            html_content = response.text
            soup = BeautifulSoup(html_content, 'html.parser')

            # 移除不需要的标签
            for tag in soup(
                    ['script', 'style', 'noscript', 'nav', 'footer', 'header', 'form', 'aside', 'ul', 'img', 'ol', 'li',
                     'video']):
                tag.decompose()

            text = soup.get_text(separator=' ', strip=True)
            return text

    except requests.RequestException as e:
        return f"无法访问该网页: {e}"
