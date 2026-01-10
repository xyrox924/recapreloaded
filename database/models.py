from dataclasses import dataclass

@dataclass
class Executable:
    path: str
    id: int | None = None
    game_id: int | None = None

@dataclass
class Game:
    name: str
    developer: str
    notes: str
    executables: list[Executable]
    id: int | None = None