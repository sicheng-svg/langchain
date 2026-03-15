"""
实验一：时间解耦 - Consumer 端
"""
import json
from common import get_channel

connection, channel = get_channel()
channel.queue_declare(queue='demo1_time_decouple', durable=True)

print("=" * 50)
print(" 实验一：时间解耦 - Consumer")
print("=" * 50)
print()
print("  Consumer 刚刚启动，看看能不能收到之前发的消息...")
print()

count = 0

def on_message(ch, method, properties, body):
    global count
    count += 1
    data = json.loads(body)
    print(f"  [收到] {data}  ← 这条消息是 Producer 在 {data['time']} 发的")
    ch.basic_ack(delivery_tag=method.delivery_tag)

channel.basic_qos(prefetch_count=1)
channel.basic_consume(queue='demo1_time_decouple', on_message_callback=on_message)

# 用 time_limit 方式消费，5 秒没有新消息就退出
import time
deadline = time.time() + 3

def check_timeout():
    if time.time() > deadline:
        channel.stop_consuming()

# 轮询消费
while True:
    connection.process_data_events(time_limit=1)
    if time.time() > deadline:
        break

print()
print(f"✓ 共收到 {count} 条消息。")
print("  结论：Producer 退出后很久，Consumer 才启动，消息一条没丢。")
print("  这就是时间解耦——收发双方不需要同时在线。")

connection.close()