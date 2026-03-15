"""
实验三：逻辑解耦（Fanout 广播）
================================
演示：Producer 发一条 "用户注册" 消息，三个不同的 Consumer 同时收到：
     - 短信服务：发送验证码
     - 邮件服务：发送欢迎邮件
     - 积分服务：赠送新人积分
     
     Producer 完全不知道下游有几个服务。
     新增一个下游服务只需要新建一个 Queue 绑定到 Exchange，Producer 代码不用改。

运行方式：
  终端 1：python demo3_consumer.py sms       （短信服务）
  终端 2：python demo3_consumer.py email     （邮件服务）
  终端 3：python demo3_consumer.py points    （积分服务）
  终端 4：python demo3_producer.py           （发送注册事件）
"""
import json
import time
import pika
from common import get_channel

connection, channel = get_channel()

# 声明 Fanout Exchange —— 广播到所有绑定的队列
channel.exchange_declare(exchange='user_register_fanout', exchange_type='fanout', durable=True)

print("=" * 50)
print(" 实验三：逻辑解耦 - Producer")
print("=" * 50)
print()

users = [
    {'user_id': 1001, 'name': '张三', 'phone': '138****1234'},
    {'user_id': 1002, 'name': '李四', 'phone': '139****5678'},
    {'user_id': 1003, 'name': '王五', 'phone': '137****9012'},
]

for user in users:
    event = {
        'event': 'user.register',
        'data': user,
        'timestamp': time.strftime('%H:%M:%S'),
    }
    channel.basic_publish(
        exchange='user_register_fanout',
        routing_key='',  # Fanout 忽略 routing_key，填空即可
        body=json.dumps(event, ensure_ascii=False),
        properties=pika.BasicProperties(delivery_mode=2),
    )
    print(f"  [广播] 用户注册事件: {user['name']} ({user['user_id']})")
    time.sleep(1)

print()
print("✓ 3 条注册事件已广播。")
print("  Producer 不知道也不关心下游有几个服务在监听。")
print("  去看三个 Consumer 终端，每个都收到了全部 3 条消息。")

connection.close()