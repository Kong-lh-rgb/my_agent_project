# 负责将信息整理并写入文件的智能体
from typing import Dict, Any, List
from core.llm_provider import get_llm
from core.prompt_templates import WRITER_PROMPT
from core import config
from tools.save_file_tool import save_to_file
from tools.generate_filename_tool import generate_filename
from langchain.agents import AgentExecutor, create_openai_tools_agent
from langchain_core.documents import Document
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

def _create_writer_agent_executor():
    """
    【内部函数】创建一个可复用的 writer agent executor。
    """
    tools = [save_to_file, generate_filename]
    llm = get_llm(smart=False)
    agent = create_openai_tools_agent(llm, tools, WRITER_PROMPT)
    agent_executor = AgentExecutor(agent=agent, tools=tools, verbose=True)
    return agent_executor


_writer_agent_executor = _create_writer_agent_executor()

def writer_process(state: Dict[str, Any]):
    """
        【优化后的节点函数】
        负责将信息整理并写入文件的智能体。
        它根据提供的资料和用户问题，生成一份结构清晰，内容详实的文档。
        """
    user_input = state["input"]
    documents = state["documents"]
    doc_details = "\n\n".join([
        f"--- 相关资料 {i + 1} ---\n{doc.page_content}"
        for i, doc in enumerate(documents)
    ])


    result = _writer_agent_executor.invoke({
        "input": user_input,
        "details": doc_details
    })

    return result

# if __name__ == '__main__':
#     # 模拟一个包含检索结果的 state
#     test_state = {
#         "input": "小b的父母是谁",
#         "documents": [
#             Document(page_content="小a是小b的爸爸"),
#             Document(page_content="小c是小b的妈妈"),
#         ]
#     }
#
#     # 运行智能体节点
#     final_result = create_writer_agent(test_state)
#
#     print("\n" + "="*20 + " AGENT FINAL OUTPUT " + "="*20 + "\n")
#     print(final_result)
