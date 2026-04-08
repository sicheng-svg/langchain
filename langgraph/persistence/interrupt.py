from langgraph.types import interrupt, Command
from langgraph.constants import START, END
from langgraph.graph import StateGraph
from langgraph.checkpoint.memory import InMemorySaver

class State:
    input: str
    output: str

def node(state: State):
    # 调用interrupt可以使执行流中断，通过参数将信息传递给外部(人类)
    # 通过在外部使用Command命令，恢复执行流，Command传入的参数通过interrupt的返回值交给节点
    result = interrupt("yes or no")
    if result == "yes":
        return { "output": "hi i am a ai"}
    else:
        return {"output": "bye"}

# 定义图，添加节点和边
builder = StateGraph(State)
builder.add_node(node)
builder.add_edge(START, "node")
builder.add_edge("node", END)

# 中断是基于线程持久化的，所以必须指定checkpoint
graph = builder.compile(checkpointer=InMemorySaver())

# 执行
config = {"configurable": {"thread_id":"1"}}
result1 = graph.invoke({"input":"hi"}, config=config)
print(result1["__interrupt__"][0].value)

# interrupt使图暂停后，要通过Command恢复执行，其中resume的内容会传入给节点，通过interrupt的返回值传递给节点
# 使用Command恢复中断时，会从中断的节点头部重新开始执行。而langgraph在底层会维护一张表，节点中有interrupt则存入，第二次进入后如果发现已经执行过了，则标记，然后继续向后执行
# 使用interrupt时，只能传递一些简单的可以序列化的数据
# interrput不能包裹在try/except块中，因为interrupt底层使用一种特殊的异常时流程中断，如果用最大的异常捕捉，则会在langgraph捕捉在处理改异常，导致中断失败
# 中断前的动作要幂等，因为Command恢复后，会从头开始执行，导致部分代码重复执行
# 中断顺序应该固定，而不是写在判断中，避免恢复后无法正确标记已执行的中断
result2 = graph.invoke(Command(resume="no"), config=config)
print(result2)