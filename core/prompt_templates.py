from langchain_core.prompts import ChatPromptTemplate,MessagesPlaceholder

RESEARCH_PROMPT = ChatPromptTemplate.from_messages([
    ("system", "你是一个世界一流的研究员。你的任务是使用你可用的工具来搜集、分析并提供关于用户问题的最新、最准确的信息。"),
    ("human", "{input}"),
    # 这个占位符至关重要，Agent Executor会在这里插入中间步骤
    ("placeholder", "{agent_scratchpad}"),
])

# NAVIGATE_PROMPT = ChatPromptTemplate.from_messages([
#     ("system", "你是意图判断ai助理。作为接受用户输入的第一个结点，"
#                "你的任务是根据用户输入，输出对应的任务导航进入对应的结点解决用户的问题"
#                "你只能返回如下字段："
#                "code_agent"
#                "writer_agent"
#                "research_agent"
#                "三个结点之一"),
#     ("human", "{input}"),
#     # 这个占位符至关重要，Agent Executor会在这里插入中间步骤
#     ("placeholder", "{agent_scratchpad}"),
# ])

NAVIGATE_PROMPT = ChatPromptTemplate.from_messages([
    ("system", "你是一个智能路由助理。你的任务是分析用户的对话历史和最新问题，"
               "然后决定下一步应该由哪个智能体来处理，或者判断任务是否已经可以结束。"),

    MessagesPlaceholder(variable_name="messages"),
    ("human", "{input}"),
])