from langchain_core.messages import AIMessage
from langchain_core.output_parsers import StrOutputParser
from langchain_core.runnables import RunnablePassthrough
from core.prompt_templates import QA_PROMPT
from core.llm_provider import get_llm
from langchain.agents import AgentExecutor, create_openai_tools_agent


def create_qa_agent():
    """
    创建一个 RAG 链，它接收文档、聊天记录和问题来生成答案。
    """
    tools = []
    llm = get_llm(smart=False)
    # 【关键修改】这里的链结构要和 qa_node 的输入对应
    agent = create_openai_tools_agent(llm, tools, QA_PROMPT)
    agent_executor = AgentExecutor(agent=agent, tools=tools, verbose=True, handle_parsing_errors=True)
    return agent_executor

_qa_agent = create_qa_agent()

def qa_process(state):
    """
        节点函数：根据检索到的文档和聊天历史生成最终答案。
        """
    print("---调用 QA 节点，生成答案---")
    documents = state.get("documents", [])[:3]
    messages = state.get("messages", [])
    # 【关键修改】确定要回答的问题
    # 优先使用重写后的问题，其次是当前任务，最后是原始输入
    question = state.get("current_task")

    if not question:
        answer = "抱歉，我不知道要回答什么问题。"
        print(f"QA 节点错误: {answer}")
        return {"messages": messages + [AIMessage(content=answer)]}

    if not documents:
        answer = "对不起，我没有找到相关信息来回答您的问题。"
        print(f"QA 节点警告: {answer}")
        return {"messages": messages + [AIMessage(content=answer)]}

    print(f"QA 节点正在回答问题: '{question}'")

    # 【关键修改】准备聊天记录（排除最后一条用户输入）
    # 注意：manager_node 已经将当前输入加入了 messages，所以这里取 [:-1]
    chat_history = messages[:-1] if messages else []

    # 创建并调用链

    docs_content = "\n\n".join([doc.page_content for doc in documents])

    answer = _qa_agent.invoke({"input": question, "documents": docs_content, "chat_history": chat_history}).get("output","")

    print(f"QA 节点生成的答案: {answer}")

    # 将 AI 的回答追加到消息历史中
    # 注意：manager_node 已经加了 HumanMessage，这里只加 AIMessage
    return {"messages": [AIMessage(content=answer)]}

