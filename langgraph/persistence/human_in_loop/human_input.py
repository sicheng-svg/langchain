from typing import TypedDict
from langgraph.types import interrupt, Command
from langgraph.constants import START, END
from langgraph.graph import StateGraph
from langgraph.checkpoint.memory import InMemorySaver

class State(TypedDict):
    age: int|None

def age_node(state: State):
    prompt = "请输入年龄"
    while True:
        age = interrupt(prompt)
        if isinstance(age, int) and age > 0:
            return {"age": age}
        prompt = "请重新输入年龄，必须是整数且大于0"

builder = StateGraph(State)
builder.add_node(age_node)
builder.add_edge(START, "age_node")
builder.add_edge("age_node", END)

graph = builder.compile(checkpointer=InMemorySaver())
config = {"configurable": {"thread_id": "1"}}

first  = graph.invoke({"age": None}, config)
print(first["__interrupt__"][0].value)

result1 = graph.invoke(Command(resume="三十"), config=config)
print(result1["__interrupt__"][0].value)

result2 = graph.invoke(Command(resume=19), config=config)
print(result2)
