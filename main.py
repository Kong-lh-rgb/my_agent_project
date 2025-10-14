import asyncio
import uuid
from workflow.task_graph import build_graph
from dotenv import load_dotenv
load_dotenv()

# 为每次会话生成一个唯一的 ID
config = {"configurable": {"thread_id": str(uuid.uuid4())}}

async def main():
    """
    主执行函数
    """
    # 编译图
    graph = build_graph()

    print("你好！我是一个智能助理。输入 'exit' 或 'quit' 退出。")
    while True:
        # 接收用户输入
        user_input = input("你: ")
        if user_input.lower() in ["exit", "quit"]:
            print("再见！")
            break

        # 准备图的初始状态
        inputs = {"input": user_input}

        print("\n" + "="*30)
        print("--- 开始处理 ---")

        # 使用 astream_events 以异步流式方式执行图
        async for event in graph.astream_events(inputs, config=config, version="v1"):
            kind = event["event"]
            if kind == "on_chain_start":
                # 可以在这里打印节点的开始信息
                if event["name"] != "LangGraph": # 过滤掉顶层图的事件
                    print(f"\n> 开始执行节点: {event['name']}")
            elif kind == "on_chain_end":
                # 检查节点执行完毕后的输出
                if event["name"] != "LangGraph":
                    print(f"< 节点 '{event['name']}' 执行完毕。")
                    # event['data']['output'] 包含节点的直接返回值
                    # 如果想打印完整的 State，需要更复杂的处理
                    # 这里我们只简单示意
                    output = event['data'].get('output')
                    if isinstance(output, dict):
                        if "current_task" in output and output["current_task"]:
                             print(f"  - 当前任务: {output['current_task']}")
                        if "report_summary" in output and output["report_summary"]:
                             print(f"  - 最终报告:\n{output['report_summary']}")


        print("\n--- 处理完成 ---")
        print("="*30 + "\n")


if __name__ == "__main__":
    # 异步运行 main 函数
    asyncio.run(main())
