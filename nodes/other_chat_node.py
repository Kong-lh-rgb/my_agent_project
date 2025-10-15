from core.llm_provider import get_llm
from core.prompt_templates import CHAT_PROMPT
from langchain.agents import AgentExecutor, create_openai_tools_agent
from langchain_core.messages import AIMessage

def creat_chat_agent():
    llm = get_llm(smart=False)
    tools = []
    prompt = CHAT_PROMPT
    agent = create_openai_tools_agent(llm, tools, prompt)
    agent_executor = AgentExecutor(agent=agent, tools=tools, verbose=True)
    return agent_executor

_chat_agent = creat_chat_agent()

def other_chat_process(state):
    messages = state.get("messages") or state.get("input")
    question = messages[-1].content if messages else state.get("input")
    chat_history = messages[-7:-1] if messages else []
    answer = _chat_agent.invoke({"input": question, "chat_history": chat_history}).get("output","")
    print(f"Chat 节点生成的回答: {answer}")
    return {"messages": [AIMessage(content=answer)]}