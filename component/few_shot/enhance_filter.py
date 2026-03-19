from typing import Optional, List
from langchain_openai import ChatOpenAI
from pydantic import BaseModel, Field
from langchain_core.prompts import ChatPromptTemplate,MessagesPlaceholder
from langchain_core.messages import SystemMessage
from langchain_core.utils.function_calling import tool_example_to_messages


# 定义结构化的数据
class Person(BaseModel):
    """个人信息"""
    name :Optional[str] = Field(default=None, description="名字")
    age :Optional[int] = Field(default=None, description="年龄")
    height :Optional[int] = Field(default=None, description="身高")
    hair :Optional[str] = Field(default=None, description="头发颜色")

class Data(BaseModel):
    """信息列表"""
    people: List[Person]


# 2. 定义示例
examples = [
    (
        "海洋是广阔而蓝色的。它有两万多英尺深。",
        Data(people=[]), # 没有人物信息的情况
    ),
    (
        "18岁身高1米80的小强从中国远行到美国。",
        Data(people=[
            Person(name="小强", age=None, height=None, hair=None),
        ]), # 部分信息缺失的情况
    ),
]

# 3. 定义提示词模板
prompt_template =  ChatPromptTemplate(
    [
        SystemMessage(content="你是一个信息提取的专家"),
        MessagesPlaceholder("example_messages"),# 由示例转来的消息，用作少样本输入
        ("user", "{input}") # 用户输入
    ]
)

# 4. 逻辑处理，根据示例，让llm学习 “是否检测到人”，从而对输出的格式进行特殊处理
example_messages = [] # 最后输入的message
for txt, tool_call in examples:
    if tool_call.people:
        ai_response = "检测到人"
    else:
        ai_response = "未检测到人"

    example_messages.extend(
        tool_example_to_messages(
            txt, 
            [tool_call], 
            ai_response=ai_response
        )
    )

# 对提示词模板进行测试实例化
# prompt = prompt_template.invoke(
#     {
#         "example_messages":example_messages, # 示例message
#         "input":"篮球场上，身高两米的中锋王伟默契地将球传给一米七的后卫挚友李明，完成一记绝杀", # 新输入
#     }
# )
# messages=[
#   SystemMessage(content='你是一个信息提取的专家', additional_kwargs={}, response_metadata={}), 
#   HumanMessage(content='海洋是广阔而蓝色的。它有两万多英尺深。', additional_kwargs={}, response_metadata={}), 
#   AIMessage(content='', additional_kwargs={'tool_calls': [{'id': 'a3ed1bb8-20ab-4017-ac06-5595c12aae18', 'type': 'function', 'function': {'name': 'Data', 'arguments': '{"people":[]}'}}]}, response_metadata={}, tool_calls=[{'name': 'Data', 'args': {'people': []}, 'id': 'a3ed1bb8-20ab-4017-ac06-5595c12aae18', 'type': 'tool_call'}], invalid_tool_calls=[]), 
#   ToolMessage(content='You have correctly called this tool.', tool_call_id='a3ed1bb8-20ab-4017-ac06-5595c12aae18'), 
#   AIMessage(content='未检测到人', additional_kwargs={}, response_metadata={}, tool_calls=[], invalid_tool_calls=[]), 
#   HumanMessage(content='18岁身高1米80的小强从中国远行到美国。', additional_kwargs={}, response_metadata={}), 
#   AIMessage(content='', additional_kwargs={'tool_calls': [{'id': '1d9ca82f-8962-448b-b2f6-1b810825c7eb', 'type': 'function', 'function': {'name': 'Data', 'arguments': '{"people":[{"name":"小强","age":null,"height":null,"hair":null}]}'}}]}, response_metadata={}, tool_calls=[{'name': 'Data', 'args': {'people': [{'name': '小强', 'age': None, 'height': None, 'hair': None}]}, 'id': '1d9ca82f-8962-448b-b2f6-1b810825c7eb', 'type': 'tool_call'}], invalid_tool_calls=[]), 
#   ToolMessage(content='You have correctly called this tool.', tool_call_id='1d9ca82f-8962-448b-b2f6-1b810825c7eb'), 
#   AIMessage(content='检测到人', additional_kwargs={}, response_metadata={}, tool_calls=[], invalid_tool_calls=[]), 
#   HumanMessage(content='篮球场上，身高两米的中锋王伟默契地将球传给一米七的后卫挚友李明，完成一记绝杀', additional_kwargs={}, response_metadata={})
#]
# print(prompt)

# 5. 定义结构化输出模型，自动解析为pydantic
model = ChatOpenAI(
    model="deepseek-chat",
    base_url="https://api.deepseek.com/v1"
)
structured_model = model.with_structured_output(schema=Data, method="function_calling")

# 定义调用链
chain = prompt_template | structured_model
print(chain.invoke(
    {
        "example_messages":example_messages, # 示例message
        "input":"篮球场上，身高两米的中锋王伟默契地将球传给一米七的后卫挚友李明，完成一记绝杀", # 新输入
        # "input":"1+1 -- 2", # 新输入
    }
))