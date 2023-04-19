import asyncio
import requests 
from datetime import datetime, timedelta
import pandas as pd
import matplotlib.pyplot as plt
from pandas.plotting import table 
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes
import io


YOUR_API_TOKEN = '6175545283:AAGTNAZfExDenLTkNlgk7y2HDhc7FjOIJts'
YOUR_CHAT_ID = '6000226899'


async def fetch_stats_data(update: Update,placeholder_message) -> pd.DataFrame:
    # 登录接口和参数
    login_url = 'https://user.51.la/api/user/login'
    login_data = {
        'account': '16761780288',
        'password': 'Qaz123',
        'source': 'cms',
        'redirect': 'https://www.51.la/',
        'register': '2'
    }

    # 创建一个requests，保持Cookie
    session = requests.Session()

    # 模拟登录
    session.post(login_url, data=login_data)

    # 创建占位符消息
    placeholder_message = await update.message.reply_text("正在获取数据 (0/7) 完成")

    # 获取七天
    today = datetime.now()
    date_list = [(today - timedelta(days=i)).strftime('%Y-%m-%d')
                 for i in range(1, 8)]

    # 统计数据接口
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

        await asyncio.sleep(1)
        
        # 更新占位符消息
        await placeholder_message.edit_text(f"正在获取数据... ({i + 1}/7) 完成")
        
        if response.status_code != 200:
            print(f"请求失败，状态码：{response.status_code}")
            print(response.text)
        else:
            daily_stats = response.json()
            stats_data.append(daily_stats["bean"])

    # 将数据保存到DataFrame
    data = []

    for stats in stats_data:
        bounce_rate = "{:.2%}".format(stats["curBounceRate"])
        avg_duration = "{:02}:{:02}".format(
            *divmod(round(stats["curAvgDuration"] / 1000), 60))

        data.append([stats["curTime"], stats["curPv"], stats["curSv"],
                    stats["curUv"], stats["curIp"], bounce_rate, avg_duration])

    # 创建DataFrame
    columns = ["日期", "浏览次数（PV）", "日活跃用户",
               "独立访客（UV）", "每日IP（IP数）", "跳出率", "访问时长"]
    df = pd.DataFrame(data, columns=columns)

    # 将 DataFrame保存为Excel
    print(df)
    df.to_excel("stats.xlsx", index=False)

    
    # 所有数据获取完成，发送更新的占位符消息
    await placeholder_message.edit_text("所有数据获取完成，正在生成表格，请稍等...")
    
    return df
    

def plot_dataframe(df):
    from pylab import mpl
    mpl.rcParams['font.sans-serif'] = ['Microsoft YaHei']
    mpl.rcParams['axes.unicode_minus'] = False

    fig = plt.figure(figsize=(4, 2), dpi=800)  # 修改了figsize参数，使其符合 Telegram 要求
    ax = fig.add_subplot(111, frame_on=False)
    ax.xaxis.set_visible(False)
    ax.yaxis.set_visible(False)

    table(ax, df, loc='center')

    buf = io.BytesIO()
    plt.savefig(buf, format='png')
    plt.close(fig)
    buf.seek(0)
    return buf


async def static(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    # 发送占位符消息
    placeholder_message = await update.message.reply_text("正在获取数据，请稍等...")
    
    # 获取数据
    df = await fetch_stats_data(update,placeholder_message)
    await placeholder_message.delete()
    # 将 DataFrame 生成图片
    image_buf = plot_dataframe(df)

    # 发送图片
    await update.message.reply_photo(photo=image_buf)
    


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    await update.message.reply_text(f'统计代码')


async def error(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    await update.message.reply_text(text=context)

app = ApplicationBuilder().token(YOUR_API_TOKEN).build()

app.add_handler(CommandHandler("test", start))

app.add_handler(CommandHandler("Static", static))

# app.add_error_handler(CommandHandler('Error', error))

app.run_polling()
