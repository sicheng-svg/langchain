from langgraph.graph import StateGraph
from langgraph.constants import START, END
from langgraph.prebuilt import ToolNode, tools_condition

from src.common.context import context_schema
from src.node.reserve import get_title, get_phone, get_id, generate_order, add_reserve_message, call_orders
from src.state.reserve import reserveState

def generate_or_end(state: reserveState):
    lastMsg = state["messages"][-1]
    if len(lastMsg.tool_calls) > 0:
        return "generate_order"
    return END

reserveGraph = (
    StateGraph(reserveState, context_schema=context_schema)
    .add_node(get_title)
    .add_node(get_phone)
    .add_node(get_id)
    .add_node(add_reserve_message)
    .add_node(call_orders)
    .add_node("generate_order", ToolNode([generate_order], name="generate_order"))
    .add_edge(START, "get_title")
    .add_edge("get_title", "get_phone")
    .add_edge("get_phone", "get_id")
    .add_edge("get_id", "add_reserve_message")
    .add_edge("add_reserve_message", "call_orders")
    .add_conditional_edges(
        "call_orders",
        tools_condition,
        {"__end__": END, "tools":"generate_order"}
    )
    .add_edge("generate_order", "call_orders")
    .compile()
)