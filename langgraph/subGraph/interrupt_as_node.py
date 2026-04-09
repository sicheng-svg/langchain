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

builder = StateGraph(State)
builder.add_node("node_1", subgraph)
builder.add_edge(START, "node_1")
graph = builder.compile(checkpointer=InMemorySaver())
config = {"configurable": {"thread_id": "1"}}
graph.invoke({"foo": ""}, config)
parent_state = graph.get_state(config)
# 访问子图状态只能在子图被中断时才可用。​
# 一旦恢复了图，将无法访问子图状态。​
subgraph_state = graph.get_state(config, subgraphs=True).tasks[0].state
print(subgraph_state)
print(graph.invoke(Command(resume="bar"), config))