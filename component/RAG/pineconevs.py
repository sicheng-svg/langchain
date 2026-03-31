from langchain_openai import OpenAIEmbeddings
from langchain_pinecone import PineconeVectorStore
from pinecone import Pinecone, ServerlessSpec
from langchain_community.document_loaders import UnstructuredMarkdownLoader
from langchain_text_splitters import CharacterTextSplitter

# 建立索引​
pc = Pinecone(api_key="pcsk_3zgQZP_B38ijC9t4LXRi4kEx3cTkwtfcgJSL3edYdf9Ai6kuxemsDKFEoeQT8PV2Sn8goE")
index_name = "review"
if not pc.has_index(index_name):
    pc.create_index(
        name=index_name, # 索引名称​
        dimension=1024, # 尺寸，表示向量维度，需要和嵌入模型维度一致​
        metric="cosine", # 度量方式，cosine 表示余弦相似度​
        spec=ServerlessSpec(
            cloud="aws", # 亚马逊云​
            region="us-east-1" # 区域​
        ),
    )
# 定义嵌入模型​
embeddings = OpenAIEmbeddings(
    model="BAAI/bge-m3", 
    base_url="https://api.siliconflow.cn/v1", 
    api_key="sk-ujtqlhorbfsiemxyvltkjyocbfiulbdfbjdoqkrrtydlvmzv",
    chunk_size=64, # 每个块的token大小，默认为64，表示每个块的文本长度为64个token​
)

# 获取索引​
index = pc.Index(index_name)

# 定义 Pinecone 向量存储​
vector_store = PineconeVectorStore(embedding=embeddings, index=index)

# 1.先加载文档
# loader = UnstructuredMarkdownLoader("/mnt/d/Users/xsc/Desktop/点赞服务面试复盘.md")
# data = loader.load()
# 
# # 2.分割文档
# token_splitter = CharacterTextSplitter.from_tiktoken_encoder(
#     encoding_name="cl100k_base", # tiktoken编码名称，cl100k_base是OpenAI的编码器，支持所有的OpenAI模型
#     chunk_size=100, #每个块token大小，也是文档大小
#     chunk_overlap=10,
# )
# # 为文档添加元数据
# docs = token_splitter.split_documents(data)
# for i, doc in enumerate(docs, start=1):
#     doc.metadata["category"] = "review"
#     doc.metadata["num"] = i
# 
# # 3.将文档添加到Pinecone向量存储中
# ids = vector_store.add_documents(docs)
# print(f"文档数量:{len(docs)}")
# print(f"索引数量:{len(ids)}")

# # 全量删除​
# vector_store.delete(delete_all=True)
# # 删除指定id的文档列表​
# delete_ids = []
# vector_store.delete(ids=delete_ids)

search_docs = vector_store.similarity_search(
    query="CGO",
    k=2,
    filter={"category": "review"},
)
for doc in search_docs:
    print("*" * 30)
    print(f"Content: {doc.page_content}...")
    print(f"Metadata: {doc.metadata}")