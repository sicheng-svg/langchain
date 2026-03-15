"""
实验一：时间解耦
=================
演示：Producer 发完消息后退出，Consumer 过一会儿再启动，消息不会丢。
对比：如果是 HTTP 直接调用，Consumer 不在线时 Producer 就失败了。

运行方式：
  第一步：python demo1_producer.py     （发完 5 条消息后自动退出）
  第二步：等几秒钟，随便等多久
  第三步：python demo1_consumer.py     （启动后立刻收到之前的 5 条消息）
"""
import json
import time
import pika
from common import get_channel

connection, channel = get_channel()

# 声明持久化队列
channel.queue_declare(queue='demo1_time_decouple', durable=True)

print("=" * 50)
print(" 实验一：时间解耦 - Producer")
print("=" * 50)
print()

for i in range(1, 6):
    msg = {'id': i, 'content': f'消息 #{i}', 'time': time.strftime('%H:%M:%S')}
    channel.basic_publish(
        exchange='',  # 用默认 Exchange，routing_key = 队列名
        routing_key='demo1_time_decouple',
        body=json.dumps(msg, ensure_ascii=False),
        properties=pika.BasicProperties(delivery_mode=2),
    )
    print(f"  [发送] {msg}")
    time.sleep(0.5)

print()
print("✓ 5 条消息已全部发送，Producer 现在退出了。")
print("  消息安全地躺在 Queue 里等待 Consumer 来取。")
print()
print("→ 现在运行: python demo1_consumer.py")
print("  （你可以等 10 秒、1 分钟、甚至明天再启动 Consumer，消息都不会丢）")

connection.close()