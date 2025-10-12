from typing import Dict, Any


def find(state: Dict[str,Any]):
    """获取检索器和用户输入，检索文档将结果存入state"""
    print("检索...")
    retriever = state["retriever"]
    input = state["input"]
    if not retriever or not input:
        print("错误：在 state 中未找到 retriever 或 input。")
        return {"documents": []}
    documents = retriever.invoke(input)
    return {"documents": documents}
