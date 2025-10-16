from langchain_core.messages import AIMessage

from core.llm_provider import get_llm
from tools.code_interpreter import execute_code
from core.prompt_templates import CODE_PROMPT

from langchain.agents import AgentExecutor, create_openai_tools_agent


MAX_EXECUTION_ATTEMPTS = 3

def create_code_agent():
    llm = get_llm(smart = False)
    tools = [execute_code]
    prompt = CODE_PROMPT
    agent = create_openai_tools_agent(llm, tools, prompt)
    agent_executor = AgentExecutor(agent = agent, tools = tools, verbose = True)
    return agent_executor

_code_agent = create_code_agent()

def code_agent_process(state):
    attempts = state.get("code_execution_attempts",0)
    print(f"代码执行尝试次数: {attempts + 1}/{MAX_EXECUTION_ATTEMPTS}")

    if attempts >= MAX_EXECUTION_ATTEMPTS:
        error_message = f"代码执行失败次数过多（已达 {MAX_EXECUTION_ATTEMPTS} 次上限），已停止尝试。请检查代码或环境问题。"
        print(f"错误: {error_message}")
        return {
            "messages": [AIMessage(content=error_message)],
            "code_execution_attempts": attempts + 1
        }


    last_message = state['messages'][-1]
    question = last_message.content
    chat_history = state['messages'][-7:-1]
    answer = _code_agent.invoke({"input": question, "chat_history": chat_history}).get("output","")
    return {"messages":[AIMessage(content=answer)]}


# --- 使用示例 ---
# if __name__ == '__main__':
#     # # 示例1: 成功执行
#     # request1 = "计算 1 到 10 的平方和并打印结果。"
#     # print(f"用户请求: {request1}")
#     # # AgentExecutor 使用 invoke 方法，并传入一个字典
#     # # chat_history 在单次测试中可以为空列表
#     # response1 = _code_agent.invoke({"input": request1, "chat_history": []})
#     # print(f"\n最终答案:\n{response1.get('output')}")
#     #
#     # print("\n" + "=" * 50 + "\n")
#
#     # 示例2: 纠错
#     request2 = "#include <stdio.h>int main() {printf(" 'nj'")return 0;}为什么我的代码报错"
#     print(f"用户请求: {request2}")
#     response2 = _code_agent.invoke({"input": request2, "chat_history": []})
#     print(f"\n最终答案:\n{response2.get('output')}")