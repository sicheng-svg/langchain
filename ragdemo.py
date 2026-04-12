from langchain_openai import OpenAIEmbeddings, ChatOpenAI
from langchain_redis import RedisConfig, RedisVectorStore
from langchain_core.output_parsers import StrOutputParser
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.runnables import RunnablePassthrough

model = ChatOpenAI(
    model = "deepseek-chat",
    base_url = "https://api.deepseek.com/v1",
)

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
# 定义 Redis 向量存储​
vector_store = RedisVectorStore(embedding, config=config)

# 生成检索器​
retriever = vector_store.as_retriever()

# 定义提示词模板​
prompt = ChatPromptTemplate.from_messages(
    [
        (
            "human",
            """你是负责回答问题的助手。使用以下检索到的上下文片段来回答问题。如果你不知
            道答案，就说你不知道。最多只用三句话，回答要简明扼要。
            Question: {question}
            Context: {context}
            Answer:""",
        ),
    ]
)
# 将文档转换为字符串​
def format_docs(docs):
    return "\n\n".join(doc.page_content for doc in docs)
# 定义链​
rag_chain = (
    {"context": retriever | format_docs, "question": RunnablePassthrough()}
    | prompt
    | model
    | StrOutputParser()
)
# 执行链，流式输出​
while True:
    query = input("##: ")
    if query.lower() in ["exit", "quit"]:
        break
    for chunk in rag_chain.stream(query):
        print(chunk, end="", flush=True)
    print("\n")

from langgraph.graph import MessagesState
from typing import TypedDict

class State(MessagesState):
    user_preference: dict # 用户偏好信息
    user_intent: str      # 用户意图，用来让大模型智能路由

    city: str # 城市​
    budget_min: float # 最低预算​
    budget_max: float # 最高预算​
    district: str # 区域​
    room_type: str # 房屋类型​
    orientation: str # 朝向​
    room_count: int # 推荐数量​
    others: str # 其它要求​ 

    title: str
    phone: str
    id: str

# 推荐子图执行完后，会打印提示消息，让用户决定是否要进行预定
class need_reserve_output(TypedDict):
    reserve: str