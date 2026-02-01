from __future__ import annotations

import curses
import re
from dataclasses import dataclass
from typing import List, Optional

from tuichess.models import AppData, GameSummary, LobbyChallenge, Settings, Tournament


@dataclass
class ScreenState:
    title: str
    lines: List[str]
    footer: str


@dataclass
class MoveEntry:
    ply: int
    san: str


def _draw_screen(stdscr: "curses._CursesWindow", state: ScreenState) -> None:
    stdscr.clear()
    height, width = stdscr.getmaxyx()
    stdscr.addstr(0, 0, state.title[: width - 1], curses.A_BOLD)
    for idx, line in enumerate(state.lines, start=2):
        if idx >= height - 2:
            break
        stdscr.addstr(idx, 0, line[: width - 1])
    stdscr.addstr(height - 1, 0, state.footer[: width - 1], curses.A_DIM)
    stdscr.refresh()


def run_ui(
    data: AppData,
    settings: Settings,
    token_present: bool,
    on_save_token,
    on_clear_token,
    on_refresh,
    on_queue_action,
) -> None:
    token_state = [token_present]
    selected_game: Optional[GameSummary] = None
    lobby_index = 0
    now_index = 0
    friends_index = 0
    tournament_index = 0
    move_index = 0
    selected_square: Optional[str] = None
    def _default_moves() -> List[MoveEntry]:
        return [
            MoveEntry(1, "e2-e4"),
            MoveEntry(2, "e7-e5"),
            MoveEntry(3, "g1-f3"),
            MoveEntry(4, "b8-c6"),
        ]

    def _initial_board() -> List[List[str]]:
        return [
            list("rnbqkbnr"),
            list("pppppppp"),
            list("........"),
            list("........"),
            list("........"),
            list("........"),
            list("PPPPPPPP"),
            list("RNBQKBNR"),
        ]

    def _square_to_index(square: str) -> tuple[int, int]:
        file_char, rank_char = square[0], square[1]
        row = 8 - int(rank_char)
        col = ord(file_char) - ord("a")
        return row, col

    def _piece_at(square: str) -> str:
        row, col = _square_to_index(square)
        return board_state[row][col]

    def _parse_coord_move(move: str) -> Optional[tuple[str, str]]:
        match = re.match(r"^([a-h][1-8])[- ]?([a-h][1-8])$", move.strip().lower())
        if not match:
            return None
        return match.group(1), match.group(2)

    def _apply_coord_move(source: str, dest: str) -> bool:
        src_row, src_col = _square_to_index(source)
        dst_row, dst_col = _square_to_index(dest)
        piece = board_state[src_row][src_col]
        if piece == ".":
            return False
        board_state[src_row][src_col] = "."
        board_state[dst_row][dst_col] = piece
        return True

    def _rebuild_board() -> None:
        nonlocal board_state
        board_state = _initial_board()
        for move in moves:
            parsed = _parse_coord_move(move.san)
            if parsed:
                _apply_coord_move(*parsed)

    def _reset_game_state() -> None:
        nonlocal moves, move_index, selected_square, board_state
        moves = _default_moves()
        move_index = max(0, len(moves) - 1)
        selected_square = None
        board_state = _initial_board()
        _rebuild_board()

    moves: List[MoveEntry] = _default_moves()
    board_state = _initial_board()
    _rebuild_board()

    def _format_summary(game: GameSummary) -> str:
        clock = f"{game.clock}s" if game.clock else "?"
        rated = "Rated" if game.rated else "Casual"
        return (
            f"{game.game_id} vs {game.opponent} · {game.perf} · {clock} · {rated}"
        )

    def _format_lobby(challenge: LobbyChallenge) -> str:
        rated = "Rated" if challenge.rated else "Casual"
        return (
            f"{challenge.challenge_id} · {challenge.creator} · {challenge.perf} "
            f"{challenge.clock}s · {rated}"
        )

    def _format_tournament(tournament: Tournament) -> str:
        status = "Joined" if tournament.joined else "Open"
        return f"{tournament.name} · {tournament.perf} · {tournament.starts_in} · {status}"

    def _render_board() -> List[str]:
        coords = "  a b c d e f g h"
        board = []
        for idx, row in enumerate(board_state):
            rank = 8 - idx
            board.append(f"{rank} " + " ".join(row) + f" {rank}")
        if settings.show_coordinates:
            return [coords, *board, coords]
        return board

    def _render_moves() -> List[str]:
        output = []
        for idx, move in enumerate(moves):
            prefix = "➤" if idx == move_index else " "
            output.append(f"{prefix} {move.ply}. {move.san}")
        return output

    def _prompt(stdscr: "curses._CursesWindow", message: str) -> str:
        curses.echo()
        stdscr.clear()
        stdscr.addstr(0, 0, message)
        response = stdscr.getstr(1, 0).decode("utf-8").strip()
        curses.noecho()
        return response

    def _inner(stdscr: "curses._CursesWindow") -> None:
        curses.curs_set(0)
        stdscr.keypad(True)
        stdscr.nodelay(False)
        curses.mousemask(curses.ALL_MOUSE_EVENTS | curses.REPORT_MOUSE_POSITION)
        curses.mouseinterval(0)
        screen = "home"

        def _set_screen(name: str) -> None:
            nonlocal screen
            screen = name

        def _refresh() -> None:
            nonlocal data
            data = on_refresh()

        def _handle_mouse(
            click_actions: dict[int, callable], board_click=None
        ) -> None:
            try:
                _, x, y, _, state = curses.getmouse()
            except curses.error:
                return
            if not state & (curses.BUTTON1_CLICKED | curses.BUTTON1_PRESSED):
                return
            if board_click and board_click(y, x):
                return
            action = click_actions.get(y)
            if action:
                action()

        def _add_move(stdscr: "curses._CursesWindow") -> None:
            entry = _prompt(stdscr, "Enter move (SAN or e2-e4): ")
            _append_move(entry)

        def _delete_move() -> None:
            nonlocal move_index
            if not moves:
                return
            removed = moves.pop(move_index)
            move_index = max(0, move_index - 1)
            _rebuild_board()
            on_queue_action(f"Delete move {removed.san}")

        def _resign() -> None:
            on_queue_action("Resign game")
            data.status_message = "Resign queued."

        def _offer_draw() -> None:
            on_queue_action("Offer draw")
            data.status_message = "Draw offer queued."

        def _append_move(entry: str) -> None:
            nonlocal move_index
            if entry:
                moves.append(MoveEntry(len(moves) + 1, entry))
                move_index = len(moves) - 1
                _rebuild_board()
                on_queue_action(f"Move {entry}")

        def _add_token(stdscr: "curses._CursesWindow") -> None:
            token = _prompt(stdscr, "Enter Lichess token: ")
            if token:
                on_save_token(token)
                token_state[0] = True
            _set_screen("home")

        def _clear_token() -> None:
            on_clear_token()
            token_state[0] = False
            _set_screen("home")

        def _toggle_theme() -> None:
            settings.theme = "Dark" if settings.theme == "Classic" else "Classic"

        def _toggle_pieces() -> None:
            settings.pieces = "ASCII" if settings.pieces == "Unicode" else "Unicode"

        def _toggle_coordinates() -> None:
            settings.show_coordinates = not settings.show_coordinates

        def _toggle_sound() -> None:
            settings.sound = not settings.sound

        def _toggle_notifications() -> None:
            settings.notifications = not settings.notifications

        while True:
            if screen == "home":
                lines: List[str] = []
                click_actions: dict[int, callable] = {}

                def add_line(text: str, action=None) -> None:
                    lines.append(text)
                    if action is not None:
                        row = len(lines) + 1
                        click_actions[row] = action

                add_line("Welcome to Tuichess.")
                add_line(
                    f"Account: {data.account_name or 'Offline / Not authenticated'}"
                )
                add_line(f"Token: {'configured' if token_state[0] else 'missing'}")
                add_line(f"Status: {data.status_message}")
                add_line(f"Queued actions: {len(data.queued_actions)}")
                add_line("")
                add_line("[L] Lobby", lambda: _set_screen("lobby"))
                add_line("[N] Now Playing", lambda: _set_screen("now_playing"))
                add_line("[F] Friends", lambda: _set_screen("friends"))
                add_line("[T] Tournaments", lambda: _set_screen("tournaments"))
                add_line("[S] Settings", lambda: _set_screen("settings"))
                add_line("[R] Refresh", lambda: _refresh())
                add_line("[Q] Quit", lambda: _set_screen("quit"))
                _draw_screen(
                    stdscr,
                    ScreenState(
                        title="Tuichess",
                        lines=lines,
                        footer="Press a key or click an option.",
                    ),
                )
                key = stdscr.getch()
                if key == curses.KEY_MOUSE:
                    _handle_mouse(click_actions)
                    if screen == "quit":
                        return
                    continue
                if key in (ord("q"), ord("Q")):
                    return
                if key in (ord("l"), ord("L")):
                    screen = "lobby"
                elif key in (ord("n"), ord("N")):
                    screen = "now_playing"
                elif key in (ord("f"), ord("F")):
                    screen = "friends"
                elif key in (ord("t"), ord("T")):
                    screen = "tournaments"
                elif key in (ord("s"), ord("S")):
                    screen = "settings"
                elif key in (ord("r"), ord("R")):
                    data = on_refresh()
            elif screen == "lobby":
                if data.lobby:
                    lobby_index = max(0, min(lobby_index, len(data.lobby) - 1))
                lines = []
                click_actions = {}

                def add_line(text: str, action=None) -> None:
                    lines.append(text)
                    if action is not None:
                        row = len(lines) + 1
                        click_actions[row] = action

                add_line("Open challenges (press Enter or click to accept).")
                add_line("")
                for idx, challenge in enumerate(data.lobby):
                    prefix = "➤" if idx == lobby_index else " "

                    def _accept(idx=idx) -> None:
                        nonlocal lobby_index, data
                        lobby_index = idx
                        choice = data.lobby[lobby_index]
                        on_queue_action(f"Accept {choice.challenge_id}")
                        data.status_message = "Challenge accepted (queued)."

                    add_line(f"{prefix} {_format_lobby(challenge)}", _accept)
                add_line("")
                add_line("[Enter] Accept", lambda: _accept(lobby_index))
                add_line("[H] Home", lambda: _set_screen("home"))
                _draw_screen(
                    stdscr,
                    ScreenState(
                        title="Lobby", lines=lines, footer="Press H or click Home."
                    ),
                )
                key = stdscr.getch()
                if key == curses.KEY_MOUSE:
                    _handle_mouse(click_actions)
                    continue
                if key in (ord("h"), ord("H")):
                    screen = "home"
                elif key in (curses.KEY_UP, ord("k")):
                    lobby_index = max(0, lobby_index - 1)
                elif key in (curses.KEY_DOWN, ord("j")):
                    lobby_index = min(len(data.lobby) - 1, lobby_index + 1)
                elif key in (curses.KEY_ENTER, 10, 13) and data.lobby:
                    _accept(lobby_index)
            elif screen == "now_playing":
                lines = []
                click_actions = {}

                def add_line(text: str, action=None) -> None:
                    lines.append(text)
                    if action is not None:
                        row = len(lines) + 1
                        click_actions[row] = action

                add_line("Now Playing")
                if not data.now_playing:
                    add_line("No active games found.")
                else:
                    now_index = max(0, min(now_index, len(data.now_playing) - 1))
                    for idx, game in enumerate(data.now_playing):
                        prefix = "➤" if idx == now_index else " "

                        def _open_game(idx=idx) -> None:
                            nonlocal now_index, selected_game, screen
                            now_index = idx
                            selected_game = data.now_playing[now_index]
                            screen = "game"

                        add_line(f"{prefix} {_format_summary(game)}", _open_game)
                add_line("")
                add_line("[Enter] Open", lambda: _open_game(now_index))
                add_line("[H] Home", lambda: _set_screen("home"))
                _draw_screen(
                    stdscr,
                    ScreenState(
                        title="Now Playing",
                        lines=lines,
                        footer="Press H or click Home.",
                    ),
                )
                key = stdscr.getch()
                if key == curses.KEY_MOUSE:
                    _handle_mouse(click_actions)
                    continue
                if key in (ord("h"), ord("H")):
                    screen = "home"
                elif key in (curses.KEY_UP, ord("k")):
                    now_index = max(0, now_index - 1)
                elif key in (curses.KEY_DOWN, ord("j")):
                    now_index = min(len(data.now_playing) - 1, now_index + 1)
                elif key in (curses.KEY_ENTER, 10, 13) and data.now_playing:
                    selected_game = data.now_playing[now_index]
                    _reset_game_state()
                    screen = "game"
            elif screen == "game":
                board_lines = _render_board()
                if selected_game:
                    summary = _format_summary(selected_game)
                else:
                    summary = "No game selected."
                lines = []
                click_actions = {}

                def add_line(text: str, action=None) -> None:
                    lines.append(text)
                    if action is not None:
                        row = len(lines) + 1
                        click_actions[row] = action

                def add_move_entry(idx: int, text: str) -> None:
                    def _select_move(idx=idx) -> None:
                        nonlocal move_index
                        move_index = idx

                    add_line(text, _select_move)

                add_line(summary)
                add_line(f"Selected square: {selected_square or 'None'}")
                add_line("")
                board_start_row = len(lines) + 2
                for line in board_lines:
                    add_line(line)
                add_line("")
                add_line("Moves:")
                for idx, move_line in enumerate(_render_moves()):
                    add_move_entry(idx, move_line)
                add_line("")
                add_line("[M] Add move", lambda: _add_move(stdscr))
                add_line("[D] Delete move", lambda: _delete_move())
                add_line("[R] Resign", lambda: _resign())
                add_line("[=] Offer draw", lambda: _offer_draw())
                add_line("[B] Back", lambda: _set_screen("home"))
                _draw_screen(
                    stdscr,
                    ScreenState(
                        title="Game View",
                        lines=lines,
                        footer="Click squares to move or press B to go back.",
                    ),
                )

                def _handle_board_click(y: int, x: int) -> bool:
                    nonlocal selected_square
                    line_index = y - board_start_row
                    if line_index < 0 or line_index >= len(board_lines):
                        return False
                    line = board_lines[line_index]
                    if not line or line[0] not in "12345678":
                        return False
                    rank = line[0]
                    file_positions = {
                        2: "a",
                        4: "b",
                        6: "c",
                        8: "d",
                        10: "e",
                        12: "f",
                        14: "g",
                        16: "h",
                    }
                    file_letter = None
                    for pos, file_name in file_positions.items():
                        if abs(x - pos) <= 1:
                            file_letter = file_name
                            break
                    if not file_letter:
                        return False
                    square = f"{file_letter}{rank}"
                    if selected_square is None:
                        piece = _piece_at(square)
                        if piece == ".":
                            data.status_message = f"No piece on {square}."
                            return True
                        selected_square = square
                        data.status_message = f"Selected {square}."
                    else:
                        if square == selected_square:
                            selected_square = None
                            data.status_message = "Selection cleared."
                        else:
                            move = f"{selected_square}-{square}"
                            _append_move(move)
                            data.status_message = f"Move queued: {move}."
                            selected_square = None
                    return True

                key = stdscr.getch()
                if key == curses.KEY_MOUSE:
                    _handle_mouse(click_actions, _handle_board_click)
                    continue
                if key in (ord("b"), ord("B")):
                    screen = "home"
                elif key in (curses.KEY_UP, ord("k")):
                    move_index = max(0, move_index - 1)
                elif key in (curses.KEY_DOWN, ord("j")):
                    move_index = min(len(moves) - 1, move_index + 1)
                elif key in (ord("m"), ord("M")):
                    _add_move(stdscr)
                elif key in (ord("d"), ord("D")) and moves:
                    _delete_move()
                elif key in (ord("r"), ord("R")):
                    _resign()
                elif key == ord("="):
                    _offer_draw()
            elif screen == "friends":
                if data.friends:
                    friends_index = max(0, min(friends_index, len(data.friends) - 1))
                lines = []
                click_actions = {}

                def add_line(text: str, action=None) -> None:
                    lines.append(text)
                    if action is not None:
                        row = len(lines) + 1
                        click_actions[row] = action

                add_line("Friends")
                add_line("")

                def _message_friend(idx: int) -> None:
                    nonlocal friends_index
                    friends_index = idx
                    friend = data.friends[friends_index]
                    message = _prompt(stdscr, f"Message {friend.username}: ")
                    if message:
                        on_queue_action(f"DM to {friend.username}: {message}")
                        data.status_message = "Message queued."

                for idx, friend in enumerate(data.friends):
                    prefix = "➤" if idx == friends_index else " "
                    status = "online" if friend.online else "offline"
                    playing = "playing" if friend.playing else "idle"
                    add_line(
                        f"{prefix} {friend.username} · {status} · {playing}",
                        lambda idx=idx: _message_friend(idx),
                    )
                add_line("")
                add_line("[M] Message", lambda: _message_friend(friends_index))
                add_line("[H] Home", lambda: _set_screen("home"))
                _draw_screen(
                    stdscr,
                    ScreenState(
                        title="Friends",
                        lines=lines,
                        footer="Press H or click Home.",
                    ),
                )
                key = stdscr.getch()
                if key == curses.KEY_MOUSE:
                    _handle_mouse(click_actions)
                    continue
                if key in (ord("h"), ord("H")):
                    screen = "home"
                elif key in (curses.KEY_UP, ord("k")):
                    friends_index = max(0, friends_index - 1)
                elif key in (curses.KEY_DOWN, ord("j")):
                    friends_index = min(len(data.friends) - 1, friends_index + 1)
                elif key in (ord("m"), ord("M")) and data.friends:
                    _message_friend(friends_index)
            elif screen == "tournaments":
                if data.tournaments:
                    tournament_index = max(
                        0, min(tournament_index, len(data.tournaments) - 1)
                    )
                lines = []
                click_actions = {}

                def add_line(text: str, action=None) -> None:
                    lines.append(text)
                    if action is not None:
                        row = len(lines) + 1
                        click_actions[row] = action

                def _toggle_tournament(idx: int) -> None:
                    nonlocal tournament_index, data
                    tournament_index = idx
                    tournament = data.tournaments[tournament_index]
                    tournament.joined = not tournament.joined
                    action = "Join" if tournament.joined else "Withdraw"
                    on_queue_action(f"{action} {tournament.name}")
                    data.status_message = f"{action} queued."

                add_line("Tournaments")
                add_line("")
                for idx, tournament in enumerate(data.tournaments):
                    prefix = "➤" if idx == tournament_index else " "
                    add_line(
                        f"{prefix} {_format_tournament(tournament)}",
                        lambda idx=idx: _toggle_tournament(idx),
                    )
                add_line("")
                add_line("[J] Join/Withdraw", lambda: _toggle_tournament(tournament_index))
                add_line("[H] Home", lambda: _set_screen("home"))
                _draw_screen(
                    stdscr,
                    ScreenState(
                        title="Tournaments",
                        lines=lines,
                        footer="Press H or click Home.",
                    ),
                )
                key = stdscr.getch()
                if key == curses.KEY_MOUSE:
                    _handle_mouse(click_actions)
                    continue
                if key in (ord("h"), ord("H")):
                    screen = "home"
                elif key in (curses.KEY_UP, ord("k")):
                    tournament_index = max(0, tournament_index - 1)
                elif key in (curses.KEY_DOWN, ord("j")):
                    tournament_index = min(
                        len(data.tournaments) - 1, tournament_index + 1
                    )
                elif key in (ord("j"), ord("J")) and data.tournaments:
                    _toggle_tournament(tournament_index)
            elif screen == "settings":
                lines = []
                click_actions = {}

                def add_line(text: str, action=None) -> None:
                    lines.append(text)
                    if action is not None:
                        row = len(lines) + 1
                        click_actions[row] = action

                add_line("Settings")
                add_line("")
                add_line(
                    f"Token status: {'configured' if token_state[0] else 'missing'}"
                )
                add_line(f"Theme: {settings.theme}", lambda: _toggle_theme())
                add_line(f"Pieces: {settings.pieces}", lambda: _toggle_pieces())
                add_line(
                    f"Coordinates: {'on' if settings.show_coordinates else 'off'}",
                    lambda: _toggle_coordinates(),
                )
                add_line(
                    f"Sound: {'on' if settings.sound else 'off'}",
                    lambda: _toggle_sound(),
                )
                add_line(
                    f"Notifications: {'on' if settings.notifications else 'off'}",
                    lambda: _toggle_notifications(),
                )
                add_line("[A] Add/update token", lambda: _add_token(stdscr))
                add_line("[C] Clear token", lambda: _clear_token())
                add_line("[T] Toggle theme", lambda: _toggle_theme())
                add_line("[P] Toggle piece set", lambda: _toggle_pieces())
                add_line("[O] Toggle coordinates", lambda: _toggle_coordinates())
                add_line("[U] Toggle sound", lambda: _toggle_sound())
                add_line("[N] Toggle notifications", lambda: _toggle_notifications())
                add_line("[H] Home", lambda: _set_screen("home"))
                _draw_screen(
                    stdscr,
                    ScreenState(
                        title="Settings",
                        lines=lines,
                        footer="Press a key or click an option.",
                    ),
                )
                key = stdscr.getch()
                if key == curses.KEY_MOUSE:
                    _handle_mouse(click_actions)
                    continue
                if key in (ord("h"), ord("H")):
                    screen = "home"
                elif key in (ord("a"), ord("A")):
                    _add_token(stdscr)
                elif key in (ord("c"), ord("C")):
                    _clear_token()
                elif key in (ord("t"), ord("T")):
                    _toggle_theme()
                elif key in (ord("p"), ord("P")):
                    _toggle_pieces()
                elif key in (ord("o"), ord("O")):
                    _toggle_coordinates()
                elif key in (ord("u"), ord("U")):
                    _toggle_sound()
                elif key in (ord("n"), ord("N")):
                    _toggle_notifications()

    curses.wrapper(_inner)
