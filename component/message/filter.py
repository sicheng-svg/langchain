from langchain_openai import ChatOpenAI
from langchain_core.messages import SystemMessage, HumanMessage, AIMessage,filter_messages


model = ChatOpenAI(
    model="deepseek-chat",
    base_url = "https://api.deepseek.com/v1",
)

# 历史消息记录
messages = [
    SystemMessage("你是一个聊天助手", id="1"),
    HumanMessage("示例输入", id="2"),
    AIMessage("示例输出", id="3"),
    HumanMessage("真实输入", id="4"),
    AIMessage("真实输出", id="5"),
]

# 按类型进行筛选，下面两个调用方式都是合理的
print(filter_messages(include_types="human").invoke(messages))
print(filter_messages(messages, include_types="human"))

#按id进行筛选
print(filter_messages(messages, exclude_ids=["1", "5"]))


# types和ids都可以选择是inclue还是exclude
print(filter_messages(messages, include_types="human", exclude_ids=["4"]))
# 最常见的用途是在多 Agent 系统里，消息列表里混着不同 Agent 的消息（通过 name 字段区分），你只想让某个 Agent 看到跟它相关的那部分：