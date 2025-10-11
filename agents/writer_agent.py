# 负责将信息整理并写入文件的智能体
import os
import re
from core.llm_provider import get_llm
from core.prompt_templates import WRITER_PROMPT,FILENAME_PROMPT,FILE_EXTENSION_PROMPT
from core import config

def generate_filname(input: str, content: str) -> (str, str):
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
    if len(extension) < 2:  # 如果扩展名无效，使用默认值
        extension = ".md"
    return filename, extension


# def generate_file_extension(input: str) -> str:
#     llm = get_llm(smart = False)
#     prompt = FILE_EXTENSION_PROMPT
#     extension_chain = prompt | llm
#     result = extension_chain.invoke({"input": input})
#     extension = result.content.strip().lower()
#     # 简单清理，确保是常见的扩展名
#     if re.match(r'^[a-z0-9]+$', extension):
#         return extension
#     return "md"  # 默认扩展名

def create_writer_agent():
    """
    负责将信息整理并写入文件的智能体。
    它根据提供的资料和用户问题，生成一份结构清晰，内容详实的文档。
    """
    llm = get_llm(smart=False)
    prompt = WRITER_PROMPT
    writer_agent = prompt | llm
    return writer_agent

def save_to_file(content: str, file_path: str):
    """将内容保存到指定文件"""
    dir_name = os.path.dirname(file_path)
    if dir_name:  # 确保目录名不为空
        os.makedirs(dir_name, exist_ok=True)
    with open(file_path, 'w', encoding='utf-8') as f:
        f.write(content)
    print(f"内容已保存到 {file_path}")

def run_writer_agent(input: str,details: str):
    writer_agent = create_writer_agent()
    result = writer_agent.invoke({"input": input, "details": details})
    return result.content

if __name__ == "__main__":
    input = "帮我写一份关于人工智能的报告"
    details = "本报告将围绕人工智能的发展历程、核心技术、应用场景、未来趋势以及面临的挑战进行阐述，内容包括技术原理、行业案例和政策分析。"

    print("生成报告中...")
    content = run_writer_agent(input, details)

    core_filename, file_extension = generate_filname(input,details)
    final_filename = f"{core_filename}{file_extension}"
    print(f"生成的文件名: {final_filename}")

    output_dir = config.OUT_FILE_PATH
    out_path = os.path.join(output_dir, final_filename)
    save_to_file(content, out_path)
