from typing import TypedDict, List, Annotated
import operator
from langchain_core.messages import AnyMessage
from langgraph.types import Overwrite
from langgraph.graph import StateGraph
from langgraph.constants import START, END

class State(TypedDict):
    # 追加更新message
    messages: Annotated[List[str], operator.add]

# 定义节点
def node1(state: State):
    return {"messages":["first node"]}
def node2(state: State):
    # 在追加更新的基础上，覆盖之前的内容
    return {"messages": Overwrite(["second node"])}
    # return {"messages": ["second node"]}

# 定义图，添加节点和边
graph = StateGraph(State)
graph.add_node(node1)
graph.add_node(node2)
graph.add_edge(START, "node1")
graph.add_edge("node1", "node2")
graph.add_edge("node2", END)

# 编译图
sys = graph.compile()
# 执行图
result = sys.invoke({
    "messages": [""]
})

# ['', 'first node', 'second node']  未使用Overwrite关键字
# ['second node'] 使用Overwrite关键字
print(result["messages"])