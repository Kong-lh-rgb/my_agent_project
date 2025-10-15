from typing import Dict, Any
from langchain_community.vectorstores import FAISS
from core.llm_provider import get_embedding_model

def find(state: Dict[str,Any]):
    """获取序列化的vectorstore和用户输入，重建retriever并检索文档"""
    print("检索...")
    serialized_store = state.get("serialized_vectorstore")
    user_input = state.get("rewritten_input") or state.get("current_task")

    if not serialized_store or not user_input:
        print("错误：在 state 中未找到 serialized_vectorstore 或 input。")
        return {"documents": []}


    embeddings = get_embedding_model()


    vectorstore = FAISS.deserialize_from_bytes(
        embeddings=embeddings, serialized=serialized_store,allow_dangerous_deserialization=True
    )

    retriever = vectorstore.as_retriever()
    documents = retriever.invoke(user_input)
    return {"documents": documents}
