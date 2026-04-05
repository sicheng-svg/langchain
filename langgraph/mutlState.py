from typing import TypedDict
from langgraph.graph import StateGraph
from langgraph.constants import START, END

# 在一个图中，可以定义多个状态
class InputState(TypedDict):
    question: str
class OutputState(TypedDict):
    answer: str
class State(InputState, OutputState):
    pass

def node(state: InputState):
    return {
        "question": [state["question"]],
        "answer": ["i am a answer"],
    }

graph = StateGraph(State, input_schema=InputState, output_schema=OutputState)
graph.add_node(node)
graph.add_edge(START, "node")
graph.add_edge("node", END)

sys = graph.compile()
result = sys.invoke({
    "question": "i am a question"
})

# 使用input_schema 和 output_schema就可以进行输入和输出的校验，避免返回全量状态。
# {'answer': ['i am a answer']}
print(result)