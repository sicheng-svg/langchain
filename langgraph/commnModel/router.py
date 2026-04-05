from langchain.chat_models import init_chat_model
from langgraph.constants import START, END
from langgraph.graph import StateGraph
from typing_extensions import Literal, TypedDict
from pydantic import BaseModel, Field
class State(TypedDict):
    input: str # 用户输入​
    decision: str # 路由决策​
    output: str # 最终输出​

# 定义路由决策的数据结构​
class Route(BaseModel):
    step: Literal["pre_sale", "after_sale", "technical"] = Field(
        description="根据用户问题类型决定路由到售前、售后还是技术处理"
)

# 路由决策节点​
def model_call_router(state: State):
    model = init_chat_model(
    model="qwen3:4b",
    model_provider="ollama",
)
    decision = model.with_structured_output(Route, method="function_calling").invoke(state["input"])
    return {"decision": decision.step}

# 三个不同的处理节点​
def pre_sale_handler(state: State):
    return {"output": "售前咨询已处理，处理内容....."}
def after_sale_handler(state: State):
    return {"output": "售后问题已处理，处理内容....."}
def technical_handler(state: State):
    return {"output": "技术问题已处理，处理内容....."}
# 路由函数 - 根据决策返回下一个节点​
def route_decision(state: State):
    if state["decision"] == "pre_sale":
        return "pre_sale_handler" # 去售前处理节点​
    elif state["decision"] == "after_sale":
        return "after_sale_handler" # 去售后处理节点​
    elif state["decision"] == "technical":
        return "technical_handler" # 去技术处理节点​

# 构建路由工作流​
router_builder = StateGraph(State)
# 添加处理节点​
router_builder.add_node(pre_sale_handler)
router_builder.add_node(after_sale_handler)
router_builder.add_node(technical_handler)
router_builder.add_node(model_call_router)
# 先经过路由决策​
router_builder.add_edge(START, "model_call_router")
# 条件边：根据路由结果选择分支​
router_builder.add_conditional_edges(
    "model_call_router",
    route_decision,
    ["pre_sale_handler", "after_sale_handler", "technical_handler"]
)
# 所有分支最终都结束​
router_builder.add_edge("pre_sale_handler", END)
router_builder.add_edge("after_sale_handler", END)
router_builder.add_edge("technical_handler", END)
router_workflow = router_builder.compile()
# 测试​
test_cases = [
    "我想了解一下你们产品的价格和功能", # 售前咨询
    "我购买的产品有质量问题，需要退货", # 售后问题​
    "这个软件安装后无法正常运行，报错代码0x80070005", # 技术问题​
    "请问你们的售后服务政策是什么", # 售前咨询​
    "我的订单已经发货但还没收到", # 售后问题​
    "如何配置数据库连接参数" # 技术问题​
]
for test_case in test_cases:
    print("*" * 50)
    result = router_workflow.invoke({"input": test_case})
    print(f"用户问题：{test_case}\n{result['output']}")