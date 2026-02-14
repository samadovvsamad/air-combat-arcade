# Air Combat (Python Aircraft Shooter)

A top-down aircraft shooter built with Python, `tkinter`, and `Pillow`.

## Assets

The game uses local assets from:

- `images/`
  - `my aircraft.png` (player)
  - `enemy.png` (enemy)
  - `enemy2.png` (enemy sprite after 25 kills)
  - `bullet.jpg` (bullet sprite)
  - `bg.jpg` (day background)
  - `dark.jpg` (dark background)
  - `snow.jpg` (snow background)
  - `heart.png` (life icon)
  - `trophy.png` (records icon)
  - `rocket.png` (start icon)
  - `pilot.png` (username icon)
  - `keyboard.png` (shortcuts icon)
  - `reset.png` (reset records icon)
  - `shutdown.png` (quit icon)
  - `game_icon.png` (window/app icon)
- `sounds/`
  - `main.mp3` (menu music)

## Features

- Air Combat main menu UI with animated enemy fly-by.
- Menu music (`sounds/main.mp3`) with soft fade-in.
- Music stops when gameplay starts.
- Window icon from `images/game_icon.png` applied to main and popup windows.
- Interactive main menu:
  - You can move and shoot in the menu.
  - Shooting the menu enemy target is supported.
- Username system:
  - Dedicated `USERNAME` menu button.
  - Default username is random at app start from:
    - `Ghost`, `AirWolf`, `Viper`, `Phoenix`, `Falcon`
- Records system:
  - Top 10 records saved in `records.json`.
  - Records include `username`, `score`, `kills`, `level`, `played_at`.
  - `Reset Records` button (with `reset.png` icon) clears all saved records with confirmation.
- Gameplay progression:
  - Background transitions after 10 and 20 kills.
  - Enemy sprite changes after 25 kills.
  - Enemy double-shot starts after 30 kills.
  - Enemy death VFX: each destroyed enemy spawns 8-14 small circles that fly outward and fade.
  - Heart drops every 10 kills to reward extra life.

## Run

```powershell
pip install pillow
python main.py
```

## Controls

### Gameplay

- `W/A/S/D` or Arrow Keys: Move
- `Space`: Fire
- `P`: Pause/Resume
- `M`: Return to Main Menu
- `R` or `Enter`: Restart after game over

### Main Menu

- `Enter`: Start game
- `U`: Open username dialog
- `K` or `H`: Open shortcuts dialog
- `Esc`: Quit app
- `W/A/S/D` or Arrow Keys + `Space`: Move/shoot in menu

## Main Menu Buttons

- `START`
- `USERNAME`
- `RECORDS`
- `SHORTCUTS`
- `QUIT`

## Test Mode

`UNLIMITED_LIVES_TEST` controls invincible/infinite-life testing behavior in `main.py`.

- `True`: HUD shows `xINF`, player does not lose lives.
- `False`: Normal 3-life gameplay.

## Build EXE (Windows)

```powershell
python -m pip install pyinstaller
python -m PyInstaller --noconfirm --clean --windowed --onefile --name AirCombat --add-data "images;images" --add-data "sounds;sounds" --add-data "records.json;." main.py
```

Build output:

- `dist/AirCombat.exe`
