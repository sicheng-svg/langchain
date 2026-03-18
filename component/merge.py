from langchain_openai import ChatOpenAI
from langchain_core.messages import SystemMessage, HumanMessage,AIMessage,merge_message_runs

model = ChatOpenAI(
    model="deepseek-chat",
    base_url="https://api.deepseek.com/v1"
)

# merge_message_runs合并message，将连续相同类型的message进行合并
# 历史消息记录
messages = [
    SystemMessage("你是一个聊天助手。"),
    SystemMessage("你总是以笑话回应。"),
    HumanMessage("为什么要使用 LangChain?"),
    HumanMessage("为什么要使用 LangGraph?"),
    AIMessage("因为当你试图让你的代码更有条理时，LangGraph 会让你感到“节点”是个好主意！"),
    AIMessage("不过别担心，它不会“分散”你的注意力！"),
    HumanMessage("选择LangChain还是LangGraph?"),
]

# print(merge_message_runs(messages))

# 他也是runnable的，可以放进管道
merged = merge_message_runs()
chain = merged | model
chain.invoke(messages).pretty_print()

# 在实际项目中，merge | filter | trim 通常一起使用
# 先合并（减少冗余）→ 再过滤（去掉不需要的类型）→ 最后裁剪（控制 token 量）→ 发给模型。逻辑上从粗到细，最干净。