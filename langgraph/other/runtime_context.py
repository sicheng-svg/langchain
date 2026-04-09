from typing import TypedDict
from dataclasses import dataclass
from langgraph.runtime import Runtime
from langgraph.graph import StateGraph
from langgraph.constants import START, END

# 运行时上下文
class State(TypedDict):
    messages: list[str]
    user_name: str

# 静态运行时上下文，不可修改
@dataclass
class Context:
    user_id: str
    language: str

def node(state: State, runtime: Runtime[Context]):
    if runtime.context.language == "en":
        greeting = "hello"
    else:
        greeting = "你好"
    username = state["user_name"]
    return {"messages":[f"{greeting} {username}!!!"]}

builder = StateGraph(State, context_schema=Context)
builder.add_node(node)
builder.add_edge(START, "node")
builder.add_edge("node", END)

graph = builder.compile()
result = graph.invoke({"messages":"", "user_name": "Soren"}, context={"user_id":"123", "language":"ch"})
print(result)