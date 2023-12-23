from typing import Any, List, Optional
import discord
from discord.components import SelectOption
from discord.interactions import Interaction
from discord.utils import MISSING

class dropdown(discord.ui.Select):
    def __init__(self,options=[discord.SelectOption(label='placeholder')]):
        super().__init__(placeholder='Select Tournament from Dropdown ', options=options, min_values=1, max_values=1)

    async def callback(self, interaction):
        return self.values


class dropdownView(discord.ui.View):
    def __init__(self, options=None, timeout=60.0):
        super().__init__(timeout=timeout)
        self.add_item(dropdown(options=options))
    





