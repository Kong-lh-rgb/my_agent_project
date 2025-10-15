# from langchain_core.messages import AIMessage, HumanMessage
# from langchain_core.runnables import RunnablePassthrough
# from core.prompt_templates import REWRITE_QUERY_PROMPT
# from core.llm_provider import get_llm
# from typing import Dict, Any
#
#
#
# def get_chat_history(messages: list):
#     """从消息列表中格式化聊天记录"""
#     history = []
#     # 排除最后一条用户输入，因为它将作为当前问题
#     for msg in messages[:-1]:
#         if isinstance(msg, HumanMessage):
#             history.append(f"用户: {msg.content}")
#         elif isinstance(msg, AIMessage):
#             history.append(f"助理: {msg.content}")
#     return "\n".join(history)
#
#
# def rewrite_query(state:Dict[str,Any]):
#     """根据聊天记录重写用户查询，使其包含完整上下文"""
#     print("---调用 rewrite_query_node，优化查询---")
#     user_input = state["input"]
#     messages = state.get("messages", [])
#
#     # 格式化聊天记录
#     chat_history = get_chat_history(messages)
#
#     # 如果没有历史记录，或者只有一条消息（即当前输入），则无需重写
#     if not chat_history:
#         print("无历史记录，跳过查询重写。")
#         # 将原始输入放入 "rewritten_input" 字段，以供下游节点使用
#         return {"rewritten_input": user_input}
#
#     # 创建查询重写链
#     rewrite_chain = (
#             {
#                 "chat_history": lambda x: chat_history,
#                 "input": RunnablePassthrough()
#             }
#             | REWRITE_QUERY_PROMPT
#             | get_llm(smart=False)
#     )
#
#     # 调用链来获取重写后的查询
#     rewritten_input_result = rewrite_chain.invoke(user_input)
#     rewritten_input = rewritten_input_result.content
#
#     print(f"原始查询: {user_input}")
#     print(f"重写后查询: {rewritten_input}")
#
#     # 返回包含重写后查询的字典
#     return {"rewritten_input": rewritten_input}
