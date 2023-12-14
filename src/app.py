from models import *
from flask import Flask, make_response, jsonify, request, session
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import aliased
from sqlalchemy import or_
import os

# Local imports

from config import app, db
from models import Match , Entrant , Tournament
from BracketGen import startTournament, BiPartiteMatchMaking



@app.route('/')
def home():
    return 'testing base'


@app.route('/Create', methods = ['POST'])
def create():
    
    data = request.get_json()
    print(data)
    
    try:
        #reqbin test was good
        new_tournament = Tournament(
            name = data['name'],
            game = data['game'],
            format = data['format'],
            creator = data['creator'],
            status = 'Initialized'
        )
        
        db.session.add(new_tournament)
        db.session.commit()

        response = make_response(new_tournament.to_dict(),200)
    
    except ValueError:
        response = make_response({"Errors":["Failed to create"]},400)

    return response

@app.route('/JoinTournament/<int:t_id>', methods = ['POST'])
def Join_Tournament(t_id):

    data = request.get_json()
    tournament_status = Tournament.query.filter(Tournament.id==t_id).first().status
    entered_status = Entrant.query.filter(Entrant.tournament_id==t_id,Entrant.discord_id==data['discord_id']).first()

    if request.method == 'POST':
        
        if tournament_status == 'Underway':
            response = make_response({},403)
            print('Tournament underway, can no longer enter')

        elif entered_status:
            response = make_response({}, 409)
            print('User already entered')

        else:
             
            try:
                new_Entrant = Entrant(
                    tournament_id = t_id,
                    point_total = 0,
                    opponents = "",
                    pair_up_down = None,
                    bye = None,
                    SOS = None,
                    dropped = None,
                    username = data['username'],
                    discord_id = data['discord_id']
                )

                db.session.add(new_Entrant)
                db.session.commit()

                response = make_response(jsonify(new_Entrant.to_dict()),200)

            except SQLAlchemyError as e:
                    db.session.rollback()
                    print(f'Error {e} occured')
                    response = make_response({'error': 'Failed to create entrant'}, 500)
                    
            except ValueError as ve:
                    response = make_response({},400)
                    print(f'Error: {ve}')
    
    else:
            #DELETE
            print('delete')

    return response

@app.route('/Drop/<int:t_id>', methods = ['POST'])
def drop_entrant(t_id):
     #1. If the tournament is underway change status to dropped
     #2. If the tournament has not yet begun delete them
     #3. If tournament is in other status, finalized etc do not allow edits
     #3. Info given is the users discord_id
     

    data = request.get_json()
    tournament_status = Tournament.query.filter(Tournament.id==t_id).first().status
    entrant = Entrant.query.filter(Entrant.tournament_id==t_id,Entrant.discord_id==data['discord_id']).first_or_404()
    
    if tournament_status == 'Underway':
        entrant.dropped = True
        try:            
            db.session.add(entrant)
            db.session.commit()
            response = make_response({},202)
        except SQLAlchemyError as e:
            db.session.rollback()
            print(f'Error {e} occured')
            response = make_response({'error': 'Failed to drop'}, 500)

    elif tournament_status == 'Initialized':
        try:
            db.session.delete(entrant)
            db.session.commit()
            response = make_response({},204)
        except SQLAlchemyError as e:
            db.session.rollback()
            print(f'Error {e} occured')
            response = make_response({'error': 'Failed to delete'}, 500)
    else:
        response = make_response({'Error':'Cannot Modify'},403) #cannot modify resource anymore
 

    return response


@app.route('/start/<int:t_id>')
def start_tournament(t_id):

    t = Tournament.query.filter(Tournament.id==t_id).first()

    if t.status == 'Initialized':

        t.status = 'Underway'

        try:
            matches = startTournament(t_id)   
            
            db.session.add(t)
            db.session.commit()
              
            #I think these matches are not bound to session and is causing error
            #i think it was needing db access to turn the matches into something that is jsonifyiable and there was a desync between the sessions. I have the bracket gen function returning them in jsonifyable format now.

            response = make_response(jsonify(matches),200)

        except SQLAlchemyError as e:
            print('we here?')
            db.session.rollback()
            print(f'Error {e} has occured')
            response = make_response({'error': 'Failed to start'}, 500)
    else:
        response = make_response({},403) #tournament is underway or completed
    
    return response

@app.route('/UpdateMatch' , methods = ['PATCH'])
def updateMatch():
    
    #slower option would be to query the entrant_id from the Entrant list
    #feel like there should be a way to do this in 1 query utilizing outerjoin and relationships that i need to go over.


    data = request.get_json() #I am given the tournament id and the discord_id here

    entrant_1_alias = aliased(Entrant)
    entrant_2_alias = aliased(Entrant)

    t_round = Tournament.query.filter(Tournament.id == data['tournament_id']).first().current_round

    match = db.session.query(Match).outerjoin(entrant_1_alias, Match.player_1_id==entrant_1_alias.id ).outerjoin(entrant_2_alias, Match.player_2_id==entrant_2_alias.id).filter(or_(entrant_1_alias.discord_id==data['discord_id'],entrant_2_alias.discord_id==data['discord_id']),Match.round==t_round).first()


    if match:
        #we have a match now lets update the match results. We pass the ID of the 
        if match.result == None:

            entrant_1 = Entrant.query.filter(match.player_1_id==Entrant.id).first()
            entrant_2 = Entrant.query.filter(match.player_2_id==Entrant.id).first()

            #this should be a list for when it goes to postgres

            # entrant_2.opponents += f"{entrant_1.id},"
            # entrant_1.opponents += f"{entrant_2.id},"

            print(entrant_2.opponents)
            print(entrant_1.opponents)
            
            #SQL-alchemy does not automatically track changes made to elements within an array. so in place mutations like .append() are not detected. Since its not detected there is no to the commit and no change to the database. 
            #2 options for this, instead of using .append we do a non inplace mutation, such as copying the array and reassigning it a value, in that case we are basically creating a new array and assigning it and it would be detected. The other and better option is to use MutableList extension 

            entrant_2_updated = entrant_2.opponents + [entrant_1.id]
            entrant_1_updated = entrant_1.opponents + [entrant_2.id]

            entrant_2.opponents = entrant_2_updated
            entrant_1.opponents = entrant_1_updated


            print(entrant_2.opponents)
            print(entrant_1.opponents)


            #2 cases player_1 loss or player_2
            if match.player_1.discord_id == data['discord_id']: # player 1 has lost
                match.result = match.player_2_id #update match result
                entrant_2.point_total +=3

            else: #player 2 has lost
                match.result = match.player_1_id
                entrant_1.point_total +=3

            try:
                db.session.add_all([match,entrant_1,entrant_2])
                db.session.commit()
                
                response = make_response({},204)
            except SQLAlchemyError as e:
                db.session.rollback()
                print(f'Error {e} has occured')
                response = make_response({'error': 'Server Error failed to update'},304)
            except ValueError as ve:
                db.session.rollback
                print(f'Error {ve} has occured')
                response = make_response({'Error':'Bad Data'},422)
        else:
            response = make_response({'Error':'Already Reported'},409)
    else:
        response = make_response({'Error': 'Player is not in an active match'},400)

    return response

@app.route('/Generate_Matches/<int:t_id>')
def generate_matches(t_id):
    #. Verify that all matches are completed, if not say we are awaiting matches

    tourney = Tournament.query.filter(Tournament.id == t_id).first()
    round_check = tourney.current_round 

    unfinished_matches = Match.query.filter(Match.tournament==t_id,Match.round==round_check,Match.result==None).all()

    if len(unfinished_matches) !=0:
        #return the matchs that need to be finished
        unfinished_match_list = []
        for match in unfinished_matches:
            unfinished_match_list.append(match.to_dict())

        response = make_response(jsonify(unfinished_match_list),409)

    #. There are no unfinished matches so we run the function to create the next set of matches. the function also updates the tournament state. Need to add error handling for this Bipartite Function

    else:
        matches = BiPartiteMatchMaking(t_id) 
        response = make_response(jsonify(matches),200)
    
    return response

@app.route('/returnEntrants/<int:t_id>')
def returnEntrants(t_id):

    #We get a tournament id, from the tournament ID we look at all entrants in a tournament with that id

    entrants = Entrant.query.filter(Entrant.tournament_id==t_id).all()
    print(entrants)

    entrant_list = []

    for entrant in entrants:
        entrant_list.append(entrant.to_dict())

    response = make_response(jsonify(entrant_list),200)
    return response

@app.route('/returnMatches/<int:t_id>')
def return_all(t_id):
    matches = Match.query.filter(Match.tournament==t_id).all()
    match_list = []
    for match in matches:
        match_list.append(match.to_dict())

    response = make_response(jsonify(match_list),200)
    return response   


if __name__ == '__main__':

    app.run(port=5556, debug=True)
