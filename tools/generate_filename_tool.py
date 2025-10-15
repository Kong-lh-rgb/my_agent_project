from core.llm_provider import get_llm
from core.prompt_templates import FILENAME_PROMPT,FILE_EXTENSION_PROMPT
import re
from langchain_core.tools import tool


@tool(description="根据报告内容和用户输入生成合适的文件名和扩展名。输入包括用户的指令和报告的主要内容，输出为文件名和扩展名。")
def generate_filename(input: str, content: str) -> (str, str):
    llm = get_llm(smart = False)

    filename_chain = FILENAME_PROMPT | llm
    first_result = filename_chain.invoke({"report_content": content})
    filename = first_result.content.strip().lower()
    if not filename:
        filename = "default_report"

    ext_chain = FILE_EXTENSION_PROMPT | llm
    second_result = ext_chain.invoke({"input": input})
    extension = second_result.content.strip()
    if not extension.startswith("."):
        extension = '.' + re.sub(r'[^a-z0-9]', '', extension.lower())
    if len(extension) < 2:
        extension = ".md"
    return filename, extension
