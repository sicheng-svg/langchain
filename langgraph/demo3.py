from langchain.chat_models import init_chat_model
from langchain_openai import OpenAIEmbeddings
from langchain_core.messages import HumanMessage, AnyMessage, ToolMessage
from langchain_community.document_loaders import UnstructuredMarkdownLoader, TextLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_core.vectorstores import InMemoryVectorStore
from langchain_classic.tools.retriever import create_retriever_tool
from typing import TypedDict, Annotated, List, Literal
import operator
from langgraph.graph import MessagesState, StateGraph
from langgraph.constants import START, END
from langgraph.prebuilt import ToolNode, tools_condition
from pydantic import BaseModel, Field

# 模型定义
model = init_chat_model(
    model = "deepseek-chat",
    model_provider="openai",
    base_url="https://api.deepseek.com/v1",
)

# 定义嵌入模型
embedding = OpenAIEmbeddings(
    model="BAAI/bge-m3",
    base_url="https://api.siliconflow.cn/v1",
    api_key="sk-ujtqlhorbfsiemxyvltkjyocbfiulbdfbjdoqkrrtydlvmzv",
    chunk_size=64,
)   

# 加载文档列表​
paths = [
    "/mnt/d/Users/xsc/Desktop/GalaxyDB技术白皮书.md",
    "/mnt/d/Users/xsc/Desktop/云澜市旅游攻略.md",
    "/mnt/d/Users/xsc/Desktop/星辰科技产品手册.md",
    "/mnt/d/Users/xsc/Desktop/龙腾游戏工作室员工手册.md",
]

# docs = [TextLoader(path, encoding="utf-8").load() for path in paths]
docs = [UnstructuredMarkdownLoader(path).load() for path in paths]
docs_list = [item for sublist in docs for item in sublist]

# from_tiktoken_encoder：使用 tiktoken 编码器来计算长度的文本分割器。​
text_splitter = RecursiveCharacterTextSplitter.from_tiktoken_encoder(
    encoding_name="cl100k_base",
    chunk_size=1000,
    chunk_overlap=50
)
doc_splits = text_splitter.split_documents(docs_list)

# 使用内存中向量存储和 OpenAI 嵌入​
vectorstore = InMemoryVectorStore.from_documents(
    documents=doc_splits,
    embedding=embedding,
)

# 使用 LangChain 的预构建 create_retriever_tool 创建检索器工具：​
retriever = vectorstore.as_retriever(search_kwargs={"k": 2})
retriever_tool = create_retriever_tool(
    retriever,
    "retrieve_tool",
    "搜索指定文档返回查询内容"
)

# 工具表，以及工具名映射表
tools = [retriever_tool]
tools_map = {t.name: t for t in tools}
# print(retriever_tool.invoke({"query": "云澜市有什么著名景点？"}))

# ---------------------- langgraph RAG 系统 ----------------------
# 1.定义状态
# 在rag系统中，我们只需要维护一个meesage即可，保存工具调用或者llm临时生成的aimessage，最后整体发给llm进行回答
# 但是对于只有一个messages的状态来说，langgraph已经给我内置了：MessagesState 我们直接使用即可
# class RagMessage(TypedDict):
#     messages: Annotated[List[AnyMessage], operator.add]

# 2.定义节点
# 节点1
def First_call_node(state: MessagesState):
    """
    该节点的任务就是首次携带检索器工具进行执行
    如果返回的AIMessage中包含tool_calls，则说明这次提问需要进行检索
    反之直接生成最终结果
    """
    return {
        "messages": [model.bind_tools(tools).invoke(state["messages"])]
    }

# 节点2
# 定义工具节点时，直接使用ToolNode方法
retireve_node = ToolNode(tools)
# def retireve_node(state: MessagesState):
#     """调用检索工具节点，首节点判断需要使用检索工具，此时调用该工具进行检索"""
#     last_msg = state["messages"][-1]
#     toolMsg = []
#     for tool_call in last_msg.tool_calls:
#         target_tool = tools_map[tool_call["name"]]
#         tool_message = target_tool.invoke(tool_call["args"])
#         toolMsg.append(ToolMessage(
#             content=tool_message,
#             tool_call_id=tool_call["id"],
#         ))
#     return{
#         "messages": toolMsg,
#     }

# 节点3
GENERATE_PROMPT = (
    "你是负责回答问题的助手。 "
    "使用以下检索到的上下文片段来回答问题。 "
    "如果你不知道答案，就说你不知道。 "
    "最多只用三句话，回答要简明扼要。\n"
    "Question: {question} \n"
    "Context: {context}"
)
def finally_llm_call(state: MessagesState):
    """ 接收检索后的结果，以及问题，进行总结回答"""
    question = state["messages"][0].content
    context = state["messages"][-1].content
    prompt = GENERATE_PROMPT.format(question=question, context=context)
    return {
        "messages": [model.invoke([HumanMessage(content=prompt)])]
    }

# 节点4
REWRITE_PROMPT = (
    "查看输入并尝试推断潜在的语义意图/含义。\n"
    "这是最初的问题："
    "\n ------- \n"
    "{question}"
    "\n ------- \n"
    "请只输出改进后的问题本身，不要输出任何解释或说明。"
)
def rewriteQuestion(state: MessagesState):
    question = state["messages"][0].content
    prompt = REWRITE_PROMPT.format(question=question)
    result = model.invoke([HumanMessage(content=prompt)])
    return{
        "messages": [HumanMessage(content=result.content)]
    }
    

# 3.定义图
rag = StateGraph(MessagesState)

# 4.添加节点
rag.add_node(First_call_node)
rag.add_node("retireve", retireve_node)
rag.add_node(finally_llm_call)
rag.add_node(rewriteQuestion)

# 5.添加边
# def select_node1(state: MessagesState):
#     last_msg = state["messages"][-1]
#     if last_msg.tool_calls:
#         return "retireve_node"
#     return END

GRADE_PROMPT = (
    "你是一个评分员，评估检索到的文档与用户问题的相关性。 \n "
    "以下是检索到的文档： \n\n {context} \n\n"
    "以下是用户的问题： {question} \n"
    "如果文档包含与用户问题相关的关键字或语义，则将其评为相关。 \n"
    "给出一个二元分数“yes”或“no”，以表明该文档是否与问题相关。"
)
class GradeDocuments(BaseModel):
    """使用二值评分进行相关性检查"""
    score: str = Field(description="相关性评分：如果相关则为“yes”，如果不相关则为“no”")

def select_node2(state: MessagesState) -> Literal["rewriteQuestion", "finally_llm_call"]:
    question = state["messages"][0].content # 用户提出的问题
    context = state["messages"][-1].content # 检索到的结果
    prompt = GRADE_PROMPT.format(question=question, context=context)
    response = (model.with_structured_output(GradeDocuments, method="function_calling").invoke([{"role": "user", "content": prompt}]))
    score = response.score
    if score == "yes":
        return "finally_llm_call"
    else:
        return "rewriteQuestion"

rag.add_edge(START, "First_call_node")
rag.add_conditional_edges(
    "First_call_node",
    # select_node1,
    # ["retireve_node", END]
    tools_condition, # langgraph中内置了方法，检测aimessage中是否含有tool_calls
    {
        "tools": "retireve",
        "__end__": END,
    },
)
rag.add_conditional_edges(
    "retireve", 
    select_node2,
    ["finally_llm_call", "rewriteQuestion"]                          
)
rag.add_edge("finally_llm_call", END)
rag.add_edge("rewriteQuestion", "First_call_node")

# 6.编译图
rag_sys = rag.compile()

# 7.执行图
while True:
    query = input("##: ")
    if query in ["exit", "quit"]:
        break
    message = {
        "messages": [HumanMessage(query)],
    }
    for chunk in rag_sys.stream(message):
        # print(chunk)
        for node, update in chunk.items():
            print(f"{node}更新了状态")
            update["messages"][-1].pretty_print()
            print("\n\n")