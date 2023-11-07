from models import *
from flask import Flask, make_response, jsonify, request, session
import os

# Local imports

from config import app, db
from models import Match , Entrant , Tournament



@app.route('/')
def home():
    return 'testing base'


@app.route('/Create')
def create():
    return 'creating new Tourney'

@app.route('/Generate_Matches')
def generate_matches():
    return 'creating next round for tourney id: '

@app.route('/returnEntrants/<int:t_id>')
def returnEntrants(t_id):
    print(t_id)
    return 'all entrants'

if __name__ == '__main__':

    app.run(port=5555, debug=True)
