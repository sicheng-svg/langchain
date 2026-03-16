from langchain_core.tools import tool
from pydantic import BaseModel, Field
from typing_extensions import Annotated
from langchain_core.tools import StructuredTool

# 定义工具时，需要使用工具schema来进行校验，校验的内容包含工具名称、工具描述、工具参数
# 只有定义了这些，才能被工具schema识别为工具，大模型才能正确调用这个工具
@tool
def add(a: int, b: int) -> int:
    """
    两数相加
    Args:
        a: 第一个数字
        b: 第二个数字
    """
    return a + b

print(add.invoke({"a": 1, "b": 2}))
print(add.name)
print(add.description)
print(add.args)


class SubTool(BaseModel):
    """
    两数相减
    """
    a: int = Field(..., description="第一个数字")
    b: int = Field(..., description="第二个数字")

@tool(args_schema=SubTool)
def sub(a: int, b: int) -> int:
    return a - b

print(sub.invoke({"a": 5, "b": 3}))
print(sub.name)
print(sub.description)
print(sub.args)


@tool
def mul(
    a: Annotated[int, ..., "第一个数字"],
    b: Annotated[int, ..., "第二个数字"]
) -> int:
    """
    两数相乘
    """
    return a * b

print(mul.invoke({"a": 4, "b": 6}))
print(mul.name)
print(mul.description)
print(mul.args)

def div(a: int, b: int) -> int:
    """
    两数相除
    """
    return a / b

divTool = StructuredTool.from_function(div)
print(divTool.invoke({"a": 10, "b": 2}))
print(divTool.name)
print(divTool.description)
print(divTool.args)


# 使用structured tool
class PlusToolSchema(BaseModel):
    a: int = Field(..., description="第一个数字")
    b: int = Field(..., description="第二个数字")

def plus(a: int, b: int) -> int:
    return a + b
plusTool = StructuredTool.from_function(
    plus, 
    name="加法", 
    description="这是一个加法工具",
    args_schema=PlusToolSchema
)
print(plusTool.invoke({"a": 3, "b": 7}))
print(plusTool.name)       
print(plusTool.description)
print(plusTool.args)

# 使用structured tool除了结果外，还可以返回一些额外的信息
# 使用这种方式返回额外信息，需要在定义工具时，指定response_format为content_and_artifact
# 这样工具调用的结果就会包含content和artifacts两个字段，content是必须的，artifacts是可选的，可以包含一些额外的信息
# 这样就可以将content作为工具调用的结果返回给大模型，同时将一些额外的信息通过artifacts返回给调用方，调用方可以根据需要选择使用这些额外的信息
class Plus2ToolSchema(BaseModel):
    a: int = Field(..., description="第一个数字")
    b: int = Field(..., description="第二个数字")

def plus2(a: int, b: int) -> tuple[str, list[int]]:
    num = [a, b]
    content = f"{num}的结果为{a + b}"
    return content, num

plus2Tool = StructuredTool.from_function(
    plus2, 
    name="pp", 
    description="这是一个加法工具",
    args_schema=Plus2ToolSchema,
    response_format="content_and_artifact" # 这里指定了返回格式，content是必须的，artifacts是可选的，可以包含一些额外的信息
)

# 模拟大模型调用该工具
print(plus2Tool.invoke(
    {
        "name" : "pp",
        "args" : {
            "a": 8,
            "b": 12
        },
        "type" : "tool_call", # 必填
        "id":"111" # 必填，用来将工具调用的结果与工具调用请求关联起来
    },
))