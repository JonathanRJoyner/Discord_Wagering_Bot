import discord
from discord.ext import commands
from discord.commands import Option, slash_command

import db

async def get_sports(ctx: discord.AutocompleteContext):
    """Returns a list of sports that begin with the characters entered so far."""
    return [sport for sport in db.sports() if sport.startswith(ctx.value)]

async def get_leagues(ctx: discord.AutocompleteContext):
    """Returns a list of sports that begin with the characters entered so far."""
    return [
        league
        for league in db.leagues(ctx.options["sport"])
        if league.startswith(ctx.value)
    ]

async def get_match(ctx: discord.AutocompleteContext):
    """Returns a list of teams that are within the selected sport option"""
    return [
        f"{match[4]} vs. {match[5]} | {match[2]} {match[3]}"
        for match in db.matches(ctx.options["league"])
    ]

async def get_bets(ctx: discord.AutocompleteContext):
    return [bet for bet in db.bets(ctx.options["match"])]

def _payout(bet, amount):
    '''Calculates the payout given the betting odds and the amount a user wagers.'''
    moneyline = int(float(bet.split(" | ")[-1]))

    if moneyline < 0:
        payout = (100 / abs(moneyline)) * amount

    else:
        payout = (moneyline / 100) * amount

    return int(payout)

def _gametime(match):
    '''Gets the gametime from teh users selected match.'''
    return match.split(" | ")[-1]


def _match(match):
    '''Gets the team matchup from the users selected match.'''
    return match.split(" | ")[0]


def _teams(match):
    '''Gets the teams from the users selected match.'''
    return match.split(" vs. ")


def _team_choice(bet):
    '''Gets the odds for the users selected bet.'''
    return bet.split(" | ")[0]    

class Confirm(discord.ui.View):
    """This is a class which creates a confimation menu. If the 'confirm' button is pressed, the inner value is set to true.
    If the 'cancel' button is pressed, the inner value is set to false."""

    def __init__(self):
        super().__init__()
        self.value = None

    @discord.ui.button(label="Confirm", style=discord.ButtonStyle.green)
    async def confirm(
        self, button: discord.ui.Button, interaction: discord.Interaction
    ):
        await interaction.response.send_message(
            "The wager has been placed.", ephemeral=True
        )
        self.value = True
        self.stop()

    @discord.ui.button(label="Cancel", style=discord.ButtonStyle.grey)
    async def cancel(
        self, button: discord.ui.Button, interaction: discord.Interaction
    ):
        await interaction.response.send_message(
            "The wager has been cancelled.", ephemeral=True
        )
        self.value = False
        self.stop()

class Wager(commands.Cog):
    
    def __init__(self, bot):
        self.bot = bot

    @discord.slash_command(guild_ids=[958450378083561472,888919487255031848])
    async def wager(
        self,
        ctx: discord.ApplicationContext,
        sport: Option(
            str, 
            "Pick a league!", 
            autocomplete=discord.utils.basic_autocomplete(get_sports)
        ),
        league: Option(
            str,
            "Pick a league!",
            autocomplete=discord.utils.basic_autocomplete(get_leagues),
        ),
        match: Option(
            str, 
            "Pick a match!", 
            autocomplete=discord.utils.basic_autocomplete(get_match)
        ),
        bet: Option(
            str, 
            "Pick a bet!", 
            autocomplete=discord.utils.basic_autocomplete(get_bets)
        ),
        bet_amount: Option(
            int,
            "Pick an amount!",
            min_value=0,
        ),
        ):
            view = Confirm()

            user = [str(ctx.author.id), str(ctx.author.name)]
            user_amount = db.user_lookup(user)[0][-1]

            if bet_amount > user_amount:
                await ctx.respond(f"You only have {user_amount} points", ephemeral=True)

            payout = _payout(bet, bet_amount)

            gametime = _gametime(match)

            match = _match(match)

            teams = _teams(match)

            team_choice = _team_choice(bet)

            # response embed
            info_embed = discord.Embed(
                title=match, color=0x00FF00
            )
            info_embed.set_author(
                name=ctx.author.display_name, icon_url=ctx.author.display_avatar
            )
            info_embed.add_field(
                name="Game Time", value=f'{gametime} (UTC)', inline=False
            )
            info_embed.add_field(
                name="Your Team", value=team_choice, inline=False
            )
            info_embed.add_field(
                name="Your Bet", value=bet_amount, inline=True
            )
            info_embed.add_field(
                name="Payout", value=payout, inline=True
            )
            info_embed.add_field(
                name="_", value='View this project on [GitHub](https://github.com/JonathanRJoyner/Discord_Wagering_Bot).', inline=False
            )

            # responding to the confirmation
            await ctx.send_response("Confirm your wager:", view=view, embed=info_embed)

            await view.wait()

            if view.value is None:
                pass

            elif view.value:
                data = (
                    user[0],
                    league,
                    gametime[0:10],
                    teams[0],
                    teams[1],
                    team_choice,
                    bet_amount,
                    payout,
                    None,
                    None,
                )
                db.user_bet(data)

            else:
                pass

def setup(bot):
    bot.add_cog(Wager(bot))