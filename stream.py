from langchain_openai import ChatOpenAI
import asyncio

model = ChatOpenAI(
    model = "deepseek-chat",   
    base_url = "https://api.deepseek.com/v1",
)

# 使用invoke时，模型会将所有的输出收集完毕后，整体发给我们
# print(model.invoke("写一首关于春天的诗，100字").content)

# 使用stream进行流式输出时，此时模型返回的是一个迭代器.
# 类型是AIMessageChunk的迭代器，我们可以通过for循环来获取每一块内容，模型会在生成内容的过程中不断地将内容分块返回给我们，这样我们就可以在内容生成的过程中就开始处理这些内容，而不需要等到整个内容生成完毕后才处理。
# 这些aimessagechunk可以进行相加，并且结果依旧是aimessagechunk
# for chunk in model.stream("写一首关于春天的诗，100字"):
#    print(chunk.content, end="", flush=True) # print打印默认会加\n，设置end=""可以去掉换行符

async def main():
    async for chunk in model.astream("写一首关于春天的诗，100字"):
        print("异步调用")
        print(chunk.content, end="", flush=True)

asyncio.run(main())