import time
import asyncio

# 同步调用
# def bubble_water():
#     print("开始烧水...")
#     time.sleep(5)
#     print("水烧开了...")
# def send_msg():
#     print("开始发送消息...")
#     time.sleep(2)
#     print("消息发送成功...")
# 
# if __name__ == "__main__":
#     bubble_water()
#     send_msg()

# 异步调用
# async定义了协程函数
# 直接调用协程函数并不会执行，而是返回一个协程对象
async def bubble_water():
    print("开始烧水...")
    await asyncio.sleep(5)
    print("水烧开了...")

async def send_msg():
    print("开始发送消息...")
    await asyncio.sleep(2)
    print("消息发送成功...")

async def main():
    # 创建两个任务
    task1 = asyncio.create_task(bubble_water())
    task2 = asyncio.create_task(send_msg())
    # 等待两个任务完成
    await task1
    await task2

asyncio.run(main())