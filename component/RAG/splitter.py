# 文档分割器
# 根据长度和语义来分割文档
from langchain_community.document_loaders import UnstructuredMarkdownLoader
from langchain_text_splitters import CharacterTextSplitter, RecursiveCharacterTextSplitter
import tiktoken

# md文档加载器
# 使用默认的mode=single，将整个文档加载为一个大的Document对象
loader = UnstructuredMarkdownLoader("/mnt/d/Users/xsc/Desktop/点赞服务面试复盘.md")
data = loader.load()

# 文本分割器 ———— 基于字符长度进行切分
text_splitter = CharacterTextSplitter(
    separator="\n\n", # 换行符
    chunk_size=100, #每个块大小，也是文档大小
    chunk_overlap=20, #块重叠大小，块之间的重叠部分大小
    is_separator_regex=False, # separator是否是正则表达式
)

# Created a chunk of size 110, which is longer than the specified 100
# Created a chunk of size 105, which is longer than the specified 100
# Created a chunk of size 147, which is longer than the specified 100
# Created a chunk of size 149, which is longer than the specified 100
# Created a chunk of size 157, which is longer than the specified 100
# Created a chunk of size 154, which is longer than the specified 100
# Created a chunk of size 138, which is longer than the specified 100
# 我们可以看到有很多的chunk的大小都超过了100，这是因为chunk_size只是一个建议。文本分割器会尽量按照分隔符来切分文本。
# 但要是分隔符之间的文本长度超过了chunk_size，那么文本分割器就会直接把这个文本作为一个chunk，而不是继续切分它。
# 同时为了一句话的语义完整，文本分割器也会尽量避免切分一句话，所以有时候chunk的大小就会超过chunk_size，同时也会有一些重叠的部分，这样就可以保证文本的语义完整性。
# 为了避免长短落没有遇到分隔符的情况，我们可以设置分隔符优先级，如果没有遇到第一个，则根据后续的也可以进行分割
# docs = text_splitter.split_documents(data)
# for doc in docs[:10]:
#     print("*"*20)
#     print(doc)


# 基于token进行切分
# token_splitter = CharacterTextSplitter.from_tiktoken_encoder(
#     encoding_name="cl100k_base", # tiktoken编码名称，cl100k_base是OpenAI的编码器，支持所有的OpenAI模型
#     chunk_size=400, #每个块token大小，也是文档大小
#     chunk_overlap=20, #块重叠大小，块之间的重叠部分大小
# )
# 
# docs = token_splitter.split_documents(data)
# for doc in docs[:10]:
#     print("*"*20)
#     print(doc)

# 严格按照chunk_size进行切分
# token_splitter = RecursiveCharacterTextSplitter.from_tiktoken_encoder(
#     encoding_name="cl100k_base", # tiktoken编码名称，cl100k_base是OpenAI的编码器，支持所有的OpenAI模型
#     chunk_size=10, #每个块token大小，也是文档大小
#     chunk_overlap=0, #块重叠大小，块之间的重叠部分大小
# )
# 
# docs = token_splitter.split_documents(data)
# for doc in docs[:10]:
#     print("*"*20)
#     print(doc)


# 递归文本分割符可以根据分隔符列表进行多次分割。
# 首先使用第一个进行分割，如果分割后的文本块仍然超过chunk_size，那么就会继续使用下一个分隔符进行分割
token_splitter = RecursiveCharacterTextSplitter(
    separators=["\n\n", "\n", " ", ""], # 分隔符列表，按照优先级进行分割，首先使用第一个进行分割，如果分割后的文本块仍然超过chunk_size，那么就会继续使用下一个分隔符进行分割
    chunk_size=100, #每个块token大小，也是文档大小
    chunk_overlap=0, #块重叠大小，块之间的重叠部分大小
    is_separator_regex=False, # separator是否是正则表达式
)

docs = token_splitter.split_documents(data)
for doc in docs[:10]:
    print("*"*20)
    print(doc)