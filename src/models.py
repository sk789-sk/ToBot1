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
    discord_id = db.Column(db.BigInteger)

    def __repr__(self):
        return f'User is ${self.username}'


class Tournament(db.Model, SerializerMixin):
    __tablename__ = 'Tournaments'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String)
    game = db.Column(db.String)
    format = db.Column(db.String) #This is to indicate tournamnet format, DE, Swiss, ladder etc
    created_at = db.Column(db.DateTime(timezone=True), default= db.func.now())
    status = db.Column(db.String) #Not yet started, in progress, completed
    current_round = db.Column(db.Integer, default = 0)
    creator = db.Column(db.BigInteger) 

    #ForeignKeys
    

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
    player_1_id = db.Column(db.Integer, db.ForeignKey('Entrants.id'))
    player_2_id = db.Column(db.Integer, db.ForeignKey('Entrants.id'))

    #relationships

    player_1 = db.relationship('Entrant', foreign_keys = [player_1_id],) #back_populates='matches_as_P1',
    player_2 = db.relationship('Entrant', foreign_keys = [player_2_id],) #back_populates='matches_as_P2',



    #validations
    #serialization rules

    #repr


class Entrant(db.Model, SerializerMixin):
    __tablename__ = 'Entrants'
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String)
    discord_id = db.Column(db.BigInteger)
    point_total = db.Column(db.Integer)
    opponents = db.Column(db.ARRAY((db.Integer)))
    dropped = db.Column(db.Boolean, default=False)
    pair_up_down = db.Column(db.Boolean, default = 0)
    bye = db.Column(db.Boolean, default=False)
    SOS = db.Column(db.Float)

    #CHoosing to have an opponents array stored in the database. The logic here is that while it denormalizes the database since we can get the information from the Matches, doing this prevents use from having to query the matches tables before created new matches, extracting the information into a dictionary and then before creating any edge on the graph we check the dictionary value to see what the weight should be. 
    
    # As long as i update players opponents columns and matches column in 1 transaction this should be fine. Basically turn that into 1 atomized action. 
    # This also means that if I delete a match for any reason I would need to update the arrays as well. 


    #Foreign Keys
    tournament_id = db.Column(db.Integer, db.ForeignKey('Tournaments.id'))

    #relationships

    # matches_as_P1 = db.relationship('Match', backref = 'player_1', foreign_keys='Match.player_1_id',)
    # matches_as_P2 = db.relationship('Match', backref = 'player_2', foreign_keys='Match.player_2_id',)

    @validates('point_total')
    def validate_points(self,key,point_total):
        if point_total >= 0:
            return point_total
        raise ValueError("Point total must be greater than 0")

