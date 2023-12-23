from typing import Optional
from table2ascii import table2ascii
import discord

def create_table(data,header= ['Rank', 'Player', 'Points', 'Tiebreak1','Tiebreak2'],tiebreaker_metrics=['SOS','SOSOS']):
    body = []
    for idx, entrant in enumerate(data):
        body.append([idx+1,entrant['username'],entrant['point_total'],entrant[tiebreaker_metrics[0]],entrant[tiebreaker_metrics[1]]])
    message = table2ascii(header=header, body= body)   
    return message

#Create function that turns match data into discord message

#class for the dropdown menu
#class for the ui.view component

#So when you go to join or etc we create a list of tournaments that have already been created. 

def check_interaction(interaction,ctx):
    return interaction.message.id == ctx.message.id and interaction.user.id == ctx.author.id

def check_message(ctx, message):
    return message.author == ctx.author and ctx.channel==message.channel





