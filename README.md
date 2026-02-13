# Sky Assault (Python Aircraft Shooter)

A simple top-down aircraft shooter built with Python, `tkinter`, and your image assets in the `images/` folder:

- `images/my aircraft.png` (player aircraft)
- `images/enemy.png` (enemy aircraft)
- `images/enemy2.png` (enemy aircraft after 25 kills)
- `images/bullet.jpg` (bullet sprite)
- `images/bg.jpg` (background)
- `images/dark.jpg` (dark background after 10 kills)
- `images/snow.jpg` (snow background after 20 kills)
- `images/heart.png` (lives icon)
- `images/trophy.png` (records icon)
- `images/rocket.png` (start icon)
- `images/shutdown.png` (quit icon)

## Run

```powershell
pip install pillow
python main.py
```

## Controls

- `W/A/S/D` or Arrow Keys: Move your aircraft
- `Space`: Fire bullets
- `P`: Pause/Resume
- `R` or `Enter`: Restart after game over
- `Pause` button: Pause/Resume
- `New Game` button: Start a new run immediately
- `Records` button: Show top saved scores

## Main Menu

Before gameplay starts, a main menu is shown with:

- `START`: Begin a new run
- `RECORDS`: View top scores
- `QUIT`: Exit the app

## Goal

Destroy enemy aircraft, avoid enemy bullets, and survive as long as possible.
Difficulty increases as your kill count grows.
After 10 enemy kills, background transitions from `bg.jpg` to `dark.jpg`.
After 20 enemy kills, background transitions from `dark.jpg` to `snow.jpg`.
After 25 enemy kills, enemies switch to `enemy2.png`.
For every 10 enemy aircraft destroyed, a heart drops from the enemy/top side.
Collect the heart to gain `+1 life`.

## Records

Top records are saved automatically in `records.json` (top 10 runs).
