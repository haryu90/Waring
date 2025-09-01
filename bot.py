import discord
from discord.ext import commands
from discord import app_commands
from dotenv import load_dotenv
import os

load_dotenv()
TOKEN_1 = os.getenv("TOKEN_1")

intents = discord.Intents.default()
intents.members = True

bot = commands.Bot(command_prefix="!", intents=intents)
tree = bot.tree

warnings = {}  # { guild_id: { user_id: count } }
bot.cautions = {}  # { guild_id: { user_id: count } }

# 경고 횟수별 역할 ID 매핑
warnings_roles = {
    1: 1411609989969219614,  # 경고1회
    2: 1411609990648696903,  # 경고2회
    3: 1411610001264480276,  # 경고3회
    4: 1411610001784438804,  # 경고4회
}

# 주의 횟수별 역할 ID 매핑
cautions_roles = {
    1: 1411609945937547416,  # 주의1회
    2: 1411609988161470564,  # 주의2회
    3: 1411609989138747483,  # 주의3회
}

async def update_role(guild, member, count, type_):
    # type_이 "경고"면 warnings_roles, "주의"면 cautions_roles 사용
    roles_map = warnings_roles if type_ == "경고" else cautions_roles

    role_id = roles_map.get(count)
    old_role_id = roles_map.get(count - 1)

    if old_role_id:
        old_role = guild.get_role(old_role_id)
        if old_role and old_role in member.roles:
            await member.remove_roles(old_role)

    if role_id:
        role = guild.get_role(role_id)
        if role and role not in member.roles:
            await member.add_roles(role)

@tree.command(name="경고", description="유저에게 경고를 부여합니다.")
@app_commands.describe(횟수="경고 횟수", 대상="경고를 받을 유저", 사유="경고 사유")
async def 경고(interaction: discord.Interaction, 횟수: int, 대상: discord.Member, 사유: str):
    guild_id = interaction.guild.id
    user_id = 대상.id

    if guild_id not in warnings:
        warnings[guild_id] = {}

    current = warnings[guild_id].get(user_id, 0)
    new_count = current + 횟수
    warnings[guild_id][user_id] = new_count

    await update_role(interaction.guild, 대상, new_count, "경고")

    embed = discord.Embed(title="⚠️ 경고 발부", color=discord.Color.red())
    embed.add_field(name="대상", value=대상.mention, inline=True)
    embed.add_field(name="누적 경고", value=f"{new_count}회", inline=True)
    embed.add_field(name="사유", value=사유, inline=False)

    await interaction.response.send_message(embed=embed)

@tree.command(name="주의", description="유저에게 주의를 부여합니다.")
@app_commands.describe(횟수="주의 횟수", 대상="주의를 받을 유저", 사유="주의 사유")
async def 주의(interaction: discord.Interaction, 횟수: int, 대상: discord.Member, 사유: str):
    guild_id = interaction.guild.id
    user_id = 대상.id

    if guild_id not in bot.cautions:
        bot.cautions[guild_id] = {}

    current = bot.cautions[guild_id].get(user_id, 0)
    new_count = current + 횟수
    bot.cautions[guild_id][user_id] = new_count

    await update_role(interaction.guild, 대상, new_count, "주의")

    embed = discord.Embed(title="🟡 주의 발부", color=discord.Color.gold())
    embed.add_field(name="대상", value=대상.mention, inline=True)
    embed.add_field(name="누적 주의", value=f"{new_count}회", inline=True)
    embed.add_field(name="사유", value=사유, inline=False)

    await interaction.response.send_message(embed=embed)

@tree.command(name="경고조회", description="유저의 누적 경고 및 주의 횟수를 조회합니다.")
@app_commands.describe(대상="조회할 유저")
async def 경고조회(interaction: discord.Interaction, 대상: discord.Member):
    guild_id = interaction.guild.id
    user_id = 대상.id

    경고횟수 = warnings.get(guild_id, {}).get(user_id, 0)
    주의횟수 = bot.cautions.get(guild_id, {}).get(user_id, 0)

    embed = discord.Embed(title=f"{대상.display_name}님의 기록", color=discord.Color.blue())
    embed.add_field(name="경고 누적 횟수", value=f"{경고횟수}회", inline=True)
    embed.add_field(name="주의 누적 횟수", value=f"{주의횟수}회", inline=True)

    await interaction.response.send_message(embed=embed)

@tree.command(name="경고삭제", description="유저의 경고 횟수를 삭제합니다.")
@app_commands.describe(대상="경고를 삭제할 유저")
async def 경고삭제(interaction: discord.Interaction, 대상: discord.Member):
    guild_id = interaction.guild.id
    user_id = 대상.id

    if guild_id in warnings and user_id in warnings[guild_id]:
        count = warnings[guild_id][user_id]
        del warnings[guild_id][user_id]

        old_role_id = warnings_roles.get(count)
        if old_role_id:
            role = interaction.guild.get_role(old_role_id)
            if role and role in 대상.roles:
                await 대상.remove_roles(role)

        await interaction.response.send_message(f"{대상.mention}님의 경고 기록을 삭제했습니다.")
    else:
        await interaction.response.send_message(f"{대상.mention}님은 경고 기록이 없습니다.")

@bot.event
async def on_ready():
    print(f"✅ 로그인됨: {bot.user}")
    try:
        synced = await tree.sync()
        print(f"🔧 슬래시 커맨드 {len(synced)}개 등록 완료")
    except Exception as e:
        print(f"명령어 등록 실패: {e}")

bot.run(TOKEN_1)
