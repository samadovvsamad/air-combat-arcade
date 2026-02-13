import json
import random
import time
import ctypes
from datetime import datetime
from pathlib import Path
import tkinter as tk
from tkinter import messagebox

try:
    from PIL import Image, ImageDraw, ImageFilter, ImageTk
except ImportError:
    Image = None
    ImageDraw = None
    ImageFilter = None
    ImageTk = None


WIDTH = 900
HEIGHT = 600
FPS = 60

PLAYER_SPEED = 360
PLAYER_FIRE_INTERVAL = 0.2
PLAYER_BULLET_SPEED = -620

ENEMY_BASE_SPEED = 120
ENEMY_BULLET_SPEED = 320
START_SPAWN_INTERVAL = 1.05
MIN_SPAWN_INTERVAL = 0.32
RECORD_LIMIT = 10
LIFE_REWARD_KILLS = 10
HEART_DROP_SPEED = 175
BACKGROUND_DARK_KILLS = 10
BACKGROUND_SNOW_KILLS = 20
ENEMY_SWAP_KILLS = 25
BG_TRANSITION_DURATION = 1.2
BG_TRANSITION_FRAMES = 24
MENU_PLANE_SPEED = 120
MENU_BUTTON_WIDTH = 200
MENU_BUTTON_HEIGHT = 50
MENU_BUTTON_RADIUS = 25
MENU_BUTTON_GAP = 20
MENU_BUTTON_VERTICAL_OFFSET = 70
TROPHY_MENU_SIZE = 18
TROPHY_UI_SIZE = 14
TROPHY_RECORDS_SIZE = 48
TROPHY_PULSE_MIN = 46
TROPHY_PULSE_MAX = 50
TROPHY_PULSE_STEP = 2
MENU_SHADOW_OFFSET = 2
MENU_SHADOW_BLUR = 4
MENU_SHADOW_ALPHA = 77
MENU_SHADOW_ACTIVE_OFFSET = 3
MENU_SHADOW_ACTIVE_BLUR = 5
MENU_SHADOW_ACTIVE_ALPHA = 120
OPENING_SOUND_FILE = "main.mp3"
OPENING_SOUND_TARGET_VOLUME = 700
OPENING_SOUND_FADE_STEP = 40
OPENING_SOUND_FADE_INTERVAL_MS = 90
DEFAULT_USERNAMES = ("Ghost", "AirWolf", "Viper", "Phoenix", "Falcon")
MAX_USERNAME_LENGTH = 20
UNLIMITED_LIVES_TEST = True 


class AirCombatGame:
    def __init__(self, root):
        self.root = root
        self.root.title("Air Combat")
        self.root.resizable(False, False)
        self.root.protocol("WM_DELETE_WINDOW", self.quit_application)

        self.asset_dir = Path(__file__).resolve().parent / "images"
        self.sound_dir = Path(__file__).resolve().parent / "sounds"
        self.records_path = Path(__file__).resolve().parent / "records.json"
        self.default_username = random.choice(DEFAULT_USERNAMES)
        self.records = self.load_records()
        self.load_assets()
        self.opening_sound_path = self.sound_dir / OPENING_SOUND_FILE
        self.opening_sound_alias = "sky_assault_opening"
        self.opening_sound_loaded = False
        self.opening_sound_volume = 0
        self.opening_sound_fade_after_id = None
        self.load_opening_sound()

        self.canvas = tk.Canvas(root, width=WIDTH, height=HEIGHT, highlightthickness=0)
        self.canvas.pack()
        self.background_id = self.canvas.create_image(WIDTH // 2, HEIGHT // 2, image=self.bg_photo)

        self.pressed_keys = set()
        self.running = True
        self.paused = False
        self.game_started = False
        self.menu_active = True
        self.round_recorded = False
        self.records_window = None
        self.records_backdrop = None
        self.records_trophy_label = None
        self.records_trophy_after_id = None
        self.records_trophy_frame_index = 0
        self.shortcuts_window = None
        self.shortcuts_backdrop = None
        self.username_window = None
        self.username_backdrop = None
        self.username_entry_var = None
        self.username = self.default_username
        self.menu_points = 0
        self.unlimited_lives_test = UNLIMITED_LIVES_TEST

        self.enemies = []
        self.bullets = []
        self.powerups = []

        self.score = 0
        self.kills = 0
        self.lives = 3
        self.level = 1
        self.next_life_reward_kills = LIFE_REWARD_KILLS

        self.spawn_interval = START_SPAWN_INTERVAL
        self.last_spawn_time = time.monotonic()
        self.last_frame_time = time.monotonic()
        self.last_player_shot = 0.0
        self.invincible_until = 0.0
        self.background_stage = 0
        self.bg_transition_active = False
        self.bg_transition_start_time = 0.0
        self.bg_transition_frame_index = 0
        self.bg_transition_frames = []
        self.bg_transition_target_stage = 0

        self.player = self.canvas.create_image(WIDTH // 2, HEIGHT - 72, image=self.player_photo)

        self.hud = self.canvas.create_text(
            14,
            12,
            anchor="nw",
            fill="#f8fafc",
            font=("Segoe UI", 15, "bold"),
            text="",
            tags=("ui",),
        )
        self.lives_icon = self.canvas.create_image(WIDTH - 110, 22, image=self.heart_hud_photo, tags=("ui",))
        self.lives_text = self.canvas.create_text(
            WIDTH - 90,
            22,
            anchor="w",
            fill="#f8fafc",
            font=("Segoe UI", 13, "bold"),
            text="xINF" if self.unlimited_lives_test else "x3",
            tags=("ui",),
        )
        self.bonus_text = self.canvas.create_text(
            WIDTH // 2,
            48,
            anchor="n",
            fill="#fde68a",
            font=("Segoe UI", 13, "bold"),
            text="",
            state="hidden",
            tags=("ui",),
        )
        self.overlay = self.canvas.create_text(
            WIDTH // 2,
            HEIGHT // 2,
            fill="#f8fafc",
            font=("Segoe UI", 30, "bold"),
            justify="center",
            text="",
            state="hidden",
            tags=("ui",),
        )
        self.create_main_menu()

        self.root.bind("<KeyPress>", self.on_key_press)
        self.root.bind("<KeyRelease>", self.on_key_release)

        self.update_hud()
        self.show_main_menu()
        self.play_opening_sound()
        self.loop()

    def apply_menu_button_visual(self, button):
        if button["pressed"]:
            button_image = self.menu_button_hover_photo
            shadow_image = self.menu_button_shadow_active_photo
            text_color = "#ffffff"
        else:
            button_image = self.menu_button_hover_photo if button["hovered"] else self.menu_button_normal_photo
            shadow_image = self.menu_button_shadow_photo
            text_color = "#ffffff" if button["hovered"] else "#f8fafc"

        self.canvas.itemconfig(button["image_id"], image=button_image)
        self.canvas.itemconfig(button["shadow_id"], image=shadow_image)
        self.canvas.itemconfig(button["text_id"], fill=text_color)

    def set_menu_button_state(self, tag, hovered):
        button = self.menu_buttons.get(tag)
        if not button:
            return

        button["hovered"] = hovered
        self.apply_menu_button_visual(button)

    def on_menu_button_enter(self, tag):
        self.set_menu_button_state(tag, True)

    def on_menu_button_leave(self, tag):
        self.set_menu_button_state(tag, False)

    def on_menu_button_press(self, tag):
        button = self.menu_buttons.get(tag)
        if not self.menu_active or not button:
            return

        button["pressed"] = True
        self.apply_menu_button_visual(button)

    def on_menu_button_release(self, tag):
        button = self.menu_buttons.get(tag)
        if not self.menu_active or not button:
            return

        was_pressed = button["pressed"]
        button["pressed"] = False
        self.apply_menu_button_visual(button)

        if was_pressed and button["hovered"]:
            button["command"]()

    def create_menu_canvas_button(self, label, center_x, center_y, command, icon_photo=None):
        index = len(self.menu_buttons)
        tag = f"menu_button_{index}"
        shadow_id = self.canvas.create_image(
            center_x,
            center_y,
            image=self.menu_button_shadow_photo,
            tags=("menu", "ui", tag),
        )
        image_id = self.canvas.create_image(
            center_x,
            center_y,
            image=self.menu_button_normal_photo,
            tags=("menu", "ui", tag),
        )
        icon_id = None
        text_x = center_x
        if icon_photo is not None:
            icon_id = self.canvas.create_image(
                center_x - MENU_BUTTON_WIDTH // 2 + 24,
                center_y,
                image=icon_photo,
                tags=("menu", "ui", tag),
            )
            text_x = center_x + 10
        text_id = self.canvas.create_text(
            text_x,
            center_y,
            text=label,
            fill="#f8fafc",
            font=("Segoe UI", 13, "bold"),
            tags=("menu", "ui", tag),
        )

        self.menu_buttons[tag] = {
            "shadow_id": shadow_id,
            "image_id": image_id,
            "text_id": text_id,
            "icon_id": icon_id,
            "command": command,
            "hovered": False,
            "pressed": False,
        }
        self.canvas.tag_bind(tag, "<Enter>", lambda _e, t=tag: self.on_menu_button_enter(t))
        self.canvas.tag_bind(tag, "<Leave>", lambda _e, t=tag: self.on_menu_button_leave(t))
        self.canvas.tag_bind(tag, "<ButtonPress-1>", lambda _e, t=tag: self.on_menu_button_press(t))
        self.canvas.tag_bind(tag, "<ButtonRelease-1>", lambda _e, t=tag: self.on_menu_button_release(t))
        return tag

    def create_main_menu(self):
        self.menu_buttons = {}
        self.menu_overlay = self.canvas.create_image(
            WIDTH // 2,
            HEIGHT // 2,
            image=self.menu_overlay_photo,
            tags=("menu", "ui"),
        )
        self.menu_plane = self.canvas.create_image(
            -80,
            175,
            image=self.enemy_photo,
            tags=("menu", "ui"),
        )
        self.canvas.tag_lower(self.menu_plane, self.menu_overlay)
        self.menu_title_glow = self.canvas.create_text(
            WIDTH // 2 + 2,
            160,
            text="AIR COMBAT",
            fill="#93c5fd",
            font=("Segoe UI Black", 46, "bold"),
            tags=("menu", "ui"),
        )
        self.menu_title_shadow = self.canvas.create_text(
            WIDTH // 2 + 2,
            164,
            text="AIR COMBAT",
            fill="#0b1220",
            font=("Segoe UI Black", 46, "bold"),
            tags=("menu", "ui"),
        )
        self.menu_title = self.canvas.create_text(
            WIDTH // 2,
            160,
            text="AIR COMBAT",
            fill="#e2e8f0",
            font=("Segoe UI Black", 46, "bold"),
            tags=("menu", "ui"),
        )
        self.menu_username_icon = self.canvas.create_image(
            20,
            20,
            anchor="nw",
            image=self.pilot_menu_photo,
            tags=("menu", "ui"),
        )
        self.menu_username_text = self.canvas.create_text(
            44,
            18,
            anchor="nw",
            text=f"Pilot: {self.username}",
            fill="#cbd5e1",
            font=("Segoe UI", 12, "bold"),
            tags=("menu", "ui"),
        )

        gap = MENU_BUTTON_HEIGHT + MENU_BUTTON_GAP
        menu_rows = 5
        total_height = menu_rows * MENU_BUTTON_HEIGHT + (menu_rows - 1) * MENU_BUTTON_GAP
        start_y = HEIGHT // 2 - (total_height // 2) + MENU_BUTTON_HEIGHT // 2 + MENU_BUTTON_VERTICAL_OFFSET
        self.menu_start_tag = self.create_menu_canvas_button(
            "START", WIDTH // 2, start_y, self.start_game_from_menu, icon_photo=self.rocket_menu_photo
        )
        self.menu_username_tag = self.create_menu_canvas_button(
            "USERNAME",
            WIDTH // 2,
            start_y + gap,
            self.show_username_window,
            icon_photo=self.pilot_menu_photo,
        )
        self.menu_records_tag = self.create_menu_canvas_button(
            "RECORDS",
            WIDTH // 2,
            start_y + gap * 2,
            self.show_records,
            icon_photo=self.trophy_menu_photo,
        )
        self.menu_shortcuts_tag = self.create_menu_canvas_button(
            "SHORTCUTS",
            WIDTH // 2,
            start_y + gap * 3,
            self.show_shortcuts,
            icon_photo=self.keyboard_menu_photo,
        )
        self.menu_quit_tag = self.create_menu_canvas_button(
            "QUIT", WIDTH // 2, start_y + gap * 4, self.quit_application, icon_photo=self.shutdown_menu_photo
        )

    def set_game_ui_visible(self, visible):
        state = "normal" if visible else "hidden"
        for item_id in (
            self.hud,
            self.lives_icon,
            self.lives_text,
        ):
            self.canvas.itemconfig(item_id, state=state)

        if not visible:
            self.canvas.itemconfig(self.bonus_text, state="hidden")
            self.canvas.itemconfig(self.overlay, state="hidden")

    def clear_dynamic_entities(self):
        for enemy in self.enemies:
            self.canvas.delete(enemy["id"])
        for bullet in self.bullets:
            self.canvas.delete(bullet["id"])
        for powerup in self.powerups:
            self.canvas.delete(powerup["id"])
        self.enemies.clear()
        self.bullets.clear()
        self.powerups.clear()

    def show_main_menu(self):
        self.menu_active = True
        self.game_started = False
        self.running = True
        self.paused = False
        self.pressed_keys.clear()
        self.close_records_window()
        self.close_shortcuts_window()
        self.close_username_window()
        self.background_stage = 0
        self.bg_transition_active = False
        self.bg_transition_start_time = 0.0
        self.bg_transition_frame_index = 0
        self.bg_transition_frames = []
        self.bg_transition_target_stage = 0
        self.menu_points = 0
        self.last_player_shot = 0.0
        self.clear_dynamic_entities()
        self.canvas.itemconfig(self.background_id, image=self.bg_day_photo)
        self.canvas.coords(self.player, WIDTH // 2, HEIGHT - 72)
        self.canvas.itemconfig(self.player, state="normal")
        self.canvas.itemconfig(self.menu_username_text, text=f"Pilot: {self.username}")
        for button in self.menu_buttons.values():
            button["hovered"] = False
            button["pressed"] = False
            self.apply_menu_button_visual(button)
        self.set_game_ui_visible(False)
        self.canvas.itemconfig("menu", state="normal")
        self.canvas.coords(self.menu_plane, -80, random.randint(140, 210))

    def hide_main_menu(self):
        self.menu_active = False
        self.canvas.itemconfig("menu", state="hidden")
        self.set_game_ui_visible(True)

    def start_game_from_menu(self):
        self.game_started = True
        self.close_username_window()
        self.unload_opening_sound()
        self.restart()
        self.hide_main_menu()

    def quit_application(self):
        self.close_records_window()
        self.close_shortcuts_window()
        self.close_username_window()
        self.unload_opening_sound()
        self.root.destroy()

    @staticmethod
    def mci_send(command):
        if not hasattr(ctypes, "windll") or not hasattr(ctypes.windll, "winmm"):
            return 1
        return ctypes.windll.winmm.mciSendStringW(command, None, 0, None)

    def cancel_opening_sound_fade(self):
        if self.opening_sound_fade_after_id is None:
            return
        try:
            self.root.after_cancel(self.opening_sound_fade_after_id)
        except tk.TclError:
            pass
        self.opening_sound_fade_after_id = None

    def set_opening_sound_volume(self, volume):
        if not self.opening_sound_loaded:
            return False

        clamped = max(0, min(1000, int(volume)))
        result = self.mci_send(f"setaudio {self.opening_sound_alias} volume to {clamped}")
        if result == 0:
            self.opening_sound_volume = clamped
            return True
        return False

    def load_opening_sound(self):
        if not hasattr(ctypes, "windll") or not hasattr(ctypes.windll, "winmm"):
            return
        if not self.opening_sound_path.exists():
            return

        sound_path = str(self.opening_sound_path).replace('"', '""')
        result = self.mci_send(f'open "{sound_path}" type mpegvideo alias {self.opening_sound_alias}')
        self.opening_sound_loaded = result == 0

    def fade_in_opening_sound_step(self):
        if not self.opening_sound_loaded:
            self.opening_sound_fade_after_id = None
            return

        if self.opening_sound_volume >= OPENING_SOUND_TARGET_VOLUME:
            self.opening_sound_fade_after_id = None
            return

        next_volume = min(OPENING_SOUND_TARGET_VOLUME, self.opening_sound_volume + OPENING_SOUND_FADE_STEP)
        if not self.set_opening_sound_volume(next_volume):
            self.opening_sound_fade_after_id = None
            return

        self.opening_sound_fade_after_id = self.root.after(
            OPENING_SOUND_FADE_INTERVAL_MS, self.fade_in_opening_sound_step
        )

    def play_opening_sound(self):
        if not self.opening_sound_loaded:
            return
        self.cancel_opening_sound_fade()
        self.mci_send(f"seek {self.opening_sound_alias} to start")
        self.set_opening_sound_volume(0)
        self.mci_send(f"play {self.opening_sound_alias} repeat")
        self.fade_in_opening_sound_step()

    def unload_opening_sound(self):
        self.cancel_opening_sound_fade()
        if not self.opening_sound_loaded:
            return
        self.mci_send(f"stop {self.opening_sound_alias}")
        self.mci_send(f"close {self.opening_sound_alias}")
        self.opening_sound_loaded = False
        self.opening_sound_volume = 0

    def update_menu_animation(self, dt):
        if not self.menu_active:
            return

        self.canvas.move(self.menu_plane, MENU_PLANE_SPEED * dt, 0)
        coords = self.canvas.coords(self.menu_plane)
        if coords and coords[0] > WIDTH + 80:
            self.canvas.coords(self.menu_plane, -80, random.randint(140, 210))

    def load_assets(self):
        if Image is None or ImageTk is None or ImageDraw is None or ImageFilter is None:
            raise RuntimeError("Pillow is required. Install it with: pip install pillow")

        files = {
            "player": "my aircraft.png",
            "enemy": "enemy.png",
            "enemy2": "enemy2.png",
            "bullet": "bullet.jpg",
            "background": "bg.jpg",
            "dark_background": "dark.jpg",
            "snow_background": "snow.jpg",
            "heart": "heart.png",
            "trophy": "trophy.png",
            "rocket": "rocket.png",
            "pilot": "pilot.png",
            "keyboard": "keyboard.png",
            "reset": "reset.png",
            "shutdown": "shutdown.png",
        }
        missing = [name for name in files.values() if not (self.asset_dir / name).exists()]
        if missing:
            raise RuntimeError(f"Missing asset files: {', '.join(missing)}")

        resample = Image.Resampling.LANCZOS if hasattr(Image, "Resampling") else Image.LANCZOS

        with Image.open(self.asset_dir / files["background"]) as img:
            bg_day = img.convert("RGB").resize((WIDTH, HEIGHT), resample)

        with Image.open(self.asset_dir / files["dark_background"]) as img:
            bg_dark = img.convert("RGB").resize((WIDTH, HEIGHT), resample)

        with Image.open(self.asset_dir / files["snow_background"]) as img:
            bg_snow = img.convert("RGB").resize((WIDTH, HEIGHT), resample)

        with Image.open(self.asset_dir / files["player"]) as img:
            player = img.convert("RGBA").resize((78, 78), resample)

        with Image.open(self.asset_dir / files["enemy"]) as img:
            enemy = img.convert("RGBA").rotate(180).resize((66, 66), resample)

        with Image.open(self.asset_dir / files["enemy2"]) as img:
            enemy2 = img.convert("RGBA").rotate(180).resize((66, 66), resample)

        with Image.open(self.asset_dir / files["bullet"]) as img:
            bullet_base = self.make_white_transparent(img.convert("RGBA"))
            bullet_base = bullet_base.resize((20, 30), resample)

            # Keep player and enemy bullets visually opposite.
            player_bullet = self.tint_with_alpha(bullet_base.rotate(180), (125, 211, 252))
            enemy_bullet = self.tint_with_alpha(bullet_base, (251, 113, 133))

        with Image.open(self.asset_dir / files["heart"]) as img:
            heart_base = self.make_white_transparent(img.convert("RGBA"))
            heart_hud = heart_base.resize((20, 20), resample)
            heart_drop = heart_base.resize((28, 28), resample)

        with Image.open(self.asset_dir / files["trophy"]) as img:
            trophy_base = self.make_white_transparent(img.convert("RGBA"))
            trophy_menu = trophy_base.resize((TROPHY_MENU_SIZE, TROPHY_MENU_SIZE), resample)
            trophy_ui = trophy_base.resize((TROPHY_UI_SIZE, TROPHY_UI_SIZE), resample)
            trophy_records = trophy_base.resize((TROPHY_RECORDS_SIZE, TROPHY_RECORDS_SIZE), resample)
            trophy_pulse_sizes = list(range(TROPHY_PULSE_MIN, TROPHY_PULSE_MAX + 1, TROPHY_PULSE_STEP))
            trophy_pulse_sizes += list(range(TROPHY_PULSE_MAX - TROPHY_PULSE_STEP, TROPHY_PULSE_MIN, -TROPHY_PULSE_STEP))
            trophy_records_pulse = [trophy_base.resize((size, size), resample) for size in trophy_pulse_sizes]

        with Image.open(self.asset_dir / files["rocket"]) as img:
            rocket_icon = self.make_white_transparent(img.convert("RGBA")).resize(
                (TROPHY_MENU_SIZE, TROPHY_MENU_SIZE), resample
            )

        with Image.open(self.asset_dir / files["pilot"]) as img:
            pilot_base = self.make_white_transparent(img.convert("RGBA")).resize(
                (TROPHY_MENU_SIZE, TROPHY_MENU_SIZE), resample
            )
            pilot_icon = self.tint_with_alpha(pilot_base, (226, 232, 240))

        with Image.open(self.asset_dir / files["keyboard"]) as img:
            keyboard_base = self.make_white_transparent(img.convert("RGBA")).resize(
                (TROPHY_MENU_SIZE, TROPHY_MENU_SIZE), resample
            )
            keyboard_icon = self.tint_with_alpha(keyboard_base, (226, 232, 240))

        with Image.open(self.asset_dir / files["reset"]) as img:
            reset_base = self.make_white_transparent(img.convert("RGBA")).resize(
                (TROPHY_MENU_SIZE, TROPHY_MENU_SIZE), resample
            )
            reset_icon = self.tint_with_alpha(reset_base, (248, 113, 113))

        with Image.open(self.asset_dir / files["shutdown"]) as img:
            shutdown_icon = self.make_white_transparent(img.convert("RGBA")).resize(
                (TROPHY_MENU_SIZE, TROPHY_MENU_SIZE), resample
            )

        menu_overlay = Image.new("RGBA", (WIDTH, HEIGHT), (0, 0, 0, 153))
        menu_button_normal = self.build_gradient_rounded_panel(
            width=MENU_BUTTON_WIDTH,
            height=MENU_BUTTON_HEIGHT,
            radius=MENU_BUTTON_RADIUS,
            top_rgba=(30, 41, 59, 245),   # #1e293b base
            bottom_rgba=(27, 38, 55, 245),
            outline_rgba=(100, 116, 139, 220),
            outline_width=2,
        )
        menu_button_hover = self.build_gradient_rounded_panel(
            width=MENU_BUTTON_WIDTH,
            height=MENU_BUTTON_HEIGHT,
            radius=MENU_BUTTON_RADIUS,
            top_rgba=(51, 65, 85, 250),   # #334155 hover
            bottom_rgba=(45, 59, 78, 250),
            outline_rgba=(148, 163, 184, 235),
            outline_width=2,
        )
        menu_button_shadow = self.build_shadow_panel(
            width=MENU_BUTTON_WIDTH,
            height=MENU_BUTTON_HEIGHT,
            radius=MENU_BUTTON_RADIUS,
            offset_x=MENU_SHADOW_OFFSET,
            offset_y=MENU_SHADOW_OFFSET,
            blur_radius=MENU_SHADOW_BLUR,
            alpha=MENU_SHADOW_ALPHA,
        )
        menu_button_shadow_active = self.build_shadow_panel(
            width=MENU_BUTTON_WIDTH,
            height=MENU_BUTTON_HEIGHT,
            radius=MENU_BUTTON_RADIUS,
            offset_x=MENU_SHADOW_ACTIVE_OFFSET,
            offset_y=MENU_SHADOW_ACTIVE_OFFSET,
            blur_radius=MENU_SHADOW_ACTIVE_BLUR,
            alpha=MENU_SHADOW_ACTIVE_ALPHA,
        )
        self.bg_day_to_dark_photos = []
        for frame in range(BG_TRANSITION_FRAMES + 1):
            alpha = frame / BG_TRANSITION_FRAMES
            self.bg_day_to_dark_photos.append(ImageTk.PhotoImage(Image.blend(bg_day, bg_dark, alpha)))

        self.bg_dark_to_snow_photos = []
        for frame in range(BG_TRANSITION_FRAMES + 1):
            alpha = frame / BG_TRANSITION_FRAMES
            self.bg_dark_to_snow_photos.append(ImageTk.PhotoImage(Image.blend(bg_dark, bg_snow, alpha)))

        self.bg_day_photo = self.bg_day_to_dark_photos[0]
        self.bg_dark_photo = self.bg_day_to_dark_photos[-1]
        self.bg_snow_photo = self.bg_dark_to_snow_photos[-1]
        self.bg_photo = self.bg_day_photo
        self.player_photo = ImageTk.PhotoImage(player)
        self.enemy_photo = ImageTk.PhotoImage(enemy)
        self.enemy2_photo = ImageTk.PhotoImage(enemy2)
        self.player_bullet_photo = ImageTk.PhotoImage(player_bullet)
        self.enemy_bullet_photo = ImageTk.PhotoImage(enemy_bullet)
        self.heart_hud_photo = ImageTk.PhotoImage(heart_hud)
        self.heart_drop_photo = ImageTk.PhotoImage(heart_drop)
        self.trophy_menu_photo = ImageTk.PhotoImage(trophy_menu)
        self.trophy_ui_photo = ImageTk.PhotoImage(trophy_ui)
        self.trophy_records_photo = ImageTk.PhotoImage(trophy_records)
        self.trophy_records_pulse_photos = [ImageTk.PhotoImage(img) for img in trophy_records_pulse]
        self.rocket_menu_photo = ImageTk.PhotoImage(rocket_icon)
        self.pilot_menu_photo = ImageTk.PhotoImage(pilot_icon)
        self.keyboard_menu_photo = ImageTk.PhotoImage(keyboard_icon)
        self.reset_menu_photo = ImageTk.PhotoImage(reset_icon)
        self.shutdown_menu_photo = ImageTk.PhotoImage(shutdown_icon)
        self.menu_overlay_photo = ImageTk.PhotoImage(menu_overlay)
        self.menu_button_normal_photo = ImageTk.PhotoImage(menu_button_normal)
        self.menu_button_hover_photo = ImageTk.PhotoImage(menu_button_hover)
        self.menu_button_shadow_photo = ImageTk.PhotoImage(menu_button_shadow)
        self.menu_button_shadow_active_photo = ImageTk.PhotoImage(menu_button_shadow_active)

    @staticmethod
    def make_white_transparent(img, threshold=238):
        px = img.load()
        width, height = img.size
        for y in range(height):
            for x in range(width):
                r, g, b, a = px[x, y]
                if r >= threshold and g >= threshold and b >= threshold:
                    px[x, y] = (r, g, b, 0)
                else:
                    px[x, y] = (r, g, b, a)
        return img

    @staticmethod
    def tint_with_alpha(img, color):
        r, g, b = color
        alpha = img.split()[-1]
        tinted = Image.new("RGBA", img.size, (r, g, b, 255))
        tinted.putalpha(alpha)
        return tinted

    @staticmethod
    def build_rounded_panel(width, height, radius, fill_rgba, outline_rgba, outline_width=2):
        panel = Image.new("RGBA", (width, height), (0, 0, 0, 0))
        draw = ImageDraw.Draw(panel)
        draw.rounded_rectangle(
            [0, 0, width - 1, height - 1],
            radius=radius,
            fill=fill_rgba,
            outline=outline_rgba,
            width=outline_width,
        )
        return panel

    @staticmethod
    def build_gradient_rounded_panel(
        width,
        height,
        radius,
        top_rgba,
        bottom_rgba,
        outline_rgba,
        outline_width=2,
    ):
        panel = Image.new("RGBA", (width, height), (0, 0, 0, 0))
        gradient = Image.new("RGBA", (width, height), (0, 0, 0, 0))
        grad_draw = ImageDraw.Draw(gradient)

        for y in range(height):
            t = y / max(1, height - 1)
            color = tuple(int(top_rgba[i] + (bottom_rgba[i] - top_rgba[i]) * t) for i in range(4))
            grad_draw.line([(0, y), (width, y)], fill=color)

        mask = Image.new("L", (width, height), 0)
        mask_draw = ImageDraw.Draw(mask)
        mask_draw.rounded_rectangle([0, 0, width - 1, height - 1], radius=radius, fill=255)

        panel.paste(gradient, (0, 0), mask)
        draw = ImageDraw.Draw(panel)
        draw.rounded_rectangle(
            [0, 0, width - 1, height - 1],
            radius=radius,
            outline=outline_rgba,
            width=outline_width,
        )
        return panel

    @staticmethod
    def build_shadow_panel(width, height, radius, offset_x, offset_y, blur_radius, alpha):
        pad = blur_radius * 3 + max(abs(offset_x), abs(offset_y)) + 2
        shadow_w = width + pad * 2
        shadow_h = height + pad * 2

        shadow = Image.new("RGBA", (shadow_w, shadow_h), (0, 0, 0, 0))
        draw = ImageDraw.Draw(shadow)
        draw.rounded_rectangle(
            [
                pad + offset_x,
                pad + offset_y,
                pad + offset_x + width - 1,
                pad + offset_y + height - 1,
            ],
            radius=radius,
            fill=(0, 0, 0, alpha),
        )

        if blur_radius > 0:
            shadow = shadow.filter(ImageFilter.GaussianBlur(blur_radius))
        return shadow

    def on_key_press(self, event):
        key = event.keysym.lower()

        if self.username_window is not None and self.username_window.winfo_exists():
            if key == "escape":
                self.close_username_window()
            return

        if self.menu_active:
            if key == "return":
                self.start_game_from_menu()
                return
            if key == "u":
                self.show_username_window()
                return
            if key in ("k", "h"):
                self.show_shortcuts()
                return
            if key == "escape":
                self.quit_application()
                return
            if key in ("w", "a", "s", "d", "up", "down", "left", "right", "space"):
                self.pressed_keys.add(key)
            return

        if key in ("r", "return") and not self.running:
            self.restart()
            return
        if key == "m" and self.game_started:
            self.show_main_menu()
            return
        if key == "p" and self.running and self.game_started:
            self.toggle_pause()
            return
        if self.running and self.game_started and not self.paused:
            self.pressed_keys.add(key)

    def on_key_release(self, event):
        self.pressed_keys.discard(event.keysym.lower())

    def toggle_pause(self):
        if not self.running:
            return

        self.paused = not self.paused
        self.pressed_keys.clear()

        if self.paused:
            self.canvas.itemconfig(self.overlay, text="Paused", state="normal")
        else:
            self.canvas.itemconfig(self.overlay, state="hidden")

    def start_new_game(self):
        self.record_current_run()
        self.restart()

    def show_shortcuts(self):
        if self.shortcuts_window is not None and self.shortcuts_window.winfo_exists():
            self.shortcuts_window.lift()
            self.shortcuts_window.focus_set()
            return

        self.root.update_idletasks()
        root_x = self.root.winfo_rootx()
        root_y = self.root.winfo_rooty()
        root_w = self.root.winfo_width()
        root_h = self.root.winfo_height()

        self.shortcuts_backdrop = tk.Toplevel(self.root)
        self.shortcuts_backdrop.overrideredirect(True)
        self.shortcuts_backdrop.geometry(f"{root_w}x{root_h}+{root_x}+{root_y}")
        self.shortcuts_backdrop.configure(bg="#000000")
        try:
            self.shortcuts_backdrop.attributes("-alpha", 0.55)
        except tk.TclError:
            pass
        self.shortcuts_backdrop.transient(self.root)
        self.shortcuts_backdrop.lift()

        self.shortcuts_window = tk.Toplevel(self.root)
        self.shortcuts_window.title("Air Combat Keyboard Shortcuts")
        self.shortcuts_window.configure(bg="#0f172a")
        self.shortcuts_window.resizable(False, False)

        width, height = 420, 300
        win_x = root_x + max(0, (root_w - width) // 2)
        win_y = root_y + max(0, (root_h - height) // 2)
        self.shortcuts_window.geometry(f"{width}x{height}+{win_x}+{win_y}")
        self.shortcuts_window.transient(self.root)
        self.shortcuts_window.lift()
        self.shortcuts_window.grab_set()
        self.shortcuts_window.protocol("WM_DELETE_WINDOW", self.close_shortcuts_window)
        self.shortcuts_window.bind("<Escape>", lambda _e: self.close_shortcuts_window())

        outer = tk.Frame(self.shortcuts_window, bg="#0f172a", padx=24, pady=20)
        outer.pack(fill="both", expand=True)

        title = tk.Label(
            outer,
            text="KEYBOARD SHORTCUTS",
            bg="#0f172a",
            fg="#e2e8f0",
            font=("Segoe UI", 18, "bold"),
        )
        title.pack(anchor="w")

        separator = tk.Frame(outer, height=2, bg="#334155")
        separator.pack(fill="x", pady=(10, 14))

        panel = tk.Frame(
            outer,
            bg="#111827",
            highlightthickness=1,
            highlightbackground="#334155",
            padx=16,
            pady=14,
        )
        panel.pack(fill="both", expand=True)

        controls = [
            ("Move", "W/A/S/D or Arrow Keys"),
            ("Fire", "Space"),
            ("Pause", "P"),
            ("Restart (after game over)", "R or Enter"),
            ("Main Menu", "M"),
        ]
        for action, keys in controls:
            row = tk.Frame(panel, bg="#111827")
            row.pack(fill="x", pady=4)
            tk.Label(
                row,
                text=action,
                width=22,
                anchor="w",
                bg="#111827",
                fg="#cbd5e1",
                font=("Segoe UI", 10, "bold"),
            ).pack(side="left")
            tk.Label(
                row,
                text=keys,
                anchor="w",
                bg="#111827",
                fg="#e2e8f0",
                font=("Segoe UI", 10),
            ).pack(side="left")

        close_btn = tk.Button(
            outer,
            text="Close",
            command=self.close_shortcuts_window,
            font=("Segoe UI", 10, "bold"),
            bg="#1e293b",
            fg="#e2e8f0",
            activebackground="#334155",
            activeforeground="#f8fafc",
            relief="flat",
            bd=0,
            padx=14,
            pady=6,
            highlightthickness=0,
            takefocus=False,
            cursor="hand2",
        )
        close_btn.pack(anchor="e", pady=(14, 0))

    def close_shortcuts_window(self):
        if self.shortcuts_window is not None:
            try:
                self.shortcuts_window.grab_release()
            except tk.TclError:
                pass
            try:
                self.shortcuts_window.destroy()
            except tk.TclError:
                pass
            self.shortcuts_window = None

        if self.shortcuts_backdrop is not None:
            try:
                self.shortcuts_backdrop.destroy()
            except tk.TclError:
                pass
            self.shortcuts_backdrop = None

    def normalize_username(self, value):
        name = str(value).strip() if value is not None else ""
        if not name:
            name = self.default_username
        return name[:MAX_USERNAME_LENGTH]

    def show_username_window(self):
        if self.username_window is not None and self.username_window.winfo_exists():
            self.username_window.lift()
            self.username_window.focus_set()
            return

        self.root.update_idletasks()
        root_x = self.root.winfo_rootx()
        root_y = self.root.winfo_rooty()
        root_w = self.root.winfo_width()
        root_h = self.root.winfo_height()

        self.username_backdrop = tk.Toplevel(self.root)
        self.username_backdrop.overrideredirect(True)
        self.username_backdrop.geometry(f"{root_w}x{root_h}+{root_x}+{root_y}")
        self.username_backdrop.configure(bg="#000000")
        try:
            self.username_backdrop.attributes("-alpha", 0.55)
        except tk.TclError:
            pass
        self.username_backdrop.transient(self.root)
        self.username_backdrop.lift()

        self.username_window = tk.Toplevel(self.root)
        self.username_window.title("Air Combat Username")
        self.username_window.configure(bg="#0f172a")
        self.username_window.resizable(False, False)

        width, height = 420, 210
        win_x = root_x + max(0, (root_w - width) // 2)
        win_y = root_y + max(0, (root_h - height) // 2)
        self.username_window.geometry(f"{width}x{height}+{win_x}+{win_y}")
        self.username_window.transient(self.root)
        self.username_window.lift()
        self.username_window.grab_set()
        self.username_window.protocol("WM_DELETE_WINDOW", self.close_username_window)
        self.username_window.bind("<Escape>", lambda _e: self.close_username_window())

        outer = tk.Frame(self.username_window, bg="#0f172a", padx=24, pady=18)
        outer.pack(fill="both", expand=True)

        tk.Label(
            outer,
            text="PILOT USERNAME",
            bg="#0f172a",
            fg="#e2e8f0",
            font=("Segoe UI", 16, "bold"),
        ).pack(anchor="w")

        tk.Label(
            outer,
            text=f"Max {MAX_USERNAME_LENGTH} characters",
            bg="#0f172a",
            fg="#94a3b8",
            font=("Segoe UI", 10),
        ).pack(anchor="w", pady=(4, 10))

        self.username_entry_var = tk.StringVar(value=self.username)
        entry = tk.Entry(
            outer,
            textvariable=self.username_entry_var,
            font=("Segoe UI", 12),
            bg="#111827",
            fg="#f8fafc",
            insertbackground="#f8fafc",
            relief="flat",
            bd=0,
            highlightthickness=1,
            highlightbackground="#334155",
            highlightcolor="#64748b",
        )
        entry.pack(fill="x", pady=(0, 14), ipady=7)
        entry.focus_set()
        entry.select_range(0, "end")
        self.username_window.bind("<Return>", lambda _e: self.apply_username_from_entry())

        actions = tk.Frame(outer, bg="#0f172a")
        actions.pack(fill="x")

        cancel_btn = tk.Button(
            actions,
            text="Cancel",
            command=self.close_username_window,
            font=("Segoe UI", 10, "bold"),
            bg="#1f2937",
            fg="#cbd5e1",
            activebackground="#334155",
            activeforeground="#f8fafc",
            relief="flat",
            bd=0,
            padx=12,
            pady=6,
            highlightthickness=0,
            takefocus=False,
            cursor="hand2",
        )
        cancel_btn.pack(side="right")

        save_btn = tk.Button(
            actions,
            text="Save",
            command=self.apply_username_from_entry,
            font=("Segoe UI", 10, "bold"),
            bg="#1e293b",
            fg="#e2e8f0",
            activebackground="#334155",
            activeforeground="#f8fafc",
            relief="flat",
            bd=0,
            padx=12,
            pady=6,
            highlightthickness=0,
            takefocus=False,
            cursor="hand2",
        )
        save_btn.pack(side="right", padx=(0, 10))

    def apply_username_from_entry(self):
        if self.username_entry_var is None:
            return

        self.username = self.normalize_username(self.username_entry_var.get())
        self.canvas.itemconfig(self.menu_username_text, text=f"Pilot: {self.username}")
        self.close_username_window()

    def close_username_window(self):
        if self.username_window is not None:
            try:
                self.username_window.grab_release()
            except tk.TclError:
                pass
            try:
                self.username_window.destroy()
            except tk.TclError:
                pass
            self.username_window = None

        self.username_entry_var = None

        if self.username_backdrop is not None:
            try:
                self.username_backdrop.destroy()
            except tk.TclError:
                pass
            self.username_backdrop = None

    def load_records(self):
        if not self.records_path.exists():
            return []
        try:
            raw = json.loads(self.records_path.read_text(encoding="utf-8"))
        except (json.JSONDecodeError, OSError):
            return []

        if not isinstance(raw, list):
            return []

        cleaned = []
        for item in raw:
            if not isinstance(item, dict):
                continue
            try:
                cleaned.append(
                    {
                        "username": self.normalize_username(item.get("username", DEFAULT_USERNAMES[0])),
                        "score": int(item.get("score", 0)),
                        "kills": int(item.get("kills", 0)),
                        "level": int(item.get("level", 1)),
                        "played_at": str(item.get("played_at", "Unknown")),
                    }
                )
            except (TypeError, ValueError):
                continue

        cleaned.sort(key=lambda entry: (entry["score"], entry["kills"], entry["level"]), reverse=True)
        return cleaned[:RECORD_LIMIT]

    def save_records(self):
        try:
            self.records_path.write_text(json.dumps(self.records, indent=2), encoding="utf-8")
        except OSError:
            pass

    def reset_records(self):
        if not self.records:
            messagebox.showinfo("Air Combat Records", "No records to reset.")
            return

        confirm = messagebox.askyesno(
            "Air Combat Records",
            "Reset all saved records? This cannot be undone.",
            icon="warning",
        )
        if not confirm:
            return

        self.records = []
        self.save_records()

        if self.records_window is not None and self.records_window.winfo_exists():
            self.close_records_window()
            self.show_records()

    def record_current_run(self):
        if self.round_recorded:
            return

        self.round_recorded = True
        if self.score <= 0 and self.kills <= 0:
            return

        entry = {
            "username": self.username,
            "score": self.score,
            "kills": self.kills,
            "level": self.level,
            "played_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        }
        self.records.append(entry)
        self.records.sort(key=lambda row: (row["score"], row["kills"], row["level"]), reverse=True)
        self.records = self.records[:RECORD_LIMIT]
        self.save_records()

    def show_records(self):
        if self.records_window is not None and self.records_window.winfo_exists():
            self.records_window.lift()
            self.records_window.focus_set()
            return

        self.root.update_idletasks()
        root_x = self.root.winfo_rootx()
        root_y = self.root.winfo_rooty()
        root_w = self.root.winfo_width()
        root_h = self.root.winfo_height()

        self.records_backdrop = tk.Toplevel(self.root)
        self.records_backdrop.overrideredirect(True)
        self.records_backdrop.geometry(f"{root_w}x{root_h}+{root_x}+{root_y}")
        self.records_backdrop.configure(bg="#000000")
        try:
            self.records_backdrop.attributes("-alpha", 0.6)
        except tk.TclError:
            pass
        self.records_backdrop.transient(self.root)
        self.records_backdrop.lift()

        self.records_window = tk.Toplevel(self.root)
        self.records_window.title("🏆 Air Combat Records")
        self.records_window.configure(bg="#0f172a")
        self.records_window.resizable(False, False)

        width, height = 700, 540
        win_x = root_x + max(0, (root_w - width) // 2)
        win_y = root_y + max(0, (root_h - height) // 2)
        self.records_window.geometry(f"{width}x{height}+{win_x}+{win_y}")
        self.records_window.transient(self.root)
        self.records_window.lift()
        self.records_window.grab_set()
        self.records_window.protocol("WM_DELETE_WINDOW", self.close_records_window)
        self.records_window.bind("<Escape>", lambda _e: self.close_records_window())

        outer = tk.Frame(self.records_window, bg="#0f172a", padx=24, pady=18)
        outer.pack(fill="both", expand=True)

        header = tk.Frame(outer, bg="#0f172a")
        header.pack(fill="x", pady=(0, 10))

        self.records_trophy_label = tk.Label(
            header,
            image=self.trophy_records_photo,
            bg="#0f172a",
            width=48,
            height=48,
        )
        self.records_trophy_label.pack(pady=(2, 6))

        title = tk.Label(
            header,
            text="TOP 10 PILOTS",
            bg="#0f172a",
            fg="#e2e8f0",
            font=("Segoe UI", 20, "bold"),
        )
        title.pack()

        separator = tk.Frame(outer, height=2, bg="#334155")
        separator.pack(fill="x", pady=(8, 12))

        actions = tk.Frame(outer, bg="#0f172a")
        actions.pack(side="bottom", fill="x", pady=(12, 0))

        panel = tk.Frame(
            outer,
            bg="#111827",
            highlightthickness=1,
            highlightbackground="#334155",
            padx=12,
            pady=10,
        )
        panel.pack(fill="both", expand=True)

        if not self.records:
            empty = tk.Label(
                panel,
                text="No records yet.\nFinish a game to create one.",
                bg="#111827",
                fg="#94a3b8",
                font=("Segoe UI", 14, "bold"),
                justify="center",
            )
            empty.pack(expand=True)
        else:
            header = tk.Frame(panel, bg="#111827")
            header.pack(fill="x", pady=(0, 8))
            tk.Label(
                header,
                text="Rank",
                width=6,
                anchor="w",
                bg="#111827",
                fg="#cbd5e1",
                font=("Segoe UI", 10, "bold"),
            ).pack(side="left")
            tk.Label(
                header,
                text="User",
                width=16,
                anchor="w",
                bg="#111827",
                fg="#cbd5e1",
                font=("Segoe UI", 10, "bold"),
            ).pack(side="left")
            tk.Label(
                header,
                text="Score",
                width=10,
                anchor="w",
                bg="#111827",
                fg="#cbd5e1",
                font=("Segoe UI", 10, "bold"),
            ).pack(side="left")
            tk.Label(
                header,
                text="Kills",
                width=9,
                anchor="w",
                bg="#111827",
                fg="#cbd5e1",
                font=("Segoe UI", 10, "bold"),
            ).pack(side="left")
            tk.Label(
                header,
                text="Level",
                width=8,
                anchor="w",
                bg="#111827",
                fg="#cbd5e1",
                font=("Segoe UI", 10, "bold"),
            ).pack(side="left")
            tk.Label(
                header,
                text="Played At",
                anchor="w",
                bg="#111827",
                fg="#cbd5e1",
                font=("Segoe UI", 10, "bold"),
            ).pack(side="left")

            divider = tk.Frame(panel, height=1, bg="#334155")
            divider.pack(fill="x", pady=(0, 4))

            for index, record in enumerate(self.records, start=1):
                row_bg = "#0f172a" if index % 2 == 0 else "#111827"
                row = tk.Frame(panel, bg=row_bg)
                row.pack(fill="x", pady=2)

                rank_text = f"#{index}"
                if index == 1:
                    rank_text = "🥇 #1"
                elif index == 2:
                    rank_text = "🥈 #2"
                elif index == 3:
                    rank_text = "🥉 #3"

                tk.Label(
                    row,
                    text=rank_text,
                    width=6,
                    anchor="w",
                    bg=row_bg,
                    fg="#f8fafc",
                    font=("Segoe UI", 10, "bold"),
                ).pack(side="left")
                tk.Label(
                    row,
                    text=record["username"],
                    width=16,
                    anchor="w",
                    bg=row_bg,
                    fg="#e2e8f0",
                    font=("Segoe UI", 10),
                ).pack(side="left")
                tk.Label(
                    row,
                    text=str(record["score"]),
                    width=10,
                    anchor="w",
                    bg=row_bg,
                    fg="#e2e8f0",
                    font=("Segoe UI", 10),
                ).pack(side="left")
                tk.Label(
                    row,
                    text=str(record["kills"]),
                    width=9,
                    anchor="w",
                    bg=row_bg,
                    fg="#e2e8f0",
                    font=("Segoe UI", 10),
                ).pack(side="left")
                tk.Label(
                    row,
                    text=str(record["level"]),
                    width=8,
                    anchor="w",
                    bg=row_bg,
                    fg="#e2e8f0",
                    font=("Segoe UI", 10),
                ).pack(side="left")
                tk.Label(
                    row,
                    text=record["played_at"],
                    anchor="w",
                    bg=row_bg,
                    fg="#94a3b8",
                    font=("Segoe UI", 10),
                ).pack(side="left")

        reset_btn = tk.Button(
            actions,
            text="Reset Records",
            image=self.reset_menu_photo,
            compound="left",
            command=self.reset_records,
            font=("Segoe UI", 10, "bold"),
            bg="#3f1d22",
            fg="#fecaca",
            activebackground="#7f1d1d",
            activeforeground="#fee2e2",
            relief="flat",
            bd=0,
            padx=12,
            pady=6,
            highlightthickness=0,
            takefocus=False,
            cursor="hand2",
        )
        reset_btn.pack(side="left")

        close_btn = tk.Button(
            actions,
            text="Close",
            command=self.close_records_window,
            font=("Segoe UI", 10, "bold"),
            bg="#1e293b",
            fg="#e2e8f0",
            activebackground="#334155",
            activeforeground="#f8fafc",
            relief="flat",
            bd=0,
            padx=14,
            pady=6,
            highlightthickness=0,
            takefocus=False,
            cursor="hand2",
        )
        close_btn.pack(side="right")

        self.records_trophy_frame_index = 0
        self.animate_records_trophy()

    def animate_records_trophy(self):
        if self.records_window is None or not self.records_window.winfo_exists():
            return
        if self.records_trophy_label is None or not self.records_trophy_label.winfo_exists():
            return
        if not self.trophy_records_pulse_photos:
            return

        photo = self.trophy_records_pulse_photos[self.records_trophy_frame_index]
        self.records_trophy_label.configure(image=photo)
        self.records_trophy_frame_index = (self.records_trophy_frame_index + 1) % len(
            self.trophy_records_pulse_photos
        )
        self.records_trophy_after_id = self.records_window.after(120, self.animate_records_trophy)

    def close_records_window(self):
        if self.records_trophy_after_id is not None and self.records_window is not None:
            try:
                self.records_window.after_cancel(self.records_trophy_after_id)
            except tk.TclError:
                pass
        self.records_trophy_after_id = None
        self.records_trophy_label = None

        if self.records_window is not None:
            try:
                self.records_window.grab_release()
            except tk.TclError:
                pass
            try:
                self.records_window.destroy()
            except tk.TclError:
                pass
            self.records_window = None

        if self.records_backdrop is not None:
            try:
                self.records_backdrop.destroy()
            except tk.TclError:
                pass
            self.records_backdrop = None

    def loop(self):
        now = time.monotonic()
        dt = min(now - self.last_frame_time, 0.045)
        self.last_frame_time = now
        self.update_background_transition(now)

        if self.menu_active:
            self.update_menu_animation(dt)
            self.update_player(dt)
            self.handle_player_fire(now)
            self.update_bullets(dt)
            self.check_menu_collisions()
        elif self.running and not self.paused:
            self.update_player(dt)
            self.handle_player_fire(now)
            self.spawn_enemy(now)
            self.update_enemies(dt, now)
            self.update_bullets(dt)
            self.update_powerups(dt)
            self.check_collisions(now)
            self.update_difficulty()
            self.update_hud()

        self.canvas.tag_raise("ui")
        self.root.after(int(1000 / FPS), self.loop)

    def check_menu_collisions(self):
        plane_box = self.canvas.bbox(self.menu_plane)
        if not plane_box:
            return

        for bullet in list(self.bullets):
            if bullet["owner"] != "player":
                continue

            bullet_box = self.canvas.bbox(bullet["id"])
            if not bullet_box or not self.overlaps(bullet_box, plane_box):
                continue

            self.canvas.delete(bullet["id"])
            self.bullets.remove(bullet)
            self.menu_points += 1
            self.canvas.coords(self.menu_plane, -80, random.randint(140, 210))
            break

    def update_player(self, dt):
        left = "a" in self.pressed_keys or "left" in self.pressed_keys
        right = "d" in self.pressed_keys or "right" in self.pressed_keys
        up = "w" in self.pressed_keys or "up" in self.pressed_keys
        down = "s" in self.pressed_keys or "down" in self.pressed_keys

        dx = (1 if right else 0) - (1 if left else 0)
        dy = (1 if down else 0) - (1 if up else 0)
        if dx == 0 and dy == 0:
            return

        if dx != 0 and dy != 0:
            dx *= 0.7071
            dy *= 0.7071

        move_x = dx * PLAYER_SPEED * dt
        move_y = dy * PLAYER_SPEED * dt

        current_x, current_y = self.canvas.coords(self.player)
        box = self.canvas.bbox(self.player)
        if not box:
            return

        half_w = (box[2] - box[0]) / 2
        half_h = (box[3] - box[1]) / 2

        next_x = max(half_w + 8, min(WIDTH - half_w - 8, current_x + move_x))
        next_y = max(half_h + 40, min(HEIGHT - half_h - 8, current_y + move_y))
        self.canvas.coords(self.player, next_x, next_y)

    def handle_player_fire(self, now):
        if "space" not in self.pressed_keys:
            return

        fire_interval = max(0.09, PLAYER_FIRE_INTERVAL - (self.level - 1) * 0.007)
        if now - self.last_player_shot < fire_interval:
            return

        self.last_player_shot = now
        px, py = self.canvas.coords(self.player)
        offsets = (-14, 14) if self.level >= 3 else (0,)

        for offset in offsets:
            bullet = self.canvas.create_image(
                px + offset,
                py - 30,
                image=self.player_bullet_photo,
            )
            self.bullets.append({"id": bullet, "owner": "player", "vy": PLAYER_BULLET_SPEED})

    def spawn_enemy(self, now):
        if now - self.last_spawn_time < self.spawn_interval:
            return
        self.last_spawn_time = now

        x = random.randint(42, WIDTH - 42)
        y = -36
        enemy_sprite = self.enemy2_photo if self.kills >= ENEMY_SWAP_KILLS else self.enemy_photo
        enemy_id = self.canvas.create_image(x, y, image=enemy_sprite)

        speed = random.uniform(ENEMY_BASE_SPEED + self.level * 12, ENEMY_BASE_SPEED + self.level * 22)
        vx = random.uniform(-95, 95)
        delay = random.uniform(max(0.42, 1.35 - self.level * 0.07), 1.85)
        hp = 2 if random.random() < min(0.45, self.level * 0.06) else 1

        self.enemies.append(
            {
                "id": enemy_id,
                "speed": speed,
                "vx": vx,
                "next_shot": now + random.uniform(0.5, 1.4),
                "shoot_delay": delay,
                "hp": hp,
            }
        )

    def update_enemies(self, dt, now):
        for enemy in list(self.enemies):
            enemy_id = enemy["id"]
            self.canvas.move(enemy_id, enemy["vx"] * dt, enemy["speed"] * dt)
            box = self.canvas.bbox(enemy_id)
            if not box:
                self.enemies.remove(enemy)
                continue

            x1, y1, x2, y2 = box
            if x1 < 8 or x2 > WIDTH - 8:
                enemy["vx"] *= -1

            if now >= enemy["next_shot"] and y1 > 0:
                bullet = self.canvas.create_image((x1 + x2) / 2, y2 + 10, image=self.enemy_bullet_photo)
                self.bullets.append(
                    {"id": bullet, "owner": "enemy", "vy": ENEMY_BULLET_SPEED + self.level * 18}
                )
                enemy["next_shot"] = now + enemy["shoot_delay"] * random.uniform(0.85, 1.2)

            if y1 > HEIGHT + 40:
                self.canvas.delete(enemy_id)
                self.enemies.remove(enemy)
                self.score = max(0, self.score - 10)

    def update_bullets(self, dt):
        for bullet in list(self.bullets):
            bullet_id = bullet["id"]
            self.canvas.move(bullet_id, 0, bullet["vy"] * dt)
            box = self.canvas.bbox(bullet_id)
            if not box or box[3] < -30 or box[1] > HEIGHT + 30:
                self.canvas.delete(bullet_id)
                self.bullets.remove(bullet)

    def spawn_heart_drop(self):
        x = random.randint(42, WIDTH - 42)
        y = -28
        heart_id = self.canvas.create_image(x, y, image=self.heart_drop_photo)
        self.powerups.append(
            {
                "id": heart_id,
                "type": "heart",
                "vy": HEART_DROP_SPEED,
                "vx": random.uniform(-45, 45),
            }
        )

    def update_powerups(self, dt):
        for powerup in list(self.powerups):
            powerup_id = powerup["id"]
            self.canvas.move(powerup_id, powerup["vx"] * dt, powerup["vy"] * dt)
            box = self.canvas.bbox(powerup_id)
            if not box:
                self.powerups.remove(powerup)
                continue

            x1, y1, x2, y2 = box
            if x1 < 8 or x2 > WIDTH - 8:
                powerup["vx"] *= -1

            if y1 > HEIGHT + 28:
                self.canvas.delete(powerup_id)
                self.powerups.remove(powerup)

    def check_collisions(self, now):
        player_box = self.canvas.bbox(self.player)
        if not player_box:
            return

        for bullet in list(self.bullets):
            if bullet["owner"] != "player":
                continue

            bullet_box = self.canvas.bbox(bullet["id"])
            if not bullet_box:
                continue

            target_enemy = None
            for enemy in self.enemies:
                enemy_box = self.canvas.bbox(enemy["id"])
                if enemy_box and self.overlaps(bullet_box, enemy_box):
                    target_enemy = enemy
                    break

            if target_enemy:
                self.canvas.delete(bullet["id"])
                self.bullets.remove(bullet)
                target_enemy["hp"] -= 1
                if target_enemy["hp"] <= 0:
                    self.destroy_enemy(target_enemy, give_points=True)
                else:
                    self.score += 4

        for powerup in list(self.powerups):
            powerup_box = self.canvas.bbox(powerup["id"])
            if powerup_box and self.overlaps(player_box, powerup_box):
                self.canvas.delete(powerup["id"])
                self.powerups.remove(powerup)
                self.lives += 1
                self.show_bonus_message("+1 Life")
                player_box = self.canvas.bbox(self.player) or player_box

        if now < self.invincible_until:
            return

        for bullet in list(self.bullets):
            if bullet["owner"] != "enemy":
                continue
            bullet_box = self.canvas.bbox(bullet["id"])
            if bullet_box and self.overlaps(player_box, bullet_box):
                self.canvas.delete(bullet["id"])
                self.bullets.remove(bullet)
                self.damage_player(now)
                if not self.running:
                    return
                player_box = self.canvas.bbox(self.player) or player_box
                break

        for enemy in list(self.enemies):
            enemy_box = self.canvas.bbox(enemy["id"])
            if enemy_box and self.overlaps(player_box, enemy_box):
                self.destroy_enemy(enemy, give_points=False)
                self.damage_player(now)
                if not self.running:
                    return
                player_box = self.canvas.bbox(self.player) or player_box

    def destroy_enemy(self, enemy, give_points):
        self.canvas.delete(enemy["id"])
        if enemy in self.enemies:
            self.enemies.remove(enemy)
        if give_points:
            self.kills += 1
            self.score += 22 + (self.level - 1) * 2
            self.update_background_stage_by_kills()
            self.reward_life_if_needed()

    def reward_life_if_needed(self):
        rewarded = False
        while self.kills >= self.next_life_reward_kills:
            self.spawn_heart_drop()
            self.next_life_reward_kills += LIFE_REWARD_KILLS
            rewarded = True
        if rewarded:
            self.show_bonus_message("Heart incoming!")

    def show_bonus_message(self, message):
        self.canvas.itemconfig(self.bonus_text, text=message, state="normal")
        self.root.after(900, lambda: self.canvas.itemconfig(self.bonus_text, state="hidden"))

    def update_background_stage_by_kills(self):
        if self.bg_transition_active:
            return

        if self.background_stage == 0 and self.kills >= BACKGROUND_DARK_KILLS:
            self.start_background_transition(self.bg_day_to_dark_photos, target_stage=1)
        elif self.background_stage == 1 and self.kills >= BACKGROUND_SNOW_KILLS:
            self.start_background_transition(self.bg_dark_to_snow_photos, target_stage=2)

    def start_background_transition(self, frames, target_stage):
        if self.bg_transition_active or self.background_stage >= target_stage:
            return
        self.bg_transition_active = True
        self.bg_transition_start_time = time.monotonic()
        self.bg_transition_frame_index = 0
        self.bg_transition_frames = frames
        self.bg_transition_target_stage = target_stage
        if self.bg_transition_frames:
            self.canvas.itemconfig(self.background_id, image=self.bg_transition_frames[0])

    def update_background_transition(self, now):
        if not self.bg_transition_active or not self.bg_transition_frames:
            return

        elapsed = now - self.bg_transition_start_time
        progress = min(1.0, elapsed / BG_TRANSITION_DURATION)
        frame = int(progress * BG_TRANSITION_FRAMES)
        frame = min(frame, len(self.bg_transition_frames) - 1)

        if frame != self.bg_transition_frame_index:
            self.bg_transition_frame_index = frame
            self.canvas.itemconfig(self.background_id, image=self.bg_transition_frames[frame])

        if progress >= 1.0:
            self.bg_transition_active = False
            self.background_stage = self.bg_transition_target_stage
            self.canvas.itemconfig(self.background_id, image=self.bg_transition_frames[-1])
            self.bg_transition_frames = []
            self.bg_transition_target_stage = 0
            self.update_background_stage_by_kills()

    def damage_player(self, now):
        if now < self.invincible_until or not self.running:
            return

        if self.unlimited_lives_test:
            self.invincible_until = now + 0.2
            return

        self.lives -= 1
        self.invincible_until = now + 0.8

        for i in range(6):
            state = "hidden" if i % 2 == 0 else "normal"
            self.root.after(i * 80, lambda s=state: self.canvas.itemconfig(self.player, state=s))
        self.root.after(500, lambda: self.canvas.itemconfig(self.player, state="normal"))

        if self.lives <= 0:
            self.game_over()

    def update_difficulty(self):
        self.level = self.kills // 10 + 1
        self.spawn_interval = max(MIN_SPAWN_INTERVAL, START_SPAWN_INTERVAL - (self.level - 1) * 0.06)

    def update_hud(self):
        self.canvas.itemconfig(
            self.hud,
            text=f"Score: {self.score}   Level: {self.level}   Kills: {self.kills}",
        )
        lives_text = "xINF" if self.unlimited_lives_test else f"x{self.lives}"
        self.canvas.itemconfig(self.lives_text, text=lives_text)

    def game_over(self):
        if not self.running:
            return

        self.record_current_run()
        self.running = False
        self.paused = False
        self.pressed_keys.clear()
        self.canvas.itemconfig(
            self.overlay,
            text=f"Mission Failed\nScore: {self.score}\nKills: {self.kills}\nPress R to Restart",
            state="normal",
        )

    def restart(self):
        self.clear_dynamic_entities()

        self.score = 0
        self.kills = 0
        self.lives = 3
        self.level = 1
        self.next_life_reward_kills = LIFE_REWARD_KILLS
        self.spawn_interval = START_SPAWN_INTERVAL
        self.last_spawn_time = time.monotonic()
        self.last_player_shot = 0.0
        self.invincible_until = 0.0
        self.running = True
        self.paused = False
        self.round_recorded = False
        self.pressed_keys.clear()
        self.background_stage = 0
        self.bg_transition_active = False
        self.bg_transition_start_time = 0.0
        self.bg_transition_frame_index = 0
        self.bg_transition_frames = []
        self.bg_transition_target_stage = 0

        self.canvas.coords(self.player, WIDTH // 2, HEIGHT - 72)
        self.canvas.itemconfig(self.player, state="normal")
        self.canvas.itemconfig(self.background_id, image=self.bg_day_photo)
        self.canvas.itemconfig(self.bonus_text, state="hidden")
        self.canvas.itemconfig(self.overlay, state="hidden")
        self.update_hud()

    @staticmethod
    def overlaps(a, b):
        ax1, ay1, ax2, ay2 = a
        bx1, by1, bx2, by2 = b
        return ax1 < bx2 and ax2 > bx1 and ay1 < by2 and ay2 > by1


def main():
    if Image is None or ImageTk is None or ImageDraw is None or ImageFilter is None:
        print("Pillow is required. Install it with: pip install pillow")
        return

    root = tk.Tk()
    try:
        AirCombatGame(root)
    except RuntimeError as error:
        messagebox.showerror("Air Combat", str(error))
        root.destroy()
        return
    root.mainloop()


if __name__ == "__main__":
    main()
