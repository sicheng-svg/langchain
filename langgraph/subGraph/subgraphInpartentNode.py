from typing import TypedDict
from langgraph.graph import StateGraph
from langgraph.constants import START, END

# 子图状态
class ChildState(TypedDict):
    input: str
    output: str

# 主图状态
class ParentState(TypedDict):
    query: str

# 子图节点
def child_node1(state: ChildState):
    return {"input": "hi i am child node1"}

def child_node2(state: ChildState):
    return {"output": state["output"] + state["input"]}

child_graph =(
    StateGraph(ChildState)
    .add_node(child_node1)
    .add_node(child_node2)
    .add_edge(START, "child_node1")
    .add_edge("child_node1", "child_node2")
    .add_edge("child_node2", END)
    .compile()
)
# print(child_graph.invoke({"output":"hi i am soren"}))

# 主图节点
def node1(state: ParentState):
    return {"query": "hi" + state["query"]}

def node2(state: ParentState):
    response = child_graph.invoke({"output": "hhhhhhhhhhhhhhhh"})
    return {"query": response["output"]}

parent_graph = (
    StateGraph(ParentState)
    .add_node(node1)
    .add_node(node2)
    .add_edge(START, "node1")
    .add_edge("node1", "node2")
    .add_edge("node2", END)
    .compile()
)

# print(parent_graph.invoke({"query": "小明"}))
for chunk in parent_graph.stream({"query":"小明"}, subgraphs=True):
    print(chunk)