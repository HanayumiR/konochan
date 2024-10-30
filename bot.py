import discord
from discord.ext import commands
from discord import app_commands
from datetime import datetime
import asyncio
import json
import os
import re

intents = discord.Intents.default()
bot = commands.Bot(command_prefix="/", intents=intents)

#初期化
user_data = {}
user_tsun_mode = {}

#ロード
def load_data():
    global user_data
    try:
        with open("schedule_data.json", "r") as f:
            user_data = json.load(f)
    except FileNotFoundError:
        user_data = {}

#セーブ
def save_data():
    with open("schedule_data.json", "w") as f:
        json.dump(user_data, f)

load_data()

#正規化
def normalize_time(time_str):
    time_str = re.sub(r'\D', '', time_str)
    if len(time_str) == 3:
        return f"{time_str[0]}:{time_str[1:3]}"
    elif len(time_str) == 4:
        return f"{time_str[:2]}:{time_str[2:]}"
    elif len(time_str) == 2:
        return f"{time_str}:00"
    return time_str

#/changeまわり
def format_message(user_id, normal_message, tsundere_message):
    if user_tsun_mode.get(user_id, False):
        return tsundere_message
    return normal_message

#本体
@bot.event
async def on_ready():
    await bot.tree.sync()
    await bot.change_presence(activity=discord.Game(name="📖みなさんのお手伝い中！"))
    print("河野ちゃん Ver.1.0(正式版)　　起動しました！")

@bot.tree.command(name="set_schedule", description="今日の目標を設定します。使用例: /set_schedule 目標")
async def set_schedule(interaction: discord.Interaction, task: str):
    user_id = str(interaction.user.id)
    user_data[user_id] = {'task': task, 'start_time': datetime.now().isoformat()}
    save_data()

    await interaction.response.send_message(
        format_message(user_id, 
                       f"{interaction.user.mention}さんの今日の目標は{task}なんですね。今から計測を始めますよ。応援してます♪", 
                       f"{interaction.user.mention}の今日の目標は{task}！言ったからにはちゃんと取り組みなさいよ！")
    )

@bot.tree.command(name="finish_schedule", description="設定した目標の計測を終了します。")
async def finish_schedule(interaction: discord.Interaction):
    user_id = str(interaction.user.id)
    if user_id in user_data and 'start_time' in user_data[user_id]:
        start_time = datetime.fromisoformat(user_data[user_id]['start_time'])
        elapsed_time = datetime.now() - start_time

        hours, remainder = divmod(elapsed_time.total_seconds(), 3600)
        minutes, _ = divmod(remainder, 60)

        task = user_data[user_id]['task']
        await interaction.response.send_message(
            format_message(user_id, 
                           f"{interaction.user.mention}さんは今日の目標の{task}を {int(hours)} 時間 {int(minutes)} 分間行いました！お疲れさまです♪", 
                           f"あら、{interaction.user.mention}。今日は{task}を {int(hours)} 時間 {int(minutes)} 分間やったのね。少しはやるじゃない、お疲れ様。　...べつに少しくらいは褒めてあげるわよ。")
        )
        
        del user_data[user_id]
        save_data()
    else:
        await interaction.response.send_message(
            format_message(user_id, 
                           f"{interaction.user.mention}さん、まだ目標が設定されていないようですよ？", 
                           f"{interaction.user.mention}、まだ目標なんて設定してないの？ほんとにダメね。")
        )

@bot.tree.command(name="remove_schedule", description="今日の目標を削除します。")
async def remove_schedule(interaction: discord.Interaction):
    user_id = str(interaction.user.id)
    if user_id in user_data and 'task' in user_data[user_id]:
        del user_data[user_id]
        save_data()
        await interaction.response.send_message(
            format_message(user_id, 
                           f"{interaction.user.mention}さん、もう一度予定を立て直しませんか？", 
                           f"{interaction.user.mention}、まずは新しい目標を建てるわよ！")
        )
    else:
        await interaction.response.send_message(
            format_message(user_id, 
                           f"{interaction.user.mention}さん、まず建てるべき目標が設定されていないようですよ？", 
                           f"{interaction.user.mention}、目標がないのに何をするってわけ？")
        )

@bot.tree.command(name="set_reminder", description="設定した時刻にお知らせします。使用例: /set_reminder 12:00")
async def set_reminder(interaction: discord.Interaction, time: str):
    user_id = str(interaction.user.id)
    user_data[user_id] = user_data.get(user_id, {})

    if not re.match(r'^(0[0-9]|1[0-9]|2[0-3]|[0-9]):[0-5][0-9]$', time):
        await interaction.response.send_message(
            format_message(user_id, 
                           f"{interaction.user.mention}さん、嘘は良くないと思います。", 
                           f"アンタねぇ、なに適当なこと言ってんのよ！")
        )
        return

    user_data[user_id]['reminder_time'] = normalize_time(time)
    save_data()

    await interaction.response.send_message(
        format_message(user_id, 
                       f"{interaction.user.mention}さん、{user_data[user_id]['reminder_time']}に勉強の時間をお知らせしますね。", 
                       f"{interaction.user.mention}がサボらないためにも、{user_data[user_id]['reminder_time']}になったら教えてあげるわよ。感謝しなさいよね！")
    )

    while 'reminder_time' in user_data[user_id]:
        now = datetime.now().strftime("%H:%M")
        if now == user_data[user_id]['reminder_time']:
            await interaction.channel.send(
                format_message(user_id, 
                               f"{interaction.user.mention}さん、勉強の時間ですよ～！一緒に頑張りましょう！", 
                               f"ねぇ{interaction.user.mention}、アンタがサボろうとしてたの、見逃さないからね！今すぐ始めるわよ！")
            )
            del user_data[user_id]['reminder_time']
            save_data()
            break
        await asyncio.sleep(60)

@bot.tree.command(name="remove_reminder", description="設定したリマインダーを削除します。")
async def remove_reminder(interaction: discord.Interaction):
    user_id = str(interaction.user.id)
    if user_id in user_data and 'reminder_time' in user_data[user_id]:
        del user_data[user_id]['reminder_time']
        save_data()
        await interaction.response.send_message(
            format_message(user_id, 
                           f"リマインダーを削除しました！", 
                           f"リマインダーを消したあげたわよ。別にアンタのためを想ってやったわけじゃないから！")
        )
    else:
        await interaction.response.send_message(
            format_message(user_id, 
                           f"{interaction.user.mention}さん、削除するリマインダーが設定されていないようですよ？", 
                           f"ねぇ{interaction.user.mention}、最初からそんなの設定なんてしてなかったでしょ？")
        )

@bot.tree.command(name="change", description="性格を切り替えます")
async def change(interaction: discord.Interaction):
    user_id = str(interaction.user.id)
    user_tsun_mode[user_id] = not user_tsun_mode.get(user_id, False)

    if user_tsun_mode[user_id]:
        await interaction.response.send_message(
            f"ねぇ{interaction.user.mention}、私はあんまりアンタに期待してるわけじゃないから！　でも...ちょっとだけ、ちょっとだけなら期待しててあげるわ。"
        )
    else:
        await interaction.response.send_message(
            f"さぁ、{interaction.user.mention}さん、今日も頑張りましょう！"
        )

bot.run("#ここにdiscordbot用トークンを置き換え")
