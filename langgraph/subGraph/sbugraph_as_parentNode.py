from typing import TypedDict
from langgraph.graph import StateGraph
from langgraph.constants import START, END

# 子图状态
class ChildState(TypedDict):
    input: str
    parent: str

# 主图状态
class ParentState(TypedDict):
    parent: str

# 子图节点
def child_node1(state: ChildState):
    return {"input": " hi i am child node1"}

def child_node2(state: ChildState):
    return {"parent": state["parent"] + state["input"]}

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
    return {"parent": "hi" + state["parent"]}

parent_graph = (
    StateGraph(ParentState)
    .add_node(node1)
    .add_node("node2", child_graph)
    .add_edge(START, "node1")
    .add_edge("node1", "node2")
    .add_edge("node2", END)
    .compile()
)

    # 如果要让子图和主图都拥有短期记忆，可以在编译主图时指定checkpoint，这个状态会直接传递子图
# print(parent_graph.invoke({"parent": "小明"}))
for chunk in parent_graph.stream({"parent":"小明"}, subgraphs=True):
    print(chunk)