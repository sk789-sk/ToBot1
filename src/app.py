from models import *
from flask import Flask, make_response, jsonify, request, session
import os

# Local imports

from config import app, db
from models import Match , Entrant , Tournament



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

@app.route('/JoinTournament/<int:t_id>', methods = ['POST', 'DELETE'])
def alter_Tournament_Entrant(t_id):

    data = request.get_json()

    if request.method == 'POST':
        print('post')
    else:
        print('delete')

    return 'success'

@app.route('/Generate_Matches')
def generate_matches():
    return 'creating next round for tourney id: '

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

    app.run(port=5555, debug=True)
