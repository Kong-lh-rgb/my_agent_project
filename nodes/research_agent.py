# from langchain_core.runnables import RunnablePassthrough
# from pydantic import BaseModel,Field
# from typing import Literal
# from core.llm_provider import get_llm
# from tools.search_tool import search_tool
# from core.prompt_templates import RESEARCH_PROMPT,DECISION_PROMPT
# from langchain.nodes import AgentExecutor,create_openai_tools_agent
#
#
# class choice(BaseModel):
#     """根据研究结果和用户问题，决定下一步行动"""
#     destination: Literal["writer_agent","END"] = Field(
#         description="如果用户要求生成报告或长文，选择 'writer_agent'。如果用户只是提问，选择 'END' 直接回答。"
#     )
#     response:str = Field(
#         description = "当 destination 为 'END' 时，这里是给用户的最终答案。"
#                       "当 destination 为 'writer_agent' 时，这里是传递给 writer_agent 的详细研究资料和指令。"
#
#     )
#
# DECISION_PROMPT = DECISION_PROMPT
#
# def create_research_agent():
#     """
#     负责处理需要深入研究和信息收集的任务。
#     它可以使用搜索工具来获取最新的信息，并进行分析和总结。
#     """
#     tools = [search_tool]
#     llm = get_llm(smart = False)
#     prompt = RESEARCH_PROMPT
#     agent = create_openai_tools_agent(llm,tools,prompt)
#     research_agent = AgentExecutor(agent=agent,tools=tools, verbose=True)
#
#     decision_llm = get_llm(smart = False)
#     structured_decision_llm = decision_llm.with_structured_output(choice)
#     decision_chain = DECISION_PROMPT | structured_decision_llm
#
#     last_chain = RunnablePassthrough.assign(
#         summary = research_agent | (lambda x: x['output'])
#     ) | decision_chain
#
#     return last_chain
# # if __name__ == "__main__":
# #     researcher = create_research_agent()
# #     result = researcher.invoke({"input":"马云是谁？"})
# #     print(result)
#
# if __name__ == "__main__":
#     researcher = create_research_agent()
#
#     print("\n--- 测试场景1: 用户只是提问 ---")
#     result1 = researcher.invoke({"input": "马云是谁？"})
#     print(f"决策目标: {result1.destination}")
#     print(f"最终回答: {result1.response}")
#
#     print("\n" + "="*20 + "\n")
#
#     print("--- 测试场景2: 用户要求生成报告 ---")
#     result2 = researcher.invoke({"input": "请帮我整理一份关于马云的详细报告。"})
#     print(f"决策目标: {result2.destination}")
#     print(f"传递给下一步的指令/资料: {result2.response}")
#

from core.llm_provider import get_llm
from tools.search_tool import search_tool
from tools.web_tool import web_tool
from core.prompt_templates import RESEARCH_PROMPT
from langchain.agents import AgentExecutor, create_openai_tools_agent


def _create_research_agent_executor():
    """
    【内部函数】创建一个拥有搜索和网页浏览能力的自主研究代理。
    """
    tools = [search_tool, web_tool]
    llm = get_llm(smart=False)
    agent = create_openai_tools_agent(llm, tools, RESEARCH_PROMPT)
    agent_executor = AgentExecutor(agent=agent, tools=tools, verbose=True, handle_parsing_errors=True)
    return agent_executor


_research_agent_executor = _create_research_agent_executor()

def research_process(state):
    """
    【优化后的节点函数】
    接受用户输入，进行信息检索和初步分析。
    """
    result = _research_agent_executor.invoke({"input": state["current_task"]})
    return {
        "raw_text": result["output"]
    }



# 后续把返回的长文本传递给rag存入chromedb

# if __name__ == "__main__":
#     researcher = create_research_agent()
#     question = "有什么关于openai的最新新闻？"
#     result = researcher.invoke({"input": question})
#     print(result)
