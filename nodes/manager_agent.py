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
# nodes/manager_agent.py
from langchain_core.messages import HumanMessage, AIMessage
from pydantic import BaseModel, Field
from typing import Literal
from core.prompt_templates import NAVIGATE_PROMPT, REWRITE_QUERY_PROMPT
from core.llm_provider import get_llm
from langgraph.graph import START, END
from langchain_core.output_parsers import StrOutputParser
from langchain_core.prompts import ChatPromptTemplate

MAX_MESSAGES_IN_CONTEXT = 10
# 设定一个比摘要上下文略小的阈值，以保留最近的对话
MESSAGES_TO_RETAIN_AFTER_SUMMARY = 5


class RouteDecision(BaseModel):
    """根据用户的查询路由到正确的智能体。"""
    destination: Literal[
        "ask_user", "writer_agent", "research_agent", "code_agent", "qa_agent", "other_chat_node", "END"] = Field(
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


def create_rewrite_chain():
    """
    创建一个用于改写用户输入的链。
    """
    llm = get_llm(smart=False)
    rewrite_chain = REWRITE_QUERY_PROMPT | llm | StrOutputParser()
    return rewrite_chain


def create_summary_chain():
    llm = get_llm(smart=False)
    prompt = ChatPromptTemplate.from_messages([
        ("system", "你是一个专业的文本摘要生成器。请根据以下对话内容生成简洁明了的摘要。"),
        ("user", "{chat_history}")
    ])
    summary_chain = prompt | llm | StrOutputParser()
    return summary_chain


def manager_process(state):
    print("---调用 Manager 节点，开始进行意图判断---")
    messages = state.get("messages", [])
    user_input = state["input"]
    updates = {}

    # --- 摘要逻辑修复 ---
    # 当消息的长度超过阈值时对消息进行摘要
    if len(messages) > MAX_MESSAGES_IN_CONTEXT:
        print(f"---消息数量 ({len(messages)}) 超过阈值 ({MAX_MESSAGES_IN_CONTEXT})，开始摘要---")
        summary_chain = create_summary_chain()
        old_summary = state.get("conversation_summary", "")

        # 我们摘要掉除了最近几条之外的所有消息
        num_messages_to_summarize = len(messages) - MESSAGES_TO_RETAIN_AFTER_SUMMARY
        messages_to_summarize = messages[:num_messages_to_summarize]

        history_str = "\n".join(
            [f"{'用户' if isinstance(m, HumanMessage) else '助理'}: {m.content}" for m in messages_to_summarize]
        )
        new_summary = summary_chain.invoke({
            "chat_history": f"这是已有的对话摘要，请在此基础上进行总结和扩展：\n{old_summary}\n\n这是最近的对话内容：\n{history_str}"
        })

        # 创建新的消息列表：[摘要] + [最近未被摘要的消息]
        summary_message = AIMessage(content=f"[对话摘要] {new_summary}")
        retained_messages = messages[num_messages_to_summarize:]

        # 使用 updates 字典来更新状态，而不是直接修改
        updates["messages"] = [summary_message] + retained_messages
        updates["conversation_summary"] = new_summary

        # 更新本节点内使用的 messages 变量，以确保后续逻辑基于更新后的消息列表
        messages = updates["messages"]
        print("---摘要完成，消息列表已更新---")

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
                updates.update({
                    "messages": messages + [HumanMessage(content=user_input), clarification_message],
                    "awaiting_clarification": True,
                    "clarification_type": "report_needed",
                    "next_node": END
                })
                return updates
            print(f"用户已澄清，是否需要报告: {required_report}")
            updates.update({
                "messages": messages + [HumanMessage(content=user_input)],
                "required_report": required_report,
                "awaiting_clarification": False,
                "next_node": "research_agent",
                "current_task": original_task
            })
            return updates
        elif clarification_type == "topic":
            print("---用户已提供主题，合并任务并开始研究---")
            new_task = f"{original_task}，特别是关于 '{user_input}' 的方面"
            print(f"合并后的新任务: {new_task}")
            updates.update({
                "messages": messages + [HumanMessage(content=user_input)],
                "awaiting_clarification": False,
                "next_node": "research_agent",
                "current_task": new_task,
                "required_report": True
            })
            return updates

    manager_chain = create_manager_router_chain()
    current_messages = messages + [HumanMessage(content=user_input)]

    preliminary_decision = manager_chain.invoke({
        "messages": current_messages[-MAX_MESSAGES_IN_CONTEXT:],
        "input": user_input,
    })

    if preliminary_decision.destination == "other_chat_node":
        print("Manager 决策: 初步判断为聊天，直接路由到 -> other_chat_node")
        updates.update({
            "messages": current_messages,
            "next_node": "other_chat_node",
            "current_task": user_input
        })
        return updates

    rewritten_input = user_input
    if len(messages) > 0:
        print("---进行查询改写---")
        rewrite_chain = create_rewrite_chain()
        # 使用摘要前的完整历史进行改写
        chat_history = state.get("messages", [])
        rewritten_input = rewrite_chain.invoke({
            "chat_history": chat_history,
            "input": user_input
        })
        print(f"原始输入: '{user_input}'")
        print(f"改写后输入: '{rewritten_input}'")

    updates["rewritten_input"] = rewritten_input

    final_decision = manager_chain.invoke({
        "messages": current_messages[-MAX_MESSAGES_IN_CONTEXT:],
        "input": rewritten_input,
    })
    if final_decision.destination == "ask_user":
        question = ""
        if final_decision.clarification_type == "report_needed":
            question = "好的，我将为您查找相关资料。请问您需要我为您生成一份正式的报告吗？ (y/n)"
            print(f"---需求不明确 (report_needed)，向用户反问: {question}---")
        elif final_decision.clarification_type == "topic":
            question = "您想要关于什么主题的报告？"
            print(f"---需求不明确 (topic)，向用户反问: {question}---")
        else:
            question = "我不太理解您的意思，可以更详细地说明一下吗？"
            print(f"---需求不明确 (fallback)，向用户反问: {question}---")

        clarification_message = AIMessage(content=question)
        updates.update({
            "messages": current_messages + [clarification_message],
            "current_task": final_decision.next_input,
            "awaiting_clarification": True,
            "clarification_type": final_decision.clarification_type,
            "next_node": END
        })
        return updates

    print(f"Manager 决策: 下一步路由到 -> {final_decision.destination}")
    print(f"Manager 决策: 下一步任务 -> {final_decision.next_input}")

    updates.update({
        "messages": current_messages,
        "next_node": final_decision.destination,
        "current_task": final_decision.next_input,
    })

    if final_decision.destination == "code_agent":
        updates["code_execution_attempts"] = 0

    return updates







