# from langchain_openai import ChatOpenAI
# from langchain.nodes import AgentExecutor,create_openai_tools_agent
# from core.prompt_templates import NAVIGATE_PROMPT
# from core.llm_provider import get_llm
#
# def create_manager_agent():
#     llm = get_llm(smart = False)
#     tools = []
#     prompt = NAVIGATE_PROMPT
#     agent = create_openai_tools_agent(llm,tools,prompt)
#     agent_executor = AgentExecutor(agent = agent,tools = tools,verbose=True)
#     return agent_executor
# if __name__ == "__main__":
#     res = create_manager_agent()
#     result = res.invoke({"input":"帮我看一下我的代码哪里有问题"})
#     print(result["output"])
#


from pydantic import BaseModel, Field
from typing import Literal
from core.prompt_templates import NAVIGATE_PROMPT
from core.llm_provider import get_llm

class RouteDecision(BaseModel):
    """根据用户的查询路由到正确的智能体。"""
    destination: Literal["research_agent", "code_agent", "writer_agent", "END"] = Field(
        description="根据用户问题选择的下一个目标智能体。如果任务完成或问题简单，则选择'END'。"
    )
    next_input: str = Field(description="传递给下一个智能体的具体任务指令。")


def create_manager_router_chain():
    """
    创建一个用于决策路由的链。
    它接收状态，并输出一个路由决策。
    """
    llm = get_llm(smart=False)

    structured_llm = llm.with_structured_output(RouteDecision)
    router_chain = NAVIGATE_PROMPT | structured_llm
    return router_chain


if __name__ == "__main__":
    manager_chain = create_manager_router_chain()

    from langchain_core.messages import HumanMessage

    result = manager_chain.invoke({
        "input": "帮我调研一下langgraph的最新特性，并写一份总结报告",
        "messages": [HumanMessage(content="帮我调研一下langgraph的最新特性，并写一份总结报告")]
    })
    print(f"下一步路由到: {result.destination}")
    print(f"传递给下一个Agent的任务: {result.next_input}")
