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

# UI: ボタンとモーダルを使ったVC名変更
class RenameVCView(discord.ui.View):
    def __init__(self, vc):
        super().__init__(timeout=None)
        self.vc = vc

    @discord.ui.button(label="部屋名変更", style=discord.ButtonStyle.primary)
    async def rename(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.send_modal(RenameVCModal(self.vc))

class RenameVCModal(discord.ui.Modal, title="部屋名変更"):
    new_name = discord.ui.TextInput(label="部屋名", placeholder="○○しよ！", required=True)

    def __init__(self, vc):
        super().__init__()
        self.vc = vc

    async def on_submit(self, interaction: discord.Interaction):
        await self.vc.edit(name=self.new_name.value)
        await interaction.response.send_message(
            f"✅ 部屋名を「{self.new_name.value}」に変更したよ！", ephemeral=True
        )

bot.run(config["TOKEN"])
