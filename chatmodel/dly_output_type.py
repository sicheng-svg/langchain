from langchain_openai import ChatOpenAI
from langchain_core.output_parsers import StrOutputParser
from typing import Iterator, List

model = ChatOpenAI(
    model = "deepseek-chat",
    base_url = "https://api.deepseek.com/v1",
)

# 定义输出解析器
parser = StrOutputParser()

# 自定义生成器
# 根据输出的要求，不再一个字一个字的输出，而是遇到句号时，将一整句话输出
# 自定义生成器接收到的输入是一个字符串迭代器
# yield可以让函数变为一个生成器
# 普通函数在return直接，栈帧就销毁了，而生成器可以通过yield产生多次输出，每次yield都会暂停函数的执行，保存当前的状态，下次可以接着继续执行
def split(input: Iterator[str]) -> Iterator[List[str]]:
    content = ""
    for chunk in input:
        content += chunk
        while "。" in content:
            stop_index = content.index("。") 
            yield [content[:stop_index+1].strip()]
            content = content[stop_index+1:]
    yield [content.strip()]

# langchain是链式的，这里定义链来调用大模型
chain = model | parser | split

for chunk in chain.stream("写一首关于春天的诗，6句话，每句话以句号结尾"):
    print(chunk, end="", flush=True)