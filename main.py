import pygame
import sys
import random
import array
import math

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------
SCREEN_W, SCREEN_H = 800, 600
FPS = 60

BLACK   = (  0,   0,   0)
WHITE   = (255, 255, 255)
GREEN   = (  0, 255,   0)
RED     = (255,   0,   0)
CYAN    = (  0, 255, 255)
YELLOW  = (255, 255,   0)
MAGENTA = (255,   0, 255)
ORANGE  = (255, 128,   0)

ENEMY_COLS      = 11
ENEMY_ROWS      = 5
ENEMY_SPACING_X = 60
ENEMY_SPACING_Y = 48
ENEMY_START_X   = 80
ENEMY_START_Y   = 90


# ---------------------------------------------------------------------------
# Drawing helpers – pixel-art alien silhouettes
# ---------------------------------------------------------------------------
def _draw_crab(surface, cx, cy, color, frame):
    """Top-row enemy (magenta crab)."""
    pygame.draw.rect(surface, color, (cx - 10, cy - 5,  20, 11))
    pygame.draw.rect(surface, color, (cx -  8, cy - 12,  5,  7))
    pygame.draw.rect(surface, color, (cx +  3, cy - 12,  5,  7))
    if frame == 0:
        pygame.draw.line(surface, color, (cx - 14, cy),     (cx - 18, cy + 7), 2)
        pygame.draw.line(surface, color, (cx + 14, cy),     (cx + 18, cy + 7), 2)
        pygame.draw.line(surface, color, (cx -  6, cy + 5), (cx -  2, cy + 10), 2)
        pygame.draw.line(surface, color, (cx +  6, cy + 5), (cx +  2, cy + 10), 2)
    else:
        pygame.draw.line(surface, color, (cx - 14, cy),     (cx - 10, cy + 7), 2)
        pygame.draw.line(surface, color, (cx + 14, cy),     (cx + 10, cy + 7), 2)
        pygame.draw.line(surface, color, (cx -  6, cy + 5), (cx - 10, cy + 10), 2)
        pygame.draw.line(surface, color, (cx +  6, cy + 5), (cx + 10, cy + 10), 2)


def _draw_squid(surface, cx, cy, color, frame):
    """Middle-row enemy (cyan squid)."""
    pygame.draw.rect(surface, color, (cx -  8, cy - 7, 16, 13))
    pygame.draw.rect(surface, color, (cx -  4, cy - 12, 8,  6))
    pygame.draw.rect(surface, BLACK, (cx -  6, cy - 5,  4,  4))
    pygame.draw.rect(surface, BLACK, (cx +  2, cy - 5,  4,  4))
    tentacles = [-10, -4, 4, 10] if frame == 0 else [-12, -4, 4, 12]
    for ox in tentacles:
        pygame.draw.line(surface, color, (cx + ox // 2, cy + 6), (cx + ox, cy + 13), 2)


def _draw_octopus(surface, cx, cy, color, frame):
    """Bottom-row enemy (green octopus)."""
    pygame.draw.ellipse(surface, color, (cx - 10, cy - 8, 20, 16))
    pygame.draw.rect(surface, BLACK, (cx -  6, cy - 6,  4,  4))
    pygame.draw.rect(surface, BLACK, (cx +  2, cy - 6,  4,  4))
    offsets = [-14, -6, 6, 14] if frame == 0 else [-12, -4, 4, 12]
    for ox in offsets:
        pygame.draw.line(surface, color, (cx + ox // 2, cy + 7), (cx + ox, cy + 14), 2)


# ---------------------------------------------------------------------------
# Game objects
# ---------------------------------------------------------------------------
class Player:
    W, H   = 40, 18
    SPEED  = 5

    def __init__(self):
        self.x     = SCREEN_W // 2
        self.y     = SCREEN_H - 52
        self.rect  = pygame.Rect(self.x - self.W // 2, self.y - self.H // 2, self.W, self.H)
        self.alive = True

    def update(self, keys):
        if keys[pygame.K_LEFT]  or keys[pygame.K_a]:
            self.x -= self.SPEED
        if keys[pygame.K_RIGHT] or keys[pygame.K_d]:
            self.x += self.SPEED
        self.x = max(self.W // 2, min(SCREEN_W - self.W // 2, self.x))
        self.rect.centerx = self.x
        self.rect.centery  = self.y

    def draw(self, surface):
        pygame.draw.rect(surface, GREEN, self.rect, border_radius=3)
        pygame.draw.rect(surface, GREEN, (self.x - 3, self.y - self.H // 2 - 9, 6, 9))


class Bullet:
    W, H = 3, 12

    def __init__(self, x, y, speed, color):
        self.x, self.y = x, y
        self.speed     = speed
        self.color     = color
        self.rect      = pygame.Rect(x - self.W // 2, y - self.H // 2, self.W, self.H)
        self.active    = True

    def update(self):
        self.y       += self.speed
        self.rect.centery = self.y
        if self.y < 0 or self.y > SCREEN_H:
            self.active = False

    def draw(self, surface):
        pygame.draw.rect(surface, self.color, self.rect)


class Enemy:
    W, H = 36, 22
    COLORS = [MAGENTA, CYAN, CYAN, GREEN, GREEN]
    POINTS = [   30,    20,   20,    10,    10]

    def __init__(self, col, row, x, y):
        self.col   = col
        self.row   = row
        self.x     = float(x)
        self.y     = float(y)
        self.rect  = pygame.Rect(int(x) - self.W // 2, int(y) - self.H // 2, self.W, self.H)
        self.alive = True
        self.color = self.COLORS[row]
        self.points = self.POINTS[row]

    def sync_rect(self):
        self.rect.centerx = int(self.x)
        self.rect.centery  = int(self.y)

    def draw(self, surface, frame):
        if not self.alive:
            return
        cx, cy = int(self.x), int(self.y)
        if self.row == 0:
            _draw_crab(surface, cx, cy, self.color, frame)
        elif self.row <= 2:
            _draw_squid(surface, cx, cy, self.color, frame)
        else:
            _draw_octopus(surface, cx, cy, self.color, frame)


class Shield:
    BS = 5   # block size

    def __init__(self, cx, y):
        layout = [
            [1, 1, 1, 1, 1, 1, 1, 1, 1, 1],
            [1, 1, 1, 1, 1, 1, 1, 1, 1, 1],
            [1, 1, 1, 1, 1, 1, 1, 1, 1, 1],
            [1, 1, 1, 1, 1, 1, 1, 1, 1, 1],
            [1, 1, 0, 0, 0, 0, 0, 0, 1, 1],
        ]
        cols = len(layout[0])
        rows = len(layout)
        ox   = cx - cols * self.BS // 2
        self.blocks = []
        for r, line in enumerate(layout):
            for c, cell in enumerate(line):
                if cell:
                    self.blocks.append(
                        pygame.Rect(ox + c * self.BS, y + r * self.BS, self.BS, self.BS)
                    )

    def draw(self, surface):
        for b in self.blocks:
            pygame.draw.rect(surface, GREEN, b)

    def hit(self, bullet_rect):
        for b in self.blocks:
            if b.colliderect(bullet_rect):
                self.blocks.remove(b)
                return True
        return False

    def erode_bottom(self, enemy_rect):
        """Enemies destroy shield blocks they overlap."""
        self.blocks = [b for b in self.blocks if not b.colliderect(enemy_rect)]


class UFO:
    W, H   = 52, 18
    SPEED  = 2
    POINTS = 150

    def __init__(self):
        self.active = False
        self.x      = 0.0
        self.y      = 44
        self.dir    = 1
        self.rect   = pygame.Rect(0, self.y - self.H // 2, self.W, self.H)

    def spawn(self):
        if self.active:
            return
        self.dir    = random.choice([-1, 1])
        self.x      = -self.W if self.dir == 1 else SCREEN_W + self.W
        self.active = True

    def update(self):
        if not self.active:
            return
        self.x          += self.SPEED * self.dir
        self.rect.centerx = int(self.x)
        self.rect.centery  = self.y
        if self.x < -self.W or self.x > SCREEN_W + self.W:
            self.active = False

    def draw(self, surface):
        if not self.active:
            return
        cx, cy = int(self.x), self.y
        pygame.draw.ellipse(surface, RED,    (cx - 26, cy - 8,  52, 16))
        pygame.draw.ellipse(surface, RED,    (cx - 13, cy - 18, 26, 14))
        for ox in range(-20, 22, 8):
            pygame.draw.circle(surface, YELLOW, (cx + ox, cy - 2), 3)


# ---------------------------------------------------------------------------
# Explosion particle
# ---------------------------------------------------------------------------
class Explosion:
    def __init__(self, x, y):
        self.x, self.y = x, y
        self.timer     = 24
        self.particles = [(random.uniform(-3, 3), random.uniform(-3, 3)) for _ in range(10)]

    def update(self):
        self.timer -= 1

    def draw(self, surface):
        frac  = self.timer / 24
        color = (255, int(200 * frac), 0)
        for vx, vy in self.particles:
            age  = (24 - self.timer)
            px   = int(self.x + vx * age)
            py   = int(self.y + vy * age)
            r    = max(1, int(3 * frac))
            pygame.draw.circle(surface, color, (px, py), r)


# ---------------------------------------------------------------------------
# Procedural sound synthesis  (no external files required)
# ---------------------------------------------------------------------------
_SR = 22050  # sample rate

def _buf(samples, vol=1.0):
    """Convert a list of floats [-1,1] to a stereo pygame.mixer.Sound."""
    buf = array.array('h')
    for s in samples:
        v = max(-32767, min(32767, int(s * vol * 32767)))
        buf.append(v); buf.append(v)
    return pygame.mixer.Sound(buffer=buf)

def _sine_samples(freq, dur, vol=1.0, fade_tail=0.05):
    n   = int(_SR * dur)
    ft  = int(_SR * fade_tail)
    out = []
    for i in range(n):
        t   = i / _SR
        env = min(1.0, (n - i) / ft) if i > n - ft else 1.0
        out.append(math.sin(2 * math.pi * freq * t) * env * vol)
    return out

def _sweep_samples(f0, f1, dur, vol=1.0, square=False):
    n     = int(_SR * dur)
    phase = 0.0
    out   = []
    for i in range(n):
        freq   = f0 + (f1 - f0) * (i / n)
        phase += 2 * math.pi * freq / _SR
        wave   = (1.0 if math.sin(phase) >= 0 else -1.0) if square else math.sin(phase)
        env    = min(1.0, (n - i) / max(1, int(n * 0.08)))
        out.append(wave * env * vol)
    return out

def _noise_samples(dur, vol=1.0):
    n = int(_SR * dur)
    return [random.uniform(-vol, vol) for _ in range(n)]

def _mix(*lists):
    length = max(len(l) for l in lists)
    out = [0.0] * length
    for l in lists:
        for i, v in enumerate(l):
            out[i] += v
    peak = max(abs(x) for x in out) or 1.0
    if peak > 1.0:
        out = [x / peak for x in out]
    return out


class Sounds:
    def __init__(self):
        pygame.mixer.init(frequency=_SR, size=-16, channels=2, buffer=512)
        self._build()

    def _build(self):
        # Player laser: quick square sweep 900 → 150 Hz
        self.shoot = _buf(_sweep_samples(900, 150, 0.10, vol=0.30, square=True))

        # Enemy explosion: noise + low-pitched sine thump
        self.explode = _buf(_mix(
            _noise_samples(0.18, vol=0.55),
            _sweep_samples(220, 40, 0.18, vol=0.45),
        ))

        # Player death: long descending wail + noise
        self.player_die = _buf(_mix(
            _sweep_samples(600, 60, 0.60, vol=0.45),
            _noise_samples(0.60, vol=0.30),
            _sweep_samples(400, 80, 0.40, vol=0.35),
        ))

        # UFO hit: short descending chime
        self.ufo_hit = _buf(_mix(
            _sweep_samples(1200, 300, 0.25, vol=0.40),
            _sweep_samples(800,  200, 0.25, vol=0.30),
        ))

        # Enemy march: 4 short square-wave tones (classic alternating low notes)
        self.march = [
            _buf(_sweep_samples(f, f, 0.06, vol=0.28, square=True))
            for f in (160, 131, 110, 125)
        ]
        self._march_idx = 0

        # UFO engine: one loopable cycle of two-tone oscillation
        cycle = _mix(
            _sine_samples(220, 0.25, vol=0.20),
            _sine_samples(165, 0.25, vol=0.20),
        )
        self.ufo_engine = _buf(cycle)

        # Level clear: quick ascending arpeggio
        notes = [_sine_samples(f, 0.10, vol=0.35) for f in (330, 415, 494, 659)]
        arp   = []
        for n in notes:
            arp.extend(n)
        self.level_clear = _buf(arp)

    # -- convenience wrappers ------------------------------------------------
    def play_shoot(self):      self.shoot.play()
    def play_explode(self):    self.explode.play()
    def play_player_die(self): self.player_die.play()
    def play_ufo_hit(self):    self.ufo_hit.play()
    def play_level_clear(self): self.level_clear.play()

    def play_march(self):
        self.march[self._march_idx].play()
        self._march_idx = (self._march_idx + 1) % 4

    def start_ufo(self):  self.ufo_engine.play(loops=-1)
    def stop_ufo(self):   self.ufo_engine.stop()

    def set_muted(self, muted):
        vol = 0.0 if muted else 1.0
        for snd in (self.shoot, self.explode, self.player_die,
                    self.ufo_hit, self.ufo_engine, self.level_clear):
            snd.set_volume(vol)
        for m in self.march:
            m.set_volume(vol)


# ---------------------------------------------------------------------------
# Difficulty presets  {move_interval_mul, shoot_interval_mul, bullet_speed_base}
# ---------------------------------------------------------------------------
DIFFICULTIES = ["EASY", "NORMAL", "HARD"]
DIFF_SETTINGS = {
    "EASY":   dict(move_mul=1.7, shoot_mul=1.6, bullet_spd=3),
    "NORMAL": dict(move_mul=1.0, shoot_mul=1.0, bullet_spd=5),
    "HARD":   dict(move_mul=0.55, shoot_mul=0.55, bullet_spd=8),
}


# ---------------------------------------------------------------------------
# Main Game
# ---------------------------------------------------------------------------
class Game:
    def __init__(self):
        pygame.init()
        self.screen     = pygame.display.set_mode((SCREEN_W, SCREEN_H))
        pygame.display.set_caption("Space Invaders")
        self.clock      = pygame.time.Clock()
        self.font_lg    = pygame.font.Font(None, 56)
        self.font_md    = pygame.font.Font(None, 34)
        self.font_sm    = pygame.font.Font(None, 24)
        self.high_score = 0
        self.sfx        = Sounds()
        # persistent settings
        self.sound_on   = True
        self.difficulty = "NORMAL"
        # menu state
        self.menu_cursor  = 0
        self.menu_anim    = 0      # ticks for alien animation in menu (public for _draw_menu)
        self._menu_anim   = 0
        self.in_game      = False   # True once a game has been started
        self.score        = 0
        self.lives        = 3
        self.level        = 1
        self.state        = "menu"
        self._init_level_objects()   # create dummy objects so draw() never crashes

    # ------------------------------------------------------------------
    def _new_game(self):
        self.score   = 0
        self.lives   = 3
        self.level   = 1
        self.in_game = True
        self.state   = "playing"
        self._init_level()

    def _init_level_objects(self):
        """Initialise all game-object lists to safe empty state (used before first game)."""
        self.player         = Player()
        self.player_bullets = []
        self.enemy_bullets  = []
        self.explosions     = []
        self.shoot_cooldown = 0
        self.enemies        = []
        self.anim_frame     = 0
        self.move_dir       = 1
        self.step_down      = False
        self.move_interval  = 30
        self.move_timer     = 0
        self.shoot_interval = 60
        self.shoot_timer    = 0
        self.shields        = []
        self.ufo              = UFO()
        self.ufo_timer        = 0
        self.ufo_wait         = 999999
        self.invincible       = 0
        self._diff_bullet_spd = 5

    def _init_level(self):
        diff = DIFF_SETTINGS[self.difficulty]

        self.player         = Player()
        self.player_bullets = []
        self.enemy_bullets  = []
        self.explosions     = []
        self.shoot_cooldown = 0

        # Enemies
        self.enemies = [
            Enemy(c, r,
                  ENEMY_START_X + c * ENEMY_SPACING_X,
                  ENEMY_START_Y + r * ENEMY_SPACING_Y)
            for r in range(ENEMY_ROWS)
            for c in range(ENEMY_COLS)
        ]
        self.anim_frame    = 0
        self.move_dir      = 1
        self.step_down     = False
        base_speed         = max(2, 42 - self.level * 3)
        self.move_interval = max(2, int(base_speed * diff["move_mul"]))
        self.move_timer    = 0

        # Enemy shooting
        base_shoot          = max(20, 90 - self.level * 6)
        self.shoot_interval = max(15, int(base_shoot * diff["shoot_mul"]))
        self.shoot_timer    = 0
        self._diff_bullet_spd = diff["bullet_spd"]

        # Shields
        positions = [150, 310, 470, 630]
        self.shields = [Shield(cx, SCREEN_H - 138) for cx in positions]

        # UFO
        self.ufo        = UFO()
        self.ufo_timer  = 0
        self.ufo_wait   = random.randint(500, 1100)

        # Invincibility frames after being hit
        self.invincible = 0

    # ------------------------------------------------------------------
    def _alive_enemies(self):
        return [e for e in self.enemies if e.alive]

    def _enemy_speed_interval(self):
        alive = len(self._alive_enemies())
        factor = max(1, alive // 8 + 1)
        return max(2, self.move_interval // factor)

    # ------------------------------------------------------------------
    def _player_fire(self):
        if self.shoot_cooldown <= 0 and len(self.player_bullets) < 2:
            bx = self.player.x
            by = self.player.y - Player.H // 2 - 6
            self.player_bullets.append(Bullet(bx, by, -11, WHITE))
            self.shoot_cooldown = 12
            self.sfx.play_shoot()

    def _enemy_fire(self):
        alive = self._alive_enemies()
        if not alive:
            return
        # Prefer bottom-row enemies to shoot
        bottom_in_col = {}
        for e in alive:
            if e.col not in bottom_in_col or e.row > bottom_in_col[e.col].row:
                bottom_in_col[e.col] = e
        shooter = random.choice(list(bottom_in_col.values()))
        bx = int(shooter.x)
        by = int(shooter.y) + Enemy.H // 2 + 4
        spd = self._diff_bullet_spd + self.level // 2
        self.enemy_bullets.append(Bullet(bx, by, spd, RED))

    # ------------------------------------------------------------------
    def _move_enemies(self):
        alive = self._alive_enemies()
        if not alive:
            return

        if self.step_down:
            for e in alive:
                e.y += 18
                e.sync_rect()
            self.move_dir  *= -1
            self.step_down  = False
        else:
            step = 10 * self.move_dir
            for e in alive:
                e.x += step
                e.sync_rect()

            xs = [e.x for e in alive]
            if max(xs) >= SCREEN_W - Enemy.W // 2 - 8:
                self.step_down = True
            elif min(xs) <= Enemy.W // 2 + 8:
                self.step_down = True

        self.anim_frame ^= 1
        self.sfx.play_march()

    # ------------------------------------------------------------------
    def _check_collisions(self):
        # Player bullets → enemies
        for b in self.player_bullets[:]:
            if not b.active:
                continue
            for e in self.enemies:
                if e.alive and b.rect.colliderect(e.rect):
                    e.alive = False
                    b.active = False
                    self.score += e.points
                    self.high_score = max(self.high_score, self.score)
                    self.explosions.append(Explosion(e.x, e.y))
                    self.sfx.play_explode()
                    break

        # Player bullets → UFO
        if self.ufo.active:
            for b in self.player_bullets[:]:
                if b.active and b.rect.colliderect(self.ufo.rect):
                    b.active = False
                    self.ufo.active = False
                    self.score += UFO.POINTS
                    self.high_score = max(self.high_score, self.score)
                    self.explosions.append(Explosion(int(self.ufo.x), self.ufo.y))
                    self.sfx.stop_ufo()
                    self.sfx.play_ufo_hit()

        # Any bullet → shields
        for bullet_list in (self.player_bullets, self.enemy_bullets):
            for b in bullet_list[:]:
                if not b.active:
                    continue
                for sh in self.shields:
                    if sh.hit(b.rect):
                        b.active = False
                        break

        # Enemy bullets → player
        if self.invincible <= 0:
            for b in self.enemy_bullets[:]:
                if b.active and b.rect.colliderect(self.player.rect):
                    b.active = False
                    self.lives     -= 1
                    self.invincible = 120
                    self.explosions.append(Explosion(self.player.x, self.player.y))
                    self.sfx.play_player_die()
                    if self.lives <= 0:
                        self.state = "game_over"
                    break

        # Enemies touching shields (erode them)
        for e in self._alive_enemies():
            for sh in self.shields:
                sh.erode_bottom(e.rect)

        # Enemies reaching player line → instant game over
        for e in self._alive_enemies():
            if e.y >= SCREEN_H - 80:
                self.state = "game_over"
                return

        # Remove spent bullets
        self.player_bullets = [b for b in self.player_bullets if b.active]
        self.enemy_bullets  = [b for b in self.enemy_bullets  if b.active]

    # ------------------------------------------------------------------
    def _menu_items(self):
        """Return list of (label, kind) for the current menu."""
        items = []
        if self.in_game:
            items.append(("RESUME", "action"))
        items.append(("NEW GAME", "action"))
        items.append((f"SOUND:       {'ON ' if self.sound_on else 'OFF'}", "toggle_sound"))
        items.append((f"DIFFICULTY:  {self.difficulty}", "toggle_diff"))
        items.append(("QUIT", "action"))
        return items

    def _open_menu(self):
        self.sfx.stop_ufo()
        self.state = "menu"
        # keep cursor in bounds as item count may change
        self.menu_cursor = min(self.menu_cursor, len(self._menu_items()) - 1)

    def _menu_activate(self, kind, label):
        if kind == "action":
            if "RESUME" in label:
                self.state = "playing"
            elif "NEW GAME" in label:
                self._new_game()
            elif "QUIT" in label:
                pygame.quit(); sys.exit()
        elif kind == "toggle_sound":
            self.sound_on = not self.sound_on
            self.sfx.set_muted(not self.sound_on)
        elif kind == "toggle_diff":
            idx = DIFFICULTIES.index(self.difficulty)
            self.difficulty = DIFFICULTIES[(idx + 1) % len(DIFFICULTIES)]

    def _menu_change(self, kind, delta):
        """Left/right adjustment for toggleable items."""
        if kind == "toggle_sound":
            self.sound_on = not self.sound_on
            self.sfx.set_muted(not self.sound_on)
        elif kind == "toggle_diff":
            idx = DIFFICULTIES.index(self.difficulty)
            self.difficulty = DIFFICULTIES[(idx + delta) % len(DIFFICULTIES)]

    def handle_events(self):
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()
            if event.type == pygame.KEYDOWN:

                if self.state == "menu":
                    items = self._menu_items()
                    n     = len(items)
                    if event.key in (pygame.K_UP, pygame.K_w):
                        self.menu_cursor = (self.menu_cursor - 1) % n
                    elif event.key in (pygame.K_DOWN, pygame.K_s):
                        self.menu_cursor = (self.menu_cursor + 1) % n
                    elif event.key in (pygame.K_RETURN, pygame.K_SPACE):
                        label, kind = items[self.menu_cursor]
                        self._menu_activate(kind, label)
                    elif event.key == pygame.K_LEFT:
                        _, kind = items[self.menu_cursor]
                        self._menu_change(kind, -1)
                    elif event.key == pygame.K_RIGHT:
                        _, kind = items[self.menu_cursor]
                        self._menu_change(kind, 1)
                    elif event.key == pygame.K_ESCAPE and self.in_game:
                        self.state = "playing"

                elif self.state == "playing":
                    if event.key == pygame.K_ESCAPE:
                        self._open_menu()
                    elif event.key == pygame.K_SPACE:
                        self._player_fire()

                elif self.state in ("game_over", "win"):
                    if event.key in (pygame.K_r, pygame.K_RETURN,
                                     pygame.K_SPACE, pygame.K_ESCAPE):
                        self.in_game = False
                        self._open_menu()

    def update(self):
        self._menu_anim = (self._menu_anim + 1) % 60 // 30  # 0 or 1, flips every 30 frames
        if self.state != "playing":
            return

        keys = pygame.key.get_pressed()
        self.player.update(keys)

        if self.shoot_cooldown  > 0: self.shoot_cooldown  -= 1
        if self.invincible      > 0: self.invincible      -= 1

        for b in self.player_bullets + self.enemy_bullets:
            b.update()

        # Enemy movement
        self.move_timer += 1
        if self.move_timer >= self._enemy_speed_interval():
            self.move_timer = 0
            self._move_enemies()

        # Enemy shooting
        self.shoot_timer += 1
        if self.shoot_timer >= self.shoot_interval:
            self.shoot_timer = 0
            self._enemy_fire()

        # UFO
        was_active = self.ufo.active
        self.ufo_timer += 1
        if self.ufo_timer >= self.ufo_wait:
            self.ufo_timer = 0
            self.ufo_wait  = random.randint(500, 1100)
            self.ufo.spawn()
            if self.ufo.active and not was_active:
                self.sfx.start_ufo()
        self.ufo.update()
        if was_active and not self.ufo.active:   # exited screen naturally
            self.sfx.stop_ufo()

        self._check_collisions()

        # Explosions
        for ex in self.explosions:
            ex.update()
        self.explosions = [ex for ex in self.explosions if ex.timer > 0]

        # Win condition
        if all(not e.alive for e in self.enemies):
            self.sfx.stop_ufo()
            self.sfx.play_level_clear()
            self.level += 1
            self._init_level()

    # ------------------------------------------------------------------
    def draw(self):
        self.screen.fill(BLACK)

        if self.state == "menu":
            self._draw_menu()

        elif self.state == "playing":
            self._draw_game()

        elif self.state == "game_over":
            self._draw_game()
            self._overlay("GAME OVER",
                          f"Score: {self.score}        press any key for menu")

        elif self.state == "win":
            self._draw_game()
            self._overlay("YOU WIN!",
                          f"Score: {self.score}        press any key for menu")

        pygame.display.flip()

    def _draw_game(self):
        pygame.draw.line(self.screen, GREEN, (0, SCREEN_H - 34), (SCREEN_W, SCREEN_H - 34), 2)
        for sh in self.shields:
            sh.draw(self.screen)
        for e in self.enemies:
            e.draw(self.screen, self.anim_frame)
        self.ufo.draw(self.screen)
        if self.invincible == 0 or (self.invincible // 6) % 2 == 0:
            self.player.draw(self.screen)
        for b in self.player_bullets + self.enemy_bullets:
            b.draw(self.screen)
        for ex in self.explosions:
            ex.draw(self.screen)
        self._draw_hud()

    def _draw_menu(self):
        # Starfield background
        rng = random.Random(42)
        for _ in range(80):
            sx = rng.randint(0, SCREEN_W - 1)
            sy = rng.randint(0, SCREEN_H - 1)
            br = rng.randint(80, 220)
            self.screen.set_at((sx, sy), (br, br, br))

        # Title
        title = self.font_lg.render("SPACE INVADERS", True, GREEN)
        self.screen.blit(title, (SCREEN_W // 2 - title.get_width() // 2, 60))
        # decorative aliens flanking the title
        _draw_crab(self.screen,    60, 78, MAGENTA, self._menu_anim)
        _draw_crab(self.screen, SCREEN_W - 60, 78, MAGENTA, self._menu_anim)

        # High score
        hi = self.font_sm.render(f"HI-SCORE  {self.high_score}", True, YELLOW)
        self.screen.blit(hi, (SCREEN_W // 2 - hi.get_width() // 2, 118))

        # Menu items
        items   = self._menu_items()
        item_h  = 46
        start_y = 180

        for i, (label, kind) in enumerate(items):
            selected = (i == self.menu_cursor)
            color    = YELLOW if selected else WHITE

            # Cursor arrow
            if selected:
                arrow = self.font_md.render(">", True, GREEN)
                self.screen.blit(arrow, (SCREEN_W // 2 - 160, start_y + i * item_h - 2))

            text = self.font_md.render(label, True, color)
            self.screen.blit(text, (SCREEN_W // 2 - 130, start_y + i * item_h - 2))

            # left/right hints for toggleable items
            if selected and kind in ("toggle_sound", "toggle_diff"):
                hint = self.font_sm.render("< >", True, CYAN)
                self.screen.blit(hint,
                    (SCREEN_W // 2 + text.get_width() - 110, start_y + i * item_h + 4))

        # Footer
        footer = self.font_sm.render(
            "UP/DOWN  navigate        ENTER  select        LEFT/RIGHT  change setting",
            True, (120, 120, 120))
        self.screen.blit(footer, (SCREEN_W // 2 - footer.get_width() // 2, SCREEN_H - 28))

    def _draw_hud(self):
        s   = self.font_md.render(f"SCORE  {self.score:>6}", True, WHITE)
        hi  = self.font_md.render(f"HI  {self.high_score:>6}",    True, YELLOW)
        lv  = self.font_md.render(f"LEVEL {self.level}",          True, CYAN)
        self.screen.blit(s,  (10,  8))
        self.screen.blit(hi, (SCREEN_W // 2 - hi.get_width() // 2, 8))
        self.screen.blit(lv, (SCREEN_W - lv.get_width() - 10, 8))

        # Life ships
        for i in range(self.lives):
            lx = 14 + i * 36
            ly = SCREEN_H - 18
            pygame.draw.rect(self.screen, GREEN, (lx - 11, ly - 6, 22, 12), border_radius=2)
            pygame.draw.rect(self.screen, GREEN, (lx - 2,  ly - 12, 4, 6))

        # Alien score legend (bottom-right)
        legend = [
            (_draw_crab,    -1, 30,  MAGENTA),
            (_draw_squid,    0, 20,  CYAN),
            (_draw_octopus,  0, 10,  GREEN),
        ]
        bx = SCREEN_W - 120
        by = SCREEN_H - 20
        for fn, _, pts, color in reversed(legend):
            label = self.font_sm.render(f"= {pts:3}pts", True, WHITE)
            fn(self.screen, bx, by, color, 0)
            self.screen.blit(label, (bx + 20, by - 7))
            by -= 22

    def _overlay(self, title, sub):
        surf = pygame.Surface((SCREEN_W, SCREEN_H), pygame.SRCALPHA)
        surf.fill((0, 0, 0, 160))
        self.screen.blit(surf, (0, 0))
        t  = self.font_lg.render(title, True, WHITE)
        s  = self.font_md.render(sub,   True, YELLOW)
        self.screen.blit(t, (SCREEN_W // 2 - t.get_width() // 2, SCREEN_H // 2 - 44))
        self.screen.blit(s, (SCREEN_W // 2 - s.get_width() // 2, SCREEN_H // 2 + 20))

    # ------------------------------------------------------------------
    def run(self):
        while True:
            self.handle_events()
            self.update()
            self.draw()
            self.clock.tick(FPS)


if __name__ == "__main__":
    game = Game()
    game.run()
