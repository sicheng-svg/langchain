from typing import TypedDict, Annotated
from langgraph.graph import StateGraph
from langgraph.constants import START, END
import operator

# 1.状态定义
# 在langgraph中，状态默认更新都是覆盖更新，如果我们需要累加更新，则需要使用Annotated来标记需要累加更新的字段，并指定累加操作符。
class PackageState(TypedDict):
    # normal state
    # package Id
    # package origin
    # package destination
    package_id: str
    origin: str
    destination: str

    # 配送状态
    status: str # 待揽收、已揽收、运输中、派送中、已签收
    history: Annotated[list[str], operator.add]
    total_distance: Annotated[float, operator.add]

    # 备注
    note: str # 加急、普通


# 2.节点定义 本质上就是定义一系列函数,这些函数接受状态，然后返回更新后的状态
# 揽收节点
def pickup_node(state: PackageState) -> PackageState:
    # 模拟揽收过程
    return {
        "status": "已揽收",
        "history": [f"包裹从{state['origin']}揽收"],
        "total_distance": 0.0,
    }
# 分拣节点
def sorting_node(state: PackageState) -> PackageState:
    # 模拟分拣过程
    dst = state['destination']
    if "北京" in dst:
        next = "北京分拣中心"
    elif "上海" in dst:
        next = "上海分拣中心"
    else:        
        next = "其他分拣中心"

    return {
        "status": "运输中",
        "history": [f"包裹在{next}分拣中心分拣"],
        "total_distance": 100.0,
    }

# 普通运输节点
def normal_transport_node(state: PackageState) -> PackageState:
    # 模拟运输过程
    return {
        "status": "运输中",
        "history": [f"包裹正在运输"],
        "total_distance": 200.0,
    }
# 加急运输节点
def express_transport_node(state: PackageState) -> PackageState:
    # 模拟加急运输过程
    return {
        "status": "运输中",
        "history": [f"包裹正在加急运输"],
        "total_distance": 150.0,
    }
# 派送节点
def delivery_node(state: PackageState) -> PackageState:
    # 模拟派送过程
    return {
        "status": "派送中",
        "history": [f"包裹正在派送"],
        "total_distance": 50.0,
    }

# 3.定义图
delivery = StateGraph(PackageState)

# 4. 添加节点
# 第一个参数是给节点重命名，如果没有指定，默认就是函数名
delivery.add_node("pickup", pickup_node)
delivery.add_node("sorting", sorting_node)
delivery.add_node("normal_transport", normal_transport_node)
delivery.add_node("express_transport", express_transport_node)
delivery.add_node("delivery", delivery_node)

# 5. 添加边
# 添加固定边
delivery.add_edge(START, "pickup")
delivery.add_edge("pickup", "sorting")

# 添加条件边
def select_next_node(state: PackageState) -> str:
    if state['note'] == "加急":
        return "express_transport"
    else:
        return "normal_transport"
delivery.add_conditional_edges(
    "sorting", # 开始
    select_next_node,# 条件函数，接受当前状态，返回一个字符串，表示满足哪个条件
    # 如果想要直接写列表，则选择函数返回的字符串必须和列表中的某个值完全匹配，否则会报错
    # 如果不相同，可以将列表改为字典，进行手动映射
    ["normal_transport", "express_transport"] # 可能的目标节点列表，必须包含条件函数返回的所有可能值
)
# 添加固定边
delivery.add_edge("normal_transport", "delivery")
delivery.add_edge("express_transport", "delivery")
delivery.add_edge("delivery", END)

# 6. 编译图
delivery_sys = delivery.compile()

# 7. 执行图
# 8. 测试配送​
test_packages = [
    {
        "package_id": "P001",
        "origin": "北京",
        "destination": "上海",
        "note": "普通",
        "history": [],
        "total_distance": 0
    },
    {
        "package_id": "P002",
        "origin": "广州",
        "destination": "乌鲁木齐",
        "note": "加急",
        "history": [],
        "total_distance": 0
    }
]
for package in test_packages:
    print(f"\n配送包裹: {package['package_id']}")
    result = delivery_sys.invoke(package)
    print("最终状态:", result["status"])
    print("配送历史:", result["history"])
    print("总里程:", result["total_distance"])