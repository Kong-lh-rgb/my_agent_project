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
from langgraph.graph import START,END


MAX_MESSAGES_IN_CONTEXT = 6

class RouteDecision(BaseModel):
    """根据用户的查询路由到正确的智能体。"""
    destination: Literal["ask_user","writer_agent","research_agent", "code_agent", "qa_agent", "other_chat_node","END"] = Field(
        description="根据用户问题选择的下一个目标智能体。如果任务完成或问题简单，则选择'END'。"
    )
    next_input: str = Field(description="为下一个节点准备的、经过重写的清晰任务指令")
    clarification_type: Literal["topic", "report_needed", "none"] = Field(
        description="当 'destination' 为 'ask_user' 时，指定需要澄清的问题类型。"
                    "'topic' 表示主题不明确；"
                    "'report_needed' 表示不清楚是否要生成报告；"
                    "'none' 表示不需要澄清。"
    )

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
        original_task = state["current_task"]
        clarification_type = state.get("clarification_type")

        if clarification_type == "report_needed":
            print("---处理用户对报告需求的澄清 (y/n)---")
            choice = user_input.strip().lower()
            if choice == 'y':
                required_report = True
            elif choice == 'n':
                required_report = False
            else:
                clarification_message = AIMessage(content="无效输入，请重新回答 'y' 或 'n'。")
                return {
                    "messages": messages + [HumanMessage(content=user_input), clarification_message],
                    "awaiting_clarification": True,
                    "clarification_type": "report_needed",
                    "next_node": END
                }
            print(f"用户已澄清，是否需要报告: {required_report}")
            return {
                "messages": messages + [HumanMessage(content=user_input)],
                "required_report": required_report,
                "awaiting_clarification": False,
                "next_node": "research_agent",
                "current_task": original_task
            }
        elif clarification_type == "topic":
            print("---用户已提供主题，合并任务并开始研究---")
            new_task = f"{original_task}，特别是关于 '{user_input}' 的方面"
            print(f"合并后的新任务: {new_task}")
            return {
                "messages": messages + [HumanMessage(content=user_input)],
                "awaiting_clarification": False,
                "next_node": "research_agent",
                "current_task": new_task,
                "required_report": True
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

    if res.destination == "other_chat_node":
        print("Manager 决策: 意图为聊天，直接路由到 -> other_chat_node")
        return {"messages": messages, "next_node": "other_chat_node", "current_task": user_input}

    if res.destination == "ask_user":
        question = ""
        if res.clarification_type == "report_needed":
            question = "好的，我将为您查找相关资料。请问您需要我为您生成一份正式的报告吗？ (y/n)"
            print(f"---需求不明确 (report_needed)，向用户反问: {question}---")
        elif res.clarification_type == "topic":
            question = "您想要关于什么主题的报告？"
            print(f"---需求不明确 (topic)，向用户反问: {question}---")
        else:  # 默认或 fallback
            question = "我不太理解您的意思，可以更详细地说明一下吗？"
            print(f"---需求不明确 (fallback)，向用户反问: {question}---")

        clarification_message = AIMessage(content=question)
        return {
            "messages": messages + [clarification_message],
            "current_task": res.next_input,
            "awaiting_clarification": True,
            "clarification_type": res.clarification_type,
            "next_node": END
        }



    print(f"Manager 决策: 下一步路由到 -> {res.destination}")
    print(f"Manager 决策: 下一步任务 -> {res.next_input}")



    return {
        "messages": messages,
        "next_node": res.destination,
        "current_task": res.next_input,
    }



