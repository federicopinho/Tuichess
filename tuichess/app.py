from __future__ import annotations

import os
from typing import List, Optional

from tuichess.api import LichessClient
from tuichess.models import (
    AppData,
    Friend,
    GameSummary,
    LobbyChallenge,
    Settings,
    Tournament,
)
from tuichess.storage import Config, clear_config, load_config, save_config
from tuichess.ui import run_ui


def _resolve_token(config: Config) -> Optional[str]:
    return os.environ.get("LICHESS_TOKEN") or config.token


def _format_now_playing(payload: dict) -> List[GameSummary]:
    games = payload.get("nowPlaying") or []
    formatted: List[GameSummary] = []
    for game in games:
        opponent = game.get("opponent", {}).get("username", "Unknown")
        color = game.get("color", "?")
        game_id = game.get("gameId", "unknown")
        perf = game.get("perf", "Standard")
        clock = game.get("clock", {}).get("initial")
        formatted.append(
            GameSummary(
                game_id=game_id,
                opponent=opponent,
                color=color,
                perf=perf,
                clock=clock,
                rated=bool(game.get("rated", False)),
                variant=game.get("variant", "Standard"),
                status=game.get("status", "In progress"),
            )
        )
    return formatted


def _mock_now_playing() -> List[GameSummary]:
    return [
        GameSummary(
            game_id="mock1",
            opponent="Ada",
            color="white",
            perf="Blitz",
            clock=300,
            rated=True,
        ),
        GameSummary(
            game_id="mock2",
            opponent="Turing",
            color="black",
            perf="Rapid",
            clock=600,
            rated=False,
        ),
    ]


def _mock_lobby() -> List[LobbyChallenge]:
    return [
        LobbyChallenge(
            challenge_id="open1",
            creator="Open challenge",
            perf="Bullet",
            clock=120,
            rated=True,
            variant="Standard",
        ),
        LobbyChallenge(
            challenge_id="open2",
            creator="Open challenge",
            perf="Classical",
            clock=1800,
            rated=False,
            variant="Standard",
        ),
    ]


def _mock_friends() -> List[Friend]:
    return [
        Friend(username="Ada", online=True, playing=True),
        Friend(username="Turing", online=True, playing=False),
        Friend(username="Hopper", online=False, playing=False),
    ]


def _mock_tournaments() -> List[Tournament]:
    return [
        Tournament(name="Evening Blitz", perf="Blitz", starts_in="10m", joined=False),
        Tournament(name="Night Bullet", perf="Bullet", starts_in="1h", joined=True),
    ]


def _refresh_data(client: LichessClient, token: Optional[str]) -> AppData:
    account_name = None
    now_playing = _mock_now_playing()
    status = "Offline mode."
    if token:
        account = client.get_account()
        if account.ok and account.data:
            account_name = account.data.get("username")
            status = "Connected to Lichess."
        elif account.error:
            status = f"Account error: {account.error}"
        playing = client.get_now_playing()
        if playing.ok and playing.data:
            now_playing = _format_now_playing(playing.data)
    return AppData(
        account_name=account_name,
        now_playing=now_playing,
        lobby=_mock_lobby(),
        friends=_mock_friends(),
        tournaments=_mock_tournaments(),
        status_message=status,
    )


def main() -> None:
    config = load_config()
    token = _resolve_token(config)
    client = LichessClient(token)

    data = _refresh_data(client, token)
    settings = Settings()

    def _save_token(new_token: str) -> None:
        config.token = new_token
        save_config(config)

    def _clear_token() -> None:
        config.token = None
        clear_config()

    def _refresh() -> AppData:
        nonlocal data
        data = _refresh_data(client, token)
        return data

    def _queue_action(action: str) -> None:
        data.queued_actions.append(action)

    run_ui(
        data=data,
        settings=settings,
        token_present=bool(token),
        on_save_token=_save_token,
        on_clear_token=_clear_token,
        on_refresh=_refresh,
        on_queue_action=_queue_action,
    )
