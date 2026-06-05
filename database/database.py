import sqlite3

from pathlib import Path
from datetime import datetime

from database.models import Executable, Game
from utils import normalize_exe_path

class DatabaseError(Exception):
    pass

class Database:
    def __init__(self, db_path: str):
        self.db_path = db_path

        # create db
        conn = None
        try:
            # i'm just closing and opening the connections for everything i do, maybe this isn't right and i should keep one always open
            conn = sqlite3.connect(self.db_path)
            conn.execute("PRAGMA foreign_keys = ON")
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
        except sqlite3.Error as e:
            print("Something went wrong while creating the database")
            raise DatabaseError("Could not initialize the database.") from e
        finally:
            if conn:
                print(f"Database at {self.db_path}")
                conn.close() # type: ignore

    def _connect(self):
        conn = sqlite3.connect(self.db_path)
        conn.execute("PRAGMA foreign_keys = ON")
        return conn

    def _validate_game(self, game: Game):
        if not game.name.strip():
            raise DatabaseError("Game name is required.")

        seen_paths = set()
        for exe in game.executables:
            normalized_path = normalize_exe_path(exe.path)
            if normalized_path in seen_paths:
                raise DatabaseError("The same executable is listed more than once.")
            seen_paths.add(normalized_path)

    def _validate_executables_available(self, cur, game: Game):
        cur.execute("SELECT game_id, full_path FROM executables")
        existing_paths = {
            normalize_exe_path(full_path): game_id
            for game_id, full_path in cur.fetchall()
            if full_path
        }

        for exe in game.executables:
            existing_game_id = existing_paths.get(normalize_exe_path(exe.path))
            if existing_game_id is not None and existing_game_id != game.id:
                raise DatabaseError("That executable is already assigned to another game.")

    def _raise_integrity_error(self, error: sqlite3.IntegrityError):
        message = str(error).lower()
        if "games.name" in message:
            raise DatabaseError("A game with that name already exists.") from error
        if "executables.full_path" in message:
            raise DatabaseError("That executable is already assigned to another game.") from error
        raise DatabaseError("The database rejected the change.") from error

    def insert_game(self, game: Game) -> Game:
        self._validate_game(game)
        conn = None
        try:
            conn = self._connect()
            cur = conn.cursor()
            self._validate_executables_available(cur, game)
            
            cur.execute("INSERT INTO games (name, developer, notes, banner_file) VALUES (?, ?, ?, ?)", 
                    (game.name, game.developer, game.notes, game.banner_path))
            game.id = cur.lastrowid
            
            for exe in game.executables:
                cur.execute("INSERT INTO executables (game_id, exe_name, full_path) VALUES (?, ?, ?)",
                        (game.id, Path(exe.path).name, normalize_exe_path(exe.path)))
                exe.game_id = game.id
                exe.id = cur.lastrowid
            
            conn.commit()
            return game
        except sqlite3.IntegrityError as e:
            if conn:
                conn.rollback()
            self._raise_integrity_error(e)
        except sqlite3.Error as e:
            if conn:
                conn.rollback()
            print(f"Error inserting game: {e}")
            raise DatabaseError("Could not save the game.") from e
        finally:
            if conn:
                conn.close() # type: ignore

    def update_game(self, game: Game) -> Game:
        self._validate_game(game)
        conn = None
        try:
            conn = self._connect()
            cur = conn.cursor()
            self._validate_executables_available(cur, game)
            
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
                            (game.id, Path(exe.path).name, normalize_exe_path(exe.path)))
                exe.game_id = game.id
                exe.id = cur.lastrowid
            
            conn.commit()
            return game
        except sqlite3.IntegrityError as e:
            if conn:
                conn.rollback()
            self._raise_integrity_error(e)
        except sqlite3.Error as e:
            if conn:
                conn.rollback()
            print(f"error updating game: {e}")
            raise DatabaseError("Could not save the game settings.") from e
        finally:
            if conn:
                conn.close()  # type: ignore

    def get_game(self, game_id: int):
        conn = None
        try:
            conn = self._connect()
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

        except sqlite3.Error as e:
            print(f"Something went wrong while getting a game. ID is {game_id}")
            raise DatabaseError("Could not load the game.") from e
        finally:
            if conn:
                conn.close() # type: ignore

    def get_game_full(self, game_id: int):
        conn = None
        try:
            conn = self._connect()
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
                executable_list.append(Executable(path=exe[0]))
            
            return Game(
                id=game_id,
                name=game_row[0],
                developer=game_row[1],
                notes=game_row[2],
                executables=executable_list,
                banner_path=game_row[3]
            )

        except sqlite3.Error as e:
            print(f"Something went wrong while getting a game. ID is {game_id}")
            raise DatabaseError("Could not load the game settings.") from e
        finally:
            if conn:
                conn.close() # type: ignore

    def get_all_games(self):
        conn = None
        try:
            conn = self._connect()
            cur = conn.cursor()

            cur.execute("SELECT id, name FROM games")

            return cur.fetchall()

        except sqlite3.Error as e:
            print(f"Something went wrong while getting all games.")
            raise DatabaseError("Could not load the game list.") from e
        finally:
            if conn:
                conn.close() # type: ignore

    def get_game_playtime(self, game_id) -> int:
        conn = None
        try:
            conn = self._connect()
            cur = conn.cursor()

            cur.execute("""
                SELECT SUM((julianday(s.end_time) - julianday(s.start_time)) * 86400)
                FROM sessions s
                WHERE s.game_id = ?
            """, (game_id,))

            total_seconds = cur.fetchone()[0] or 0 # maybe or 0 i don't need it idk
            return int(total_seconds)

        except sqlite3.Error as e:
            print(f"Something went wrong while getting all games.")
            raise DatabaseError("Could not load playtime.") from e
        finally:
            if conn:
                conn.close() # type: ignore

    def get_game_first_time(self, game_id):
        conn = None
        try:
            conn = self._connect()
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

        except sqlite3.Error as e:
            print(f"Something went wrong while getting all games.")
            raise DatabaseError("Could not load first played date.") from e
        finally:
            if conn:
                conn.close() # type: ignore

    def get_game_last_time(self, game_id):
        conn = None
        try:
            conn = self._connect()
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

        except sqlite3.Error as e:
            print(f"Something went wrong while getting all games.")
            raise DatabaseError("Could not load last played date.") from e
        finally:
            if conn:
                conn.close() # type: ignore

    def get_average_playtime_day(self, game_id):
        conn = None
        try:
            conn = self._connect()
            cur = conn.cursor()

            cur.execute("""
                SELECT 
                    SUM(julianday(end_time) - julianday(start_time)) * 86400 as total_seconds,
                    COUNT(DISTINCT DATE(start_time)) as unique_days
                FROM sessions 
                WHERE game_id = ?
            """, (game_id,))

            result = cur.fetchone()

            if result and result[0] is not None and result[1] is not None and result[1] > 0:
                total_seconds = result[0]
                unique_days = result[1]

                return float(total_seconds / unique_days)
            return 0
        except sqlite3.Error as e:
            print(f"Something went wrong getting average playtime per day.")
            raise DatabaseError("Could not load average playtime.") from e
        finally:
            if conn:
                conn.close() # type: ignore

    def insert_session(self, game_id, start_time, end_time):
        conn = None
        try:
            conn = self._connect()
            cur = conn.cursor()

            cur.execute("INSERT INTO sessions (game_id, start_time, end_time) VALUES (?, ?, ?)",
                        (game_id, start_time, end_time))
            conn.commit() # i always forget this somehow
        except sqlite3.Error as e:
            print(f"Something went wrong while writing session.")
            raise DatabaseError("Could not save play session.") from e
        finally:
            if conn:
                conn.close() # type: ignore

    def get_known_executables(self):
        conn = None
        try:
            conn = self._connect()
            cur = conn.cursor()
            
            cur.execute("SELECT game_id, exe_name, full_path FROM executables")
            rows = cur.fetchall()
            
            return [
                {
                    "game_id": row[0],
                    "exe_name": row[1].lower(),
                    "full_path": normalize_exe_path(row[2]) if row[2] else "",
                }
                for row in rows
            ]
        
        except sqlite3.Error as e:
            print(f"Error getting executables: {e}")
            raise DatabaseError("Could not load executable tracking data.") from e
        finally:
            if conn:
                conn.close()
