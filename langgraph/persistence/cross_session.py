from os import name
import uuid
from langgraph.store.memory import InMemoryStore
from langgraph.store.postgres import PostgresStore
from langgraph.checkpoint.postgres import PostgresSaver
from langchain.embeddings import init_embeddings
from openai import api_key


# 内存级store
# embedding = OpenAIEmbeddings(
#     model="BAAI/bge-m3",
#     base_url="https://api.siliconflow.cn/v1",
#     api_key="sk-ujtqlhorbfsiemxyvltkjyocbfiulbdfbjdoqkrrtydlvmzv",
# )

store1 = InMemoryStore()
store = InMemoryStore(
    index={
        "embed": init_embeddings(
            "openai:BAAI/bge-m3", 
            base_url="https://api.siliconflow.cn/v1", 
            api_key="sk-ujtqlhorbfsiemxyvltkjyocbfiulbdfbjdoqkrrtydlvmzv",
        ),
        "dims":1200,
        "fields":["$"],
    },
)

# # 定义命名空间
# user_id = "user_001"
# namespace1 = (user_id, "preference", "food")
# namespace2 = (user_id, "preference", "music")
# 
# # 定义一条记忆 kv
# memory_id1 = str(uuid.uuid4())
# memory_content1 = {"中餐":["米饭", "大盘鸡"]}
# 
# memory_id2 = str(uuid.uuid4())
# memory_content2 = {"中式音乐": ["海屿你"]}
# 
# # 存储store中
# store.put(namespace=namespace1, key=memory_id1, value=memory_content1)
# store.put(namespace=namespace2, key=memory_id2, value=memory_content2)

# 记忆读取
# [Item(
#     namespace=['user_001', 'preference'], 
#     key='fbaabbfd-8417-4aa0-8561-5648269bc139', 
#     value={
#         'food': 
#             ['meat', 'pizza'], 
#         'sports': 
#         ['run', 'swiming']
#     }, 
#     created_at='2026-04-07T07:37:42.789498+00:00', 
#     updated_at='2026-04-07T07:37:42.789503+00:00', 
#       score=None
# )]
# namespace = (user_id, "preference",)
# result = store.get(namespace, key)

# result = store.search(namespace, query="我最喜欢的音乐", limit=2)
# for memory in result:
#     print(memory.dict())

DB_URI = "postgresql://postgres:Xsc.200411@127.0.0.1:5432/postgres"
with (
    PostgresSaver.from_conn_string(DB_URI) as checkpointer,
    PostgresStore.from_conn_string(DB_URI) as store2,
    ):
    # 定义命名空间
    store2.setup()
    user_id = "user_001"
    namespace1 = (user_id, "preference", "food")
    # 定义一条记忆 kv
    memory_id1 = str(uuid.uuid4())
    memory_content1 = {"中餐":["米饭", "大盘鸡"]}
    # 存储store中
    # store2.put(namespace=namespace1, key=memory_id1, value=memory_content1)

    namespace = (user_id, "preference","food")
    result = store2.get(namespace, "1c802349-bfab-4333-af93-5f02e487e784")
    print(result)
