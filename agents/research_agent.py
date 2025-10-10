from core.llm_provider import get_llm
from tools.search_tool import search_tool
from core.prompt_templates import RESEARCH_PROMPT
from langchain.agents import AgentExecutor,create_openai_tools_agent


def create_research_agent():
    tools = [search_tool]
    llm = get_llm(smart = False)
    prompt = RESEARCH_PROMPT
    agent = create_openai_tools_agent(llm, tools,prompt)

    agent_executor = AgentExecutor(agent = agent,tools = tools,verbose=True)
    return agent_executor

if __name__ == "__main__":
    researcher = create_research_agent()
    result = researcher.invoke({"input":"马云是谁？"})
    print(result)