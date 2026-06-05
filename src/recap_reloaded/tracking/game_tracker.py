import threading

from datetime import datetime

from PySide6.QtCore import QObject, Signal

from recap_reloaded.database.database import DatabaseError
from recap_reloaded.utils import get_running_processes, normalize_exe_path


class GameTracker(QObject):
    game_started = Signal(int, str)
    game_stopped = Signal(int, str)

    def __init__(self, db, parent=None):
        super().__init__(parent)
        self.db = db
        self.active_sessions = {}
        self.active_sessions_lock = threading.Lock()
        self.stop_event = threading.Event()
        self.lifecycle_lock = threading.Lock()
        self.started = False
        self.stopped = False
        self.thread = threading.Thread(target=self._tracking_loop, daemon=True)

    def start(self):
        with self.lifecycle_lock:
            if self.started or self.stopped:
                return
            self.started = True
            self.thread.start()

    def stop(self):
        with self.lifecycle_lock:
            if self.stopped:
                return
            self.stopped = True

        self.stop_event.set()
        if self.started:
            self.thread.join(timeout=12)

        with self.active_sessions_lock:
            active_sessions = list(self.active_sessions.items())
            self.active_sessions.clear()

        for game_id, start_time in active_sessions:
            try:
                self.db.insert_session(game_id, start_time, datetime.now())
            except DatabaseError as e:
                print(e)

    def _get_running_game_ids(self, running_names, running_paths, known_exes):
        exe_name_game_ids = {}
        for known_exe in known_exes:
            exe_name = known_exe["exe_name"]
            exe_name_game_ids.setdefault(exe_name, set()).add(known_exe["game_id"])

        running_game_ids = set()
        for known_exe in known_exes:
            full_path = known_exe["full_path"]
            exe_name = known_exe["exe_name"]

            if full_path and normalize_exe_path(full_path) in running_paths:
                running_game_ids.add(known_exe["game_id"])
            elif len(exe_name_game_ids.get(exe_name, set())) == 1 and exe_name in running_names:
                running_game_ids.add(known_exe["game_id"])

        return running_game_ids

    def _tracking_loop(self):
        while not self.stop_event.is_set():
            running_names, running_paths = get_running_processes()
            try:
                known_exes = self.db.get_known_executables()
            except DatabaseError as e:
                print(e)
                self.stop_event.wait(10)
                continue

            running_game_ids = self._get_running_game_ids(running_names, running_paths, known_exes)

            started_game_ids = []
            stopped_sessions = []

            with self.active_sessions_lock:
                for game_id in running_game_ids:
                    if game_id not in self.active_sessions:
                        self.active_sessions[game_id] = datetime.now()
                        started_game_ids.append(game_id)

                for game_id in list(self.active_sessions.keys()):
                    if game_id not in running_game_ids:
                        stopped_sessions.append((game_id, self.active_sessions.pop(game_id), datetime.now()))

            for game_id in started_game_ids:
                try:
                    game = self.db.get_game(game_id)
                except DatabaseError as e:
                    print(e)
                    continue
                if game is not None:
                    print(f"Started tracking game {game.name}")
                    self.game_started.emit(game_id, game.name)

            for game_id, start_time, end_time in stopped_sessions:
                try:
                    self.db.insert_session(game_id, start_time, end_time)
                except DatabaseError as e:
                    print(e)
                    with self.active_sessions_lock:
                        self.active_sessions.setdefault(game_id, start_time)
                    continue

                try:
                    game = self.db.get_game(game_id)
                except DatabaseError as e:
                    print(e)
                    continue

                if game is not None:
                    print(f"Ended tracking game {game.name}")
                    self.game_stopped.emit(game_id, game.name)

            self.stop_event.wait(10)
