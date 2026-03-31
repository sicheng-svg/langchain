from langchain_openai import OpenAIEmbeddings
from langchain_community.document_loaders import UnstructuredMarkdownLoader
from langchain_text_splitters import CharacterTextSplitter
import tiktoken


embedding = OpenAIEmbeddings(
    model="BAAI/bge-m3",
    base_url="https://api.siliconflow.cn/v1",
    api_key="sk-ujtqlhorbfsiemxyvltkjyocbfiulbdfbjdoqkrrtydlvmzv",
)
##################################################### 将query转换为向量 #####################################################
vector = embedding.embed_query("hello world")
# print(f"向量维度: {len(vector)}")
# print(f"前5个维度的值: {vector[:5]}")

##################################################### 将文档转换为向量 #####################################################
# 1.先加载文档
loader = UnstructuredMarkdownLoader("/mnt/d/Users/xsc/Desktop/点赞服务面试复盘.md")
data = loader.load()

# 2.分割文档
token_splitter = CharacterTextSplitter.from_tiktoken_encoder(
    encoding_name="cl100k_base", # tiktoken编码名称，cl100k_base是OpenAI的编码器，支持所有的OpenAI模型
    chunk_size=400, #每个块token大小，也是文档大小
    chunk_overlap=20, #块重叠大小，块之间的重叠部分大小
)

# 3.将分割后的文档转换为向量
# 转换文档时，参数是list[str]，所以我们需要先将Document对象转换为字符串
docs = token_splitter.split_documents(data)
docs_list = [doc.page_content for doc in docs]
vecs = embedding.embed_documents(docs_list)
print(f"文档数量: {len(vecs)}")
print(f"向量数量: {len(vecs)}")
print(f"第一个向量的维度: {len(vecs[0])}")
print(f"第一个向量的前5个维度的值: {vecs[0][:5]}")