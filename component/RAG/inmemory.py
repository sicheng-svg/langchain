from langchain_openai import OpenAIEmbeddings
from langchain_community.document_loaders import UnstructuredMarkdownLoader
from langchain_text_splitters import CharacterTextSplitter
from langchain_core.vectorstores import InMemoryVectorStore
from langchain_core.documents import Document

# 1.先加载文档
loader = UnstructuredMarkdownLoader("/mnt/d/Users/xsc/Desktop/点赞服务面试复盘.md")
data = loader.load()

# 2.分割文档
token_splitter = CharacterTextSplitter.from_tiktoken_encoder(
    encoding_name="cl100k_base", # tiktoken编码名称，cl100k_base是OpenAI的编码器，支持所有的OpenAI模型
    chunk_size=400, #每个块token大小，也是文档大小
    chunk_overlap=20, #块重叠大小，块之间的重叠部分大小
)
docs = token_splitter.split_documents(data)

# 3.定义内存级存储向量
embedding = OpenAIEmbeddings(
    model="BAAI/bge-m3",
    base_url="https://api.siliconflow.cn/v1",
    api_key="sk-ujtqlhorbfsiemxyvltkjyocbfiulbdfbjdoqkrrtydlvmzv",
)
vector_stores = InMemoryVectorStore(embedding=embedding)

# 4.存储分割后的文档到内存向量存储中
ids = vector_stores.add_documents(docs)
print(f"文档数量:{len(docs)}")
print(f"索引数量:{len(ids)}")
# print(f"前两个索引的值:{ids[:2]}")
# 
# # 5.通过索引获取对应的文档列表
# doc = vector_stores.get_by_ids(ids[:2])
# print(f"前两个索引对应的文档内容为{doc}")
# 
# # 6.通过索引删除对应的文档列表
# vector_stores.delete(ids[:2])
# doc = vector_stores.get_by_ids(ids[:3])
# print(f"前三个索引对应的文档内容为{doc}")

# 5.通过query进行相似度搜索，获取相关的文档列表
# k表示返回的相关文档的数量
# docs = vector_stores.similarity_search("点赞和踩的互斥", k=2)
# for doc in docs:
#     print("*"*20)
#     print(doc)

# 可以先通过元数据过滤掉一些，在进行语义相似性搜索
def filterimpl(doc:Document) -> bool:
    return doc.metadata.get("source") == "/mnt/d/Users/xsc/Desktop/点赞服务面试复盘.md"

docs = vector_stores.similarity_search(
    query="点赞和踩的互斥", 
    k=2,
    filter=filterimpl
)
for doc in docs:
    print("*"*20)
    print(doc)
