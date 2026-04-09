from langgraph.graph import START, StateGraph
from langgraph.checkpoint.memory import InMemorySaver
from langgraph.types import interrupt, Command
from typing_extensions import TypedDict
class State(TypedDict):
    foo: str
# 子图​
def subgraph_node_1(state: State):
    print("sub_node_1")
    return {}
def subgraph_node_2(state: State):
    print("sub_node_2")
    value = interrupt("输入值:")
    return {"foo": state["foo"] + value}
subgraph_builder = StateGraph(State)
subgraph_builder.add_node(subgraph_node_1)
subgraph_builder.add_node(subgraph_node_2)
subgraph_builder.add_edge(START, "subgraph_node_1")
subgraph_builder.add_edge("subgraph_node_1", "subgraph_node_2")
subgraph = subgraph_builder.compile()
# 主图​
def node_1(state: State):
    print("node_1")
    response = subgraph.invoke({"foo": state["foo"]})
    return {"foo": response["foo"]}
builder = StateGraph(State)
builder.add_node("node_1", node_1)
builder.add_edge(START, "node_1")
graph = builder.compile(checkpointer=InMemorySaver())
config = {"configurable": {"thread_id": "1"}}
graph.invoke({"foo": ""}, config)
print(graph.invoke(Command(resume="bar"), config))