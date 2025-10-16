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
    agent = create_openai_tools_agent(llm, tools, QA_PROMPT)
    agent_executor = AgentExecutor(agent=agent, tools=tools, verbose=True, handle_parsing_errors=True)
    return agent_executor

_qa_agent = create_qa_agent()

def qa_process(state):
    """
    节点函数：根据检索到的文档和聊天历史生成最终答案。
    如果没有文档，则仅根据聊天历史回答。
    """
    print("---调用 QA 节点，生成答案---")
    documents = state.get("documents", [])
    messages = state.get("messages", [])
    question = state.get("current_task")

    if not question:
        answer = "抱歉，我不知道要回答什么问题。"
        print(f"QA 节点错误: {answer}")
        return {"messages": [AIMessage(content=answer)]}

    # 如果没有文档，打印警告，但继续执行，让 LLM 基于历史记录回答
    if not documents:
        print("QA 节点警告: 未找到相关文档，将仅基于对话历史回答。")

    print(f"QA 节点正在回答问题: '{question}'")

    # 提取除最新用户消息之外的所有历史记录
    chat_history = messages[:-1] if messages else []

    # 准备文档内容，即使为空也要传入
    docs_content = "\n\n".join([doc.page_content for doc in documents])

    # 调用 agent，传入问题、文档内容（可能为空）和聊天历史
    response = _qa_agent.invoke({
        "input": question,
        "documents": docs_content,
        "chat_history": chat_history
    })
    answer = response.get("output", "抱歉，我无法回答这个问题。")

    print(f"QA 节点生成的答案: {answer}")

    # LangGraph 会自动将 AIMessage 添加到 state 的 messages 中，这里我们只返回内容
    return {"messages": [AIMessage(content=answer)]}
