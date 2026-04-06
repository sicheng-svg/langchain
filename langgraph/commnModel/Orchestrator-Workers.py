from langchain.chat_models import init_chat_model
from langchain_core.messages import HumanMessage
from langgraph.graph import StateGraph
from langgraph.constants import START, END
from langgraph.types import Send
from typing import TypedDict, Annotated
from pydantic import BaseModel
import operator

# 编排-工作者模式
# 由编排者根据输入动态选择需要哪些工作者进行执行，随后将所有工作者的结果进行汇总进行返回
# 与并行化不同在于，并行化fan-out后续的节点都是固定的。构建图的时候就知道接下来进行那个节点。而编排工作者，是根据编排者的输出来动态决定后续需要哪些节点

# 定义状态
class State(TypedDict):
    topic: str
    tasks: list
    answers: Annotated[list, operator.add]
    finallyAns: str
# 定义结构化输出，让大模型输出指定的内容
class Task(BaseModel):
    name: str
    description: str
class Tasks(BaseModel):
    tasks: list[Task]

# 创建模型
model = init_chat_model(model="qwen3:4b", model_provider="ollama")
planner = model.with_structured_output(Tasks)

# 创建节点
# 1.编排者
def orchestrator(state: State):
    print("------------------- 编排者这在进行任务拆分-----------------")
    result = planner.invoke([
        HumanMessage(content=f"为主题'{state['topic']}'制定报告大纲，包含3个章节"),
    ])
    return {
        "tasks": result.tasks
    }
# 2.工作者
def worker1(state: State):
    """根据编排者分配的任务进行执行"""
    print("------------------- 工作者正在进行执行任务-----------------")
    task = state["task"]
    result = model.invoke([
        HumanMessage(content=f"编写报告章节：{task.name}，内容要求：{task.description}"),
    ])
    return {
        "answers": [result.content]
    }
# 3.汇总者
def synthesizer(state: State):
    print("-------------------结果汇总-----------------")
    answers = state["answers"]
    final_report = "\n\n---\n\n".join(answers)
    return {"finallyAns": final_report}

# 创建图，添加节点和边
def dispatch(state: State):
    worker_tasks = []
    for task in state["tasks"]:
        worker_tasks.append(
        Send("worker1", {"task": task}) # 发送任务给工作者​
    )
    return worker_tasks
builder  = StateGraph(State)
builder.add_node(orchestrator)
builder.add_node(worker1)
builder.add_node(synthesizer)
builder.add_edge(START, "orchestrator")
builder.add_conditional_edges(
    "orchestrator",
    dispatch,
    # 不需要指定可能的节点，因为是动态决定的
)
builder.add_edge("worker1", "synthesizer")
builder.add_edge("synthesizer", END)
# 编译图
workflow = builder.compile()
# 执行图
response =workflow.invoke({"topic": "中国近代史"})
print(response["finallyAns"])