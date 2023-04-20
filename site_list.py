import asyncio
import requests
from datetime import datetime, timedelta
import pandas as pd
import matplotlib.pyplot as plt
from pandas.plotting import table
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ApplicationBuilder, CommandHandler, CallbackQueryHandler, CallbackContext, ContextTypes
import io
from asyncio import Semaphore


YOUR_API_TOKEN = '5617220143:AAHLElaNN7cOtO0K4RUJDw_FcKEFUvLq7iA'
YOUR_CHAT_ID = '6000226899'

LOGIN_DATA = {
    'account': '16761780288',
    'password': 'Qaz123',
    'source': 'cms',
    'redirect': 'https://www.51.la/',
    'register': '2'
}

STATS_URL = 'https://v6.51.la/api/report/trend/chainList'
SITE_LIST_URL = 'https://v6.51.la/api/site/list'


async def fetch_stats_data(com_id: str, site_name: str, placeholder_message) -> pd.DataFrame:
    # 创建一个requests，保持Cookie
    session = requests.Session()

    # 模拟登录
    session.post('https://user.51.la/api/user/login', data=LOGIN_DATA)

    # 获取七天
    today = datetime.now()
    date_list = [(today - timedelta(days=i)).strftime('%Y-%m-%d') for i in range(1, 8)]

    stats_data = []
    for i in range(len(date_list)):
        start_date = date_list[i]
        end_date = date_list[i]
        before_start_date = date_list[i + 1] if i < len(date_list) - 1 else (today - timedelta(days=8)).strftime('%Y-%m-%d')
        before_end_date = date_list[i + 1] if i < len(date_list) - 1 else (today - timedelta(days=8)).strftime('%Y-%m-%d')

        params = {
            'comId': com_id,
            'startDate': start_date,
            'endDate': end_date,
            'beforeStartDate': before_start_date,
            'beforeEndDate': before_end_date,
            'pageSize': '24'
        }

        response = session.post(STATS_URL, data=params)

        await asyncio.sleep(1)

        # 更新占位符消息
        await placeholder_message.edit_text(f"正在获取 {site_name} 数据... ({i + 1}/7) 完成")

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
        avg_duration = "00:{:02}:{:02}".format(*divmod(round(stats["curAvgDuration"] / 1000), 60))

        data.append([stats["curTime"], stats["curPv"], stats["curSv"],
                     stats["curUv"], stats["curIp"], bounce_rate, avg_duration])

    # 创建DataFrame
    columns = ["日期", "浏览次数（PV）", "日活跃用户",
               "独立访客（UV）", "每日IP（IP数）", "跳出率", "访问时长"]
    df = pd.DataFrame(data, columns=columns)

    # 将DataFrame保存为Excel
    df.to_excel("stats.xlsx", index=False)

    # 发送获取数据完成的消息
    await placeholder_message.edit_text("所有数据获取完成，正在生成表格，请稍等...")

    return df, site_name  # 返回站点名称



async def fetch_site_list() -> list:
    # 创建一个requests，保持Cookie
    session = requests.Session()
    # 模拟登录
    session.post('https://user.51.la/api/user/login', data=LOGIN_DATA)

    params = {
        'ascCheck': 'false',
        'sortField': 'ip',
        'pageSize': '30',
        'curPage': '1'
    }

    response = session.post(SITE_LIST_URL, data=params)

    if response.status_code != 200:
        print(f"请求失败，状态码：{response.status_code}")
        print(response.text)
        return []

    site_list = response.json().get('data', [])

    return site_list


async def choose_site(update: Update, context: CallbackContext) -> None:
    site_list = await fetch_site_list()
    if not site_list:
        await update.message.reply_text("获取站点列表失败，请稍后重试")
        return

    buttons = []
    for site in site_list:
        buttons.append(InlineKeyboardButton(site['name'], callback_data=str(site['comId'])))
    
    keyboard = InlineKeyboardMarkup(build_menu(buttons, n_cols=3))

    await update.message.reply_text('请选择51LA统计:', reply_markup=keyboard)


def build_menu(buttons, n_cols, header_buttons=None, footer_buttons=None):
    menu = [buttons[i:i + n_cols] for i in range(0, len(buttons), n_cols)]
    if header_buttons:
        menu.insert(0, header_buttons)
    if footer_buttons:
        menu.append(footer_buttons)
    return menu



async def process_site_stats(com_id, site_name, placeholder_message, query):
    # 使用 async with 限制并发数
    async with concurrent_limit:
        # 获取数据
        df, site_name = await fetch_stats_data(com_id, site_name, placeholder_message)

        # 将 DataFrame 生成图片
        image_buf = plot_dataframe(df, site_name)

        # 发送图片
        await query.message.reply_photo(photo=image_buf)

        # 删除占位符消息
        await placeholder_message.delete()

concurrent_limit = Semaphore(2)

async def handle_site_selection(update: Update, context: CallbackContext) -> None:
    # 在脚本的全局区域创建一个 Semaphore 对象
    

    query = update.callback_query
    com_id = query.data
    # 创建占位符消息
    placeholder_message = await query.message.reply_text("正在获取数据，请稍等...")

    # 获取站点名称
    site_list = await fetch_site_list()
    site_name = next((site['name'] for site in site_list if str(site['comId']) == com_id), None)

    if site_name is None:
        await placeholder_message.edit_text("找不到站点名称，请稍后重试")
        return

    asyncio.create_task(process_site_stats(com_id, site_name, placeholder_message, query))





def plot_dataframe(df, site_name):
    from pylab import mpl
    mpl.rcParams['font.sans-serif'] = ['Microsoft YaHei']
    mpl.rcParams['axes.unicode_minus'] = False
    fig = plt.figure(figsize=(5, 2), dpi=800)  # 修改了figsize参数，使其符合 Telegram 要求
    ax = fig.add_subplot(111, frame_on=False)
    ax.xaxis.set_visible(False)
    ax.yaxis.set_visible(False)

    cell_text = df.to_numpy().tolist()  # 将 DataFrame 转换为列表
    columns = df.columns

    tbl = ax.table(cellText=cell_text, colLabels=columns, loc='center')  # 使用自定义数据创建表格
    

    ax.set_title(site_name or '')  # 设置表格标题
    buf = io.BytesIO()
    plt.savefig(buf, format='png')
    plt.close(fig)
    buf.seek(0)
    return buf


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    await update.message.reply_text(f'统计代码')


async def error(update: Update, context: CallbackContext) -> None:
    if update.message:
        await update.message.reply_text(text=str(context.error))


app = ApplicationBuilder().token(YOUR_API_TOKEN).build()

app.add_handler(CommandHandler("start", start))
app.add_handler(CommandHandler("tongji", choose_site))
app.add_handler(CallbackQueryHandler(handle_site_selection))

app.add_error_handler(error)

app.run_polling()

