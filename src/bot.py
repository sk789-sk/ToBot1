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


@client.command()
async def join(ctx, t_id: int): #enter a tournament
    #1. enter a tournament given a tournament id.
    #2. If user already entered return feedback
    #3. If tournament has started do not enter and feedback
    #4. if failure inform

    data = {
        'tournament_id' : t_id,
        'username': str(ctx.author),
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
async def drop(ctx, t_id:int): #drop from a tournament information
    #if tournament is underway change player status to dropped
    #if tournament has not started remove them from the entrants 
    #delete an entrant from a tournament
    #return a confirmation that the delete occured

    data = {
        'tournament_id' : t_id,
        'discord_id' : int(ctx.author.id)
    }

    headers = {'Content-Type': 'application/json'}
    r = requests.post(f'http://127.0.0.1:5556/Drop/{t_id}', json=data)

    if r.ok:
        response = f'{ctx.author} dropped sucessfully'
    else:
        if r.status_code == 403:
            response = f'Entrants can no longer be modified'
        else:
            response = f'Error, please try again or check if registered'
    
    await ctx.send(response)


@client.command()
async def message(ctx):
    await ctx.author.send('hello')

@client.command()
async def start(ctx, t_id:int):
    #start a tournament
    #Send a reqeust to the server to start the tournament
    #Server will then send back a list of matches
    #Bot will then message the people in the matches that Tournament is underway and that your opponent is username. 

    r = requests.get(f'http://127.0.0.1:5556/start/{t_id}')

    #Ok we get back a list of tournaments
    data = r.json()

    message = "Pairings for the tournament: \n"

    for match in data: 
        # print(match)
        P1 = match['player_1']['discord_id']
        P2 = match['player_2']['discord_id']


        user_1 = await client.fetch_user(P1)
        user_2 = await client.fetch_user(P2) #returns a class discord.User
        
        m1 = f'Your opponent is {user_2.name}'
        m2 = f'Your opponent is {user_1.name}'

        
        await user_1.send(m1)
        await user_2.send(m2)

        await ctx.send(f"{user_1.mention} vs. {user_2.mention}")

        message += f'\n {user_1.mention} vs. {user_2.mention}'

        print(message)

    await ctx.send('Tournament Started, Pairings Generated')
  
    await ctx.send(message)




@client.command()
async def entrants(ctx): #view tournament information
    r = requests.get('http://127.0.0.1:5556/returnEntrants/1')
    
    await ctx.send(r.text)


@client.command()
async def info(ctx, id:int):
    #request the tournament info from the API
    #return the Basic info, entrant count etc
    pass




    


client.run(os.getenv('Disc_Token'))

