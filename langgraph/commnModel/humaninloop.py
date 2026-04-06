from langgraph.graph import StateGraph, START, END
from langgraph.types import interrupt, Command
from langgraph.checkpoint.memory import InMemorySaver
from typing import TypedDict

# 场景：AI 生成一封邮件，人类审核后决定发送还是修改

class State(TypedDict):
    topic: str        # 邮件主题
    draft: str        # AI 生成的草稿
    approved: bool    # 是否批准

# 节点1：AI 生成邮件草稿
def generate_draft(state: State):
    # 实际项目中这里调用 LLM
    draft = f"尊敬的客户，关于「{state['topic']}」，我们已经处理完毕..."
    print(f"\n📝 AI 生成的草稿：\n{draft}")
    return {"draft": draft}

# 节点2：人类审核（关键节点）
def human_review(state: State):
    # interrupt() 会暂停图的执行，等待人类输入
    # 参数是展示给人类看的信息
    decision = interrupt({
        "message": "请审核以下邮件草稿",
        "draft": state["draft"],
        "options": "输入 'approve' 批准发送，或输入修改意见"
    })
    
    # 人类恢复执行后，decision 就是人类传入的值
    if decision == "approve":
        return {"approved": True}
    else:
        # 人类给了修改意见，更新草稿
        return {"draft": f"[根据反馈修改] {decision}", "approved": False}

# 节点3：发送邮件
def send_email(state: State):
    print(f"\n✅ 邮件已发送：{state['draft']}")
    return {}

# 路由：根据审核结果决定下一步
def after_review(state: State):
    if state.get("approved"):
        return "send_email"
    else:
        return "generate_draft"  # 回到生成节点重新来

# 构建图
builder = StateGraph(State)
builder.add_node(generate_draft)
builder.add_node(human_review)
builder.add_node(send_email)

builder.add_edge(START, "generate_draft")
builder.add_edge("generate_draft", "human_review")
builder.add_conditional_edges("human_review", after_review)
builder.add_edge("send_email", END)

# 必须使用 checkpointer，否则 interrupt 无法工作
checkpointer = InMemorySaver()
graph = builder.compile(checkpointer=checkpointer)

# ========== 执行流程 ==========

# 第一次调用：图会运行到 interrupt() 处暂停
config = {"configurable": {"thread_id": "email-001"}}
result = graph.invoke({"topic": "订单退款"}, config)
print(f"\n⏸️  图已暂停，等待人类审核...")

# 此时图的状态已经被 checkpointer 保存了
# 在实际应用中，这里可能是前端界面等待用户点击按钮

# 第二次调用：人类传入审核结果，恢复执行
# 使用 Command 传入人类的决定
result = graph.invoke(
    Command(resume="approve"),  # 传入 "approve" 批准
    config
)
print(f"\n最终结果：{result}")