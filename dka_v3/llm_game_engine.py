"""
DKA V3 — Komplett LLM Game Engine
==================================
A DKA adja a jatek infrastrukturat (Pygame, allapotgep, kamera, tilemap,
hang, UI, reszecskek, mentes, idozitok, input). Az LLM adja a jateklogikat
(init, update, draw, collision, menu_init, menu_draw, menu_handle).

Az LLM minden kepesseget hasznalhat az `engine` objektumon keresztul.

Hasznalat:
  engine = DKAEngine()
  engine.run(\"\"\"
    ===init===
    ...
    ===update===
    ...
    ===draw===
    ...
    ===collision===
    ...
    ===menu_init===
    ...  (opcionalis)
    ===menu_draw===
    ...  (opcionalis)
    ===menu_handle===
    ...  (opcionalis)
  \"\"\")
"""

from __future__ import annotations
import sys, os, re, subprocess, tempfile, time, json, math, random
from pathlib import Path
from typing import Optional

try:
    import pygame
except ImportError:
    pygame = None


# ═══════════════════════════════════════════════════════════════
# SZÍNEK
# ═══════════════════════════════════════════════════════════════

COLORS = {
    "WHITE": (255, 255, 255), "BLACK": (0, 0, 0),
    "RED": (255, 0, 0), "DARK_RED": (180, 0, 0),
    "GREEN": (0, 255, 0), "DARK_GREEN": (0, 150, 0),
    "BLUE": (0, 0, 255), "DARK_BLUE": (0, 0, 150),
    "YELLOW": (255, 255, 0), "GOLD": (255, 215, 0),
    "PURPLE": (128, 0, 128), "MAGENTA": (255, 0, 255),
    "CYAN": (0, 255, 255), "TEAL": (0, 128, 128),
    "ORANGE": (255, 165, 0), "BROWN": (139, 69, 19),
    "GRAY": (128, 128, 128), "DARK_GRAY": (64, 64, 64),
    "LIGHT_GRAY": (200, 200, 200), "PINK": (255, 192, 203),
}

# ═══════════════════════════════════════════════════════════════
# FILTER — egyszerű képernyő effekt (villódzás, elsötétülés)
# ═══════════════════════════════════════════════════════════════

class ScreenFilter:
    """Képernyő effekt overlay."""
    def __init__(self):
        self.flash_alpha = 0
        self.flash_color = (255, 255, 255)
        self.fade_alpha = 0
        self.fade_color = (0, 0, 0)
        self.fade_dir = 0  # -1 fade out, 1 fade in, 0 idle
    
    def flash(self, color=(255, 255, 255)):
        """Villanás (fehér, piros stb.)"""
        self.flash_color = color
        self.flash_alpha = 180
    
    def fade_out(self, duration=1.0, color=(0, 0, 0)):
        """Elsötétedés"""
        self.fade_color = color
        self.fade_alpha = 0
        self.fade_dir = -1
        self.fade_speed = 255.0 / max(duration, 0.01) / 60.0
    
    def fade_in(self, duration=1.0, color=(0, 0, 0)):
        """Bevillanás"""
        self.fade_color = color
        self.fade_alpha = 255
        self.fade_dir = 1
        self.fade_speed = 255.0 / max(duration, 0.01) / 60.0
    
    def update(self, dt):
        if self.flash_alpha > 0:
            self.flash_alpha -= 500 * dt
            if self.flash_alpha < 0: self.flash_alpha = 0
        if self.fade_dir != 0:
            self.fade_alpha += self.fade_dir * self.fade_speed * 60 * dt
            if self.fade_dir == -1 and self.fade_alpha >= 255:
                self.fade_alpha = 255
                self.fade_dir = 0
            elif self.fade_dir == 1 and self.fade_alpha <= 0:
                self.fade_alpha = 0
                self.fade_dir = 0
    
    def render(self, screen):
        if self.flash_alpha > 0:
            surf = pygame.Surface(screen.get_size())
            surf.set_alpha(int(self.flash_alpha))
            surf.fill(self.flash_color)
            screen.blit(surf, (0, 0))
        if self.fade_alpha > 0:
            surf = pygame.Surface(screen.get_size())
            surf.set_alpha(int(self.fade_alpha))
            surf.fill(self.fade_color)
            screen.blit(surf, (0, 0))
    
    @property
    def is_fading(self):
        return self.fade_dir != 0


# ═══════════════════════════════════════════════════════════════
# KAMERA / VIEWPORT
# ═══════════════════════════════════════════════════════════════

class Camera:
    """Görgethető kamera viewport-tal."""
    def __init__(self, width=800, height=600, world_width=3200, world_height=2400):
        self.x = 0.0
        self.y = 0.0
        self.width = width
        self.height = height
        self.world_width = world_width
        self.world_height = world_height
        self.shake_intensity = 0.0
        self.shake_offset_x = 0.0
        self.shake_offset_y = 0.0
        self.smooth = True
        self.lerp_factor = 0.08  # smooth follow sebesség
    
    def follow(self, target_x: float, target_y: float, margin_x: int = 100, margin_y: int = 80):
        """Követ egy célpontot (pl. játékos)."""
        tx = target_x - self.width // 2
        ty = target_y - self.height // 2
        # Csak akkor mozog, ha a cél a margón kívül van
        if abs(self.x - tx) > margin_x:
            if self.smooth:
                self.x += (tx - self.x) * self.lerp_factor
            else:
                self.x = tx
        if abs(self.y - ty) > margin_y:
            if self.smooth:
                self.y += (ty - self.y) * self.lerp_factor
            else:
                self.y = ty
        # Világ határok
        self.x = max(0, min(self.x, self.world_width - self.width))
        self.y = max(0, min(self.y, self.world_height - self.height))
    
    def world_to_screen(self, wx: float, wy: float) -> tuple[float, float]:
        """Világ koordinátából képernyő koordináta."""
        return (wx - self.x, wy - self.y)
    
    def screen_to_world(self, sx: float, sy: float) -> tuple[float, float]:
        """Képernyő koordinátából világ koordináta."""
        return (sx + self.x, sy + self.y)
    
    def shake(self, intensity: float = 5.0):
        """Kamera shake (pl. robbanáskor)."""
        self.shake_intensity = intensity
    
    def update(self):
        """Kamera shake frissítése."""
        if self.shake_intensity > 0:
            self.shake_offset_x = random.uniform(-self.shake_intensity, self.shake_intensity)
            self.shake_offset_y = random.uniform(-self.shake_intensity, self.shake_intensity)
            self.shake_intensity *= 0.85
            if self.shake_intensity < 0.5:
                self.shake_intensity = 0
                self.shake_offset_x = 0
                self.shake_offset_y = 0
    
    def apply(self, rect: pygame.Rect) -> pygame.Rect:
        """Rect offsettelése a kamera pozíciójához képest."""
        r = rect.copy()
        r.x -= self.x - self.shake_offset_x
        r.y -= self.y - self.shake_offset_y
        return r
    
    def is_visible(self, rect: pygame.Rect) -> bool:
        """Látszik-e a rect a képernyőn?"""
        sx, sy = self.world_to_screen(rect.x, rect.y)
        return (-rect.width < sx < self.width + rect.width and
                -rect.height < sy < self.height + rect.height)


# ═══════════════════════════════════════════════════════════════
# TILE MAP
# ═══════════════════════════════════════════════════════════════

class TileMap:
    """JSON alapú tile map pályákhoz (platformer, RPG stb.)."""
    def __init__(self):
        self.width = 0
        self.height = 0
        self.tile_size = 32
        self.layers: list[list[list[int]]] = []  # [layer][row][col]
        self.layer_names: list[str] = []
        self.solids: set[int] = set()  # tile típusok amik szilárdak
        self.tile_textures: dict[int, pygame.Surface] = {}
        self.data_raw: dict = {}
    
    def load(self, data: dict):
        """Betölt egy tile map JSON-t."""
        self.data_raw = data
        self.width = data.get("width", 50)
        self.height = data.get("height", 20)
        self.tile_size = data.get("tilesize", 32)
        self.solids = set(data.get("solids", []))
        
        for layer_data in data.get("layers", []):
            raw = layer_data.get("data", [])
            name = layer_data.get("name", f"layer{len(self.layers)}")
            # Ha lapos lista -> mátrix
            if raw and isinstance(raw[0], int):
                grid = []
                for row in range(self.height):
                    start = row * self.width
                    grid.append(raw[start:start + self.width])
            else:
                grid = raw
            self.layers.append(grid)
            self.layer_names.append(name)
    
    def get_tile(self, layer: int, col: int, row: int) -> int:
        """Tile érték lekérése adott pozíción."""
        if 0 <= layer < len(self.layers):
            if 0 <= row < self.height and 0 <= col < self.width:
                return self.layers[layer][row][col]
        return 0
    
    def collides(self, rect: pygame.Rect, layer: int = 0) -> list[tuple[int, int, int]]:
        """Visszaadja az összes tile-t ami ütközik a rect-tel.
        Visszatérés: [(tile_type, col, row), ...]
        """
        hits = []
        left = max(0, rect.left // self.tile_size)
        right = min(self.width - 1, rect.right // self.tile_size)
        top = max(0, rect.top // self.tile_size)
        bottom = min(self.height - 1, rect.bottom // self.tile_size)
        
        for row in range(top, bottom + 1):
            for col in range(left, right + 1):
                tile = self.get_tile(layer, col, row)
                if tile in self.solids and tile > 0:
                    tile_rect = pygame.Rect(
                        col * self.tile_size, row * self.tile_size,
                        self.tile_size, self.tile_size
                    )
                    if rect.colliderect(tile_rect):
                        hits.append((tile, col, row))
        return hits
    
    def get_collision_rects(self, rect: pygame.Rect, layer: int = 0) -> list[pygame.Rect]:
        """Ütköző tile-ek téglalapjai."""
        return [
            pygame.Rect(h[1] * self.tile_size, h[2] * self.tile_size,
                       self.tile_size, self.tile_size)
            for h in self.collides(rect, layer)
        ]
    
    def render(self, screen: pygame.Surface, camera: Camera, layer: int = 0):
        """Tile map kirajzolása a látható részen."""
        if layer >= len(self.layers):
            return
        grid = self.layers[layer]
        # Csak a látható tile-okat rajzoljuk
        start_col = max(0, int(camera.x // self.tile_size))
        end_col = min(self.width - 1, int((camera.x + camera.width) // self.tile_size) + 1)
        start_row = max(0, int(camera.y // self.tile_size))
        end_row = min(self.height - 1, int((camera.y + camera.height) // self.tile_size) + 1)
        
        for row in range(start_row, end_row + 1):
            for col in range(start_col, end_col + 1):
                tile = grid[row][col]
                if tile == 0:
                    continue
                sx = col * self.tile_size - camera.x + camera.shake_offset_x
                sy = row * self.tile_size - camera.y + camera.shake_offset_y
                
                if tile in self.tile_textures:
                    screen.blit(self.tile_textures[tile], (sx, sy))
                else:
                    # Fallback: színezett négyzet tile típus alapján
                    colors = [None, (100, 100, 100), (50, 150, 50), (150, 100, 50),
                              (200, 200, 200), (50, 50, 150), (100, 50, 50)]
                    color = colors[tile % len(colors)] if tile < len(colors) else (80, 80, 80)
                    pygame.draw.rect(screen, color, (sx, sy, self.tile_size, self.tile_size))
                    pygame.draw.rect(screen, (40, 40, 40), (sx, sy, self.tile_size, self.tile_size), 1)
    
    def set_tile(self, layer: int, col: int, row: int, value: int):
        """Tile módosítása (dinamikus pályaváltozáshoz)."""
        if 0 <= layer < len(self.layers):
            if 0 <= row < self.height and 0 <= col < self.width:
                self.layers[layer][row][col] = value


# ═══════════════════════════════════════════════════════════════
# AUDIO RENDSZER
# ═══════════════════════════════════════════════════════════════

class AudioSystem:
    """Hang és zene kezelés."""
    def __init__(self):
        self.enabled = False
        self.sfx_volume = 0.5
        self.music_volume = 0.5
        self.sfx_cache: dict[str, pygame.mixer.Sound] = {}
        self.current_music: str | None = None
    
    def init(self):
        try:
            pygame.mixer.init(frequency=22050, size=-16, channels=2, buffer=512)
            self.enabled = True
        except Exception:
            self.enabled = False
    
    def load_sfx(self, name: str, path: str):
        """Hang effekt betöltése."""
        if not self.enabled:
            return
        try:
            self.sfx_cache[name] = pygame.mixer.Sound(path)
            self.sfx_cache[name].set_volume(self.sfx_volume)
        except Exception:
            pass
    
    def play_sfx(self, name: str) -> bool:
        """Hang effekt lejátszása. Ha channel, akkor nem ismétli a hangot."""
        if not self.enabled or name not in self.sfx_cache:
            return False
        try:
            self.sfx_cache[name].play()
            return True
        except Exception:
            return False
    
    def play_music(self, path: str, loop: bool = True):
        """Zene lejátszása fájlból."""
        if not self.enabled:
            return False
        try:
            if not os.path.exists(path):
                return False
            pygame.mixer.music.load(path)
            pygame.mixer.music.set_volume(self.music_volume)
            pygame.mixer.music.play(-1 if loop else 0)
            self.current_music = path
            return True
        except Exception:
            return False
    
    def stop_music(self):
        """Zene leállítása."""
        if self.enabled:
            pygame.mixer.music.stop()
            self.current_music = None
    
    def pause_music(self):
        if self.enabled:
            pygame.mixer.music.pause()
    
    def unpause_music(self):
        if self.enabled:
            pygame.mixer.music.unpause()
    
    def set_volume(self, sfx: float = None, music: float = None):
        """Hangerő beállítása (0.0 - 1.0)."""
        if sfx is not None:
            self.sfx_volume = max(0.0, min(1.0, sfx))
            for s in self.sfx_cache.values():
                s.set_volume(self.sfx_volume)
        if music is not None:
            self.music_volume = max(0.0, min(1.0, music))
            if self.enabled:
                pygame.mixer.music.set_volume(self.music_volume)
    
    def generate_tone(self, name: str, frequency: int = 440, duration: int = 200):
        """Egyszerű hang generálás (sin hullám) - ha nincs wav fájl."""
        if not self.enabled:
            return
        try:
            sample_rate = 22050
            n_samples = int(sample_rate * duration / 1000.0)
            buf = pygame.sndarray.make_sound(
                ((2**15 - 1) * __import__('numpy', fromlist=['']).sin(
                    2.0 * math.pi * frequency * 
                    __import__('numpy', fromlist=['']).arange(n_samples) / sample_rate
                )).astype(__import__('numpy', fromlist=['']).int16)
            )
            self.sfx_cache[name] = buf
            self.sfx_cache[name].set_volume(self.sfx_volume)
        except ImportError:
            pass  # nincs numpy, skip


# ═══════════════════════════════════════════════════════════════
# SPRITE / ANIMÁCIÓ
# ═══════════════════════════════════════════════════════════════

class Animation:
    """Képkocka alapú animáció."""
    def __init__(self, frames: list[pygame.Surface], speed: float = 0.1, loop: bool = True):
        self.frames = frames
        self.speed = speed
        self.loop = loop
        self.current_frame = 0.0
        self.done = False
    
    def update(self, dt: float):
        if self.done:
            return
        self.current_frame += dt / self.speed
        total = len(self.frames)
        if self.current_frame >= total:
            if self.loop:
                self.current_frame = self.current_frame % total
            else:
                self.current_frame = total - 1
                self.done = True
    
    def get_frame(self) -> pygame.Surface:
        idx = min(int(self.current_frame), len(self.frames) - 1)
        return self.frames[idx]
    
    def reset(self):
        self.current_frame = 0.0
        self.done = False


class SpriteSheet:
    """Sprite sheet kezelő."""
    def __init__(self, image_path: str):
        self.image = pygame.image.load(image_path).convert_alpha() if os.path.exists(image_path) else None
    
    def get_frame(self, x: int, y: int, w: int, h: int) -> pygame.Surface | None:
        if self.image is None:
            return None
        frame = pygame.Surface((w, h), pygame.SRCALPHA)
        frame.blit(self.image, (0, 0), (x, y, w, h))
        return frame
    
    def get_frames(self, cols: int, rows: int, w: int, h: int) -> list[pygame.Surface]:
        """Összes képkocka kinyerése."""
        frames = []
        for row in range(rows):
            for col in range(cols):
                f = self.get_frame(col * w, row * h, w, h)
                if f:
                    frames.append(f)
        return frames


def create_colored_surface(width: int, height: int, color: tuple) -> pygame.Surface:
    """Egyszerű színezett Surface készítése (ha nincs sprite kép)."""
    surf = pygame.Surface((width, height), pygame.SRCALPHA)
    surf.fill(color)
    return surf


# ═══════════════════════════════════════════════════════════════
# IDŐZÍTŐ / ESEMÉNY SCHEDULER
# ═══════════════════════════════════════════════════════════════

class TimerSystem:
    """Ismétlődő és egyszeri időzítők."""
    def __init__(self):
        self.timers: dict[str, float] = {}   # name -> current countdown
        self.intervals: dict[str, float] = {} # name -> interval
        self.one_shot: set[str] = set()       # egyszeri időzítők
        self.elapsed: float = 0.0
    
    def set(self, name: str, interval: float):
        """Ismétlődő időzítő létrehozása / átállítása."""
        self.timers[name] = interval
        self.intervals[name] = interval
        self.one_shot.discard(name)
    
    def set_timeout(self, name: str, delay: float):
        """Egyszeri időzítő (csak egyszer lesz ready=true)."""
        self.timers[name] = delay
        self.intervals[name] = delay
        self.one_shot.add(name)
    
    def ready(self, name: str) -> bool:
        """Időzítő letelt-e? Ha igen, automatikus reset."""
        if name not in self.timers:
            return False
        return self.timers[name] <= 0
    
    def done(self, name: str) -> bool:
        """Egyszeri időzítő letelt-e? (nem resetelődik)"""
        return name in self.timers and self.timers[name] <= 0 and name in self.one_shot
    
    def remove(self, name: str):
        """Időzítő törlése."""
        self.timers.pop(name, None)
        self.intervals.pop(name, None)
        self.one_shot.discard(name)
    
    def clear(self):
        """Minden időzítő törlése."""
        self.timers.clear()
        self.intervals.clear()
        self.one_shot.clear()
    
    def update(self, dt: float):
        """Minden képkockában hívandó."""
        self.elapsed += dt
        to_remove = []
        for name, remaining in self.timers.items():
            self.timers[name] = remaining - dt
        # Reset ismétlődő időzítők
        for name in list(self.timers.keys()):
            if self.timers[name] <= 0:
                if name not in self.one_shot:
                    self.timers[name] = self.intervals[name]
                else:
                    to_remove.append(name)
        for name in to_remove:
            self.timers.pop(name, None)
            self.intervals.pop(name, None)
            self.one_shot.discard(name)
    
    def get_remaining(self, name: str) -> float:
        """Visszaadja a hátralévő időt (0 ha nincs ilyen időzítő)."""
        return self.timers.get(name, 0.0)


# ═══════════════════════════════════════════════════════════════
# RÉSZECSKE RENDSZER
# ═══════════════════════════════════════════════════════════════

class Particle:
    def __init__(self, x, y, vx, vy, life, color, size, gravity=0):
        self.x = x
        self.y = y
        self.vx = vx
        self.vy = vy
        self.life = life
        self.max_life = life
        self.color = list(color) if isinstance(color, tuple) else color
        self.size = size
        self.gravity = gravity
        self.dead = False
    
    def update(self, dt):
        self.vy += self.gravity * dt * 60
        self.x += self.vx * dt * 60
        self.y += self.vy * dt * 60
        self.life -= dt
        if self.life <= 0:
            self.dead = True
    
    def draw(self, screen, camera=None):
        alpha = max(0, int(255 * self.life / self.max_life))
        x, y = self.x, self.y
        if camera:
            x -= camera.x - camera.shake_offset_x
            y -= camera.y - camera.shake_offset_y
        
        if alpha < 255:
            surf = pygame.Surface((int(self.size * 2), int(self.size * 2)), pygame.SRCALPHA)
            pygame.draw.circle(surf, (*self.color[:3], min(255, alpha)), 
                             (int(self.size), int(self.size)), int(self.size))
            screen.blit(surf, (int(x - self.size), int(y - self.size)))
        else:
            pygame.draw.circle(screen, self.color, (int(x), int(y)), int(self.size))


class ParticleSystem:
    """Részecske rendszer robbanáshoz, tűzhöz, nyomhoz, esőhöz, hóhoz."""
    def __init__(self):
        self.particles: list[Particle] = []
    
    def update(self, dt):
        for p in self.particles[:]:
            p.update(dt)
            if p.dead:
                self.particles.remove(p)
    
    def render(self, screen, camera: Camera = None):
        for p in self.particles:
            p.draw(screen, camera)
    
    def emit(self, x: float, y: float, count: int = 10, kind: str = "explosion",
             color: tuple = None, speed: float = None):
        """Részecskék kibocsátása.
        
        kind: "explosion", "spark", "trail", "smoke", "rain", "snow"
        """
        if speed is None:
            speed = 100
        if color is None:
            color = (255, 200, 50)
        
        for _ in range(count):
            if kind == "explosion":
                angle = random.uniform(0, math.pi * 2)
                spd = random.uniform(speed * 0.5, speed * 1.5)
                vx = math.cos(angle) * spd
                vy = math.sin(angle) * spd
                life = random.uniform(0.3, 0.8)
                sz = random.randint(2, 5)
                c = (random.randint(200, 255), random.randint(100, 200), random.randint(0, 50))
                g = 200
            elif kind == "spark":
                angle = random.uniform(0, math.pi * 2)
                spd = random.uniform(speed * 0.8, speed * 2.0)
                vx = math.cos(angle) * spd
                vy = math.sin(angle) * spd
                life = random.uniform(0.1, 0.4)
                sz = random.randint(1, 3)
                c = (255, 255, 200)
                g = 0
            elif kind == "trail":
                vx = random.uniform(-speed * 0.3, speed * 0.3)
                vy = random.uniform(-speed * 0.2, speed * 0.2) - 20
                life = random.uniform(0.2, 0.5)
                sz = random.randint(2, 4)
                c = color
                g = 50
            elif kind == "smoke":
                vx = random.uniform(-speed * 0.2, speed * 0.2)
                vy = random.uniform(-speed * 0.5, -speed * 0.1)
                life = random.uniform(0.8, 2.0)
                sz = random.randint(4, 12)
                c = (random.randint(100, 180), random.randint(100, 180), random.randint(100, 180))
                g = -10  # felfelé száll
            elif kind == "rain":
                vx = random.uniform(-10, 10)
                vy = random.uniform(300, 600)
                life = random.uniform(0.5, 1.0)
                sz = 1
                c = (180, 200, 255)
                g = 0
            elif kind == "snow":
                vx = random.uniform(-30, 30)
                vy = random.uniform(30, 80)
                life = random.uniform(2.0, 5.0)
                sz = random.randint(2, 5)
                c = (255, 255, 255)
                g = 20
            else:  # custom
                vx = random.uniform(-speed, speed)
                vy = random.uniform(-speed, speed)
                life = random.uniform(0.3, 0.8)
                sz = random.randint(2, 5)
                c = color
                g = 100
            
            self.particles.append(Particle(x, y, vx, vy, life, c, sz, g))
    
    def clear(self):
        self.particles.clear()


# ═══════════════════════════════════════════════════════════════
# UI RENDSZER (gomb, label, progress bar, text input)
# ═══════════════════════════════════════════════════════════════

class UISystem:
    """Felhasználói felület elemek."""
    def __init__(self):
        self.font_small = None
        self.font_medium = None
        self.font_large = None
        self._clicked_buttons: set[str] = set()
        self._prev_mouse = (0, 0, False)
        self.text_input_active = False
        self.text_input_buffer = ""
        self.text_input_cursor = 0
    
    def init_fonts(self, small=24, medium=36, large=72):
        try:
            self.font_small = pygame.font.Font(None, small)
            self.font_medium = pygame.font.Font(None, medium)
            self.font_large = pygame.font.Font(None, large)
        except Exception:
            self.font_small = pygame.font.Font(None, small)
            self.font_medium = pygame.font.Font(None, medium)
            self.font_large = pygame.font.Font(None, large)
    
    def draw_label(self, screen: pygame.Surface, text: str, pos: tuple,
                   color: tuple = (255, 255, 255), font=None, center: bool = False,
                   bg_color: tuple = None) -> pygame.Rect:
        """Szöveg kiírása a képernyőre."""
        if font is None:
            font = self.font_medium
        try:
            if bg_color:
                surf = font.render(text, True, color)
                bg_surf = pygame.Surface((surf.get_width() + 8, surf.get_height() + 4))
                bg_surf.fill(bg_color)
                if center:
                    screen.blit(bg_surf, (pos[0] - bg_surf.get_width()//2, pos[1]))
                    screen.blit(surf, (pos[0] - surf.get_width()//2 + 4, pos[1] + 2))
                    return bg_surf.get_rect(topleft=(pos[0] - bg_surf.get_width()//2, pos[1]))
                else:
                    screen.blit(bg_surf, pos)
                    screen.blit(surf, (pos[0] + 4, pos[1] + 2))
                    return bg_surf.get_rect(topleft=pos)
            else:
                surf = font.render(text, True, color)
                if center:
                    r = surf.get_rect(center=pos)
                    screen.blit(surf, r)
                    return r
                else:
                    screen.blit(surf, pos)
                    return surf.get_rect(topleft=pos)
        except Exception:
            return pygame.Rect(pos[0], pos[1], 0, 0)
    
    def button(self, screen: pygame.Surface, text: str, rect: pygame.Rect,
               color: tuple = (80, 80, 200), hover_color: tuple = (100, 100, 220),
               text_color: tuple = (255, 255, 255), font=None) -> bool:
        """Gomb. Visszaad True-t ha rákattintottak."""
        mouse_x, mouse_y = pygame.mouse.get_pos()
        mouse_down = pygame.mouse.get_pressed()[0]
        hovered = rect.collidepoint(mouse_x, mouse_y)
        
        # Rajzolás
        pygame.draw.rect(screen, hover_color if hovered else color, rect, border_radius=6)
        pygame.draw.rect(screen, (255, 255, 255, 60) if hovered else (0, 0, 0, 40), rect, 2, border_radius=6)
        
        if font is None:
            font = self.font_medium
        surf = font.render(text, True, text_color)
        screen.blit(surf, surf.get_rect(center=rect.center))
        
        # Kattintás detektálás (csak felfelé)
        btn_id = f"btn_{text}_{rect.x}_{rect.y}"
        if hovered and mouse_down and not self._prev_mouse[2]:
            self._clicked_buttons.add(btn_id)
            return False
        if btn_id in self._clicked_buttons and not mouse_down:
            self._clicked_buttons.discard(btn_id)
            return True
        if not mouse_down:
            self._clicked_buttons.discard(btn_id)
        
        return False
    
    def progress_bar(self, screen: pygame.Surface, x: int, y: int, w: int, h: int,
                     percent: float, color: tuple = (0, 255, 0),
                     bg_color: tuple = (60, 60, 60)):
        """Folyamatjelző sáv (0.0 - 1.0)."""
        pygame.draw.rect(screen, bg_color, (x, y, w, h), border_radius=4)
        fill_w = max(2, int(w * min(max(percent, 0), 1)))
        pygame.draw.rect(screen, color, (x, y, fill_w, h), border_radius=4)
        pygame.draw.rect(screen, (40, 40, 40), (x, y, w, h), 1, border_radius=4)
    
    def draw_text_input(self, screen: pygame.Surface, rect: pygame.Rect,
                        active: bool = False) -> str:
        """Szöveg beviteli mező. Visszaadja a beírt szöveget."""
        color = (100, 100, 200) if active else (80, 80, 80)
        pygame.draw.rect(screen, color, rect, border_radius=4)
        pygame.draw.rect(screen, (200, 200, 200) if active else (100, 100, 100), rect, 2, border_radius=4)
        
        if self.font_small:
            display_text = self.text_input_buffer
            if active and int(time.time() * 2) % 2:
                display_text += "|"
            surf = self.font_small.render(display_text or "Írj ide...", True, 
                                         (255, 255, 255) if display_text else (150, 150, 150))
            screen.blit(surf, (rect.x + 5, rect.y + (rect.h - surf.get_height()) // 2))
        
        return self.text_input_buffer
    
    def handle_text_event(self, event) -> str:
        """Text input esemény kezelése. Visszaadja a jelenlegi szöveget."""
        if not self.text_input_active:
            return self.text_input_buffer
        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_BACKSPACE:
                self.text_input_buffer = self.text_input_buffer[:-1]
            elif event.key == pygame.K_RETURN:
                result = self.text_input_buffer
                self.text_input_buffer = ""
                self.text_input_active = False
                return result
            else:
                if len(self.text_input_buffer) < 30:
                    self.text_input_buffer += event.unicode
        return self.text_input_buffer
    
    def update_mouse(self):
        """Egér állapot frissítése (minden képkockában hívandó)."""
        self._prev_mouse = (*pygame.mouse.get_pos(), pygame.mouse.get_pressed()[0])


# ═══════════════════════════════════════════════════════════════
# INPUT RENDSZER (billentyűzet + egér)
# ═══════════════════════════════════════════════════════════════

class InputSystem:
    """Input kezelés (billentyűzet, egér, egy képkockás események)."""
    def __init__(self):
        self.keys_down: set[int] = set()
        self.keys_pressed: set[int] = set()
        self.keys_just_pressed: set[int] = set()
        self.mouse_x = 0
        self.mouse_y = 0
        self.mouse_buttons = [False, False, False]
        self.mouse_just_pressed = [False, False, False]
        self._prev_mouse_buttons = [False, False, False]
        self.quit_requested = False
        self.all_events: list = []
    
    def update(self, events: list):
        """Minden képkockában hívandó a pygame.event.get() után."""
        self.all_events = events
        self.keys_just_pressed.clear()
        
        for event in events:
            if event.type == pygame.KEYDOWN:
                self.keys_down.add(event.key)
                self.keys_pressed.add(event.key)
                self.keys_just_pressed.add(event.key)
            elif event.type == pygame.KEYUP:
                self.keys_down.discard(event.key)
                self.keys_pressed.discard(event.key)
            elif event.type == pygame.MOUSEMOTION:
                self.mouse_x, self.mouse_y = event.pos
            elif event.type == pygame.MOUSEBUTTONDOWN:
                self.mouse_buttons[event.button - 1] = True
                self.mouse_just_pressed[event.button - 1] = True
            elif event.type == pygame.MOUSEBUTTONUP:
                self.mouse_buttons[event.button - 1] = False
            elif event.type == pygame.QUIT:
                self.quit_requested = True
    
    def key_pressed(self, key: int) -> bool:
        """Billentyű lenyomva tartva."""
        return key in self.keys_down
    
    def key_just_pressed(self, key: int) -> bool:
        """Billentyű pont most lett lenyomva (csak 1 képkocka)."""
        return key in self.keys_just_pressed
    
    @property
    def mouse_pos(self) -> tuple[int, int]:
        return (self.mouse_x, self.mouse_y)
    
    def mouse_pressed(self, button: int = 1) -> bool:
        """Egér gomb lenyomva."""
        return 0 <= button - 1 < len(self.mouse_buttons) and self.mouse_buttons[button - 1]
    
    def mouse_just_pressed(self, button: int = 1) -> bool:
        """Egér gomb most lett lenyomva (1 képkocka)."""
        return 0 <= button - 1 < len(self.mouse_just_pressed) and self.mouse_just_pressed[button - 1]
    
    def get_events(self) -> list:
        return self.all_events


# ═══════════════════════════════════════════════════════════════
# MENTÉS / BETÖLTÉS
# ═══════════════════════════════════════════════════════════════

class SaveSystem:
    """Játékállapot mentése és betöltése."""
    def __init__(self, save_dir: str = None):
        if save_dir is None:
            save_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "saves")
        self.save_dir = save_dir
        os.makedirs(self.save_dir, exist_ok=True)
        self.highscores: list[dict] = []
        self._load_highscores()
    
    def save(self, data: dict, slot: int = 0) -> bool:
        """Játékállapot mentése slot-ba."""
        try:
            path = os.path.join(self.save_dir, f"save_{slot}.json")
            with open(path, 'w', encoding='utf-8') as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
            return True
        except Exception:
            return False
    
    def load(self, slot: int = 0) -> dict | None:
        """Játékállapot betöltése slot-ból."""
        try:
            path = os.path.join(self.save_dir, f"save_{slot}.json")
            if not os.path.exists(path):
                return None
            with open(path, 'r', encoding='utf-8') as f:
                return json.load(f)
        except Exception:
            return None
    
    def delete(self, slot: int = 0):
        """Mentés törlése."""
        path = os.path.join(self.save_dir, f"save_{slot}.json")
        try: os.remove(path)
        except: pass
    
    def save_highscore(self, name: str, score: int, level: int = 1, data: dict = None):
        """Highscore mentése."""
        entry = {"name": name, "score": score, "level": level, "date": time.time()}
        if data:
            entry["data"] = data
        self.highscores.append(entry)
        self.highscores.sort(key=lambda x: x["score"], reverse=True)
        self.highscores = self.highscores[:100]  # max 100
        self._save_highscores()
    
    def get_highscores(self, limit: int = 10) -> list[dict]:
        """Top highscore lista."""
        return self.highscores[:limit]
    
    def _load_highscores(self):
        path = os.path.join(self.save_dir, "highscores.json")
        try:
            if os.path.exists(path):
                with open(path, 'r') as f:
                    self.highscores = json.load(f)
        except:
            self.highscores = []
    
    def _save_highscores(self):
        path = os.path.join(self.save_dir, "highscores.json")
        try:
            with open(path, 'w') as f:
                json.dump(self.highscores, f, ensure_ascii=False, indent=2)
        except:
            pass


# ═══════════════════════════════════════════════════════════════
# FŐ ENGINE OSZTÁLY
# ═══════════════════════════════════════════════════════════════

class DKAEngine:
    """DKA V3 — Komplett LLM Game Engine.
    
    Az összes alrendszert tartalmazza. Az LLM 4-7 függvényt ad
    (init, update, draw, collision + opcionális menu_init, menu_draw, menu_handle).
    Az engine minden képességet az `engine` paraméteren keresztül ad át.
    """
    
    # Állapotok
    STATE_MENU = "MENU"
    STATE_PLAYING = "PLAYING"
    STATE_PAUSED = "PAUSED"
    STATE_GAME_OVER = "GAME_OVER"
    STATE_LEVEL_SELECT = "LEVEL_SELECT"
    STATE_INTRO = "INTRO"
    STATE_WIN = "WIN"
    
    def __init__(self, width: int = 800, height: int = 600, fps: int = 60,
                 title: str = "DKA + LLM Játék", game_dir: str = None):
        self.width = width
        self.height = height
        self.fps = fps
        self.title = title
        self.game_dir = game_dir or os.path.dirname(os.path.abspath(__file__))
        self.state = self.STATE_MENU
        self.running = True
        self.clock = None
        self.screen = None
        self.dt = 0.0
        self.frame_count = 0
        self.debug_mode = False
        
        # Alrendszerek
        self.camera = Camera(width, height)
        self.tilemap = TileMap()
        self.audio = AudioSystem()
        self.timer = TimerSystem()
        self.particles = ParticleSystem()
        self.filter = ScreenFilter()
        self.ui = UISystem()
        self.input = InputSystem()
        self.save = SaveSystem(os.path.join(self.game_dir, "saves"))
        
        # LLM által biztosított függvények
        self.llm_init = None
        self.llm_update = None
        self.llm_draw = None
        self.llm_collision = None
        self.llm_menu_init = None
        self.llm_menu_draw = None
        self.llm_menu_handle = None
        
        # Játék specifikus globális változók
        self.game_vars: dict = {}
        
        # Nyomkövetés
        self._game_over_triggered = False
        self._game_over_time = 0.0
        self._win_triggered = False
        self._screen_shots: list[str] = []
    
    # ── fő ciklus ──────────────────────────────────────────
    
    def run(self, llm_code: str | dict, title: str = None,
            width: int = None, height: int = None):
        """Belépési pont. Összerakja a játékot és elindítja.
        
        llm_code: str (=== szekciókkal) vagy dict ({"init": "...", ...})
        """
        if pygame is None:
            print("❌ Pygame nincs telepítve!")
            return
        
        pygame.init()
        if title: self.title = title
        if width: self.width = width
        if height: self.height = height
        
        self.screen = pygame.display.set_mode((self.width, self.height))
        pygame.display.set_caption(self.title)
        self.clock = pygame.time.Clock()
        
        # Audio init
        self.audio.init()
        
        # UI fontok
        self.ui.init_fonts()
        
        # LLM kód összerakása
        if isinstance(llm_code, str):
            sections = self._parse_sections(llm_code)
        else:
            sections = llm_code
        
        functions = self._compile_functions(sections)
        if functions is None:
            print("❌ Hiba: nem sikerült lefordítani a játéklogikát!")
            return
        
        # Menu alapértelmezés
        if self.llm_menu_init is None:
            self.llm_menu_init = lambda: None
        if self.llm_menu_draw is None:
            self.llm_menu_draw = lambda s: (
                self.ui.draw_label(s, self.title, 
                                 (self.width//2, self.height//3),
                                 (255, 255, 255), self.ui.font_large, center=True),
                self.ui.draw_label(s, "Nyomj SPACE-t a kezdéshez",
                                 (self.width//2, self.height//2),
                                 (200, 200, 200), center=True),
            )
        if self.llm_menu_handle is None:
            self.llm_menu_handle = lambda: (
                self.switch_state(self.STATE_PLAYING) 
                if self.input.key_just_pressed(pygame.K_SPACE) or
                   self.input.key_just_pressed(pygame.K_RETURN) 
                else None
            )
        
        # Init
        if self.llm_init:
            self.llm_init(self)
        if self.llm_menu_init:
            self.llm_menu_init(self)
        
        # Fő ciklus
        while self.running:
            self.dt = self.clock.tick(self.fps) / 1000.0
            self.frame_count += 1
            
            # Input
            events = pygame.event.get()
            self.input.update(events)
            self.ui.update_mouse()
            
            # UI text input események továbbítása
            for event in events:
                self.ui.handle_text_event(event)
            
            # Quit
            if self.input.quit_requested:
                self.running = False
                break
            
            # ESC minden állapotból kilép
            if self.input.key_just_pressed(pygame.K_ESCAPE):
                if self.state == self.STATE_PLAYING:
                    self.switch_state(self.STATE_PAUSED)
                elif self.state == self.STATE_PAUSED:
                    self.switch_state(self.STATE_PLAYING)
                elif self.state in (self.STATE_MENU, self.STATE_GAME_OVER, self.STATE_WIN):
                    self.running = False
            
            # F1 debug
            if self.input.key_just_pressed(pygame.K_F1):
                self.debug_mode = not self.debug_mode
            
            # F12 screenshot
            if self.input.key_just_pressed(pygame.K_F12):
                self._take_screenshot()
            
            # Állapot gép
            if self.state == self.STATE_MENU:
                self.llm_menu_handle(self)
                self.timer.update(self.dt)
            elif self.state == self.STATE_PLAYING:
                if self.llm_update:
                    self.llm_update(self)
                self.timer.update(self.dt)
                self.camera.update()
                self.particles.update(self.dt)
                self.filter.update(self.dt)
                
                # Collision check
                if self.llm_collision is not None and not self._game_over_triggered:
                    if self.llm_collision(self):
                        self._game_over_triggered = True
                        self._game_over_time = 0
                        self.switch_state(self.STATE_GAME_OVER)
            elif self.state == self.STATE_PAUSED:
                pass  # freeze
            elif self.state == self.STATE_GAME_OVER:
                self._game_over_time += self.dt
                self.filter.update(self.dt)
                self.particles.update(self.dt)
            elif self.state == self.STATE_WIN:
                self._game_over_time += self.dt
                self.filter.update(self.dt)
            elif self.state == self.STATE_INTRO:
                self.timer.update(self.dt)
                self.filter.update(self.dt)
            elif self.state == self.STATE_LEVEL_SELECT:
                pass
            
            # Rajzolás
            self.screen.fill((0, 0, 0))
            
            if self.state in (self.STATE_PLAYING, self.STATE_PAUSED):
                if self.llm_draw:
                    self.llm_draw(self)
                self.particles.render(self.screen, self.camera)
                self.filter.render(self.screen)
                
                if self.state == self.STATE_PAUSED:
                    self._draw_pause_overlay()
            elif self.state == self.STATE_MENU:
                if self.llm_menu_draw:
                    self.llm_menu_draw(self)
                self.filter.render(self.screen)
            elif self.state == self.STATE_GAME_OVER:
                if self.llm_draw:
                    self.llm_draw(self)
                self.particles.render(self.screen, self.camera)
                self._draw_game_over_screen()
            elif self.state == self.STATE_WIN:
                if self.llm_draw:
                    self.llm_draw(self)
                self._draw_win_screen()
            elif self.state == self.STATE_INTRO:
                if self.llm_menu_draw:
                    self.llm_menu_draw(self)
                self.filter.render(self.screen)
            elif self.state == self.STATE_LEVEL_SELECT:
                self._draw_level_select()
            
            # Debug info
            if self.debug_mode:
                self._draw_debug()
            
            pygame.display.flip()
        
        pygame.quit()
        sys.exit()
    
    def switch_state(self, new_state: str):
        """Állapot váltás."""
        old_state = self.state
        self.state = new_state
        
        if new_state == self.STATE_PLAYING and old_state == self.STATE_GAME_OVER:
            # Új játék
            self._game_over_triggered = False
            if self.llm_init:
                self.llm_init(self)
            self.particles.clear()
            self.timer.clear()
        
        if new_state == self.STATE_PLAYING and old_state == self.STATE_WIN:
            self._win_triggered = False
            if self.llm_init:
                self.llm_init(self)
            self.particles.clear()
            self.timer.clear()
    
    def quit(self):
        """Játék azonnali kilépés."""
        self.running = False
    
    # ── képernyő rajzolások ────────────────────────────────
    
    def _draw_pause_overlay(self):
        """Szünet overlay."""
        s = pygame.Surface((self.width, self.height), pygame.SRCALPHA)
        s.fill((0, 0, 0, 128))
        self.screen.blit(s, (0, 0))
        self.ui.draw_label(self.screen, "SZÜNET", 
                         (self.width//2, self.height//2 - 30),
                         (255, 255, 255), self.ui.font_large, center=True)
        self.ui.draw_label(self.screen, "ESC = folytatás",
                         (self.width//2, self.height//2 + 30),
                         (180, 180, 180), center=True)
    
    def _draw_game_over_screen(self):
        """Game Over képernyő."""
        s = pygame.Surface((self.width, self.height), pygame.SRCALPHA)
        s.fill((0, 0, 0, 160))
        self.screen.blit(s, (0, 0))
        self.ui.draw_label(self.screen, "GAME OVER",
                         (self.width//2, self.height//2 - 50),
                         (255, 50, 50), self.ui.font_large, center=True)
        
        # Pontszám
        try:
            score_val = self.game_vars.get("score", 0)
            self.ui.draw_label(self.screen, f"Pontszám: {score_val}",
                             (self.width//2, self.height//2 + 10),
                             (255, 255, 255), self.ui.font_medium, center=True)
        except:
            pass
        
        # Gombok
        retry_rect = pygame.Rect(self.width//2 - 100, self.height//2 + 60, 200, 40)
        if self.ui.button(self.screen, "Új játék", retry_rect):
            self.switch_state(self.STATE_PLAYING)
        
        menu_rect = pygame.Rect(self.width//2 - 100, self.height//2 + 110, 200, 40)
        if self.ui.button(self.screen, "Menü", menu_rect):
            self.switch_state(self.STATE_MENU)
    
    def _draw_win_screen(self):
        """Győzelem képernyő."""
        s = pygame.Surface((self.width, self.height), pygame.SRCALPHA)
        s.fill((0, 0, 0, 120))
        self.screen.blit(s, (0, 0))
        self.ui.draw_label(self.screen, "GYŐZELEM!",
                         (self.width//2, self.height//2 - 50),
                         (50, 255, 50), self.ui.font_large, center=True)
        
        try:
            score_val = self.game_vars.get("score", 0)
            self.ui.draw_label(self.screen, f"Pontszám: {score_val}",
                             (self.width//2, self.height//2 + 10),
                             (255, 255, 255), self.ui.font_medium, center=True)
        except:
            pass
        
        retry_rect = pygame.Rect(self.width//2 - 100, self.height//2 + 60, 200, 40)
        if self.ui.button(self.screen, "Újra", retry_rect):
            self.switch_state(self.STATE_PLAYING)
        
        menu_rect = pygame.Rect(self.width//2 - 100, self.height//2 + 110, 200, 40)
        if self.ui.button(self.screen, "Menü", menu_rect):
            self.switch_state(self.STATE_MENU)
    
    def _draw_level_select(self):
        """Pályaválasztó."""
        self.ui.draw_label(self.screen, "PÁLYA VÁLASZTÁS",
                         (self.width//2, 60),
                         (255, 255, 255), self.ui.font_large, center=True)
        
        for i in range(1, 9):
            row = (i - 1) // 4
            col = (i - 1) % 4
            x = self.width//2 - 180 + col * 120
            y = 120 + row * 90
            
            btn_rect = pygame.Rect(x, y, 100, 70)
            unlocked = self.save.get_highscores() or i <= 2
            
            if self.ui.button(self.screen, 
                            f"{i}" if unlocked else "🔒",
                            btn_rect,
                            color=(60, 150, 60) if unlocked else (80, 80, 80)):
                if unlocked:
                    self.game_vars["level"] = i
                    self.switch_state(self.STATE_PLAYING)
    
    def _draw_debug(self):
        """Debug információk."""
        lines = [
            f"FPS: {int(self.clock.get_fps())}",
            f"State: {self.state}",
            f"Frame: {self.frame_count}",
            f"Particles: {len(self.particles.particles)}",
            f"Camera: ({int(self.camera.x)}, {int(self.camera.y)})",
        ]
        y = 5
        for line in lines:
            self.ui.draw_label(self.screen, line, (5, y), 
                             (255, 255, 0), self.ui.font_small)
            y += 18
    
    def _take_screenshot(self):
        """Képernyőkép mentés."""
        name = f"screenshot_{int(time.time())}.png"
        path = os.path.join(self.game_dir, name)
        try:
            pygame.image.save(self.screen, path)
            self._screen_shots.append(path)
        except:
            pass
    
    def trigger_win(self):
        """Győzelem állapot aktiválása."""
        if not self._win_triggered:
            self._win_triggered = True
            self.switch_state(self.STATE_WIN)
    
    # ── tile map segéd ─────────────────────────────────────
    
    def load_tilemap(self, data: dict):
        """Tile map betöltése."""
        self.tilemap.load(data)
        # Kamera világméret beállítása
        self.camera.world_width = self.tilemap.width * self.tilemap.tile_size
        self.camera.world_height = self.tilemap.height * self.tilemap.tile_size
    
    # ── LLM kód feldolgozás ────────────────────────────────
    
    def _parse_sections(self, text: str) -> dict[str, str]:
        """LLM válaszból kinyeri a szekciókat."""
        result = {}
        current_section = None
        current_code = []
        
        for line in text.split("\n"):
            if line.strip().startswith("==="):
                if current_section and current_code:
                    result[current_section] = "\n".join(current_code).strip()
                current_code = []
                match = re.search(r'===\s*(\w+)\s*===', line)
                current_section = match.group(1) if match else None
            elif current_section:
                current_code.append(line)
        
        if current_section and current_code:
            result[current_section] = "\n".join(current_code).strip()
        
        return result
    
    def _compile_functions(self, sections: dict[str, str]) -> bool:
        """LLM kódból Python függvények létrehozása."""
        import types
        
        # Függvények template-je
        func_templates = {
            "init": ("engine", "    pass"),
            "update": ("engine", "    pass"),
            "draw": ("engine", "    pass"),
            "collision": ("engine", "    return False"),
            "menu_init": ("engine", "    pass"),
            "menu_draw": ("engine", "    pass"),
            "menu_handle": ("engine", "    pass"),
        }
        
        all_code = ""
        for key, (param, default) in func_templates.items():
            body = sections.get(key, default)
            func_code = f"def _llm_{key}({param}):\n"
            for bl in body.split("\n"):
                if not bl.strip():
                    func_code += "\n"
                else:
                    # Megőrizzük a relatív indentációt (for/if/while törzsek)
                    orig_indent = len(bl) - len(bl.lstrip())
                    content = bl.strip()
                    func_code += "    " + (" " * orig_indent) + content + "\n"
            all_code += func_code + "\n"
        
        # Fordítás
        try:
            compiled = compile(all_code, '<llm_game>', 'exec')
        except SyntaxError as e:
            # Próbáljuk javítani
            all_code = self._fix_syntax(all_code, e)
            try:
                compiled = compile(all_code, '<llm_game>', 'exec')
            except SyntaxError as e2:
                print(f"❌ Szintaxis hiba (nem javítható): {e2}")
                return None
        
        # Végrehajtás
        local_ns = {}
        try:
            exec(compiled, local_ns)
        except Exception as e:
            print(f"❌ Végrehajtási hiba: {e}")
            return None
        
        # Függvények kinyerése
        self.llm_init = local_ns.get("_llm_init", None)
        self.llm_update = local_ns.get("_llm_update", None)
        self.llm_draw = local_ns.get("_llm_draw", None)
        self.llm_collision = local_ns.get("_llm_collision", None)
        self.llm_menu_init = local_ns.get("_llm_menu_init", None)
        self.llm_menu_draw = local_ns.get("_llm_menu_draw", None)
        self.llm_menu_handle = local_ns.get("_llm_menu_handle", None)
        
        return True
    
    def _fix_syntax(self, code: str, error: SyntaxError) -> str:
        """Szintaxis hiba javítása."""
        lines = code.split("\n")
        if error.lineno and 0 < error.lineno <= len(lines):
            idx = error.lineno - 1
            if "unexpected indent" in str(error.msg):
                lines[idx] = " " * 4 + lines[idx].lstrip()
            elif "unexpected EOF" in str(error.msg):
                lines.append("    pass")
        return "\n".join(lines)
    
    # ── játékos segéd változók ──────────────────────────────
    
    def set_var(self, name: str, value):
        """Globális játékváltozó beállítása."""
        self.game_vars[name] = value
    
    def get_var(self, name: str, default=None):
        """Globális játékváltozó lekérése."""
        return self.game_vars.get(name, default)
    
    def inc_var(self, name: str, amount=1) -> int:
        """Változó növelése."""
        current = self.game_vars.get(name, 0)
        self.game_vars[name] = current + amount
        return self.game_vars[name]
    
    # ── statikus formázó (visszafelé kompatibilitás) ──────
    
    @staticmethod
    def format_prompt(game_description: str) -> str:
        """Összeállítja a prompt-ot az LLM-nek a játéklogika kéréséhez."""
        return f"""Egy Pygame játék logikáját kell megírnod.
A DKA motor biztosítja a teljes infrastruktúrát, te csak a játéklogikát.

Feladat: {game_description}

Írj 4-7 függvényt. CSAK a függvények törzsét add meg.

Az `engine` paraméteren keresztül a következőket használhatod:

  engine.width, engine.height        # Képernyő méret
  engine.dt                          # Delta time (másodperc)
  engine.state                       # Jelenlegi állapot
  engine.switch_state("PLAYING")     # Állapot váltás
  engine.quit()                      # Kilépés
  engine.trigger_win()               # Győzelem
  engine.debug_mode                  # Debug mód be/ki

  engine.set_var("score", 100)       # Változó tárolás
  engine.get_var("score")            # Változó lekérés
  engine.inc_var("score", 10)        # Változó növelés

  engine.input.key_pressed(K_LEFT)          # Billentyű lenyomva
  engine.input.key_just_pressed(K_SPACE)    # Billentyű most lett lenyomva
  engine.input.mouse_pos                     # (x, y) egér pozíció
  engine.input.mouse_pressed(1)             # Egér gomb lenyomva
  engine.input.mouse_just_pressed(1)        # Egér gomb most lett lenyomva

  engine.timer.set("spawn", 2.0)    # Ismétlődő időzítő (2 mp)
  engine.timer.ready("spawn")       # Igaz ha letelt
  engine.timer.set_timeout("msg", 5.0)  # Egyszeri időzítő
  engine.timer.done("msg")          # Igaz ha letelt

  engine.camera.follow(x, y)        # Kamera követés
  engine.camera.shake(5)            # Kamera shake
  engine.camera.world_to_screen(wx, wy) -> (sx, sy)

  engine.particles.emit(x, y, 10, "explosion")  # Részecskék
  # kind: "explosion", "spark", "trail", "smoke", "rain", "snow"

  engine.filter.flash((255,255,255))   # Villanás
  engine.filter.fade_out(1.0)          # Elhalványulás
  engine.filter.fade_in(1.0)           # Bevilágítás

  engine.ui.draw_label(screen, "szöveg", (x, y), WHITE)
  engine.ui.button(screen, "Start", rect) -> True/False
  engine.ui.progress_bar(screen, x, y, w, h, 0.5, GREEN)
  engine.ui.text_input_active = True   # Text input bekapcsolás

  engine.audio.play_sfx("explosion")    # Hang
  engine.audio.play_music("bgm.mp3")    # Zene
  engine.audio.set_volume(sfx=0.5, music=0.3)

  engine.tilemap.load(tiledata)        # Tile map betöltés
  engine.tilemap.collides(rect)        # Ütközés vizsgálat
  engine.tilemap.get_tile(layer, col, row)
  engine.tilemap.set_tile(layer, col, row, value)
  engine.load_tilemap(data)            # Teljes tilemap + kamera beállítás

  engine.save.save(data, slot=0)       # Mentés
  engine.save.load(slot=0)             # Betöltés
  engine.save.save_highscore("name", score)

Elérhető színek: WHITE, BLACK, RED, DARK_RED, GREEN, DARK_GREEN, BLUE, DARK_BLUE,
YELLOW, GOLD, PURPLE, MAGENTA, CYAN, TEAL, ORANGE, BROWN, GRAY, DARK_GRAY, LIGHT_GRAY, PINK

Konstansok: SCREEN_WIDTH, SCREEN_HEIGHT, FPS

--- Függvények ---

(1) ===init===
Játékállapot inicializálása. engine.set_var()-rel tárold a változókat.
Példa: engine.set_var("score", 0); engine.set_var("lives", 3)

(2) ===update===
Minden képkockában fut. Mozgás, spawn, AI, input.
Példa: if engine.input.key_pressed(K_LEFT): engine.set_var("x", engine.get_var("x", 400) - 5)

(3) ===draw===
Minden képkockában fut. Objektumok kirajzolása.
A screen váltózót engine.screen-ként éred el.
Példa: pygame.draw.rect(engine.screen, BLUE, (x, y, 40, 40))

(4) ===collision===
return True ha game over, False ha nem.

(5) ===menu_init=== (opcionális)
Menu init, ha nincs, alapértelmezett menü.

(6) ===menu_draw=== (opcionális)
Menu rajzolás. Alap: SPACE indítás.

(7) ===menu_handle=== (opcionális)
Menu input kezelés.
"""
    
    # ── régi API kompatibilitás ────────────────────────────
    
    def assemble(self, llm_response: str) -> str:
        """Régi API: str visszaadása (megtartva a kompatibilitást)."""
        sections = self._parse_sections(llm_response)
        code = f"""import pygame
import random
import sys
import math

# === KONSTANSOK ===
SCREEN_WIDTH = {self.width}
SCREEN_HEIGHT = {self.height}
FPS = {self.fps}

# === SZÍNEK ===
"""
        for name, rgb in COLORS.items():
            code += f"{name} = {rgb}\n"
        
        code += f"""
# === JÁTÉKLOGIKA (LLM) ===
"""
        func_templates = {
            "init": ("def init_game(engine):", "    pass"),
            "update": ("def update_game(engine):", "    pass"),
            "draw": ("def draw_game(engine):", "    pass"),
            "collision": ("def collision_check(engine):", "    return False"),
        }
        
        for key, (header, default) in func_templates.items():
            code += f"\n{header}\n"
            body = sections.get(key, default)
            for line in body.split("\n"):
                if line.strip():
                    code += f"    {line}\n"
                else:
                    code += "\n"
        
        code += """
# === FŐ JÁTÉKCIKLUS ===
def main():
    pygame.init()
    screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
    pygame.display.set_caption("DKA + LLM Játék")
    clock = pygame.time.Clock()
    
    class EngineStub:
        pass
    engine = EngineStub()
    engine.width = SCREEN_WIDTH
    engine.height = SCREEN_HEIGHT
    engine.screen = screen
    
    init_game(engine)
    running = True
    
    while running:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
        
        keys = pygame.key.get_pressed()
        update_game(engine)
        
        if collision_check(engine):
            running = False
        
        screen.fill((0, 0, 0))
        draw_game(engine)
        
        try:
            font = pygame.font.Font(None, 36)
            score_text = font.render(f"Score: {score}", True, (255, 255, 255))
            screen.blit(score_text, (10, 10))
        except:
            pass
        
        pygame.display.flip()
        clock.tick(FPS)
    
    screen.fill((0, 0, 0))
    font_big = pygame.font.Font(None, 72)
    game_over = font_big.render("GAME OVER", True, (255, 0, 0))
    text_rect = game_over.get_rect(center=(SCREEN_WIDTH//2, SCREEN_HEIGHT//2 - 30))
    screen.blit(game_over, text_rect)
    pygame.display.flip()
    pygame.time.wait(3000)
    pygame.quit()
    sys.exit()

if __name__ == "__main__":
    main()
"""
        return code
    
    def validate(self, code: str, timeout: int = 5) -> tuple[bool, str]:
        """Fordítás + futás teszt."""
        current = code
        for attempt in range(3):
            try:
                compile(current, '<game>', 'exec')
            except SyntaxError as e:
                current = self._fix_syntax(current, e)
                continue
            
            with tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False, encoding='utf-8') as f:
                f.write(current)
                tmp = f.name
            
            try:
                os.environ['SDL_VIDEODRIVER'] = 'dummy'
                result = subprocess.run(
                    [sys.executable, tmp],
                    capture_output=True, text=True, timeout=timeout,
                    env={**os.environ, 'SDL_VIDEODRIVER': 'dummy'}
                )
                if result.returncode == 0:
                    os.unlink(tmp)
                    return True, current
                
                err = result.stderr
                current = self._fix_runtime(current, err)
            except subprocess.TimeoutExpired:
                os.unlink(tmp)
                return True, current
            except Exception as e:
                current = self._fix_runtime(current, str(e))
            finally:
                try: os.unlink(tmp)
                except: pass
        
        return False, current
    
    def _fix_runtime(self, code: str, error: str) -> str:
        var_match = re.search(r"name '(\w+)' is not defined", error)
        if var_match:
            var = var_match.group(1)
            if var in ('score',):
                code = code.replace("def init_game(engine):",
                    f"def init_game(engine):\n    global {var}\n    {var} = 0", 1)
            elif var == 'enemies':
                code = code.replace("def init_game(engine):",
                    "def init_game(engine):\n    global enemies\n    enemies = []", 1)
        
        return code
