import os
from langchain_core.tools import tool
from core import config

@tool(description="将内容保存到指定文件路径。输入包括内容和文件路径，输出为确认信息。")
def save_to_file(content: str, filename: str):
    output_path = os.path.join(config.OUT_FILE_PATH, filename)
    with open(output_path, 'w', encoding='utf-8') as f:
        f.write(content)
        f.flush()
        os.fsync(f.fileno())

    success_message = f"文件已成功保存到: {output_path}"
    print(success_message)
    return success_message
