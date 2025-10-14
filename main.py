import asyncio
import uuid
from workflow.task_graph import build_graph
from dotenv import load_dotenv
load_dotenv()
from langgraph.checkpoint.sqlite.aio import AsyncSqliteSaver
import sqlite3
# 为每次会话生成一个唯一的 ID
config = {"configurable": {"thread_id": str(uuid.uuid4())}}

async def main():
    """
    主执行函数
    """
    # 编译图
    async with AsyncSqliteSaver.from_conn_string(":memory:") as memory:  # 这里用内存数据库做演示，换成 "checkpoints.sqlite" 即可保存到文件
        graph = build_graph(checkpointer=memory)

        session_id = "my-first-session"  # 使用一个固定的ID
        config = {"configurable": {"thread_id": session_id}}

        print("你好！我是一个智能助理。输入 'exit' 或 'quit' 退出。")
        while True:
            # 接收用户输入
            user_input = input("你: ")
            if user_input.lower() in ["exit", "quit"]:
                print("再见！")
                break

            if user_input.lower() == "reset":
                print("对话已重置。")
                session_id = "session_" + str(uuid.uuid4())  # 创建一个新的会话ID
                config = {"configurable": {"thread_id": session_id}}
                continue

            # 准备图的初始状态
            inputs = {"input": user_input}

            print("\n")
            print("思考中..."+"\n")

            final_state = None
            async for event in graph.astream(inputs, config=config, stream_mode="updates"):
                # 打印节点执行信息
                for node, values in event.items():
                    print(f"\n> 节点 '{node}' 返回输出:")
                    # 你可以在这里打印更详细的 values 内容进行调试
                    # print(values)
                final_state = event

            # 在图执行完毕后，检查并打印最后一条消息
            if final_state:
                last_node = list(final_state.keys())[-1]
                messages = final_state[last_node].get("messages", [])
                if messages:
                    last_message = messages[-1]
                    # 如果最后一条消息是 AI 发出的，就打印出来
                    if hasattr(last_message, 'type') and last_message.type == 'ai':
                        print(f"\n助理: {last_message.content}")

            print("\n")


if __name__ == "__main__":
    asyncio.run(main())
