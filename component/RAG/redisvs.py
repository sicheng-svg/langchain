from langchain_redis import RedisConfig, RedisVectorStore
from langchain_community.document_loaders import UnstructuredMarkdownLoader
from langchain_text_splitters import CharacterTextSplitter
import redis
from langchain_openai import OpenAIEmbeddings
from redisvl.query.filter import Tag, Num

# redis_url = "redis://localhost:6380"
# 
# # 定义redis客户端
# redis_client = redis.from_url(redis_url)
# print(redis_client.ping())

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

# 1.先加载文档
loader = UnstructuredMarkdownLoader("/mnt/d/Users/xsc/Desktop/点赞服务面试复盘.md")
data = loader.load()

# 2.分割文档
# token_splitter = CharacterTextSplitter.from_tiktoken_encoder(
#     encoding_name="cl100k_base", # tiktoken编码名称，cl100k_base是OpenAI的编码器，支持所有的OpenAI模型
#     chunk_size=100, #每个块token大小，也是文档大小
#     chunk_overlap=10,
# )
# docs = token_splitter.split_documents(data)
# for i, doc in enumerate(docs, start=1):
#     doc.metadata["category"] = "review"
#     doc.metadata["num"] = i

# 3.将文档添加到redis向量存储中
# 运行一次就已经添加了，不要重复添加
# ids = vector_store.add_documents(docs)
# print(f"文档数量:{len(docs)}")
# print(f"索引数量:{len(ids)}")

# 查询
# print(vector_store.get_by_ids(["01KN1YS3WG2QMSV223DAV6X423"]))
# 
# # 删除
# # vector_store.delete(["01KN1YS3WG2QMSV223DAV6X423"])
# print(vector_store.get_by_ids(["01KN1YS3WG2QMSV223DAV6X423"]))
# 
# # 全量删除
# vector_store.index.delete(drop=True)

# 向量搜索
# 相似性搜索
# 增加元数据过滤
docs = vector_store.similarity_search(query="Physx",k=2,)
docs_score = vector_store.similarity_search_with_score(
    query="Physx",
    k=2,
)
filterimpl = Tag("category") == "review" and Num("num") < 30
docs_filter = vector_store.similarity_search(
    query="Physx",
    k=2,
    filter=filterimpl,
)

# for doc in docs_filter:
#     print("*"*20)
#     print(doc)

# 最大边际相关性搜索 MMR
mmr_results = vector_store.max_marginal_relevance_search(
    query="Physx",
    k=2,
    fetch_k=10,
    filter=filterimpl
)
for doc in mmr_results:
    print("*" * 30)
    print(f"Content: {doc.page_content}...")
    print(f"Metadata: {doc.metadata}")