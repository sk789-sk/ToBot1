from sqlalchemy_serializer import SerializerMixin
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import MetaData, event
from sqlalchemy.orm import validates
from sqlalchemy.ext.associationproxy import association_proxy
from sqlalchemy.ext.hybrid import hybrid_property
from sqlalchemy.ext.mutable import MutableList

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
    total_round = db.Column(db.Integer)
    creator = db.Column(db.BigInteger) 
    guild_id = db.Column(db.BigInteger)

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

    player_1 = db.relationship('Entrant', foreign_keys = [player_1_id], backref = 'matches_as_P1') #back_populates='matches_as_P1',
    player_2 = db.relationship('Entrant', foreign_keys = [player_2_id], backref = 'matches_as_P2') #back_populates='matches_as_P2',

    #This is prob what i want should backref

    # player_1 = db.relationship('Entrant', backref = 'matches_as_P1',) #back_populates='matches_as_P1',
    # player_2 = db.relationship('Entrant', backref = 'matches_as_P2',) #back_populates='matches_as_P2',

    #Single Elimination Bracket parameters

    winner_next_match_id = db.Column(db.Integer, db.ForeignKey('Matches.id')) #This is the parent node for single elim brackets
    # loser_next_match_id = db.Column(db.Integer, db.ForeignKey('Matches.id'))
    parent = db.relationship('Match', remote_side=[id], backref='children')

    #validations
    #serialization rules

    serialize_rules = ('-player_1.matches_as_P1','-player_1.matches_as_P2','-player_2.matches_as_P1','-player_2.matches_as_P2','-parent.children','-children.parent','-children.children','-parent.parent')  
    #'-parent.children','children.parent' will almost certainly need these as rules as well. 
    #children.children and parent.parent shows the path to the root node for each entrant which is probably unnecessary a.


    #repr


class Entrant(db.Model, SerializerMixin):
    __tablename__ = 'Entrants'
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String)
    discord_id = db.Column(db.BigInteger)
    point_total = db.Column(db.Integer)
    opponents = db.Column(MutableList.as_mutable(db.ARRAY((db.Integer))))
    dropped = db.Column(db.Boolean, default=False) #I could store this as when 
    pair_up_down = db.Column(db.Boolean, default = 0)
    bye = db.Column(db.Integer, default=0)   #number of byes the player has received
    SOS = db.Column(db.Float, default = 0)
    SOSOS = db.Column(db.Float, default = 0)
    Bucholz = db.Column(db.Integer)
    medianBucholz = db.Column(db.Integer)
    BucholzCut1 = db.Column(db.Integer)

    #CHoosing to have an opponents array stored in the database. The logic here is that while it denormalizes the database since we can get the information from the Matches, doing this prevents use from having to query the matches tables before created new matches, extracting the information into a dictionary and then before creating any edge on the graph we check the dictionary value to see what the weight should be. 
    
    # As long as i update players opponents columns and matches column in 1 transaction this should be fine. Basically turn that into 1 atomized action. 
    # This also means that if I delete a match for any reason I would need to update the arrays as well. 


    #Foreign Keys
    tournament_id = db.Column(db.Integer, db.ForeignKey('Tournaments.id'))

    #relationships

    @validates('point_total')
    def validate_points(self,key,point_total):
        if point_total >= 0:
            return point_total
        raise ValueError("Point total must be greater than 0")

    #Entrant.matches_as_P1
    serialize_rules = ('-Match.player_1','-Match.player_2')