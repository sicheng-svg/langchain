"""
实验二：速度解耦
=================
演示：Producer 瞬间发出 20 条消息，Consumer 每条要处理 1 秒。
     Queue 充当缓冲区，Consumer 按自己的节奏慢慢消费，不会被压垮。

运行方式：
  终端 1：python demo2_consumer.py     （先启动 Consumer）
  终端 2：python demo2_producer.py     （再启动 Producer，瞬间灌入 20 条）
  
  观察终端 1：Consumer 每秒处理一条，慢慢消化完 20 条
  同时打开 http://localhost:15672 查看 Queue 深度从 20 逐渐降到 0
"""
import json
import time
import pika
from common import get_channel

connection, channel = get_channel()
channel.queue_declare(queue='demo2_speed_decouple', durable=True)

print("=" * 50)
print(" 实验二：速度解耦 - Producer（高速发送）")
print("=" * 50)
print()

start = time.time()

for i in range(1, 21):
    msg = {'task_id': i, 'payload': f'任务数据 #{i}'}
    channel.basic_publish(
        exchange='',
        routing_key='demo2_speed_decouple',
        body=json.dumps(msg, ensure_ascii=False),
        properties=pika.BasicProperties(delivery_mode=2),
    )

elapsed = time.time() - start

print(f"  [完成] 20 条消息在 {elapsed:.3f} 秒内全部发出")
print()
print("  Producer 的活干完了，可以去做其他事了。")
print("  此时 Queue 里积压了 20 条消息。")
print("  Consumer 每条处理 1 秒，需要 20 秒才能消化完。")
print()
print("→ 去终端 1 观察 Consumer 的处理进度")
print("→ 同时打开 http://localhost:15672 → Queues → demo2_speed_decouple")
print("  看 Ready 列从 20 慢慢降到 0")

connection.close()