INSERT INTO Users (username) VALUES ('sk789');
INSERT INTO Users (username) VALUES ('test');


INSERT INTO Tournaments (name,game,format,creator) VALUES ('Test1','YGO','Swiss',1);


INSERT INTO Entrants (username, point_total, tournament_id,opponents) VALUES ('WZ', 0, 1,"");
INSERT INTO Entrants (username, point_total, tournament_id,opponents) VALUES ('Firdaus', 0, 1,"");
INSERT INTO Entrants (username, point_total, tournament_id,opponents) VALUES ('shamu', 0, 1,"");
INSERT INTO Entrants (username, point_total, tournament_id,opponents) VALUES ('trapmoneys', 0, 1,"");
INSERT INTO Entrants (username, point_total, tournament_id,opponents) VALUES ('inzy', 0, 1,"");
INSERT INTO Entrants (username, point_total, tournament_id,opponents) VALUES ('bendystraw', 0, 1,"");
INSERT INTO Entrants (username, point_total, tournament_id,opponents) VALUES ('loofbone', 0, 1,"");
INSERT INTO Entrants (username, point_total, tournament_id,opponents) VALUES ('PinappleBun', 0, 1,"");


INSERT INTO Matches (round, tournament, player_1,player_2) VALUES (1,1,1,2);
INSERT INTO Matches (round, tournament, player_1,player_2) VALUES (1,1,3,4);
INSERT INTO Matches (round, tournament, player_1,player_2) VALUES (1,1,5,6);
INSERT INTO Matches (round, tournament, player_1,player_2) VALUES (1,1,7,8);

INSERT INTO Tournaments (name,game,format,creator) VALUES ('Test2','YGO','Swiss',1);

-- INSERT INTO Entrants (username, point_total, tournament_id, opponents) VALUES ('shamu', 0, 2, '[1,2,3]');

DELETE From Matches WHERE id >= 5;

DELETE FROM Entrants;

DELETE FROM Matches;

INSERT INTO Entrants (username, point_total, tournament_id,opponents,discord_id) VALUES ('WZ', 0, 1,"",1);
INSERT INTO Entrants (username, point_total, tournament_id,opponents,discord_id) VALUES ('Firdaus', 0, 1,"",2);
INSERT INTO Entrants (username, point_total, tournament_id,opponents,discord_id) VALUES ('shamu', 0, 1,"",3);
INSERT INTO Entrants (username, point_total, tournament_id,opponents,discord_id) VALUES ('trapmoneys', 0, 1,"",4);
INSERT INTO Entrants (username, point_total, tournament_id,opponents,discord_id) VALUES ('inzy', 0, 1,"",5);

DELETE FROM Matches where tournament =2;

DELETE FROM Matches where tournament =2 AND result ISNULL;

UPDATE Tournaments
SET status = 'Initialized' 
WHERE id=2;

UPDATE Entrants 
SET dropped = false
WHERE id <=5;

UPDATE Tournaments
SET current_round = 1
where id=2;