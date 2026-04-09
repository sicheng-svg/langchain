from typing import TypedDict
from langgraph.graph import StateGraph, START
from langchain_openai import ChatOpenAI

# 定义状态​
class State(TypedDict):
    input: str
    output: str

# 初始化模型​
model = ChatOpenAI(model="deepseek-chat", base_url="https://api.deepseek.com/v1")
def llm_node(state: State):
    return {"output": model.invoke([
        {"role": "system", "content": "你是一个乐于助人的助手。"},
        {"role": "user", "content": state["input"]}
    ])
}
# 构建图​
builder = StateGraph(State)
builder.add_node(llm_node)
builder.add_edge(START, "llm_node")
graph = builder.compile()
# 流式输出 LLM Tokens​
# 输出格式为(message_chunk, metadata) 元组。​
for token_chunk, metadata in graph.stream(
    {"input": "请解释什么是机器学习？ 50个字回答"},
    stream_mode="messages"
):
    if token_chunk.content:
        # 逐 Token 输出​
        print(token_chunk.content, end="", flush=True)