from langchain.chat_models import init_chat_model
from langchain_core.messages import HumanMessage
from langgraph.graph import MessagesState, StateGraph
from langgraph.graph.message import REMOVE_ALL_MESSAGES
from langgraph.types import Overwrite
from langgraph.constants import START, END
from langgraph.checkpoint.memory import InMemorySaver
from langchain_core.messages import trim_messages, RemoveMessage
from oxmsg import Message

model = init_chat_model(
    model="deepseek-chat", 
    model_provider="openai", 
    base_url="https://api.deepseek.com/v1",
)

# def call_llm(state: MessagesState):
#     messages = trim_messages(
#         state["messages"],
#         strategy="last",
#         token_counter=len,
#         max_tokens=10,
#         start_on="human",
#         end_on=("human", "tool"), 
#     )
#     result = model.invoke(messages)
#     return {
#         "messages":[result]
#     }

# def call_llm(state: MessagesState):
#     # 删除消息
#     # 删除全部消息
#     return {"messages": Overwrite([])}
#     # RemoveMessage(id=REMOVE_ALL_MESSAGES)
# 
#     # 使用RemoveMessage 删除指定id的meessage
#     # 需要注意，直接调用RemoveMessage不能删除要求，要通过return一个RemoveMessage返回的列表才可以
#     # RemoveMessage只能删除operator.add的消息
#     if len(state["messages"]) > 6:
#         return {"messages": [RemoveMessage(id=msg.id) for msg in state["messages"][:6]]}
# 
#     return {
#         "messages": [model.invoke(state["messages"])]
#     }

class State(MessagesState):
    summary: str

def call_llm(state: State):
    # 使用历史总结+最新消息发起调用​
    summary = state.get("summary", "")
    messages = model.invoke([HumanMessage(content=summary)] +
    state["messages"])
    return {"messages": messages}

def summarize_conversation(state: State):
    # 1. 创建总结提示词​
    summary = state.get("summary", "")
    if summary: # 有摘要，扩展​
        summary_message = (
            f"这是到目前为止的对话摘要：{summary}\n\n"
            "基于上面的新消息扩展摘要："
        )
    else: # 无摘要，新增​
        summary_message = "创建上面对话的摘要："
    # 2. 生成新总结：【消息列表】+【历史总结】调用模型​
    messages = state["messages"] + [HumanMessage(content=summary_message)]
    response = model.invoke(messages)
    # 3. 删除历史对话：除了最新的AI消息,都可以删除​
    return {
    "summary": response.content, # 历史总结​
    "messages": [RemoveMessage(id=m.id) for m in state["messages"][:-1]] #保留最后的消息是为了打印结果​
}

builder = StateGraph(MessagesState)
builder.add_node(call_llm)
builder.add_node(summarize_conversation)
builder.add_edge(START, "call_llm")
builder.add_edge("call_llm", "summarize_conversation")
builder.add_edge("summarize_conversation", END)
graph = builder.compile(checkpointer=InMemorySaver())

# 线程级持久化
config = {"configurable": {"thread_id": "1"}}
result1 = graph.invoke({"messages": "hi, my name is bob"}, config)
# result1["messages"][-1].pretty_print()

result2 = graph.invoke({"messages": "write a short poem about cats"}, config)
# result2["messages"][-1].pretty_print()

result3 = graph.invoke({"messages": "now do the same but for dogs"}, config)
# result3["messages"][-1].pretty_print()

final_response = graph.invoke({"messages": "what's my name?"}, config)
for msg in final_response["messages"]:
    msg.pretty_print()
# final_response["messages"][-1].pretty_print()