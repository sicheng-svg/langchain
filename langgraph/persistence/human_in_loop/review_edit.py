from typing import TypedDict
from langgraph.checkpoint.memory import InMemorySaver
from langgraph.graph import StateGraph, START, END
from langgraph.types import Command, interrupt

class ReviewState(TypedDict):
    generated_text: str
def review_node(state: ReviewState):
    # 请求审阅者编辑生成的内容​
    updated = interrupt({
        "instruction": "查看并编辑此内容",
        "content": state["generated_text"],
    })
    return {"generated_text": updated}

# 构建图​
builder = StateGraph(ReviewState)
builder.add_node("review", review_node)
builder.add_edge(START, "review")
builder.add_edge("review", END)

graph = builder.compile(checkpointer=InMemorySaver())

config = {"configurable": {"thread_id": "42"}}
initial = graph.invoke({"generated_text": "初稿"}, config=config)
print(initial["__interrupt__"]) # -> [Interrupt(value={'instruction': ...,'content': ...})]

# 用审阅者编辑后的文本恢复执行​
final_state = graph.invoke(
    Command(resume="审稿后的改进稿"),
    config=config,
)
print(final_state["generated_text"]) # -> "审稿后的改进稿"​