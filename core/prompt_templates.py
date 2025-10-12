from langchain_core.prompts import ChatPromptTemplate,MessagesPlaceholder

RESEARCH_PROMPT = ChatPromptTemplate.from_messages([
    ("system", "你是一个自动化的网络资料收集助手。你的任务是使用你可用的工具来搜索并提供关于用户问题的最相关、最准确的网页上的信息并返回资料。"
               "流程：\n"
               "1. 首先使用'search_tool'为用户的查询提供最相关的网页链接。\n"
               "2. 接下来分析搜索结果，使用'web_tool'访问每一个相关的url，并提取完整的文本内容。\n"
               "3. 最后将所有URL中提取的文本内容合并成一个单一的文本块。在每个网页内容之间用'\\n\\n--- 原始网页分割线 ---\\n\\n'进行分隔。\n"
               "规则：\n"
               "你的最终输出必须是且只能是这个合并后的原始文本。不要进行任何形式的总结、解释或添加额外信息。\n"
                ),
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

POST_RESEARCH_PROMPT = ChatPromptTemplate.from_messages([
    """
    你是一个决策助理，你的任务是分析用户的问题和刚刚总结出来的摘要。
    根据用户的问题判断他的意图，如果用户只是需要简单的回答问题则将研究摘要总结成一个清晰的答案；
    如果用户需要生成报告等，请将研究摘要作为资料，并将目标设为 'writer_agent'。
    用户问题：{input},
    研究摘要：{summary}
    """
])

WRITER_PROMPT = ChatPromptTemplate.from_messages([
    """
    你是负责将信息整理并写入文件的智能体。
    你的任务是根据提供的资料和用户问题，生成一份结构清晰，内容详实的文档。
    根据用户需求生成不同类型的文档，例如txt、md、pdf等。
    如果用户没有指定文档的类型，则默认生成md格式的文档。
    请确保文档内容准确无误，并且易于理解和阅读。
    用户问题：{input}
    资料和指令：{details}
    """
])

FILENAME_PROMPT = ChatPromptTemplate.from_template(
    "根据以下报告内容，生成一个简短、描述性强且适合用作文件名的字符串。"
    "规则：\n"
    "1. 只能使用小写英文字母和下划线 `_`。\n"
    "2. 不要包含任何文件扩展名（如 .md）。\n"
    "3. 不要包含任何解释或标点符号。\n"
    "例如：'artificial_intelligence_report' 或 'future_of_ai'。\n\n"
    "报告内容：\n"
    "--- \n"
    "{report_content}\n"
    "--- \n"
    "文件名："
)

FILE_EXTENSION_PROMPT = ChatPromptTemplate.from_template(
    "根据用户的原始请求，判断应该使用什么文件扩展名。默认是 '.md'。\n"
    "如果用户请求了特定格式（如 'txt', 'json'），请返回对应的扩展名。\n"
    "请只返回扩展名本身，例如 '.md' 或 '.txt'。\n\n"
    "用户原始请求：'{input}'\n\n"
    "文件扩展名："
)