import asyncio
import requests
import json
from datetime import datetime, timedelta
import pandas as pd

USERNAME = "df202303"
TOKEN = "eyJhbGciOiJIUzM4NCJ9.eyJzdWIiOiJhY2MiLCJhdWQiOiLnmb7luqbnu5_orqEiLCJ1aWQiOjQ2Mzc1NTc1LCJhcHBJZCI6IjEzYmQ1MDQ5YTY3NmQxMDczNzk1OTkzMjEwMmVjNTU3IiwiaXNzIjoi5ZWG5Lia5byA5Y-R6ICF5Lit5b-DIiwicGxhdGZvcm1JZCI6IjQ5NjAzNDU5NjU5NTg1NjE3OTQiLCJleHAiOjE2ODQ2NzQ2ODcsImp0aSI6Ijc0OTU0NzA4MjIxMTQxNzMwMjEifQ.qtvoMvFYdiYHVjf5EhjiL2BaRPWLCvOgZtsQjQNFofyKcWvIGcpWaW4iSBLGHdBO"

def get_site_list():
    url = "https://api.baidu.com/json/tongji/v1/ReportService/getSiteList"
    headers = {
        "Content-Type": "application/json"
    }
    data = {
        "header": {
            "userName": USERNAME,
            "accessToken": TOKEN,
        }
    }
    response = requests.post(url, headers=headers, data=json.dumps(data))
    return response.json()['body']['data'][0]['list']

def get_data(site_id, start_date, end_date):
    url = "https://api.baidu.com/json/tongji/v1/ReportService/getData"
    headers = {
        "Content-Type": "application/json"
    }
    data = {
        "header": {
            "userName": USERNAME,
            "accessToken": TOKEN,
        },
        "body": {
            "site_id": site_id,
            "start_date": start_date.strftime("%Y%m%d"),
            "end_date": end_date.strftime("%Y%m%d"),
            "metrics": "pv_count,visitor_count,ip_count,bounce_ratio,avg_visit_time",
            "method": "source/all/a"
        }
    }
    response = requests.post(url, headers=headers, data=json.dumps(data))
    return response.json()




# import pandas as pd
# import datetime

# # 示例数据，实际上应该从API接收
# data = {
#     "header": {
#         # ...
#     },
#     "body": {
#         "data": [
#             {
#                 "result": {
#                     "total": 5,
#                     "pageSum": [
#                         [
#                             853874,
#                             60249,
#                             57282,
#                             25.57,
#                             622
#                         ],
#                         [],
#                         []
#                     ],
#                     "timeSpan": [
#                         "2023/04/19"
#                     ],
#                     # ...
#                 }
#             }
#         ],
#         "expand": {}
#     }
# }

# # 提取所需数据
# result = data['body']['data'][0]['result']
# time_span = result['timeSpan'][0]
# page_sum = result['pageSum'][0]
# fields = result['fields']

# # 根据字段和数据创建一个字典
# record = {fields[i]: page_sum[i] for i in range(len(fields))}

# # 创建包含最近7天数据的列表
# today = datetime.date.today()
# last_week = [(today - datetime.timedelta(days=i)).strftime('%Y/%m/%d') for i in range(7)]

# # 构建包含所需字段的表格
# table_data = []
# for date in last_week:
#     row = {'日期': date}
#     row.update(record)
#     table_data.append(row)

# # 使用pandas处理数据
# df = pd.DataFrame(table_data)

# # 将处理好的数据保存到CSV文件
# df.to_csv('output.csv', index=False)
