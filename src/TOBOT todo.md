TOBOT todo

-I think we lost the env file, it was on the old PC
-Recreate the DB from scratch, prob a good opportunity to check models and reset
-I think that this branch doesnt have the dbl elim information, I am pretty sure double elim logic was already created. For now lets focus on swiss 





For Swiss, we want to mimic KTS as much as possible so we will use SOS and SOSOS for tiebreakers. 


To test swiss we need just username, discord_id


1. A tournament is created, which generates a tournament in the database.
2. A user can enter a tournament, which is done by using the tournament id
3. A user can drop from a tournament which also uses the tournament id. A User can drop before a tournament has started, in which case the entry is deleted. A user can drop while a tournament is underway and if so they arent deleted by instead we set a flag that means that they have dropped. 
4. The tournament is set to underway and we need to first figure out what type of tournament it is. Depending on which we call the appropriate function to create the tournament bracket/map. This will generate the initial matches as well. 
5. Match results need to be updated. The update match function, should just take in an object of parameter and value
