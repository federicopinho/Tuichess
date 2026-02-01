# Lichess TUI Feature List

## Core gameplay
- Authenticate with a Lichess account (OAuth device flow or token input).
- Store credentials securely (OS keychain when available) and allow revocation/sign-out.
- Browse the live lobby with filters for time control, variant, and rating range.
- Create challenges with customizable settings (time, increment, rated/casual, variant).
- Accept/decline incoming challenges and show challenger details.
- Spectate live games and ongoing tournaments.
- Launch a game session with a responsive, keyboard-driven board view.

## Game session UI
- Render the chessboard in text with configurable themes (ASCII/Unicode pieces).
- Highlight legal moves, last move, check, and checkmate states.
- Support piece dragging via keyboard (select square, choose destination).
- Offer move list and PGN export within the session.
- Provide draw/resign/abort controls with confirmation prompts.
- Display clocks with low-time alerts.
- Show evaluation info if engine analysis is enabled locally.

## Social & community
- List friends, online status, and recent games.
- Direct message or send chat messages in a game or lobby.
- Follow/unfollow players and view profiles (rating history, stats).
- Receive notifications for challenges, messages, and tournament updates.

## Tournaments & events
- Browse current tournaments (arena, swiss) with join/withdraw actions.
- View standings, pairings, and game results.
- Provide scheduled event reminders.

## Analysis & study
- Load completed games for analysis with move-by-move navigation.
- Import/export PGN files from local disk.
- Run local engine analysis and show best line hints.
- Open studies (read-only) with chapter navigation.

## Settings & customization
- Configure keybindings (move selection, navigation, actions).
- Toggle sound/visual notifications.
- Configure board/piece themes, orientation, and accessibility options.
- Set default challenge preferences and privacy settings.

## Reliability & offline
- Graceful handling of network disconnects with reconnection status.
- Respect Lichess API rate limits with backoff and jitter.
- Queue outgoing actions while offline with retry limits and conflict prompts.
- Clear error messages with troubleshooting tips.

## Accessibility
- Screen-reader friendly output with concise mode.
- Keyboard-only navigation with consistent focus indicators.
- Colorblind-friendly palette presets.
- Support for reduced motion updates.

## Developer ergonomics
- Config file support (TOML/YAML) with hot reload.
- Structured logging with debug and trace modes.
- Plugin hooks for custom commands or integrations.
