import io
import PyPDF2
import requests
import tiktoken
from bs4 import BeautifulSoup
from langchain_core.tools import tool


def _truncate_text_by_tokens(text: str, model_name: str = "cl100k_base", max_tokens: int = 12000) -> str:
    """
    使用 tiktoken 根据 token 数量截断文本。
    """
    try:
        encoding = tiktoken.get_encoding(model_name)
    except ValueError:
        # 如果模型名称无效，回退到 p50k_base
        encoding = tiktoken.get_encoding("p50k_base")

    tokens = encoding.encode(text)
    if len(tokens) > max_tokens:
        truncated_tokens = tokens[:max_tokens]
        return encoding.decode(truncated_tokens)
    return text


@tool(description="访问一个网页链接，返回网页的文本内容。输入应该是一个有效的URL。返回的文本内容会被截断以适应模型上下文长度。")
def web_tool(url: str):
    """
    使用requests库访问网页链接，判断内容类型，返回网页的文本内容。
    返回的文本会被截断以防止超出上下文长度限制。
    """
    try:
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        }

        response = requests.get(url, headers=headers, timeout=15)
        response.raise_for_status()

        content_type = response.headers.get('Content-Type', '').lower()
        raw_text = ""

        if 'application/pdf' in content_type:
            pdf_file = io.BytesIO(response.content)
            reader = PyPDF2.PdfReader(pdf_file)
            text_parts = []
            for page in reader.pages:
                page_text = page.extract_text()
                if page_text:
                    text_parts.append(page_text)
            raw_text = '\n'.join(text_parts)


        else:

            try:
                response.encoding = response.apparent_encoding
                html_content = response.text
            except Exception:
                response.encoding = 'utf-8'
                html_content = response.text

            soup = BeautifulSoup(html_content, 'html.parser')


            for tag in soup(['script', 'style', 'noscript', 'nav', 'footer', 'header', 'form', 'aside', 'ul', 'img', 'ol', 'li', 'video']):
                tag.decompose()

            raw_text = soup.get_text(separator=' ', strip=True)


        truncated_text = _truncate_text_by_tokens(raw_text)
        print(f"--- Web Tool: 原始字符数: {len(raw_text)}, 截断后字符数: {len(truncated_text)} ---")
        return truncated_text

    except requests.RequestException as e:
        return f"无法访问该网页: {e}"
    except Exception as e:
        return f"处理网页内容时发生未知错误: {e}"