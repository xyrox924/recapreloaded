import sqlite3

from pathlib import Path
from datetime import datetime

from database.models import *

class Database:
    def __init__(self, db_path: str):
        self.db_path = db_path

        # create db
        conn = None
        try:
            # i'm just closing and opening the connections for everything i do, maybe this isn't right and i should keep one always open
            conn = sqlite3.connect(self.db_path)
            cur = conn.cursor()

            cur.execute("""
                CREATE TABLE IF NOT EXISTS games (
                    id INTEGER PRIMARY KEY,
                    name TEXT NOT NULL UNIQUE,
                    developer TEXT,
                    notes TEXT,
                    banner_file TEXT
                )
            """)
            cur.execute("""
                CREATE TABLE IF NOT EXISTS executables (
                    id INTEGER PRIMARY KEY,
                    game_id INTEGER NOT NULL,
                    exe_name TEXT NOT NULL,
                    full_path TEXT UNIQUE,
                    FOREIGN KEY (game_id) REFERENCES games(id)
                )
            """)
            cur.execute("""
                CREATE TABLE IF NOT EXISTS sessions (
                    id INTEGER PRIMARY KEY,
                    game_id INTEGER NOT NULL,
                    start_time DATETIME NOT NULL,
                    end_time DATETIME NOT NULL,
                    FOREIGN KEY (game_id) REFERENCES games(id)
                )
            """)

            conn.commit()
        except sqlite3.Error:
            print("Something went wrong while creating the database")
            raise # just crash everything because idk at this point
        finally:
            if conn:
                print(f"Database at {self.db_path}")
                conn.close() # type: ignore

    def insert_game(self, game: Game) -> Game:
        conn = None
        try:
            conn = sqlite3.connect(self.db_path)
            cur = conn.cursor()
            
            cur.execute("INSERT INTO games (name, developer, notes, banner_file) VALUES (?, ?, ?, ?)", 
                    (game.name, game.developer, game.notes, game.banner_path))
            game.id = cur.lastrowid
            
            for exe in game.executables:
                cur.execute("INSERT INTO executables (game_id, exe_name, full_path) VALUES (?, ?, ?)",
                        (game.id, Path(exe.path).name, exe.path))
                exe.game_id = game.id
                exe.id = cur.lastrowid
            
            conn.commit()
            return game
        except sqlite3.Error as e:
            print(f"Error inserting game: {e}")
            raise
        finally:
            if conn:
                conn.close() # type: ignore

    def update_game(self, game: Game) -> Game:
        conn = None
        try:
            conn = sqlite3.connect(self.db_path)
            cur = conn.cursor()
            
            cur.execute("""UPDATE games 
                        SET name = ?, developer = ?, notes = ?, banner_file = ?
                        WHERE id = ?""", 
                        (game.name, game.developer, game.notes, game.banner_path, game.id))
            
            # delete existing executables for this game
            cur.execute("DELETE FROM executables WHERE game_id = ?", (game.id,))
            
            # insert the new/updated executables
            for exe in game.executables:
                cur.execute("""INSERT INTO executables (game_id, exe_name, full_path) 
                            VALUES (?, ?, ?)""",
                            (game.id, Path(exe.path).name, exe.path))
                exe.game_id = game.id
                exe.id = cur.lastrowid
            
            conn.commit()
            return game
        except sqlite3.Error as e:
            print(f"error updating game: {e}")
            raise
        finally:
            if conn:
                conn.close()  # type: ignore

    def get_game(self, game_id: int):
        conn = None
        try:
            conn = sqlite3.connect(self.db_path)
            cur = conn.cursor()

            cur.execute("SELECT name, developer, notes, banner_file FROM games WHERE id = ?", (game_id,))

            game_row = cur.fetchone()
        
            if not game_row:
                return None
            
            return Game(
                id=game_id,
                name=game_row[0],
                developer=game_row[1],
                notes=game_row[2],
                executables=[], # uhh hmm we don't need this in this method so empty list
                banner_path=game_row[3]
            )

        except sqlite3.Error:
            print(f"Something went wrong while getting a game. ID is {game_id}")
            return None
        finally:
            if conn:
                conn.close() # type: ignore

    def get_game_full(self, game_id: int):
        conn = None
        try:
            conn = sqlite3.connect(self.db_path)
            cur = conn.cursor()

            cur.execute("SELECT name, developer, notes, banner_file FROM games WHERE id = ?", (game_id,))

            game_row = cur.fetchone()
            if not game_row:
                return None
            
            # get executables for said game
            cur.execute(
                "SELECT full_path FROM executables WHERE game_id = ?",
                (game_id,)
            )

            exe_rows = cur.fetchall()
            if not exe_rows:
                print(f"Game {game_row[0]} found but no exes.")
                return Game(
                    id=game_id,
                    name=game_row[0],
                    developer=game_row[1],
                    notes=game_row[2],
                    executables=[], # well there weren't any exes sooo
                    banner_path=game_row[3]
                )

            executable_list = []
            for exe in exe_rows:
                executable_list.append(exe[0])
            
            return Game(
                id=game_id,
                name=game_row[0],
                developer=game_row[1],
                notes=game_row[2],
                executables=executable_list,
                banner_path=game_row[3]
            )

        except sqlite3.Error:
            print(f"Something went wrong while getting a game. ID is {game_id}")
            return None
        finally:
            if conn:
                conn.close() # type: ignore

    def get_all_games(self):
        conn = None
        try:
            conn = sqlite3.connect(self.db_path)
            cur = conn.cursor()

            cur.execute("SELECT id, name FROM games")

            game_row = cur.fetchall()
            if not game_row:
                return None
            
            return game_row

        except sqlite3.Error:
            print(f"Something went wrong while getting all games.")
            return None
        finally:
            if conn:
                conn.close() # type: ignore

    def get_game_playtime(self, game_id) -> int:
        conn = None
        try:
            conn = sqlite3.connect(self.db_path)
            cur = conn.cursor()

            cur.execute("""
                SELECT SUM((julianday(s.end_time) - julianday(s.start_time)) * 86400)
                FROM sessions s
                WHERE s.game_id = ?
            """, (game_id,))

            total_seconds = cur.fetchone()[0] or 0 # maybe or 0 i don't need it idk
            return int(total_seconds)

        except sqlite3.Error:
            print(f"Something went wrong while getting all games.")
            return 0
        finally:
            if conn:
                conn.close() # type: ignore

    def get_game_first_time(self, game_id):
        conn = None
        try:
            conn = sqlite3.connect(self.db_path)
            cur = conn.cursor()

            cur.execute("""
                SELECT MIN(s.end_time)
                FROM sessions s
                WHERE s.game_id = ?
                    AND s.end_time IS NOT NULL
            """, (game_id,))

            first_time = cur.fetchone()[0]
            if first_time is None:
                return "never"
            return datetime.fromisoformat(first_time).strftime("%B %d, %Y")

        except sqlite3.Error:
            print(f"Something went wrong while getting all games.")
            return None
        finally:
            if conn:
                conn.close() # type: ignore

    def get_game_last_time(self, game_id):
        conn = None
        try:
            conn = sqlite3.connect(self.db_path)
            cur = conn.cursor()

            cur.execute("""
                SELECT MAX(s.end_time)
                FROM sessions s
                WHERE s.game_id = ?
                    AND s.end_time IS NOT NULL
            """, (game_id,))

            last_time = cur.fetchone()[0]
            if last_time is None:
                return "never"
            return datetime.fromisoformat(last_time).strftime("%B %d, %Y")

        except sqlite3.Error:
            print(f"Something went wrong while getting all games.")
            return None
        finally:
            if conn:
                conn.close() # type: ignore

    def insert_session(self, game_id, start_time, end_time):
        conn = None
        try:
            conn = sqlite3.connect(self.db_path)
            cur = conn.cursor()

            cur.execute("INSERT INTO sessions (game_id, start_time, end_time) VALUES (?, ?, ?)",
                        (game_id, start_time, end_time))
            conn.commit() # i always forget this somehow
        except sqlite3.Error:
            print(f"Something went wrong while writing session.")
            return None
        finally:
            if conn:
                conn.close() # type: ignore

    def get_known_executables(self):
        conn = None
        try:
            conn = sqlite3.connect(self.db_path)
            cur = conn.cursor()
            
            cur.execute("SELECT exe_name, game_id FROM executables")
            rows = cur.fetchall()
            
            # return as dict: exe_name -> game_id
            return {row[0].lower(): row[1] for row in rows}
        
        except sqlite3.Error as e:
            print(f"Error getting executables: {e}")
            return {}
        finally:
            if conn:
                conn.close()