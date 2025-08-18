# naruto_vs_sasuke.py
import pygame
import numpy as np
import os
import sys
import platform
from time import time
from PIL import Image

# ================== Configuration ==================
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
ASSET_DIR = os.path.join(BASE_DIR, "asset")
SPRITESHEET_PATH_NARUTO = os.path.join(ASSET_DIR, "sprites", "sheet.png")
SPRITESHEET_PATH_SASUKE = os.path.join(ASSET_DIR, "sprites", "sheet2.png")
SOUNDS_DIR = os.path.join(ASSET_DIR, "sounds")
MAP_IMAGE_DIR = ASSET_DIR

# 🔥 Fireball images folder (expects image0.png ... image76.png)
FIREBALL_DIR = os.path.join(ASSET_DIR, "fireball")

# Runtime scale (you can change during play with +/-)
INITIAL_SCALE = 1.0

# Animation names (used when sheet provides multiple rows; for autoscan we put all frames into "idle")
ANIM_NAMES = ["idle", "walk", "attack", "jump"]

# Per-sheet slicing mode:
SHEET_CFG_NARUTO = {"mode": "autoscan_row", "expected": 4, "crop_bottom_px": 64}
SHEET_CFG_SASUKE = {"mode": "autoscan_row", "expected": 4, "crop_bottom_px": 64}

# Shooting tuning
BULLET_SPEED = 14
BULLET_DAMAGE = 12
SHOOT_COOLDOWN_FRAMES = 18  # ~3 shots/sec at 60 fps


# ================== Pygame init ==================
pygame.mixer.pre_init(44100, -16, 2, 1024)
pygame.init()

# ================== Background Music ==================
def play_background_music():
    music_path = os.path.join(ASSET_DIR, "game_music.mp3")
    if os.path.isfile(music_path):
        try:
            pygame.mixer.music.load(music_path)
            pygame.mixer.music.set_volume(0.3)
            pygame.mixer.music.play(-1)
            print("Background music playing...")
        except Exception as e:
            print("Music load failed:", e)
    else:
        print("No music file found at", music_path)

play_background_music()

print("Pygame:", pygame.get_sdl_version(), "Platform:", platform.platform())

SCREEN_WIDTH, SCREEN_HEIGHT = 800, 600
screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
pygame.display.set_caption("Naruto vs Sasuke")

WHITE, RED, GREEN, BLACK = (255,255,255), (255,0,0), (0,255,0), (0,0,0)

# ================== Sounds ==================
def create_sound(freq=440, duration=0.1, vol=0.5):
    sample_rate = 44100
    t = np.linspace(0, duration, int(sample_rate * duration), endpoint=False)
    wave = vol * np.sin(2 * np.pi * freq * t)
    decay = np.linspace(1.0, 0.1, wave.size)
    wave *= decay
    stereo = np.column_stack((wave, wave))
    arr = (stereo * 32767).astype(np.int16)
    arr = np.ascontiguousarray(arr)
    return pygame.sndarray.make_sound(arr)

def load_sound_file(filename):
    path = os.path.join(SOUNDS_DIR, filename)
    if os.path.isfile(path):
        try:
            return pygame.mixer.Sound(path)
        except Exception as e:
            print("Failed to load sound", path, e)
    return None

attack_sound = load_sound_file("attack.wav") or create_sound(880, 0.08, 0.5)
hit_sound    = load_sound_file("hit.wav")    or create_sound(220, 0.12, 0.5)
shoot_sound  = load_sound_file("shoot.wav")  or create_sound(1400, 0.05, 0.4)
bg_music     = load_sound_file("bg_loop.wav") or create_sound(110, 1.0, 0.2)
if bg_music:
    try:
        bg_music.set_volume(0.15)
        bg_music.play(-1)
    except Exception:
        pass

# ================== Maps ==================
map_images = []
for fn in ["forest.jpg", "village.jpg", "arena.jpg"]:
    p = os.path.join(MAP_IMAGE_DIR, fn)
    if os.path.isfile(p):
        try:
            img = pygame.image.load(p).convert()
            img = pygame.transform.scale(img, (SCREEN_WIDTH, SCREEN_HEIGHT))
            map_images.append(img)
            print("Loaded map:", fn)
        except Exception as e:
            print("Failed to load map:", fn, e)

if len(map_images) == 0:
    map_images = None
    print("No map images found — using color backgrounds.")
map_colors = [(34,139,34), (139,69,19), (128,128,128)]

# ================== Sheet loading helpers ==================
def pil_to_surface_alpha(img: Image.Image) -> pygame.Surface:
    if img.mode != "RGBA":
        img = img.convert("RGBA")
    data = img.tobytes()
    return pygame.image.fromstring(data, img.size, "RGBA").convert_alpha()

def load_grid_sheet(sheet_path, cols, rows):
    if not os.path.isfile(sheet_path):
        print("Sprite sheet not found:", sheet_path)
        return {}
    img = Image.open(sheet_path).convert("RGBA")
    W, H = img.size
    fw, fh = W // cols, H // rows
    animations = {}
    for r in range(rows):
        anim_name = ANIM_NAMES[r] if r < len(ANIM_NAMES) else f"row{r}"
        frames = []
        for c in range(cols):
            box = (c*fw, r*fh, (c+1)*fw, (r+1)*fh)
            frame = img.crop(box)
            frames.append(pil_to_surface_alpha(frame))
        animations[anim_name] = frames
        print(f"Loaded {len(frames)} frames for {anim_name} (grid).")
    img.close()
    return animations

def load_autoscan_row(sheet_path, expected=0, crop_bottom_px=0):
    if not os.path.isfile(sheet_path):
        print("Sprite sheet not found:", sheet_path)
        return {}

    img = Image.open(sheet_path).convert("RGBA")
    W, H = img.size

    if crop_bottom_px > 0 and crop_bottom_px < H:
        img = img.crop((0, 0, W, H - crop_bottom_px))
        W, H = img.size

    px = np.array(img)
    rgb = px[:, :, :3].astype(np.uint16)
    brightness = (0.2126*rgb[:,:,0] + 0.7152*rgb[:,:,1] + 0.0722*rgb[:,:,2])
    mask = brightness > 8
    rgba = px.copy()
    rgba[:, :, 3] = (mask * 255).astype(np.uint8)
    img_clean = Image.fromarray(rgba, mode="RGBA")

    col_nonempty = mask.any(axis=0)
    regions = []
    in_run = False
    start = 0
    for x in range(W):
        if col_nonempty[x] and not in_run:
            in_run = True; start = x
        elif not col_nonempty[x] and in_run:
            in_run = False; regions.append((start, x))
    if in_run: regions.append((start, W))

    filtered = [(a, b) for (a, b) in regions if (b - a) > 10]
    if expected and len(filtered) > expected:
        filtered = sorted(filtered, key=lambda r: (r[1]-r[0]), reverse=True)[:expected]
        filtered = sorted(filtered, key=lambda r: r[0])

    frames = []
    for (x0, x1) in filtered:
        slice_mask = mask[:, x0:x1]
        if not slice_mask.any():
            continue
        ys = np.where(slice_mask.any(axis=1))[0]
        y0, y1 = int(ys.min()), int(ys.max())+1
        pad = 4
        x0p = max(0, x0 - pad); x1p = min(W, x1 + pad)
        y0p = max(0, y0 - pad); y1p = min(H, y1 + pad)
        frame = img_clean.crop((x0p, y0p, x1p, y1p))
        frames.append(pil_to_surface_alpha(frame))

    if expected and len(frames) != expected:
        print(f"[autoscan] Warning: expected ~{expected} frames, got {len(frames)}")

    animations = {"idle": frames if frames else []}
    print(f"Loaded {len(frames)} frames via autoscan.")
    return animations

def load_sheet_by_cfg(path, cfg):
    mode = cfg.get("mode", "grid")
    if mode == "grid":
        cols = int(cfg.get("cols", 4)); rows = int(cfg.get("rows", 1))
        return load_grid_sheet(path, cols, rows)
    elif mode == "autoscan_row":
        expected = int(cfg.get("expected", 0)); crop = int(cfg.get("crop_bottom_px", 0))
        return load_autoscan_row(path, expected=expected, crop_bottom_px=crop)
    else:
        print(f"Unknown mode '{mode}' for {os.path.basename(path)}; defaulting to grid 4x1.")
        return load_grid_sheet(path, 4, 1)

def rescale_animations(anims, factor: float):
    if not anims:
        return {}
    scaled = {}
    for k, frames in anims.items():
        new_list = []
        for f in frames:
            w, h = f.get_width(), f.get_height()
            nw, nh = max(1, int(round(w*factor))), max(1, int(round(h*factor)))
            try:
                sf = pygame.transform.smoothscale(f, (nw, nh)).convert_alpha()
            except Exception:
                sf = pygame.transform.scale(f, (nw, nh)).convert_alpha()
            new_list.append(sf)
        scaled[k] = new_list
    return scaled

# ================== Load character animations ==================
orig_naruto_animations = load_sheet_by_cfg(SPRITESHEET_PATH_NARUTO, SHEET_CFG_NARUTO)
orig_sasuke_animations = load_sheet_by_cfg(SPRITESHEET_PATH_SASUKE, SHEET_CFG_SASUKE)

# ================== Load Fireball frames (original sizes) ==================
orig_fireball_frames = []
if os.path.isdir(FIREBALL_DIR):
    # Expecting image0.png ... image76.png
    for i in range(77):
        fn = os.path.join(FIREBALL_DIR, f"image{i}.png")
        if os.path.isfile(fn):
            try:
                img = pygame.image.load(fn).convert_alpha()
                orig_fireball_frames.append(img)
            except Exception as e:
                print("Failed to load fireball frame", fn, e)
        else:
            # missing frames will just be skipped
            pass
else:
    print("FIREBALL_DIR not found:", FIREBALL_DIR)

if not orig_fireball_frames:
    print("⚠️ No fireball frames loaded! Shooting will fall back to simple drawing.")

def rescale_fireballs(frames, factor: float):
    if not frames:
        return []
    scaled = []
    for f in frames:
        w, h = f.get_width(), f.get_height()
        nw, nh = max(1, int(round(w * factor))), max(1, int(round(h * factor)))
        try:
            sf = pygame.transform.smoothscale(f, (nw, nh)).convert_alpha()
        except Exception:
            sf = pygame.transform.scale(f, (nw, nh)).convert_alpha()
        scaled.append(sf)
    return scaled

# runtime scale and scaled assets
runtime_scale = float(INITIAL_SCALE)
naruto_animations = rescale_animations(orig_naruto_animations, runtime_scale)
sasuke_animations = rescale_animations(orig_sasuke_animations, runtime_scale)
fireball_frames = rescale_fireballs(orig_fireball_frames, runtime_scale)

# ================== Bullets ==================
class Bullet:
    __slots__ = ("x", "y", "vx", "owner", "frame_idx")
    def __init__(self, x, y, facing_right, owner):
        self.x = float(x)
        self.y = float(y)
        self.vx = float(BULLET_SPEED if facing_right else -BULLET_SPEED)
        self.owner = owner  # "Naruto" or "Sasuke"
        self.frame_idx = 0

    def update(self):
        self.x += self.vx
        if fireball_frames:
            self.frame_idx = (self.frame_idx + 1) % len(fireball_frames)
        else:
            # keep incrementing harmlessly
            self.frame_idx = (self.frame_idx + 1) % 1

    def offscreen(self):
        # allow some margin
        return (self.x < -200) or (self.x > SCREEN_WIDTH + 200)

    def rect(self):
        """Return a pygame.Rect for collisions based on the current frame or a small fallback rect."""
        if fireball_frames:
            fr = fireball_frames[self.frame_idx]
            r = fr.get_rect(center=(int(self.x), int(self.y)))
            return r
        else:
            # fallback small circle rect
            r = pygame.Rect(0, 0, 16, 16)
            r.center = (int(self.x), int(self.y))
            return r

    def draw(self, surface):
        if fireball_frames:
            fr = fireball_frames[self.frame_idx]
            # flip horizontally if moving left
            if self.vx < 0:
                fr = pygame.transform.flip(fr, True, False)
            r = fr.get_rect(center=(int(self.x), int(self.y)))
            surface.blit(fr, r.topleft)
        else:
            # fallback simple visual
            pygame.draw.circle(surface, (255, 140, 0), (int(self.x), int(self.y)), 8)
            pygame.draw.circle(surface, BLACK, (int(self.x), int(self.y)), 8, 1)

bullets = []

# ================== Character ==================
def _pressed(keys, key_or_keys):
    if isinstance(key_or_keys, (list, tuple)):
        return any(keys[k] for k in key_or_keys)
    return keys[key_or_keys]

class Character:
    def __init__(self, x, ground_y, name, controls, sprites=None, facing_right=True):
        self.name = name
        self.controls = controls
        self.base_anims = sprites or {}
        self.animations = sprites or {}
        self.anim_state = "idle"
        self.anim_tick = 0
        self.frame_duration = 6
        self.facing_right = facing_right

        self.vel = 5
        self.jump_power = 15
        self.gravity = 0.8
        self.vy = 0.0
        self.health = 100
        self.is_jumping = False
        self.is_attacking = False
        self.attack_cooldown = 0
        self.shoot_cooldown = 0

        self.midbottom_x = x
        self.midbottom_y = ground_y

        w, h = 50, 80
        fr = self._peek_frame()
        if fr is not None:
            w, h = fr.get_width(), fr.get_height()
        self.rect = pygame.Rect(0, 0, w, h)
        self.rect.midbottom = (self.midbottom_x, self.midbottom_y)

    def _peek_frame(self):
        if not self.animations:
            return None
        for k in ["idle", "walk", "attack", "jump"]:
            frames = self.animations.get(k, [])
            if frames:
                return frames[0]
        for frames in self.animations.values():
            if frames:
                return frames[0]
        return None

    def current_frame(self):
        frames = self.animations.get(self.anim_state)
        if not frames:
            for key in ["idle", "walk", "attack", "jump"]:
                frames = self.animations.get(key)
                if frames:
                    break
        if not frames:
            return None
        idx = (self.anim_tick // self.frame_duration) % len(frames)
        return frames[idx]

    def apply_scaled_animations(self, scaled):
        self.animations = scaled or {}
        fr = self._peek_frame()
        if fr is not None:
            self.rect.size = (fr.get_width(), fr.get_height())
            self.rect.midbottom = (self.midbottom_x, int(self.midbottom_y))

    def move_and_actions(self, keys, ground_y):
        """Moves, handles jump/melee/shoot. Returns a Bullet or None when shooting."""
        prev_state = self.anim_state
        self.anim_state = "idle"
        shot_bullet = None

        try:
            if _pressed(keys, self.controls["left"]):
                self.midbottom_x -= self.vel
                self.facing_right = False
                self.anim_state = "walk"
            if _pressed(keys, self.controls["right"]):
                self.midbottom_x += self.vel
                self.facing_right = True
                self.anim_state = "walk"
            if _pressed(keys, self.controls["jump"]) and not self.is_jumping:
                self.vy = -self.jump_power
                self.is_jumping = True
            # Melee
            if _pressed(keys, self.controls["attack"]) and self.attack_cooldown <= 0:
                self.is_attacking = True
                self.attack_cooldown = 30
                try: attack_sound.play()
                except Exception: pass
            # Shoot
            if _pressed(keys, self.controls["shoot"]) and self.shoot_cooldown <= 0:
                chest_y = self.rect.centery - self.rect.height * 0.1
                muzzle_x = self.rect.right if self.facing_right else self.rect.left
                shot_bullet = Bullet(muzzle_x, chest_y, self.facing_right, self.name)
                self.shoot_cooldown = SHOOT_COOLDOWN_FRAMES
                try: shoot_sound.play()
                except Exception: pass
        except Exception:
            pass

        if self.is_attacking:
            self.anim_state = "attack"

        if self.anim_state != prev_state:
            self.anim_tick = 0
        else:
            self.anim_tick += 1

        # Gravity
        self.vy += self.gravity
        self.midbottom_y += self.vy

        # Update rect to current frame (size may change)
        fr = self.current_frame()
        if fr:
            self.rect.size = (fr.get_width(), fr.get_height())
        self.rect.midbottom = (int(self.midbottom_x), int(self.midbottom_y))

        # Ground clamp
        if self.rect.bottom > ground_y:
            self.rect.bottom = ground_y
            self.midbottom_y = self.rect.bottom
            self.vy = 0
            self.is_jumping = False

        # Screen clamp horizontally
        self.rect.x = max(0, min(self.rect.x, SCREEN_WIDTH - self.rect.width))
        self.midbottom_x = self.rect.midbottom[0]

        # Cooldowns
        if self.attack_cooldown > 0:
            self.attack_cooldown -= 1
        else:
            self.is_attacking = False

        if self.shoot_cooldown > 0:
            self.shoot_cooldown -= 1

        return shot_bullet

    def draw(self, surface):
        fr = self.current_frame()
        if fr:
            sprite = pygame.transform.flip(fr, True, False) if not self.facing_right else fr
            r = sprite.get_rect()
            r.midbottom = self.rect.midbottom
            surface.blit(sprite, r.topleft)
        else:
            color = (255,165,0) if self.name == "Naruto" else (0,0,255)
            pygame.draw.rect(surface, color, self.rect)

    def get_attack_rect(self):
        w = max(20, int(self.rect.width * 0.5))
        h = max(20, int(self.rect.height * 0.3))
        offset = int(self.rect.width * 0.6) if self.facing_right else -int(self.rect.width * 1.1)
        x = self.rect.centerx + offset
        y = self.rect.centery - h//2
        return pygame.Rect(x, y, w, h)

# ================== UI helpers ==================
def draw_health_bar(x, y, health):
    pygame.draw.rect(screen, RED, (x, y, 100, 10))
    pygame.draw.rect(screen, GREEN, (x, y, max(0, int(health)), 10))

leaderboard = []
def update_leaderboard(winner_name):
    leaderboard.append({"name": winner_name, "time": pygame.time.get_ticks() // 1000})
    leaderboard.sort(key=lambda x: x["time"], reverse=True)
    del leaderboard[5:]

def draw_leaderboard():
    font = pygame.font.SysFont(None, 32)
    text = font.render("Leaderboard", True, WHITE)
    screen.blit(text, (SCREEN_WIDTH//2 - 100, 50))
    for i, entry in enumerate(leaderboard):
        text = font.render(f"{i+1}. {entry['name']} - {entry['time']}s", True, WHITE)
        screen.blit(text, (SCREEN_WIDTH//2 - 100, 100 + i*28))

# ================== Map Selection ==================
maps = ["Forest", "Village", "Arena"]
selected_map = None
def draw_map_selection():
    screen.fill(BLACK)
    font = pygame.font.SysFont(None, 36)
    title = font.render("Select Map (1-3) then ENTER to Start", True, WHITE)
    screen.blit(title, (SCREEN_WIDTH//2 - 260, 40))
    for i, m in enumerate(maps):
        color = GREEN if selected_map == i else WHITE
        text = font.render(f"{i+1}. {m}", True, color)
        screen.blit(text, (SCREEN_WIDTH//2 - 100, 140 + i*46))
    hint = font.render("Controls: Naruto=Arrows+RightCtrl shoot | Sasuke=WASD+LeftCtrl shoot | +/- resize", True, WHITE)
    screen.blit(hint, (SCREEN_WIDTH//2 - 360, SCREEN_HEIGHT - 60))

# ================== Instantiate Characters ==================
GROUND_Y = SCREEN_HEIGHT - 20  # feet a bit above bottom

naruto = Character(150, GROUND_Y, "Naruto", {
    "left": pygame.K_LEFT, "right": pygame.K_RIGHT, "jump": pygame.K_UP,
    "attack": pygame.K_DOWN, "shoot": pygame.K_RCTRL
}, sprites=naruto_animations, facing_right=True)

sasuke = Character(650, GROUND_Y, "Sasuke", {
    "left": pygame.K_a, "right": pygame.K_d, "jump": pygame.K_w,
    "attack": pygame.K_s, "shoot": pygame.K_LCTRL
}, sprites=sasuke_animations, facing_right=False)

# ================== Game Loop ==================
clock = pygame.time.Clock()
FPS = 60
game_over = False
game_state = "map_selection"
running = True
winner = ""

print("Controls:")
print("  Naruto: Arrows, melee=Down, SHOOT=Right Ctrl")
print("  Sasuke: WASD, melee=S, SHOOT=Left Ctrl")
print("  Select map with 1-3 then ENTER. +/- to resize, R to restart after KO.")

def rescale_both():
    global naruto_animations, sasuke_animations, fireball_frames
    naruto_animations = rescale_animations(orig_naruto_animations, runtime_scale)
    sasuke_animations = rescale_animations(orig_sasuke_animations, runtime_scale)
    fireball_frames = rescale_fireballs(orig_fireball_frames, runtime_scale)
    naruto.apply_scaled_animations(naruto_animations)
    sasuke.apply_scaled_animations(sasuke_animations)

start_time = time()
try:
    while running:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            elif event.type == pygame.KEYDOWN:
                # Resize
                if event.key in (pygame.K_KP_PLUS,) or getattr(event, "unicode", "") == "+":
                    runtime_scale = min(4.0, round(runtime_scale + 0.1, 2))
                    rescale_both()
                    print(f"Scale -> {runtime_scale:.2f}")
                elif event.key in (pygame.K_KP_MINUS,) or getattr(event, "unicode", "") == "-":
                    runtime_scale = max(0.5, round(runtime_scale - 0.1, 2))
                    rescale_both()
                    print(f"Scale -> {runtime_scale:.2f}")

                if game_state == "map_selection":
                    if event.key == pygame.K_1: selected_map = 0
                    elif event.key == pygame.K_2: selected_map = 1
                    elif event.key == pygame.K_3: selected_map = 2
                    elif event.key == pygame.K_RETURN and selected_map is not None:
                        game_state = "playing"
                elif game_state == "playing" and game_over:
                    if event.key == pygame.K_r:
                        naruto.health = sasuke.health = 100
                        naruto.midbottom_x, naruto.midbottom_y = (150, GROUND_Y)
                        sasuke.midbottom_x, sasuke.midbottom_y = (650, GROUND_Y)
                        naruto.vy = sasuke.vy = 0
                        naruto.is_jumping = sasuke.is_jumping = False
                        naruto.is_attacking = sasuke.is_attacking = False
                        naruto.attack_cooldown = sasuke.attack_cooldown = 0
                        naruto.shoot_cooldown = sasuke.shoot_cooldown = 0
                        bullets.clear()
                        rescale_both()
                        game_over = False
                        game_state = "map_selection"
                        selected_map = None
                        winner = ""

        if game_state == "map_selection":
            draw_map_selection()

        elif game_state == "playing":
            if not game_over:
                keys = pygame.key.get_pressed()

                # Move + actions (may return a bullet)
                b1 = naruto.move_and_actions(keys, GROUND_Y)
                b2 = sasuke.move_and_actions(keys, GROUND_Y)
                if b1: bullets.append(b1)
                if b2: bullets.append(b2)

                # Melee hits
                if naruto.is_attacking and naruto.get_attack_rect().colliderect(sasuke.rect):
                    sasuke.health -= 5
                    try: hit_sound.play()
                    except Exception: pass
                if sasuke.is_attacking and sasuke.get_attack_rect().colliderect(naruto.rect):
                    naruto.health -= 5
                    try: hit_sound.play()
                    except Exception: pass

                # Bullets update + collisions
                for bullet in bullets[:]:
                    bullet.update()
                    r = bullet.rect()
                    # test collision with the OTHER player only
                    if bullet.owner == "Naruto":
                        if r.colliderect(sasuke.rect):
                            sasuke.health -= BULLET_DAMAGE
                            try: hit_sound.play()
                            except Exception: pass
                            try: bullets.remove(bullet)
                            except ValueError: pass
                            continue
                    else:
                        if r.colliderect(naruto.rect):
                            naruto.health -= BULLET_DAMAGE
                            try: hit_sound.play()
                            except Exception: pass
                            try: bullets.remove(bullet)
                            except ValueError: pass
                            continue
                    if bullet.offscreen():
                        try: bullets.remove(bullet)
                        except ValueError: pass

                if naruto.health <= 0 or sasuke.health <= 0:
                    winner = "Sasuke" if naruto.health <= 0 else "Naruto"
                    update_leaderboard(winner)
                    game_over = True

            # Background
            if map_images and selected_map is not None and selected_map < len(map_images):
                screen.blit(map_images[selected_map], (0, 0))
            else:
                screen.fill(map_colors[selected_map] if selected_map is not None else WHITE)

            # Draw players
            naruto.draw(screen)
            sasuke.draw(screen)

            # Draw bullets
            for bullet in bullets:
                bullet.draw(screen)

            # UI
            draw_health_bar(50, 20, naruto.health)
            draw_health_bar(SCREEN_WIDTH-150, 20, sasuke.health)

            if game_over:
                overlay = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT), pygame.SRCALPHA)
                overlay.fill((0,0,0,180))
                screen.blit(overlay, (0,0))
                font = pygame.font.SysFont(None, 48)
                winner_text = font.render(f"{winner} Wins! Press R to Restart", True, WHITE)
                screen.blit(winner_text, (SCREEN_WIDTH//2 - 240, SCREEN_HEIGHT//2 - 20))
                draw_leaderboard()

        pygame.display.flip()
        clock.tick(FPS)

finally:
    elapsed = time() - start_time
    print(f"Exiting after {elapsed:.2f} sec")
    try: pygame.quit()
    except Exception: pass
    sys.exit(0)
