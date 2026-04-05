from typing import TypedDict
from langgraph.constants import START, END
from langgraph.graph import StateGraph

class AnalysisState(TypedDict):
    concept: str # 概念​
    market: str # 市场分析​
    competitor: str # 竞品分析​
    tech: str # 技术分析​
    report: str # 汇总报告​

# 三个并行分析任务​
def market_task(state: AnalysisState):
    return {"market": "用户关注续航、重量、防盗，对骑行社交有兴趣..."}
def competitor_task(state: AnalysisState):
    return {"competitor": "传统品牌智能化不足，互联网品牌续航和售后差..."}
def tech_task(state: AnalysisState):
    return {"tech": "轻量化电池车身、GPS防盗、社交App集成..."}
# 汇总结果​
def combine_results(state: AnalysisState):
    report = f"产品分析报告\n\n"
    report += f"市场分析：\n{state['market']}\n\n"
    report += f"竞品分析：\n{state['competitor']}\n\n"
    report += f"技术分析：\n{state['tech']}\n\n"
    report += "建议：聚焦续航、防盗、社交功能的平衡发展"
    return {"report": report}
# 构建工作流​
builder = StateGraph(AnalysisState)
builder.add_node("market", market_task)
builder.add_node("competitor", competitor_task)
builder.add_node("tech", tech_task)
builder.add_node("combine", combine_results)
# 并行执行三个分析​
builder.add_edge(START, "market")
builder.add_edge(START, "competitor")
builder.add_edge(START, "tech")
# 汇总结果​
builder.add_edge("market", "combine")
builder.add_edge("competitor", "combine")
builder.add_edge("tech", "combine")
builder.add_edge("combine", END)
workflow = builder.compile()
print(workflow.get_graph().draw_mermaid())
# 使用​
result = workflow.invoke({"concept": "城市通勤智能电动自行车"})
print(result["report"])