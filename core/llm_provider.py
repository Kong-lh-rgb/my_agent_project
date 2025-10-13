from langchain_openai import ChatOpenAI,OpenAIEmbeddings

from . import config

# 常用模型
def get_llm(smart: bool = False):
    """根据需求获取LLM实例"""
    model_name = config.SMART_MODEL_NAME if smart else config.EASY_MODEL_NAME
    return ChatOpenAI(
        base_url='https://api.openai-proxy.org/v1',
        model=model_name,
        api_key=config.OPENAI_API_KEY,
        temperature=0
    )


# 向量化模型
def get_embedding_model():

    return OpenAIEmbeddings(
        base_url='https://api.openai-proxy.org/v1',
        model=config.EMBEDDING_MODEL_NAME,
        api_key=config.OPENAI_API_KEY,
    )