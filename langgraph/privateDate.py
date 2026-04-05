from langgraph.graph import StateGraph, START, END
from typing_extensions import TypedDict
# 公共状态（最终输出中可见）​
class OverallState(TypedDict):
    final_result: str
# 节点1的私有输出​
class Node1Output(TypedDict):
    sensitive_data: str # 这个字段不会出现在最终状态中​
# 节点2需要的输入（包含私有数据）​
class Node2Input(TypedDict):
    sensitive_data: str
def node_1(state: OverallState) -> Node1Output:
    private_data = "这是敏感信息"
    print(f"Node1: 获取到敏感数据，但不会暴露给最终输出")
    return {"sensitive_data": private_data}
def node_2(state: Node2Input) -> OverallState:
    print(f"Node2: 处理敏感数据: {state['sensitive_data']}")
    # 处理数据，返回清理后的结果​
    return {"final_result": "清理后的处理结果"}
def node_3(state: OverallState) -> OverallState:
    print(f"Node3: 只能看到最终结果: {state['final_result']}")
    return {"final_result": state["final_result"] + " - 完成"}
# 构建图​
builder = StateGraph(OverallState)
# add_sequence：支持添加一系列节点，按所给的顺序执行。​
# 注意：我们使用 add_sequence 但类型系统会处理私有状态​
builder.add_sequence([node_1, node_2, node_3])
builder.add_edge(START, "node_1")
graph = builder.compile()
# 测试​
# Node1: 获取到敏感数据，但不会暴露给最终输出
# Node2: 处理敏感数据: 这是敏感信息
# Node3: 只能看到最终结果: 清理后的处理结果

# 最终输出: {'final_result': '清理后的处理结果 - 完成'}
response = graph.invoke({"final_result": "initial"})
print(f"\n最终输出: {response}")