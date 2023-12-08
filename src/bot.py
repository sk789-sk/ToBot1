import discord 
from discord.ext import commands
import random as rd
import requests 
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

client = commands.Bot(command_prefix='$',intents=intents ,case_insensitive=True)



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
    #return an rock-paper-scissors value for 

    val = rd.choice(['rock', 'paper', 'scissors'])    
    await ctx.send(val)


@client.command()
async def copy(ctx, arg):
    await ctx.send(arg)


@client.command()
async def join(ctx, t_id: int): #enter a tournament
    #enter a tournament given a tournament id.
    #if entered return user is already entered
    #if success enter sucess
    #if failure inform
    #if tournament has started do not allow them to enter

    data = {
        'point_total' : 0,
        'opponents' : "",
        'tournament_id' : t_id,
        'username': str(ctx.author),
        'dropped' : None,
        'pair_up_down' : None,
        'bye' : None,
        'SOS' : None,
        'discord_id': int(ctx.author.id)
    }

    headers = {'Content-Type': 'application/json'}
    r = requests.post(f'http://127.0.0.1:5556/JoinTournament/{t_id}', json=data)

    if r.ok:
        response = f'{ctx.author} registered successfully'
    else:
        if r.status_code == 403: 
            response = f'Tournament is underway, unable to join'
        elif r.status_code == 409:
            response = f'{ctx.author} is already registered'
        else:
            response =f'Error, please try again'

    await ctx.send(response)

@client.command()
async def entrants(ctx): #view tournament information
    r = requests.get('http://127.0.0.1:5556/returnEntrants/1')
    await ctx.send(r.text)
    pass

@client.command()
async def info(ctx, id:int):
    #request the tournament info from the API
    #return the Basic info, entrant count etc
    pass

@client.command()
async def drop(ctx): #drop from a tournament information
    #delete an entrant from a tournament
    #return a confirmation that the delete occured
    pass

@client.command()
async def create(ctx, name): #create tournament information
    #Create a Tournament, add in additional parameters, figure out how to make it as a dropdown step by step.

    data = {
        'name': name,
        'game': 'YGO',
        'format': 'Swiss',
        'creator': int(ctx.author.id)
    }

    headers = {'Content-Type': 'application/json'}
    r = requests.post('http://127.0.0.1:5556/Create', json=data)
    
    print(r.status_code)

    if r.ok:
        response = f'Tournament Created Successfully'
    else:
        response = f'Failed to create'
    
    await ctx.send(response)

    


client.run(os.getenv('Disc_Token'))

