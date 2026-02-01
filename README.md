# Tuichess

Tuichess is a terminal-based client for Lichess with a simple curses UI and a
lightweight API wrapper. It includes a home screen, lobby and now-playing
lists, a game view with move history, friends and tournaments lists, plus a
settings screen for toggling themes and storing your Lichess token locally.

## Run

```bash
python -m tuichess
```

To use the live Lichess API, export a token:

```bash
export LICHESS_TOKEN="your-token"
python -m tuichess
```

## Notes

Token storage defaults to `~/.tuichess/config.json` with restrictive file
permissions. If the optional `keyring` package is installed, it will be used to
store the token in your system keychain instead.

## Controls

- **Home:** `L` lobby, `N` now playing, `F` friends, `T` tournaments, `S` settings,
  `R` refresh, `Q` quit. Mouse clicks on menu items are supported.
- **Lobby/Now Playing:** arrow keys or `j/k` to move, `Enter` to accept/open.
- **Game:** arrow keys or `j/k` to move through moves, click squares to enter
  moves, `M` add SAN or coordinate moves (e.g. `e2-e4`), `D` delete move, `R`
  resign, `=` offer draw, `B` back.
- **Friends:** arrow keys or `j/k` to move, `M` to send a message.
- **Tournaments:** arrow keys or `j/k` to move, `J` join/withdraw.
- **Settings:** `A` add token, `C` clear token, `T` toggle theme, `P` toggle
  piece set, `O` toggle coordinates, `U` toggle sound, `N` toggle notifications.
  Most rows are clickable to toggle or execute the related action.
