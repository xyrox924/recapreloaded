from database.database import Database



if __name__ == "__main__":
    db = Database("recap.db")
    db.insert_game("Mario2", "Nintendo", "Mario's Fuck World 2 nintendo switch rom", [])

    game = db.get_game_full(7)
    print(game)
