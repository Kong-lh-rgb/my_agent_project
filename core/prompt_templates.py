from langchain_core.prompts import ChatPromptTemplate

RESEARCH_PROMPT = ChatPromptTemplate.from_messages([
    ("system", "你是一个世界一流的研究员。你的任务是使用你可用的工具来搜集、分析并提供关于用户问题的最新、最准确的信息。"),
    ("human", "{input}"),
    # 这个占位符至关重要，Agent Executor会在这里插入中间步骤
    ("placeholder", "{agent_scratchpad}"),
])

