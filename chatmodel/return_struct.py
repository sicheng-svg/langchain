from langchain_openai import ChatOpenAI
from pydantic import BaseModel, Field
from typing import Annotated, Union

model = ChatOpenAI(
    model = "deepseek-chat",
    base_url = "https://api.deepseek.com/v1",  
)

# 借助pydantic返回结构化的数据
# class Place(BaseModel):
#     """一个城市和它所在的国家"""
#     city: str = Field(..., description="城市名称")
#     country: str = Field(..., description="国家名称")
# 此时需要使用with_structured_output来返回一个新的model实例，这个实例会在调用时返回结构化的数据
# include_raw参数表示是否在返回的结果中包含原始的文本内容，默认为False，如果设置为True，则返回的结果中会包含一个raw字段，里面是模型生成的原始文本内容。
# modelWithStruct = model.with_structured_output(Place, method="function_calling", include_raw=True)

# 借助Type_Dict返回结构化的数据
class PlaceDict(BaseModel):
    """一个城市和它所在的国家"""
    city: Annotated[str, ..., "城市名称"]
    country: Annotated[str, ..., "国家名称"]
# modelWithStruct = model.with_structured_output(PlaceDict, method="function_calling",)

# 借助json_schema返回结构化数据
json_schema = {
    "type": "object",
    "title": "Place",
    "properties": {
        "city": {
            "type": "string",
            "description": "城市名称"
        },
        "country": {
            "type": "string",
            "description": "国家名称"
        }
    },
    "required": ["city", "country"]
}

# 当设置了with_structured_output后，模型就会跟我们约定好的格式进行返回，即使我们的问题并不适合返回这个结构化的数据
# 解决方案就是定义一个final类，里面union包含给出的结构，让模型在回答时根据问题的类型来选择返回哪种结构化的数据
class Place(BaseModel):
    """一个城市和它所在的国家"""
    city: str = Field(..., description="城市名称")
    country: str = Field(..., description="国家名称")
class person(BaseModel):
    """一个人的姓名和年龄"""
    name: str = Field(..., description="姓名")
    age: int = Field(..., description="年龄")
class answer(BaseModel):
    """一个回答"""
    content: str = Field(..., description="回答的内容")
class Final(BaseModel):
    """最终返回的结构化数据"""
    content: Union[Place, person, answer] = Field(..., description="最终返回的结构化数据")
modelWithStruct = model.with_structured_output(Final, method="function_calling")

print(modelWithStruct.invoke("请告诉我一个城市的名称和它所在的国家"))
print(modelWithStruct.invoke("你是谁"))

#### 结构化输出的使用场景
# 1.通过结构化输出，我们可以用来提取信息，比如从一个文本中提取出一个人的姓名和年龄，或者从一个文本中提取出一个城市的名称和它所在的国家。
# 2.少样本提示，增强模型的能力，比如我们想让模型在回答问题时，返回一个结构化的数据，我们可以通过少样本提示来告诉模型这个结构化数据的格式，这样模型就会按照我们给出的格式来返回结果。
# 3.结合工具使用，将工具调用的结果进行结构化的输出