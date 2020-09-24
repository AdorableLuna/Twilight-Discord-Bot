import discord
import pendulum

from cogs.maincog import Maincog
from discord.ext import commands

class Balance(Maincog):

    def __init__(self, client):
        Maincog.__init__(self, client, whitelistedChannels = [756884303580758086])

    @commands.Cog.listener()
    async def on_ready(self):
        self.paydayEmoji = self.client.get_emoji(758740464567713823)

    @commands.command()
    async def balance(self, ctx):
        if not self.checkIfAllowedChannel(ctx.channel.id): return
        if isinstance(ctx.message.channel, discord.DMChannel):
            await ctx.message.channel.send("This feature is, sadly, not supported. Type the command in the correct channel and I will DM your balance.")
            return

        embed = discord.Embed(color=0x3090d9, title="Balance Check")
        embed.description = "Please check private messages for balance details."
        await ctx.message.channel.send(embed=embed)

        author = ctx.message.author
        SPREADSHEET_ID = self.client.config["SPREADSHEET_ID"]
        allRows = self.client.sheet.getAllRows(SPREADSHEET_ID, "'Balance'!A2:D")

        if not allRows:
            await author.send("Something went wrong with retrieving data from the sheets, please try again. If this continues please contact someone from Council or Management.")
            return

        for i in range(len(allRows)):
            if not allRows[i]: continue
            if allRows[i][0] == author.display_name:
                try:
                    balance = allRows[i][3]
                except:
                    balance = 0

                balanceEmbed = discord.Embed(color=0x3090d9, title="Balance Information")
                balanceEmbed.description = self._getCountdownNextPayday()
                balanceEmbed.add_field(name="Current Balance", value=balance)

                await author.send(embed=balanceEmbed)
                return

        print(f"Couldn't retrieve balance of {author.display_name}")
        await author.send("Your balance could not be retrieved. Please message someone from Council or Management.")

    @commands.command()
    async def payday(self, ctx):
        await ctx.send(self._getCountdownNextPayday())

    def _getCountdownNextPayday(self):
        timezone = 'Europe/Berlin'

        # Need a starting date to count from - which is 11-9-2020 in this case
        friday = pendulum.datetime(2020, 9, 11, tz=timezone).next(pendulum.FRIDAY).next(pendulum.FRIDAY)
        today = pendulum.today(timezone)

        if friday < today:
            friday = self._addTwoWeeks(friday, today)
        if friday == today:
            return f"Payday is **today**! {self.paydayEmoji}"

        now = pendulum.now(timezone)
        period = pendulum.period(now, friday)

        return f"Next payday: **{friday.format('DD-MM-YYYY')}**, which is in **{period.days} days, {period.hours} hours, {period.minutes} minutes, {period.remaining_seconds} seconds**"

    def _addTwoWeeks(self, datetime, today):
        datetime = datetime.add(weeks=2)

        if datetime < today:
            return self._addTwoWeeks(datetime, today)
        else:
            return datetime

def setup(client):
    client.add_cog(Balance(client))
