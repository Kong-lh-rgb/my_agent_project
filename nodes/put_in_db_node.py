#专用于向量化存入数据库的结点
from core.llm_provider import get_embedding_model
from core import llm_provider
from typing import Dict, Any
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain_openai import OpenAIEmbeddings
from langchain_community.vectorstores import FAISS

def put_in_db_node(state:Dict[str, Any]) -> Dict[str, Any]:
    """接受原始文本，对文本进行分块，向量化存入数据库"""
    raw_text = state["raw_text"]
    if not raw_text:
        return {"error": "无原始数据"}

    # 分块
    text_splitter = RecursiveCharacterTextSplitter(
        chunk_size = 1000,
        chunk_overlap = 150,
    )
    chunks = text_splitter.split_text(raw_text)

    #向量化
    embeddings = get_embedding_model()
    vectorstore = FAISS.from_texts(texts = chunks, embedding = embeddings)

    serialized_store = vectorstore.serialize_to_bytes()


    # 放入state中
    return {"serialized_vectorstore": serialized_store}

# if __name__ == "__main__":
#     # 模拟一个包含大量原始文本的 state
#     test_state = {
#         "raw_text": """
#         这是第一篇关于人工智能的文档。人工智能（AI）是计算机科学的一个分支，它企图了解智能的实质，并生产出一种新的能以人类智能相似的方式做出反应的智能机器。
#         --- 原始网页分割线 ---
#         这是第二篇关于机器学习的文档。机器学习是人工智能的一个核心研究领域。它的理论主要是设计和分析一些让计算机可以自动“学习”的算法。
#         --- 原始网页分割线 ---
#         深度学习是机器学习中一个非常热门的领域，它基于人工神经网络，特别是深度神经网络。它在图像识别、语音识别等领域取得了巨大成功。
#         """
#     }
#
#     # 运行索引节点
#     indexing_result_state = put_in_db_node(test_state)
#
#     print("\n" + "="*20 + " NODE OUTPUT " + "="*20 + "\n")
#     print(indexing_result_state)
#
#     # 验证是否成功创建了检索器
#     if "retriever" in indexing_result_state:
#         retriever = indexing_result_state["retriever"]
#         print("\nRetriever created successfully.")
#
#         # 使用检索器进行一次测试查询
#         query = "深度学习是什么？"
#         relevant_docs = retriever.invoke(query)
#         print(f"\n--- Test retrieval for query: '{query}' ---")
#         for doc in relevant_docs:
#             print(doc)