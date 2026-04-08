from typing import Optional, Literal, TypedDict
from langgraph.types import interrupt, Command
from langgraph.graph import StateGraph
from langgraph.constants import START, END
from langgraph.checkpoint.memory import InMemorySaver

class State(TypedDict):
    detail: str
    status: Optional[Literal["等待", "批准", "拒绝"]]

# 除了使用这种传递状态的方式，也可以在中断节点中，利用Command(goto="")，直接跳转到指定节点
# 跳转的节点不需要在添加条件边
def review_node1(state: State):
    # result是command的resume参数，直接传递是否批准即可
    result = interrupt({
        "question":"是否批准此操作？",
        "details": state["detail"],
        "option": "批准 or 拒绝",
    })
    return {"status": result}

def review_node(state: State):
    # result是command的resume参数，直接传递是否批准即可
    result = interrupt({
        "question":"是否批准此操作？",
        "details": state["detail"],
        "option": "批准 or 拒绝",
    })
    if result == "批准":
        next_node = "allow_node"
    else:
        next_node = "cancel_node"
    return Command(goto=next_node)

def allow_node(state: State):
    return{"status": "批准"}

def cancel_node(state: State):
    return {"status": "取消"}

builder = StateGraph(State)
builder.add_node(review_node)
builder.add_node(allow_node)
builder.add_node(cancel_node)

builder.add_edge(START, "review_node")
def human(state: State):
    if state["status"] == "批准":
        return "allow_node"
    else:
        return "cancel_node"

# builder.add_conditional_edges("review_node", human, ["allow_node", "cancel_node"])
builder.add_edge("allow_node", END)
builder.add_edge("cancel_node", END)

graph = builder.compile(checkpointer=InMemorySaver())

# 执行图
config = {"configurable":{"thread_id":"1234"}}
result = graph.invoke({"detail": "支付30000元", "status": "等待"}, config=config)
print(result["__interrupt__"][0].value)

result2 = graph.invoke(Command(resume="拒绝"), config=config)
print(result2)