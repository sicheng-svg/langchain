from langchain_redis import RedisConfig, RedisVectorStore
from langchain_community.document_loaders import UnstructuredMarkdownLoader
from langchain_text_splitters import CharacterTextSplitter
from langchain_openai import OpenAIEmbeddings
from langchain_core.runnables import chain
from typing import List
from langchain_core.documents import Document

# 定义嵌入模型
embedding = OpenAIEmbeddings(
    model="BAAI/bge-m3",
    base_url="https://api.siliconflow.cn/v1",
    api_key="sk-ujtqlhorbfsiemxyvltkjyocbfiulbdfbjdoqkrrtydlvmzv",
    chunk_size=64,
)   

# redis配置
config = RedisConfig(
    redis_url="redis://localhost:6380",
    index_name="review",
    metadata_schema=[
        {"name": "category", "type": "tag"},
        {"name": "num", "type": "numeric"},
    ]
)

# 初始化redis向量存储
# 建立配置中的索引结构
vector_store = RedisVectorStore(
    embeddings=embedding,
    config=config,
)

# retriever = vector_store.as_retriever()
# retriever = vector_store.as_retriever(search_kwargs={"k": 2})
# retriever = vector_store.as_retriever(
#     search_type="mmr",
#     search_kwargs={
#         "k": 2,
#         "fetch_k": 10
#     }
# )

@chain
def retriever(query: str) -> List[Document]:
    return vector_store.similarity_search(query, k=2)
docs = retriever.invoke("CGO")
for doc in docs:
    print("*" * 30)
    print(doc.page_content)