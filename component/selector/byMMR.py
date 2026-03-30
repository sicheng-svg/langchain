from langchain_core.example_selectors import LengthBasedExampleSelector, SemanticSimilarityExampleSelector,MaxMarginalRelevanceExampleSelector
from langchain_core.prompts import FewShotPromptTemplate, PromptTemplate
from langchain_openai import OpenAIEmbeddings
from langchain_chroma import Chroma

# 反义词⽰例集合
examples = [
    {"input": "happy", "output": "sad"},
    {"input": "tall", "output": "short"},
    {"input": "energetic", "output": "lethargic"},
    {"input": "sunny", "output": "gloomy"},
    {"input": "windy", "output": "calm"},
]

# 字符串模板
example_prompt = PromptTemplate(
    input_variables=["input", "output"],
    template="Input: {input}\nOutput: {output}",
)

# 最大边际相关示例选择器 
# 主要是在语义相似性的基础上，增加了去重，多样性，避免选择的示例过于相似
example_selector = MaxMarginalRelevanceExampleSelector.from_examples(
    examples,# 示例集
    OpenAIEmbeddings(model="deepseek-chat"), # 嵌入模型
    Chroma, # 向量数据库
    k=1, # 选择最相似的1个示例
)

dynamic_prompt = FewShotPromptTemplate(
    example_selector=example_selector,
    example_prompt=example_prompt,
    prefix="你是一个反义词助手.",
    suffix="Input: {input}\nOutput:",
    input_variables=["input"],
)

print(dynamic_prompt.invoke({"input": "happy"}).to_messages()[0].content)