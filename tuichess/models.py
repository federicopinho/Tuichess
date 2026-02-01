from __future__ import annotations

from dataclasses import dataclass, field
from typing import List, Optional


@dataclass
class GameSummary:
    game_id: str
    opponent: str
    color: str
    perf: str
    clock: Optional[int]
    rated: bool = False
    variant: str = "Standard"
    status: str = "In progress"


@dataclass
class LobbyChallenge:
    challenge_id: str
    creator: str
    perf: str
    clock: int
    rated: bool
    variant: str


@dataclass
class Friend:
    username: str
    online: bool
    playing: bool


@dataclass
class Tournament:
    name: str
    perf: str
    starts_in: str
    joined: bool = False


@dataclass
class Settings:
    theme: str = "Classic"
    pieces: str = "Unicode"
    show_coordinates: bool = True
    sound: bool = False
    notifications: bool = True


@dataclass
class AppData:
    account_name: Optional[str]
    now_playing: List[GameSummary]
    lobby: List[LobbyChallenge]
    friends: List[Friend]
    tournaments: List[Tournament]
    queued_actions: List[str] = field(default_factory=list)
    status_message: str = "Ready."
