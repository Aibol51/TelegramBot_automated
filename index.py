import requests
import json
from datetime import datetime, timedelta
import pandas as pd
import matplotlib.pyplot as plt
import os
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes
import io


YOUR_API_TOKEN = '6175545283:AAGTNAZfExDenLTkNlgk7y2HDhc7FjOIJts'
YOUR_CHAT_ID = '6000226899'


def fetch_stats_data():
    # 登录接口和参数
    login_url = 'https://user.51.la/api/user/login'
    login_data = {
        'account': '16761780288',
        'password': 'Qaz123',
        'source': 'cms',
        'redirect': 'https://www.51.la/',
        'register': '2'
    }

    # 创建一个 requests 会话，以便在多个请求之间保持 Cookie
    session = requests.Session()

    # 模拟登录
    session.post(login_url, data=login_data)

    # 获取前七天的日期
    today = datetime.now()
    date_list = [(today - timedelta(days=i)).strftime('%Y-%m-%d')
                 for i in range(1, 8)]

    # 请求统计数据接口并保存结果
    stats_url = 'https://v6.51.la/api/report/trend/chainList'
    stats_data = []

    for i in range(len(date_list)):
        start_date = date_list[i]
        end_date = date_list[i]
        before_start_date = date_list[i + 1] if i < len(date_list) - 1 else (
            today - timedelta(days=8)).strftime('%Y-%m-%d')
        before_end_date = date_list[i + 1] if i < len(date_list) - 1 else (
            today - timedelta(days=8)).strftime('%Y-%m-%d')

        params = {
            'comId': '257308',
            'startDate': start_date,
            'endDate': end_date,
            'beforeStartDate': before_start_date,
            'beforeEndDate': before_end_date,
            'pageSize': '24'
        }

        response = session.post(stats_url, data=params)
        if response.status_code != 200:
            print(f"请求失败，状态码：{response.status_code}")
            print(response.text)
        else:
            daily_stats = response.json()
            stats_data.append(daily_stats["bean"])

    # 准备将数据保存到 DataFrame 中
    data = []

    for stats in stats_data:
        bounce_rate = "{:.2%}".format(stats["curBounceRate"])
        avg_duration = "{:02}:{:02}".format(
            *divmod(round(stats["curAvgDuration"] / 1000), 60))

        data.append([stats["curTime"], stats["curPv"], stats["curSv"],
                    stats["curUv"], stats["curIp"], bounce_rate, avg_duration])

    # 创建 DataFrame
    columns = ["日期", "浏览次数（PV）", "日活跃用户",
               "独立访客（UV）", "每日IP（IP数）", "跳出率", "访问时长"]
    df = pd.DataFrame(data, columns=columns)

    # 将 DataFrame 保存为 Excel 文件并转换为字节流
    print(df)
    df.to_excel("stats.xlsx", index=False)
    return df
    


async def static(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    df = fetch_stats_data()

    # 将 DataFrame 保存为字节流
    output = io.BytesIO()
    file_name = "统计.xlsx"
    with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
        df.to_excel(writer, index=False)

        # 获取工作表对象以设置列宽
        worksheet = writer.sheets['Sheet1']

        # 计算每列的最大字符宽度
        max_widths = []
        for idx, col in enumerate(df.columns):
            # 计算列名的字符宽度并添加额外宽度
            max_col_width = len(str(col)) + 5  # 在这里添加额外宽度

            # 计算该列所有单元格的字符宽度
            for value in df.iloc[:, idx]:
                max_col_width = max(max_col_width, len(str(value)))

            # 将计算的最大字符宽度添加到列表中
            max_widths.append(max_col_width)

        # 设置每列的宽度
        for idx, width in enumerate(max_widths):
            # 设置列宽，增加一点额外宽度以避免文本被截断
            worksheet.set_column(idx, idx, width + 2)

        writer.book.close()

    # 将字节流的文件指针移到开头
    output.seek(0)

    # 将字节流传递给 reply_document
    await update.message.reply_document(document=output, filename=file_name)

    os.remove(file_name)

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    await update.message.reply_text(f'每天8点')


async def error(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    await update.message.reply_text(text=context)

app = ApplicationBuilder().token(YOUR_API_TOKEN).build()

app.add_handler(CommandHandler("Start", start))

app.add_handler(CommandHandler("Static", static))

# app.add_error_handler(CommandHandler('Error', error))

app.run_polling()
