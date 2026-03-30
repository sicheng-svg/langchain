from langchain_text_splitters import PythonCodeTextSplitter

# 字符串⽂档
PYTHON_CODE = """
def hello_world():
print("Hello, World!")
def hello_python():
print("Hello, Python!")
"""
python_splitter = PythonCodeTextSplitter(
    chunk_size=50, 
    chunk_overlap=0
)
python_docs = python_splitter.create_documents([PYTHON_CODE])

for document in python_docs[:2]:
    print("*" * 30)
    print(f"{document}\n")