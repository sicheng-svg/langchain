# 支持搜索的ai系统
import operator
from typing import TypedDict, Annotated
from langgraph.graph import StateGraph
from langgraph.constants import START, END
from langgraph.checkpoint.memory import InMemorySaver
from langgraph.checkpoint.postgres import PostgresSaver
from langchain_openai import ChatOpenAI
from langchain_core.messages import HumanMessage, AIMessage, ToolMessage, AnyMessage, SystemMessage
from langchain_tavily import TavilySearch

# 模型定义
model = ChatOpenAI(
    model="deepseek-chat",
    base_url="https://api.deepseek.com/v1",
)
# 定义工具，使用三方提供的
tool = TavilySearch(
    tavily_api_key = "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",
    max_results = 3,
)
tools = [tool]
tools_map = {t.name: t for t in tools}

# 绑定工具
modelWithTool = model.bind_tools(tools=[tool])

# 1. 定义状态
class SearchState(TypedDict):
    messages: Annotated[list[AnyMessage], operator.add]
    llm_calls: Annotated[int, operator.add]

# 2. 定义节点（函数）
def llm_node(state: SearchState):
    """ 调用llm，其自主决定是否需要调用工具"""
    message = state["messages"]
    aiMsg = modelWithTool.invoke([SystemMessage(content="你是一个善于使用工具进行网络搜索的ai助理")] + message)
    return {
        "messages": [aiMsg],
        "llm_calls": 1,
    }

def tool_node(state: SearchState):
    """ 调用工具"""
    last_msg = state["messages"][-1]
    toolMsg = []
    for tool_call in last_msg.tool_calls:
        target_tool = tools_map[tool_call["name"]]
        tool_message = target_tool.invoke(tool_call["args"])
        toolMsg.append(ToolMessage(
            content=tool_message,
            tool_call_id=tool_call["id"],
        ))
    return {
        "messages": toolMsg,
    }


# 3. 定义图（节点和边）
search = StateGraph(SearchState)

# 4. 添加节点
search.add_node("llm", llm_node)
search.add_node("tool", tool_node)

# 5. 添加边（包括条件边）
search.add_edge(START, "llm") # 固定边，开始到第一次调用llm

def router(state: SearchState) -> str:
    """ 路由函数，根据当前状态决定下一步走llm还是tool"""
    # 如果tool_calls不为空，则说明需要调用工具
    last_msg = state["messages"][-1]
    if hasattr(last_msg, "tool_calls") and last_msg.tool_calls:
        return "tool"
    return END

search.add_conditional_edges(
    "llm",
    router,
    ["tool", END]
) #条件边， 判断是否需要调用工具，如果需要则路由到toll，反之直接结束

search.add_edge("tool", "llm") # 固定边，工具调用完后继续调用llm


# 定义内存持久化存储
# checkpointer = InMemorySaver()

# 定义PostgreSql持久化存储库
DB_URI = "postgresql://postgres:Xsc.200411@127.0.0.1:5432/postgres"
with PostgresSaver.from_conn_string(DB_URI) as checkpointer:
# 6. 编译图
    # checkpointer.setup()
    system = search.compile(checkpointer=checkpointer)
    config = {"configurable":{"thread_id":"2222222222"}}

    # 第一次执行
    # result = system.invoke({"messages":[HumanMessage(content="西安今天的天气怎么样？")]}, config=config)
    # result["messages"][-1].pretty_print()

    # # 第二次执行
    # result = system.invoke({"messages":[HumanMessage(content="你记得我们聊了什么么？")]}, config=config)
    # result["messages"][-1].pretty_print()

    # 获取最新的快照
    # StateSnapshot(
    #     values={
    #         'messages': [
    #             HumanMessage(content='西安今天的天气怎么样？', additional_kwargs={}, response_metadata={}), 
    #             AIMessage(content='我来帮您查询西安今天的天气情况。', additional_kwargs={'refusal': None}, response_metadata={'token_usage': {'completion_tokens': 76, 'prompt_tokens': 1851, 'total_tokens': 1927, 'completion_tokens_details': None, 'prompt_tokens_details': {'audio_tokens': None, 'cached_tokens': 1792}, 'prompt_cache_hit_tokens': 1792, 'prompt_cache_miss_tokens': 59}, 'model_provider': 'openai', 'model_name': 'deepseek-chat', 'system_fingerprint': 'fp_eaab8d114b_prod0820_fp8_kvcache_new_kvcache', 'id': '1cdc54e3-6d5b-4f9c-b44a-8aff24b740da', 'finish_reason': 'tool_calls', 'logprobs': None}, id='lc_run--019d65df-4da6-7870-804f-81832c046e0b-0', tool_calls=[{'name': 'tavily_search', 'args': {'query': '西安今天天气 温度 天气预报', 'time_range': 'day'}, 'id': 'call_00_t4SVw9Z7aotEHKKVnr3Hm4kk', 'type': 'tool_call'}], invalid_tool_calls=[], usage_metadata={'input_tokens': 1851, 'output_tokens': 76, 'total_tokens': 1927, 'input_token_details': {'cache_read': 1792}, 'output_token_details': {}}), 
    #             ToolMessage(content="{'query': '西安今天天气 温度 天气预报', 'response_time': 2.01, 'follow_up_questions': None, 'answer': None, 'images': [], 'results': [{'url': 'http://202.146.219.22/xian/qiwen', 'title': '西安气温_西安今天气温_西安一周气温、现在、明天温度 - 天气预报网', 'content': '*03月06日18:00发布，数据:中国天气网；*西安今天气温、一周气温查询！. 当前位1置：天气预报网 > 陕西天气预报10天 > 西安天气预报10天> 西安气温. 西安天气预报一周 10天天气 15天天气 30天天气 天气指数 历史天气 PM2.5. # 西安今天气温,一周气温. 今天 2026年03月06日 农历正月十八，西安今日气温为：5℃ ~ 2℃，以下是西安末来三天气温变化详细信息：(西安天气预报10天查询). 西安气温测量说明：西安天气预报中测量得到的气温，指在西安野外空气流通、不受太阳直射下测得的空气温度(一般在百叶箱内测定)。西安最高气温是一日内气温的最高值，一般出现在14-15时，西安最低气温一般出现在早晨5-6时。我国用摄氏温标，以℃表示摄氏度。一般一天观测4次（02、08、14、20四个时次），部分测站根据实际情况，一天观测3次（08、14、20三个时间段/次）；. ### 根据中央气象台提供的末来24小时西安今天气温实况走势图. ### 西安一周气温变化查询. 温馨提示：关注生活关注气温变化，把西安气温分享给自己的亲朋好友吧，网址：,相关：西安天气预报10天、西安穿衣指数. ### 西安辖区、县及周边城市天气预报查询. ### 全国主要城市天气预报10天查询. ### 全国天气预报10天查询. ### 陕西西安实用工具查询. ### 全国天气预报查询工具. Copyright © 2010-2017 bst86.com Corporation, All Rights Reserved.', 'score': 0.9997851, 'raw_content': None, 'domain': '202.146.219.22', 'popularity_score': 0.615760516944525, 'main_topic': 'news'}, {'url': 'https://www.mytxly.com/yanta/qiwen', 'title': '雁塔气温,西安雁塔今天气温、明天温度、一周气温-旅游天气网', 'content': '*03月04日08:00发布，数据:中国天气网；*雁塔今天气温、一周气温查询！. 当前位1置：旅游天气网 > 陕西天气预报10天 > 西安天气预报10天 > 雁塔天气预报10天> 雁塔气温. 雁塔天气预报一周 10天天气 15天天气 30天天气 天气指数 PM2.5. # 西安雁塔今天气温,一周气温. 今天 2026年03月04日 星期三 农历正月十六，西安雁塔今日气温为：14℃ ~ 2℃，以下是雁塔末来三天气温变化详细信息：(雁塔天气预报10天查询). 雁塔气温测量说明：西安雁塔天气预报中测量得到的气温，指在雁塔野外空气流通、不受太阳直射下测得的空气温度(一般在百叶箱内测定)。雁塔最高气温是一日内气温的最高值，一般出现在14-15时，雁塔最低气温一般出现在早晨5-6时。我国用摄氏温标，以℃表示摄氏度。一般一天观测4次（02、08、14、20四个时次），部分测站根据实际情况，一天观测3次（08、14、20三个时间段/次）；. ### 根据中央气象台提供的末来24小时西安雁塔今天气温实况走势图. ### 雁塔一周气温变化查询. 温馨提示：关注生活关注气温变化，把雁塔气温分享给自己的亲朋好友吧，网址：,相关：雁塔天气预报10天、雁塔穿衣指数. ### 西安雁塔辖区、县及周边城市天气预报查询. ### 全国主要城市天气预报10天查询. ### 全国天气预报10天查询. ### 陕西雁塔实用工具查询. ### 全国天气预报查询工具. 张湾气温 延长气温 明山气温 西沙气温 红塔气温 林口气温 宁江气温 谢家集气温 青秀气温 五通桥气温 景德镇气温 安岳气温 城西气温 维扬气温 富宁气温 谯城气温 临澧气温 庆元气温 扶风气温 梁园气温. Copyright © 2009-2021 All Rights Reserved.', 'score': 0.9993068, 'raw_content': None, 'domain': 'mytxly.com', 'popularity_score': 0.5753641449035618, 'main_topic': 'news'}, {'url': 'https://www.mytxly.com/anding/qiwen', 'title': '安定气温,定西安定今天气温、明天温度、一周气温-旅游天气网', 'content': '*03月04日08:00发布，数据:中国天气网；*安定今天气温、一周气温查询！. 当前位1置：旅游天气网 > 甘肃天气预报10天 > 定西天气预报10天 > 安定天气预报10天> 安定气温. 安定天气预报一周 10天天气 15天天气 30天天气 天气指数 历史天气. # 定西安定今天气温,一周气温. 今天 2026年03月04日 星期三 农历正月十六，定西安定今日气温为：14℃ ~ -5℃，以下是安定末来三天气温变化详细信息：(安定天气预报10天查询). 安定气温测量说明：定西安定天气预报中测量得到的气温，指在安定野外空气流通、不受太阳直射下测得的空气温度(一般在百叶箱内测定)。安定最高气温是一日内气温的最高值，一般出现在14-15时，安定最低气温一般出现在早晨5-6时。我国用摄氏温标，以℃表示摄氏度。一般一天观测4次（02、08、14、20四个时次），部分测站根据实际情况，一天观测3次（08、14、20三个时间段/次）；. ### 根据中央气象台提供的末来24小时定西安定今天气温实况走势图. ### 安定一周气温变化查询. 温馨提示：关注生活关注气温变化，把安定气温分享给自己的亲朋好友吧，网址：,相关：安定天气预报10天、安定穿衣指数. ### 定西安定辖区、县及周边城市天气预报查询. ### 全国主要城市天气预报10天查询. ### 全国天气预报10天查询. ### 甘肃安定实用工具查询. ### 全国天气预报查询工具. 西乌珠穆沁旗气温 临澧气温 集美气温 中坜气温 岱山气温 红塔气温 五通桥气温 夏县气温 龙湖气温 江东气温 龙安气温 龙潭气温 延长气温 安岳气温 谢家集气温 宁江气温 龙马潭气温 金安气温 平原气温 新洲气温. Copyright © 2009-2021 All Rights Reserved.', 'score': 0.99719906, 'raw_content': None, 'domain': 'mytxly.com', 'popularity_score': 0.5753641449035618, 'main_topic': 'news'}], 'request_id': 'ac1457e7-602f-4498-8f63-650109695f6b'}", tool_call_id='call_00_t4SVw9Z7aotEHKKVnr3Hm4kk'), 
    #             AIMessage(content='让我搜索更准确的西安今天天气信息：', additional_kwargs={'refusal': None}, response_metadata={'token_usage': {'completion_tokens': 79, 'prompt_tokens': 3601, 'total_tokens': 3680, 'completion_tokens_details': None, 'prompt_tokens_details': {'audio_tokens': None, 'cached_tokens': 1920}, 'prompt_cache_hit_tokens': 1920, 'prompt_cache_miss_tokens': 1681}, 'model_provider': 'openai', 'model_name': 'deepseek-chat', 'system_fingerprint': 'fp_eaab8d114b_prod0820_fp8_kvcache_new_kvcache', 'id': '9b87303a-9c48-4ae2-811b-d5005ed4b9e2', 'finish_reason': 'tool_calls', 'logprobs': None}, id='lc_run--019d65df-6b03-77f2-9bec-22ddd36ae315-0', tool_calls=[{'name': 'tavily_search', 'args': {'query': '西安今日天气预报 2024年 实时天气', 'time_range': 'day'}, 'id': 'call_00_NTbc9hLnmjivAtTSd3H5Wn0h', 'type': 'tool_call'}], invalid_tool_calls=[], usage_metadata={'input_tokens': 3601, 'output_tokens': 79, 'total_tokens': 3680, 'input_token_details': {'cache_read': 1920}, 'output_token_details': {}}), 
    #             ToolMessage(content="{'query': '西安今日天气预报 2024年 实时天气', 'follow_up_questions': None, 'answer': None, 'images': [], 'results': [{'url': 'https://weather.cma.cn/web/weather/V8870.html', 'title': '西安 - 中国气象局-天气预报-城市预报', 'content': '| 时间 | 23:00 | 02:00 | 05:00 | 08:00 | 11:00 | 14:00 | 17:00 | 20:00 |. | 风向 | 东北风 | 东南风 | 东北风 | 东北风 | 东北风 | 西南风 | 西南风 | 东南风 |. | 风向 | 东北风 | 东北风 | 西南风 | 西南风 | 东南风 | 西南风 | 西南风 | 西南风 |. | 风向 | 西南风 | 西南风 | 西北风 | 西北风 | 西北风 | 东南风 | 东北风 | 东北风 |. | 风向 | 东北风 | 东北风 | 东北风 | 东北风 | 东北风 | 东南风 | 东南风 | 东南风 |. | 风向 | 西南风 | 西南风 | 西南风 | 西北风 | 东北风 | 东北风 | 东北风 | 东北风 |. | 风向 | 东北风 | 东南风 | 西南风 | 西南风 | 西南风 | 东北风 | 东北风 | 东北风 |. | 风向 | 东北风 | 东北风 | 东北风 | 东北风 | 东南风 | 东北风 | 东北风 | 东北风 |.', 'score': 0.5694942, 'raw_content': None}, {'url': 'https://www.weather.com.cn/weather40d/101110101.shtml', 'title': '【西安天气】西安40天天气预报,西安更长预报,西安天气日历,西安日历 ...', 'content': '首页 预报 预警 雷达 云图 天气地图 专业产品 资讯 视频 节气 我的天空. 台风路径 空间天气 图片 专题 环境 旅游 碳中和 气象科普 一带一路 产创平台. :   北京 上海 成都 杭州 南京 天津 深圳 重庆 西安 广州 青岛 武汉. :   故宫 阳朔漓江 龙门石窟 野三坡 颐和园 九寨沟 东方明珠 凤凰古城 秦始皇陵 桃花源. :   佘山 春城湖畔 华彬庄园 观澜湖 依必朗 旭宝 博鳌 玉龙雪山 番禺南沙 东方明珠. :   曼谷 东京 首尔 吉隆坡 新加坡 巴黎 罗马 伦敦 雅典 柏林 纽约 温哥华 墨西哥城 哈瓦那 圣何塞 巴西利亚 布宜诺斯艾利斯 圣地亚哥 利马 基多 悉尼 墨尔本 惠灵顿 奥克兰 苏瓦 开罗 内罗毕 开普敦 维多利亚 拉巴特. :   开往春天的列车：风暖景明 邂逅山河浪漫  中国天气网 2026-03-23 16:04. :   防滑！今起三天四川大部多降水 川西高原等局地需防范大雪  中国天气网 2026-03-23 16:04. :   今夜起新疆北疆等地雨雪来袭局地有暴雪 风口风力可达9至10级  中国天气网 2026-03-23 15:54. :   福建福州杜鹃花次第开 多姿多彩映春光  中国天气网 2026-03-23 14:45. :   雪落青海曲麻莱 大地一片银白  中国天气网青海站 2026-03-23 12:00. # 高清图集. **青海河南县雪后初霁 俯瞰大地尽染银白** **开往春天的列车：风暖景明 邂逅山河浪漫** **雪落青海曲麻莱 大地一片银白** **北京现日晕景观 太阳自带光环** **气象科技盛宴开启！中国气象局世界气象日开放活动抢先看**. # 更多>>高清图集. * 三亚 多云 21/31℃ 适宜. * 九寨沟 小雨转多云 5/20℃ 适宜. * 大理 多云 6/20℃ 适宜. * 张家界 小雨 12/17℃ 适宜. * 桂林 小雨 15/20℃ 适宜. * 青岛 多云 7/12℃ 一般.', 'score': 0.363173, 'raw_content': None}, {'url': 'https://www.weather.com.cn/weather/101110101.shtml', 'title': '7日（明天） - 天气预报', 'content': '首页 预报 预警 雷达 云图 天气地图 专业产品 资讯 视频 节气 我的天空. 台风路径 空间天气 图片 专题 环境 旅游 碳中和 气象科普 一带一路 产创平台. :   北京 上海 成都 杭州 南京 天津 深圳 重庆 西安 广州 青岛 武汉. :   故宫 阳朔漓江 龙门石窟 野三坡 颐和园 九寨沟 东方明珠 凤凰古城 秦始皇陵 桃花源. :   佘山 春城湖畔 华彬庄园 观澜湖 依必朗 旭宝 博鳌 玉龙雪山 番禺南沙 东方明珠. :   曼谷 东京 首尔 吉隆坡 新加坡 巴黎 罗马 伦敦 雅典 柏林 纽约 温哥华 墨西哥城 哈瓦那 圣何塞 巴西利亚 布宜诺斯艾利斯 圣地亚哥 利马 基多 悉尼 墨尔本 惠灵顿 奥克兰 苏瓦 开罗 内罗毕 开普敦 维多利亚 拉巴特. :   辽宁持续升温沈阳或连创新高 大部地区昼夜温差较大早晚寒意仍明显  中国天气网 2026-03-25 10:54. :   今明天山东暖热升级济南或升至25℃ 后天中北部降温剧烈  中国天气网 2026-03-25 10:34. :   春染千般色 国家植物园满园芳菲入画来  中国天气网 2026-03-25 10:17. :   河北气温继续冲高暖意升级 石家庄最高气温27℃或创今年来新高  中国天气网 2026-03-25 09:43. :   今明天北京最高气温回升夜间能见度不佳 28日将再迎冷空气  中国天气网 2026-03-25 07:05. # 高清图集. **雪落青海曲麻莱 大地一片银白** **春染千般色 国家植物园满园芳菲入画来** **能见度不佳 北京大运河森林公园一片朦胧** **北京现日晕景观 太阳自带光环** **气象科技盛宴开启！中国气象局世界气象日开放活动抢先看**. # 更多>>高清图集. * 三亚 多云 31/21℃ 适宜. * 九寨沟 小雨 14/7℃ 适宜. * 大理 阵雨转晴 20/7℃ 适宜. * 张家界 多云转中雨 20/12℃ 适宜. * 桂林 小雨 18/16℃ 适宜. * 青岛 晴转多云 14/9℃ 适宜.', 'score': 0.20793796, 'raw_content': None}], 'response_time': 0.67, 'request_id': '99ce196d-9469-4b51-ab8f-270ae5085b0b'}", tool_call_id='call_00_NTbc9hLnmjivAtTSd3H5Wn0h'), 
    #             AIMessage(content='让我搜索更具体的西安今日天气信息：', additional_kwargs={'refusal': None}, response_metadata={'token_usage': {'completion_tokens': 81, 'prompt_tokens': 5443, 'total_tokens': 5524, 'completion_tokens_details': None, 'prompt_tokens_details': {'audio_tokens': None, 'cached_tokens': 1920}, 'prompt_cache_hit_tokens': 1920, 'prompt_cache_miss_tokens': 3523}, 'model_provider': 'openai', 'model_name': 'deepseek-chat', 'system_fingerprint': 'fp_eaab8d114b_prod0820_fp8_kvcache_new_kvcache', 'id': 'b7392fdf-52de-40af-aa74-da74ec650653', 'finish_reason': 'tool_calls', 'logprobs': None}, id='lc_run--019d65df-7e46-7be2-ac48-3d91d2242297-0', tool_calls=[{'name': 'tavily_search', 'args': {'query': '西安今天天气 温度 湿度 风向 实时更新', 'time_range': 'day'}, 'id': 'call_00_TxM1eITryH8R4PF51hgJI4ql', 'type': 'tool_call'}], invalid_tool_calls=[], usage_metadata={'input_tokens': 5443, 'output_tokens': 81, 'total_tokens': 5524, 'input_token_details': {'cache_read': 1920}, 'output_token_details': {}}), 
    #             ToolMessage(content="{'query': '西安今天天气 温度 湿度 风向 实时更新', 'follow_up_questions': None, 'answer': None, 'images': [], 'results': [{'url': 'https://weather.cma.cn/web/weather/V8870.html', 'title': '西安 - 中国气象局-天气预报-城市预报', 'content': '| 时间 | 23:00 | 02:00 | 05:00 | 08:00 | 11:00 | 14:00 | 17:00 | 20:00 |. | 风向 | 东北风 | 东南风 | 东北风 | 东北风 | 东北风 | 西南风 | 西南风 | 东南风 |. | 风向 | 东北风 | 东北风 | 西南风 | 西南风 | 东南风 | 西南风 | 西南风 | 西南风 |. | 风向 | 西南风 | 西南风 | 西北风 | 西北风 | 西北风 | 东南风 | 东北风 | 东北风 |. | 风向 | 东北风 | 东北风 | 东北风 | 东北风 | 东北风 | 东南风 | 东南风 | 东南风 |. | 风向 | 西南风 | 西南风 | 西南风 | 西北风 | 东北风 | 东北风 | 东北风 | 东北风 |. | 风向 | 东北风 | 东南风 | 西南风 | 西南风 | 西南风 | 东北风 | 东北风 | 东北风 |. | 风向 | 东北风 | 东北风 | 东北风 | 东北风 | 东南风 | 东北风 | 东北风 | 东北风 |.', 'score': 0.68090034, 'raw_content': None}, {'url': 'https://www.weather.com.cn/weather/101110101.shtml', 'title': '7日（明天） - 天气预报', 'content': '首页 预报 预警 雷达 云图 天气地图 专业产品 资讯 视频 节气 我的天空. 台风路径 空间天气 图片 专题 环境 旅游 碳中和 气象科普 一带一路 产创平台. :   北京 上海 成都 杭州 南京 天津 深圳 重庆 西安 广州 青岛 武汉. :   故宫 阳朔漓江 龙门石窟 野三坡 颐和园 九寨沟 东方明珠 凤凰古城 秦始皇陵 桃花源. :   佘山 春城湖畔 华彬庄园 观澜湖 依必朗 旭宝 博鳌 玉龙雪山 番禺南沙 东方明珠. :   曼谷 东京 首尔 吉隆坡 新加坡 巴黎 罗马 伦敦 雅典 柏林 纽约 温哥华 墨西哥城 哈瓦那 圣何塞 巴西利亚 布宜诺斯艾利斯 圣地亚哥 利马 基多 悉尼 墨尔本 惠灵顿 奥克兰 苏瓦 开罗 内罗毕 开普敦 维多利亚 拉巴特. :   辽宁持续升温沈阳或连创新高 大部地区昼夜温差较大早晚寒意仍明显  中国天气网 2026-03-25 10:54. :   今明天山东暖热升级济南或升至25℃ 后天中北部降温剧烈  中国天气网 2026-03-25 10:34. :   春染千般色 国家植物园满园芳菲入画来  中国天气网 2026-03-25 10:17. :   河北气温继续冲高暖意升级 石家庄最高气温27℃或创今年来新高  中国天气网 2026-03-25 09:43. :   今明天北京最高气温回升夜间能见度不佳 28日将再迎冷空气  中国天气网 2026-03-25 07:05. # 高清图集. **雪落青海曲麻莱 大地一片银白** **春染千般色 国家植物园满园芳菲入画来** **能见度不佳 北京大运河森林公园一片朦胧** **北京现日晕景观 太阳自带光环** **气象科技盛宴开启！中国气象局世界气象日开放活动抢先看**. # 更多>>高清图集. * 三亚 多云 31/21℃ 适宜. * 九寨沟 小雨 14/7℃ 适宜. * 大理 阵雨转晴 20/7℃ 适宜. * 张家界 多云转中雨 20/12℃ 适宜. * 桂林 小雨 18/16℃ 适宜. * 青岛 晴转多云 14/9℃ 适宜.', 'score': 0.38943097, 'raw_content': None}, {'url': 'https://www.weather.com.cn/weather1d/101110101.shtml', 'title': '7日白天 - 中国天气网', 'content': '# 5日白天. ### 蓝天预报综合天气现象、能见度、空气质量等因子，预测未来一周的天空状况。. # 5日夜间. # 生活指数. # 天气资讯. # 周边地区 *|* 周边景点 *2026-04-05 11:30更新*. # 周边地区 *|* 周边景点 *2026-04-05 11:30更新*. # 高清图集. # 重大天气事件. ## 南方降雨再度增多局地或现暴雨 北方迎显著降温东北雨雪持续. 清明假期后两日，南方降雨将再度增多，江南、华南等地或现暴雨，同时北方将现显著降温，其中东北地区大范围雨雪持续，黑龙江局地有暴雪。. ## 清明假期首日南方降雨短暂缩减 华北黄淮等地仍有风沙来扰. ## 华北黄淮强风沙尘来袭 江西福建等地有暴雨. 昨天南方新一轮强降雨和强对流天气上线，今天降雨持续，江西、福建、广东等地部分地区仍有暴雨。. ## 南方新一轮降雨和强对流天气上线 北方较大范围沙尘来袭. 南方降雨短暂缩减后，今天又会发展增多，未来三天新一轮降雨和强对流天气将上线，湖南、江西等地局地有大暴雨。与此同时，北方天气也变得复杂起来，. ## 明起南方新一轮降水过程来袭 北方大风沙尘天气将登场. 今天南方多地进入雨水间歇期。明天，南方新一轮降水过程再度来袭，需警惕强对流天气，同时冷空气将携大风降温影响北方。. ## 南方雨连连广东福建等地仍有强降雨 全国大部气温波动明显. 近期南方多地降雨连连，今天（3月31日）大范围降雨和强对流天气仍将持续。在频繁降水和冷空气影响下，全国大部气温起伏明显，而华南则维持炎热天气。. ## 南方大范围降雨持续并伴有强对流天气 中东部多地气温下滑. 今明两天（3月30日至31日），南方仍有大范围降雨，并伴有强对流天气。在冷空气和降雨的共同影响下，中东部多地气温陆续下滑，华南地区则炎热持续。. ## 南方未来三天迎较强降雨伴强对流 华南持续炎热局地或现高温. 未来三天（3月29日至31日），南方有较强降雨过程，并将今年首场大范围强对流天气。受冷空气和降雨影响，江南等地气温将出现波动。. ## 明天起南方迎新一轮强降雨和强对流天气 全国气温波动起伏. 今天（3月28日），南方大部仍将阴雨绵绵；明天开始，新一轮强降雨和强对流天气即将登场。. ## 南方阴雨模式持续北方雨雪增多 全国大部气温以偏高为主. 今明两天（3月27日至28日），南方仍将持续阴雨天气，较强降雨主要集中在广西、湖南、江西、福建等地。. ## 南方连阴雨江南华南累计雨量大 北方大部偏暖昼夜温差显著. 今后三天（3月26日至28日），南方大部将维持阴雨频繁的格局，其中，西南地区东部、江南、华南北部等地累计雨量较大。. ## 南方月底前阴雨频繁 北方晴暖升级多地气温将连创新高. 未来三天（3月25日至27日），南方阴仍多阴雨天气。29日至30日，还将有新一轮降雨发展，月底前南方维持阴雨频繁的天气格局。. ## 南方阴雨连连江南等地升温乏力 北方多地气温将达近期顶点. 未来三天（3月24日至26日），南方多地阴雨天气持续，而且月底还将有一轮较强降雨过程，需防范连续降雨对交通、农业等方面的不利影响。. # 雷达图. # 联播天气预报. # 更多>>高清图集. # 天气视频. # >> 生活旅游. ### 景点推荐. #### 景区天气气温 旅游指数. # 气象产品. # 气象服务. # 天气预报电话查询. # 手机查询. ### 网站服务. ### 营销中心. ### 相关链接. 客服邮箱：service@weather.com.cn客服电话：**010-68409444**京ICP证010385-2号\\u3000京公网安备11041400134号.', 'score': 0.14969318, 'raw_content': None}], 'response_time': 0.72, 'request_id': 'fce875f9-d025-4d1f-9daf-5468072a2b84'}", tool_call_id='call_00_TxM1eITryH8R4PF51hgJI4ql'), 
    #             AIMessage(content='让我尝试搜索更具体的西安今日天气数据：', additional_kwargs={'refusal': None}, response_metadata={'token_usage': {'completion_tokens': 86, 'prompt_tokens': 7630, 'total_tokens': 7716, 'completion_tokens_details': None, 'prompt_tokens_details': {'audio_tokens': None, 'cached_tokens': 5504}, 'prompt_cache_hit_tokens': 5504, 'prompt_cache_miss_tokens': 2126}, 'model_provider': 'openai', 'model_name': 'deepseek-chat', 'system_fingerprint': 'fp_eaab8d114b_prod0820_fp8_kvcache_new_kvcache', 'id': '107cef35-6020-4329-9b29-8ca3c498190e', 'finish_reason': 'tool_calls', 'logprobs': None}, id='lc_run--019d65df-9840-7b32-8607-0c60785d0c40-0', tool_calls=[{'name': 'tavily_search', 'args': {'query': '西安今日气温 最高温度 最低温度 天气状况 2024年', 'time_range': 'day'}, 'id': 'call_00_LjUWYOLzAnQYava3wBHLyHla', 'type': 'tool_call'}], invalid_tool_calls=[], usage_metadata={'input_tokens': 7630, 'output_tokens': 86, 'total_tokens': 7716, 'input_token_details': {'cache_read': 5504}, 'output_token_details': {}}), 
    #             ToolMessage(content="{'query': '西安今日气温 最高温度 最低温度 天气状况 2024年', 'follow_up_questions': None, 'answer': None, 'images': [], 'results': [{'url': 'https://weather.cma.cn/web/weather/V8870.html', 'title': '西安 - 中国气象局-天气预报-城市预报', 'content': '| 时间 | 23:00 | 02:00 | 05:00 | 08:00 | 11:00 | 14:00 | 17:00 | 20:00 |. | 风向 | 东北风 | 东南风 | 东北风 | 东北风 | 东北风 | 西南风 | 西南风 | 东南风 |. | 风向 | 东北风 | 东北风 | 西南风 | 西南风 | 东南风 | 西南风 | 西南风 | 西南风 |. | 风向 | 西南风 | 西南风 | 西北风 | 西北风 | 西北风 | 东南风 | 东北风 | 东北风 |. | 风向 | 东北风 | 东北风 | 东北风 | 东北风 | 东北风 | 东南风 | 东南风 | 东南风 |. | 风向 | 西南风 | 西南风 | 西南风 | 西北风 | 东北风 | 东北风 | 东北风 | 东北风 |. | 风向 | 东北风 | 东南风 | 西南风 | 西南风 | 西南风 | 东北风 | 东北风 | 东北风 |. | 风向 | 东北风 | 东北风 | 东北风 | 东北风 | 东南风 | 东北风 | 东北风 | 东北风 |.', 'score': 0.5117166, 'raw_content': None}, {'url': 'https://www.weather.com.cn/weather/101110101.shtml', 'title': '7日（明天） - 天气预报', 'content': '首页 预报 预警 雷达 云图 天气地图 专业产品 资讯 视频 节气 我的天空. 台风路径 空间天气 图片 专题 环境 旅游 碳中和 气象科普 一带一路 产创平台. :   北京 上海 成都 杭州 南京 天津 深圳 重庆 西安 广州 青岛 武汉. :   故宫 阳朔漓江 龙门石窟 野三坡 颐和园 九寨沟 东方明珠 凤凰古城 秦始皇陵 桃花源. :   佘山 春城湖畔 华彬庄园 观澜湖 依必朗 旭宝 博鳌 玉龙雪山 番禺南沙 东方明珠. :   曼谷 东京 首尔 吉隆坡 新加坡 巴黎 罗马 伦敦 雅典 柏林 纽约 温哥华 墨西哥城 哈瓦那 圣何塞 巴西利亚 布宜诺斯艾利斯 圣地亚哥 利马 基多 悉尼 墨尔本 惠灵顿 奥克兰 苏瓦 开罗 内罗毕 开普敦 维多利亚 拉巴特. :   辽宁持续升温沈阳或连创新高 大部地区昼夜温差较大早晚寒意仍明显  中国天气网 2026-03-25 10:54. :   今明天山东暖热升级济南或升至25℃ 后天中北部降温剧烈  中国天气网 2026-03-25 10:34. :   春染千般色 国家植物园满园芳菲入画来  中国天气网 2026-03-25 10:17. :   河北气温继续冲高暖意升级 石家庄最高气温27℃或创今年来新高  中国天气网 2026-03-25 09:43. :   今明天北京最高气温回升夜间能见度不佳 28日将再迎冷空气  中国天气网 2026-03-25 07:05. # 高清图集. **雪落青海曲麻莱 大地一片银白** **春染千般色 国家植物园满园芳菲入画来** **能见度不佳 北京大运河森林公园一片朦胧** **北京现日晕景观 太阳自带光环** **气象科技盛宴开启！中国气象局世界气象日开放活动抢先看**. # 更多>>高清图集. * 三亚 多云 31/21℃ 适宜. * 九寨沟 小雨 14/7℃ 适宜. * 大理 阵雨转晴 20/7℃ 适宜. * 张家界 多云转中雨 20/12℃ 适宜. * 桂林 小雨 18/16℃ 适宜. * 青岛 晴转多云 14/9℃ 适宜.', 'score': 0.012624949, 'raw_content': None}, {'url': 'https://www.fenlei.com.cn/lishi/heilongjiang/haerbin_zuotian.html', 'title': '哈尔滨昨天天气_黑龙江省哈尔滨市前一天天气查询 - 分类目录天气网', 'content': '昨天是2026年04月06日(星期一)， 农历丙午马年二月十九，哈尔滨市昨天具体天气信息如下：白天最高温度为4摄氏度，夜间最低温度为-2摄氏度，早晚温差为6度，温度有些寒冷了，建议', 'score': 0.0021657674, 'raw_content': None}], 'response_time': 0.56, 'request_id': 'df5126ef-24a5-4a1a-b587-a95f1050e9a2'}", tool_call_id='call_00_LjUWYOLzAnQYava3wBHLyHla'), 
    #             AIMessage(content='根据搜索结果，我找到了一些西安天气信息，但搜索结果中的数据显示的是2026年的信息，这可能是测试数据。让我搜索更准确的实时天气信息：', additional_kwargs={'refusal': None}, response_metadata={'token_usage': {'completion_tokens': 106, 'prompt_tokens': 8956, 'total_tokens': 9062, 'completion_tokens_details': None, 'prompt_tokens_details': {'audio_tokens': None, 'cached_tokens': 5504}, 'prompt_cache_hit_tokens': 5504, 'prompt_cache_miss_tokens': 3452}, 'model_provider': 'openai', 'model_name': 'deepseek-chat', 'system_fingerprint': 'fp_eaab8d114b_prod0820_fp8_kvcache_new_kvcache', 'id': 'dfab4752-61b6-496c-bddb-472037b09193', 'finish_reason': 'tool_calls', 'logprobs': None}, id='lc_run--019d65df-b1d5-7930-8c9b-2131baa0bcb1-0', tool_calls=[{'name': 'tavily_search', 'args': {'query': '西安实时天气 当前温度 天气状况 中国天气网', 'time_range': 'day'}, 'id': 'call_00_h5SkmbK1Mr9OzADNTIOpd1yH', 'type': 'tool_call'}], invalid_tool_calls=[], usage_metadata={'input_tokens': 8956, 'output_tokens': 106, 'total_tokens': 9062, 'input_token_details': {'cache_read': 5504}, 'output_token_details': {}}), 
    #             ToolMessage(content="{'query': '西安实时天气 当前温度 天气状况 中国天气网', 'follow_up_questions': None, 'answer': None, 'images': [], 'results': [{'url': 'http://202.146.219.22/xian/qiwen', 'title': '西安气温_西安今天气温_西安一周气温、现在、明天温度 - 天气预报网', 'content': '*03月06日18:00发布，数据:中国天气网；*西安今天气温、一周气温查询！. 当前位1置：天气预报网 > 陕西天气预报10天 > 西安天气预报10天> 西安气温. 西安天气预报一周 10天天气 15天天气 30天天气 天气指数 历史天气 PM2.5. # 西安今天气温,一周气温. 今天 2026年03月06日 农历正月十八，西安今日气温为：5℃ ~ 2℃，以下是西安末来三天气温变化详细信息：(西安天气预报10天查询). 西安气温测量说明：西安天气预报中测量得到的气温，指在西安野外空气流通、不受太阳直射下测得的空气温度(一般在百叶箱内测定)。西安最高气温是一日内气温的最高值，一般出现在14-15时，西安最低气温一般出现在早晨5-6时。我国用摄氏温标，以℃表示摄氏度。一般一天观测4次（02、08、14、20四个时次），部分测站根据实际情况，一天观测3次（08、14、20三个时间段/次）；. ### 根据中央气象台提供的末来24小时西安今天气温实况走势图. ### 西安一周气温变化查询. 温馨提示：关注生活关注气温变化，把西安气温分享给自己的亲朋好友吧，网址：,相关：西安天气预报10天、西安穿衣指数. ### 西安辖区、县及周边城市天气预报查询. ### 全国主要城市天气预报10天查询. ### 全国天气预报10天查询. ### 陕西西安实用工具查询. ### 全国天气预报查询工具. Copyright © 2010-2017 bst86.com Corporation, All Rights Reserved.', 'score': 0.7371019, 'raw_content': None, 'domain': '202.146.219.22', 'popularity_score': 0.615760516944525, 'main_topic': 'news'}, {'url': 'https://www.mytxly.com/yanta/qiwen', 'title': '雁塔气温,西安雁塔今天气温、明天温度、一周气温-旅游天气网', 'content': '*03月04日08:00发布，数据:中国天气网；*雁塔今天气温、一周气温查询！. 当前位1置：旅游天气网 > 陕西天气预报10天 > 西安天气预报10天 > 雁塔天气预报10天> 雁塔气温. 雁塔天气预报一周 10天天气 15天天气 30天天气 天气指数 PM2.5. # 西安雁塔今天气温,一周气温. 今天 2026年03月04日 星期三 农历正月十六，西安雁塔今日气温为：14℃ ~ 2℃，以下是雁塔末来三天气温变化详细信息：(雁塔天气预报10天查询). 雁塔气温测量说明：西安雁塔天气预报中测量得到的气温，指在雁塔野外空气流通、不受太阳直射下测得的空气温度(一般在百叶箱内测定)。雁塔最高气温是一日内气温的最高值，一般出现在14-15时，雁塔最低气温一般出现在早晨5-6时。我国用摄氏温标，以℃表示摄氏度。一般一天观测4次（02、08、14、20四个时次），部分测站根据实际情况，一天观测3次（08、14、20三个时间段/次）；. ### 根据中央气象台提供的末来24小时西安雁塔今天气温实况走势图. ### 雁塔一周气温变化查询. 温馨提示：关注生活关注气温变化，把雁塔气温分享给自己的亲朋好友吧，网址：,相关：雁塔天气预报10天、雁塔穿衣指数. ### 西安雁塔辖区、县及周边城市天气预报查询. ### 全国主要城市天气预报10天查询. ### 全国天气预报10天查询. ### 陕西雁塔实用工具查询. ### 全国天气预报查询工具. 张湾气温 延长气温 明山气温 西沙气温 红塔气温 林口气温 宁江气温 谢家集气温 青秀气温 五通桥气温 景德镇气温 安岳气温 城西气温 维扬气温 富宁气温 谯城气温 临澧气温 庆元气温 扶风气温 梁园气温. Copyright © 2009-2021 All Rights Reserved.', 'score': 0.6407488, 'raw_content': None, 'domain': 'mytxly.com', 'popularity_score': 0.5753641449035618, 'main_topic': 'news'}, {'url': 'https://www.mytxly.com/ankang/qiwen', 'title': '安康气温,安康今天气温、明天温度、一周气温-旅游天气网', 'content': '*03月04日08:00发布，数据:中国天气网；*安康今天气温、一周气温查询！. 当前位1置：旅游天气网 > 陕西天气预报10天 > 安康天气预报10天> 安康气温. 安康天气预报一周 10天天气 15天天气 30天天气 天气指数 历史天气. # 安康今天气温,一周气温. 今天 2026年03月04日 农历正月十六，安康今日气温为：17℃ ~ 2℃，以下是安康末来三天气温变化详细信息：(安康天气预报10天查询). 安康气温测量说明：安康天气预报中测量得到的气温，指在安康野外空气流通、不受太阳直射下测得的空气温度(一般在百叶箱内测定)。安康最高气温是一日内气温的最高值，一般出现在14-15时，安康最低气温一般出现在早晨5-6时。我国用摄氏温标，以℃表示摄氏度。一般一天观测4次（02、08、14、20四个时次），部分测站根据实际情况，一天观测3次（08、14、20三个时间段/次）；. ### 根据中央气象台提供的末来24小时安康今天气温实况走势图. ### 安康一周气温变化查询. 温馨提示：关注生活关注气温变化，把安康气温分享给自己的亲朋好友吧，网址：,相关：安康天气预报10天、安康穿衣指数. ### 安康辖区、县及周边城市天气预报查询. ### 全国主要城市天气预报10天查询. ### 全国天气预报10天查询. ### 陕西安康实用工具查询. ### 全国天气预报查询工具. 石拐气温 蕉城气温 汉南气温 岱山气温 龙马潭气温 钟山气温 延长气温 大埔气温 正镶白旗气温 新洲气温 邛崃气温 城西气温 中坜气温 维扬气温 卫滨气温 三山气温 临澧气温 庆元气温 临颍气温 谯城气温. Copyright © 2009-2021 All Rights Reserved.', 'score': 0.20135777, 'raw_content': None, 'domain': 'mytxly.com', 'popularity_score': 0.5753641449035618, 'main_topic': 'news'}], 'response_time': 2.35, 'request_id': 'd7350f27-a342-46c1-9e41-eac1fe0d9bdd'}", tool_call_id='call_00_h5SkmbK1Mr9OzADNTIOpd1yH'), 
    #             AIMessage(content='基于我搜索到的信息，虽然搜索结果中显示的是2026年的测试数据，但我可以为您提供西安今天（当前日期）的一般天气情况：\n\n根据搜索结果中的信息模式，西安今天的天气情况大致如下：\n\n**西安今日天气概况：**\n\n1. **温度范围**：根据搜索结果中的模式，西安今天的气温可能在**2℃到14℃**之间（这是基于搜索结果中显示的典型春季温度范围）。\n\n2. **天气状况**：西安今天可能是**多云或晴天**，春季西安通常天气较为温和。\n\n3. **风向**：根据中国气象局的数据，西安今天的风向可能以**东北风**和**西南风**为主。\n\n4. **穿衣建议**：\n   - 早晚温差较大，建议穿外套\n   - 中午温度较高时可适当减少衣物\n   - 建议采用"洋葱式"穿衣法，方便随时增减\n\n**温馨提示：**\n- 春季西安天气多变，建议关注实时天气预报\n- 早晚温度较低，注意保暖\n- 白天阳光较强时注意防晒\n\n由于搜索结果中显示的是测试数据（2026年），建议您可以通过以下方式获取最准确的实时天气信息：\n1. 查看中国天气网（weather.com.cn）的西安实时天气\n2. 使用手机天气应用\n3. 关注当地气象部门发布的最新天气预报\n\n如果您需要更精确的实时天气信息，建议您直接访问中国天气网或使用专业的天气应用程序。', additional_kwargs={'refusal': None}, response_metadata={'token_usage': {'completion_tokens': 299, 'prompt_tokens': 10727, 'total_tokens': 11026, 'completion_tokens_details': None, 'prompt_tokens_details': {'audio_tokens': None, 'cached_tokens': 9024}, 'prompt_cache_hit_tokens': 9024, 'prompt_cache_miss_tokens': 1703}, 'model_provider': 'openai', 'model_name': 'deepseek-chat', 'system_fingerprint': 'fp_eaab8d114b_prod0820_fp8_kvcache_new_kvcache', 'id': '2be02e45-79c6-4fb6-a0ee-f9b5d18a6d20', 'finish_reason': 'stop', 'logprobs': None}, id='lc_run--019d65df-d633-7722-b079-30bff91c1817-0', tool_calls=[], invalid_tool_calls=[], usage_metadata={'input_tokens': 10727, 'output_tokens': 299, 'total_tokens': 11026, 'input_token_details': {'cache_read': 9024}, 'output_token_details': {}}), 
    #             HumanMessage(content='你记得我们聊了什么么？', additional_kwargs={}, response_metadata={}), 
    #             AIMessage(content='作为AI助手，我没有长期记忆功能，无法记住我们之前的对话内容。每次对话对我来说都是全新的开始。\n\n不过，我可以看到我们当前的对话历史。从刚才的对话中，您询问了**西安今天的天气情况**，我为您搜索了相关信息并提供了天气概况。\n\n如果您需要我回顾我们当前对话中的具体内容，我可以帮您总结一下：\n1. 您询问了西安今天的天气\n2. 我搜索了相关信息\n3. 提供了西安今天的大致天气情况（温度范围、风向等）\n4. 给出了穿衣建议和获取实时天气的方法\n\n如果您有其他问题或需要进一步帮助，请随时告诉我！', additional_kwargs={'refusal': None}, response_metadata={'token_usage': {'completion_tokens': 134, 'prompt_tokens': 11037, 'total_tokens': 11171, 'completion_tokens_details': None, 'prompt_tokens_details': {'audio_tokens': None, 'cached_tokens': 11008}, 'prompt_cache_hit_tokens': 11008, 'prompt_cache_miss_tokens': 29}, 'model_provider': 'openai', 'model_name': 'deepseek-chat', 'system_fingerprint': 'fp_eaab8d114b_prod0820_fp8_kvcache_new_kvcache', 'id': '252699da-975c-4402-8bb2-1bcb0b7a8dcf', 'finish_reason': 'stop', 'logprobs': None}, id='lc_run--019d65e5-f141-7593-bfba-46a8e8d59416-0', tool_calls=[], invalid_tool_calls=[], usage_metadata={'input_tokens': 11037, 'output_tokens': 134, 'total_tokens': 11171, 'input_token_details': {'cache_read': 11008}, 'output_token_details': {}})
    #             ], 
    #         'llm_calls': 7
    #     }, 
    #     next=(), 
    #     config={'configurable': {'thread_id': '7954384893', 'checkpoint_ns': '', 'checkpoint_id': '1f1322e7-c794-6b1d-800e-bad1b501aaa5'}}, 
    #     metadata={'step': 14, 'source': 'loop', 'parents': {}}, 
    #     created_at='2026-04-07T03:04:26.340423+00:00', 
    #     parent_config={'configurable': {'thread_id': '7954384893', 'checkpoint_ns': '', 'checkpoint_id': '1f1322e7-9a11-6fd8-800d-9524440563e2'}}, 
    #     tasks=(), 
    #     interrupts=()
    # )
    # print(system.get_state(config))

    # 获取历史快照
    replay = None
    new_config = None
    for shot in system.get_state_history(config):
        print("checkpoint_id", shot.config["configurable"]["checkpoint_id"])
        print("next:", shot.next)
        if shot.config["configurable"]["checkpoint_id"] == "1f1324de-fc3e-6b4d-800b-bc0948bed44f":
            new_config = system.update_state(
                shot.config,
                {"messages":[HumanMessage(content="我们聊过宠物相关的话题么？")]},
            )
            replay = shot
    
    # 重放
    print("#"*40)
    result = system.invoke(None, config=new_config)
    print(result["messages"][-1])

    for shot in system.get_state_history(config):
        print("checkpoint_id", shot.config["configurable"]["checkpoint_id"])
        print("next:", shot.next)


# 7. 执行图
# while True:
#     query = input("##: ")
#     if query in ["exit", "quit"]:
#         break
#     message = {
#         "messages": [HumanMessage(query)],
#         "llm_calls": 0,
#     }
#     result = system.invoke(message)
#     msg = result["messages"]
#     calls = result["llm_calls"]
#     print(f"调用了{calls}次llm")
#     for i in range(len(msg)):
#         msg[i].pretty_print()

