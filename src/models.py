from sqlalchemy_serializer import SerializerMixin
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import MetaData, event
from sqlalchemy.orm import validates
from sqlalchemy.ext.associationproxy import association_proxy
from sqlalchemy.ext.hybrid import hybrid_property

from config import db

class User(db.Model, SerializerMixin):
    __tablename__ = 'Users'

    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String)

    def __repr__(self):
        return f'User is ${self.username}'


class Tournament(db.Model, SerializerMixin):
    __tablename__ = 'Tournaments'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String)
    game = db.Column(db.String)
    format = db.Column(db.Integer) #This is to indicate tournamnet format, DE, Swiss, ladder etc
    created_at = db.Column(db.DateTime(timezone=True), default= db.func.now())
    status = db.Column(db.String) #Not yet started, in progress, completed

    #ForeignKeys
    creator = db.Column(db.Integer, db.ForeignKey('Users.id'))

    #Relationships
    #Validations
    @validates('name')
    def validate_name(self,key,name):
        if len(name)<=10:
            return name
        raise ValueError
    #Serialization Rules
    #repr 

class Match(db.Model, SerializerMixin):
    __tablename__ = 'Matches'
    id = db.Column(db.Integer, primary_key=True)
    result = db.Column(db.Integer) #1 = P1 win, 0 = tie, 2 = P2 Win
    round = db.Column(db.Integer)

    #foreign Keys
    tournament = db.Column(db.Integer, db.ForeignKey('Tournaments.id'))
    player_1 = db.Column(db.Integer, db.ForeignKey('Users.id'))
    player_2 = db.Column(db.Integer, db.ForeignKey('Users.id'))

    #relationships
    #validations
    #serialization rules

    #repr


class Entrant(db.Model, SerializerMixin):
    __tablename__ = 'Entrants'
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String)
    point_total = db.Column(db.Integer, default = 0)
    opponents = db.Column((db.String), default="")
    dropped = db.Column(db.Boolean, default=False)
    pair_up_down = db.Column(db.Boolean, default = 0)
    bye = db.Column(db.Boolean, default='False')

    #Foreign Keys
    tournament_id = db.Column(db.Integer, db.ForeignKey('Tournaments.id'))

