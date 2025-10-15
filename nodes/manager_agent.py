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
from langchain_core.messages import HumanMessage, AIMessage
from pydantic import BaseModel, Field
from typing import Literal
from core.prompt_templates import NAVIGATE_PROMPT
from core.llm_provider import get_llm
from langgraph.graph import StateGraph,START,END


MAX_MESSAGES_IN_CONTEXT = 4

class RouteDecision(BaseModel):
    """根据用户的查询路由到正确的智能体。"""
    destination: Literal["ask_user","writer_agent","research_agent", "code_agent", "qa_agent", "END"] = Field(
        description="根据用户问题选择的下一个目标智能体。如果任务完成或问题简单，则选择'END'。"
    )
    next_input: str = Field(description="为下一个节点准备的、经过重写的清晰任务指令")


def create_manager_router_chain():
    """
    创建一个用于决策路由的链。
    它接收状态，并输出一个路由决策。
    """
    llm = get_llm(smart=False)
    structured_llm = llm.with_structured_output(RouteDecision)
    router_chain = NAVIGATE_PROMPT | structured_llm
    return router_chain

def manager_process(state):
    print("---调用 Manager 节点，开始进行意图判断---")
    messages = state.get("messages", [])
    user_input = state["input"]

    # 检查是否在等待澄清
    if state.get("awaiting_clarification"):
        print("---处理用户对报告需求的澄清---")
        # 用户的 'y'/'n' 回答在 user_input 中
        choice = user_input.strip().lower()
        if choice == 'y':
            required_report = True
        elif choice == 'n':
            required_report = False
        else:
            # 如果用户输入无效，再次反问
            clarification_message = AIMessage(content="无效输入，请重新回答 'y' 或 'n'。")
            return {
                "messages": messages + [HumanMessage(content=user_input), clarification_message],
                "awaiting_clarification": True,  # 保持等待状态
                "next_node": END  # 结束当前轮次，等待用户再次输入
            }

        print(f"用户已澄清，是否需要报告: {required_report}")
        original_task = state["current_task"]  # 获取原始任务
        messages = state["messages"]

        return {
            "messages": messages + [HumanMessage(content=user_input)],
            "required_report": required_report,
            "awaiting_clarification": False,  # 重置等待状态
            "next_node": "research_agent",  # 澄清后继续正常流程
            "current_task": original_task  # 保持原始任务不变
        }

    messages = state.get("messages", []) + [HumanMessage(content=state["input"])]
    if not messages[-1].content:
        print("错误：最新的消息内容为空")
        return {"next_node": "END"}

    in_messages = messages[-MAX_MESSAGES_IN_CONTEXT:]
    manager_chain = create_manager_router_chain()
    res = manager_chain.invoke({
        "messages": in_messages,
        "input": user_input,
    })

    # 检查是否需要澄清
    # 这里的 'ask_user' 是一个假设的路由结果，你需要修改你的 manager_router_chain 来实现它
    if res.destination == "ask_user":
        print("---报告需求不明确，向用户反问---")
        clarification_message = AIMessage(content="我注意到您没有明确说明是否需要一份研究报告。您需要生成报告吗？ (y/n)")
        return {
            "messages": messages + [clarification_message],
            "current_task": user_input,  # 保存原始问题
            "awaiting_clarification": True,  # 设置等待状态
            "next_node": END  # 结束当前轮次，等待用户输入 y/n
        }

    print(f"Manager 决策: 下一步路由到 -> {res.destination}")
    print(f"Manager 决策: 下一步任务 -> {res.next_input}")

    return {
        "messages": messages,
        "next_node": res.destination,
        "current_task": user_input,
    }



