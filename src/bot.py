import discord 
from discord.ext import commands
import random as rd
import os
from dotenv import load_dotenv

# import BracketGen

#Create Tournament 
#Send Pairings to entrants
#send results to API

load_dotenv()

intents = discord.Intents.default()
intents.message_content = True 

# client = discord.Client(intents=intents)


#So far this is just our connection to discord and we have set the message contents to true which allows us to use the events with messages. 

#Theres 2 ways to connect to discord here. client =  discord.Client is the websocket and has more flexibility.
# bot= commands.Bot(prefix,intents) then using @bot.command/event is an extension of the Client class, seems like it just has some common use cases built in and is just easier to use then. 

client = commands.Bot(command_prefix='$',intents=intents)



@client.event
async def on_ready():
    print(f'Logged in with {client.user}')
    #on_ready() is an event thats is within the client library and is called when the bot has logged in. 

@client.event
async def on_message(message):
    # print(message)
    # print(type(message.author))

    if message.author == client.user:
        return #do nothing on bot message to avoid recursion 
    
    if message.content.startswith('$h'):
        await message.channel.send('Hello!')

    #having the event for message and the command seems to conflict. seems like it prioritizes the message and then never gets to the command.
    # https://discordpy.readthedocs.io/en/latest/faq.html#why-does-on-message-make-my-commands-stop-working

    await client.process_commands(message)


    #my guess is that we send a message that has $h we will return hello work probable with $hhh?

    #Ok so this where the onmessage bit would occur. We define the messages and then what the
    #/enter, /createTournament, /createPairings, /Finalize etc., /endTourney  

 

@client.command()
async def ping(ctx):
    await ctx.send("pong")

@client.command()
async def RPS(ctx):
    val = rd.choice(['rock', 'paper', 'scissors'])    
    await ctx.send(val)






client.run(os.getenv('Disc_Token'))

# client.run('MTE3ODgxNTY3OTUwODUxNjkxNg.GlJC2j.xq6-XqZMrerCgosS-4Pemo0lzUHiPhW30TL0sY')