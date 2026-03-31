from langchain_core.documents import Document
from langchain_community.document_loaders import PyPDFLoader, UnstructuredMarkdownLoader

# 要想实现RAG，⾸先就需要从源中获取数据，即加载数据或⽂档。这是通过LangChain的⽂档加载器完成的。
# LangChain⽂档加载器可以将各种数据源加载成⼀系列的⽂档对象Document
docs = [
    Document(
        page_content="这是文档的内容",
        # 元数据
        metadata={"source": "文档的来源"},
    ),
    Document(
        page_content="狗是人类忠诚的朋友。",
        # 元数据
        metadata={"source": "pets-doc"},
    ),
    Document(
        page_content="猫是独立的个体。",
        # 元数据
        metadata={"source": "pets-doc"},
    )
]

# PDF文档加载器
# loader = PyPDFLoader("/mnt/d/Users/xsc/Documents/夏思成-17829200270-后端开发.pdf")
# 加载PDF文档
# docs = loader.load()

# md文档加载器
# md文档的默认加载器使用mode = single，将整个文档加载为一个Document对象，page_content是整个文档的内容，metadata是文档的元数据
# 可以使用mode=elements，根据文档结构，将其拆分为多个文档
loader = UnstructuredMarkdownLoader("/mnt/d/Users/xsc/Desktop/点赞服务面试复盘.md", mode="elements")
data = loader.load()

print(len(data))
print(f"第一个文档的内容为{data[0].page_content}\n")
# {
#   'source': '/mnt/d/Users/xsc/Desktop/点赞服务面试复盘.md', 
#   'category_depth': 0, 
#   'languages': ['zho'], 
#   'file_directory': '/mnt/d/Users/xsc/Desktop', 
#   'filename': '点赞服务面试复盘.md', 
#   'filetype': 'text/markdown', 
#   'last_modified': '2026-03-23T21:59:04', 
#   'category': 'Title', 
#   'element_id': 'a1bf98fcec8c1afa47a41ef83e9bad36'
# }
print(f"第一个文档的元数据为{data[0].metadata}\n")


print(f"第二个文档的内容为{data[1].page_content}\n")
# {'source': '/mnt/d/Users/xsc/Desktop/点赞服务面试复盘.md', 'category_depth': 0, 'languages': ['zho'], 'file_directory': '/mnt/d/Users/xsc/Desktop', 'filename': '点赞服务面试复盘.md', 'filetype': 'text/markdown', 'last_modified': '2026-03-23T21:59:04', 'category': 'Title', 
# 'element_id': '20a0d053e83a36452c4161d1e1b1539e'}
print(f"第二个文档的元数据为{data[1].metadata}\n")


print(f"第三个文档的内容为{data[2].page_content}\n")
# {'source': '/mnt/d/Users/xsc/Desktop/点赞服务面试复盘.md', 'category_depth': 1, 'languages': ['zho'], 'file_directory': '/mnt/d/Users/xsc/Desktop', 'filename': '点赞服务面试复盘.md', 'filetype': 'text/markdown', 'last_modified': '2026-03-23T21:59:04', 
#  'parent_id': '20a0d053e83a36452c4161d1e1b1539e', 
#  'category': 'Title', ''
# 'element_id': '689c5994ea5357c6e6797e3287ea7244'}
print(f"第三个文档的元数据为{data[2].metadata}\n")

# md文档加载器会根据md的文件，将md拆分为多个文档，元素类型有Title、Table、Image等
# 但是加载器的默认规则要么是将整个文档加载为一个Document对象，要么是根据md的结构将其拆分为多个Document对象，无法根据自定义规则进行拆分
# 一个问题的多个回答都不能被分到一个文档中
# 我们可以利用文档分割器，自定义规则，将md文档拆分为多个文档对象