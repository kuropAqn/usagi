import discord
from discord.ext import commands
import json

# 設定読み込み
with open("config.json", "r") as f:
    config = json.load(f)

intents = discord.Intents.all()
bot = commands.Bot(command_prefix="!", intents=intents)

@bot.event
async def on_ready():
    print(f"✅ Bot起動: {bot.user}")

# VC参加時に設定メッセージ送信
@bot.event
async def on_voice_state_update(member, before, after):
    if before.channel is None and after.channel is not None:
        vc = after.channel
        channel = bot.get_channel(int(config["VC_SETTINGS_CHANNEL"]))
        if channel:
            view = RenameVCView(vc)
            await channel.send(
                f"🎧 `{vc.name}` の設定メニュー：", view=view
            )

bot.run(config["TOKEN"])
