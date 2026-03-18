from langchain_openai import ChatOpenAI
from langchain_core.messages import HumanMessage, AIMessage
from langchain_core.chat_history import BaseChatMessageHistory, InMemoryChatMessageHistory
from langchain_core.runnables.history import RunnableWithMessageHistory

# invoke调用时无状态的，每一次都是独立调用
# 为了实现多轮对话，我们可以缓存历史消息将新问题与历史消息一同发送给chatmodel
model1 = ChatOpenAI(
    model = "deepseek-chat",
    base_url = "https://api.deepseek.com/v1",
)

# model1.invoke("你好，我是小明!").pretty_print()

# model1.invoke("你知道我是谁么？").pretty_print()

# RunnableWithMessageHistory 
model2 = ChatOpenAI(
    model = "deepseek-chat",
    base_url = "https://api.deepseek.com/v1"
)

store = {}
def get_session_history(session_id: str)->BaseChatMessageHistory:
    if session_id not in store:
        # InMemoryChatMessageHistory() 将消息存储在内存列表中
        store[session_id] = InMemoryChatMessageHistory()
    return store[session_id]

config = {
    "configurable":{
        "session_id": "1",
    }
}
# 包装model，使其具备管理历史聊天的功能
mode_with_message_history = RunnableWithMessageHistory(model2, get_session_history)


mode_with_message_history.invoke([
        HumanMessage(content="我是小明")
    ],
config=config).pretty_print()

mode_with_message_history.invoke([
    HumanMessage(content="你知道我是谁么，叫出我的名字")
],config=config).pretty_print()