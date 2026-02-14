# Air Combat

Top-down aircraft shooter built with Python `tkinter` + `Pillow`.

## Requirements

- Python 3.10+
- Pillow (`pip install pillow`)
- Windows is recommended for menu music playback (`winmm`/MCI is used for `main.mp3`)

## Run

```powershell
pip install pillow
python main.py
```

## Core Features

- Main menu with custom canvas buttons and icon set.
- Subtle animated cloud-drift menu background (slow, seamless vertical loop).
- Interactive menu: player can move/fire and down the menu enemy target.
- Menu music (`sounds/main.mp3`) with soft fade-in and looping.
- Menu music stops when gameplay starts.
- Cinematic mission start sequence:
  - Fade from black.
  - Center animated icon (`images/start_anim.gif`) with gentle float.
  - `MISSION START` text fade in/out.
  - Seamless transition into gameplay.
- Window icon (`images/game_icon.png`) applied to main and popup windows.

## Gameplay Features

- Dual controls: `W/A/S/D` or Arrow Keys.
- Progressive difficulty (spawn rate + enemy speed scale by level).
- Enemy visual swap at `25` kills (`enemy2.png`).
- Enemy double-shot at `30` kills.
- Enemy death particles: `8-14` outward fading circles.
- Light screen shake on enemy destruction (short, decaying, auto-centered).
- Background progression by kills:
  - Day -> Dark at `10`.
  - Dark -> Snow at `20`.
- Heart power-up drop every `10` kills.

## HUD and UI

- Score/Level/Kills HUD includes a semi-transparent dark panel + subtle text shadow for bright backgrounds.
- Lives UI includes:
  - Semi-transparent panel.
  - Heart icon + `Lives` label + value text.
  - Gentle heart pulse animation.
- Username shown in the menu with pilot icon.

## Username and Records

- Username popup from main menu (`USERNAME` button).
- Default username is randomized each launch from:
  - `Ghost`, `AirWolf`, `Viper`, `Phoenix`, `Falcon`
- Records saved to `records.json` (top 10).
- Record fields: `username`, `score`, `kills`, `level`, `played_at`.
- Records popup includes `Reset Records` button with `images/reset.png`.
- Reset action asks for confirmation before clearing data.

## Controls

### Gameplay

- `W/A/S/D` or Arrow Keys: Move
- `Space`: Fire
- `P`: Pause/Resume
- `M`: Back to main menu
- `R` or `Enter`: Restart (after game over)

### Main Menu

- `Enter`: Start game
- `U`: Open username popup
- `K` or `H`: Open shortcuts popup
- `Esc`: Quit
- `W/A/S/D` or Arrow Keys + `Space`: Move/fire in menu

## Assets

Expected files:

- `images/my aircraft.png`
- `images/enemy.png`
- `images/enemy2.png`
- `images/bullet.jpg`
- `images/bg.jpg`
- `images/dark.jpg`
- `images/snow.jpg`
- `images/heart.png`
- `images/trophy.png`
- `images/rocket.png`
- `images/pilot.png`
- `images/keyboard.png`
- `images/reset.png`
- `images/shutdown.png`
- `images/game_icon.png`
- `images/start_anim.gif`
- `sounds/main.mp3`

## Test Mode

Set in `main.py`:

- `UNLIMITED_LIVES_TEST = True`: infinite/test lives (`xINF`)
- `UNLIMITED_LIVES_TEST = False`: normal 3-life gameplay

## Build EXE (Windows)

```powershell
python -m pip install pyinstaller
python -m PyInstaller --noconfirm --clean --windowed --onefile --name AirCombat --add-data "images;images" --add-data "sounds;sounds" --add-data "records.json;." main.py
```

Output:

- `dist/AirCombat.exe`
