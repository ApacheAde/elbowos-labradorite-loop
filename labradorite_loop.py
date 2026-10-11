#!/usr/bin/env python3
"""Labradorite Loop — neon light-cycle arcade for ElbowOS. Python 3 + pygame."""
import math, os, random, subprocess, sys

RECORD = "--record" in sys.argv or os.environ.get("ELBOWOS_RECORD") == "1"
PLAY = "--play" in sys.argv
if RECORD or not PLAY:
    os.environ.setdefault("SDL_VIDEODRIVER", "dummy")
    os.environ.setdefault("SDL_AUDIODRIVER", "dummy")
import pygame

W, H, FPS, SECS = 1080, 1920, 30, 15
OUT = os.environ.get("ELBOWOS_MP4", "/workspace/artifacts/LABRADORITE_LOOP_ElbowOS.mp4")
TITLE, HANDLE = "LABRADORITE LOOP", "x.com/ElbowOS"

# Neon palette — iridescent labradorite vibes
VOID = (8, 4, 24)
INK = (18, 10, 42)
CYAN = (64, 220, 255)
MAG = (220, 80, 255)
GOLD = (255, 200, 80)
LIME = (120, 255, 140)
WHITE = (240, 245, 255)
ROSE = (255, 90, 140)
PURPLE = (140, 60, 220)

CELL = 24
COLS, ROWS = W // CELL, H // CELL

class Cycle:
    def __init__(self, x, y, dx, dy, color, is_ai=False):
        self.x, self.y = x, y
        self.dx, self.dy = dx, dy
        self.color = color
        self.trail = [(x, y)]
        self.alive = True
        self.is_ai = is_ai
        self.score = 0
        self.boost = 0

    def pos(self):
        return (self.x, self.y)

    def would_hit(self, grid, nx, ny):
        if not (0 <= nx < COLS and 0 <= ny < ROWS):
            return True
        return grid[ny][nx] != 0

    def step(self, grid, sparks):
        if not self.alive:
            return
        if self.is_ai:
            # simple look-ahead: prefer straight, turn if blocked
            options = []
            for ddx, ddy in [(self.dx, self.dy), (-self.dy, self.dx), (self.dy, -self.dx)]:
                nx, ny = self.x + ddx, self.y + ddy
                if not self.would_hit(grid, nx, ny):
                    # prefer collecting nearby spark
                    bonus = 0
                    for s in sparks:
                        if abs(s[0] - nx) + abs(s[1] - ny) < 3:
                            bonus = 2
                    options.append((bonus + random.random(), ddx, ddy))
            if options:
                options.sort(reverse=True)
                self.dx, self.dy = options[0][1], options[0][2]
            else:
                self.alive = False
                return
        nx, ny = self.x + self.dx, self.y + self.dy
        if self.would_hit(grid, nx, ny):
            self.alive = False
            return
        # leave trail
        grid[self.y][self.x] = 1
        self.x, self.y = nx, ny
        self.trail.append((self.x, self.y))
        if len(self.trail) > 180:
            ox, oy = self.trail.pop(0)
            if 0 <= ox < COLS and 0 <= oy < ROWS:
                grid[oy][ox] = 0
        # collect sparks
        for i, s in enumerate(sparks):
            if s[0] == self.x and s[1] == self.y:
                self.score += 50
                sparks.pop(i)
                break

class Game:
    def __init__(self):
        pygame.init()
        pygame.font.init()
        flags = 0 if PLAY else pygame.HIDDEN
        try:
            self.screen = pygame.display.set_mode((W, H), flags)
        except pygame.error:
            os.environ["SDL_VIDEODRIVER"] = "dummy"
            pygame.display.quit()
            pygame.display.init()
            self.screen = pygame.display.set_mode((W, H), pygame.HIDDEN)
        pygame.display.set_caption(TITLE)
        self.font_big = pygame.font.SysFont("monospace", 72, bold=True)
        self.font_mid = pygame.font.SysFont("monospace", 42, bold=True)
        self.font_sm = pygame.font.SysFont("monospace", 28)
        self.reset()

    def reset(self):
        self.grid = [[0] * COLS for _ in range(ROWS)]
        self.player = Cycle(COLS//2, ROWS - 8, 0, -1, CYAN, is_ai=True)
        self.rival = Cycle(COLS//2 + 6, ROWS - 12, 0, -1, MAG, is_ai=True)
        self.sparks = []
        self.frame = 0
        self.total_score = 0
        self.spawn_timer = 0

    def spawn_spark(self):
        for _ in range(20):
            x = random.randint(4, COLS-5)
            y = random.randint(4, ROWS-10)
            if self.grid[y][x] == 0:
                self.sparks.append((x, y))
                return

    def update(self):
        self.frame += 1
        self.spawn_timer += 1
        if self.spawn_timer > 40 and len(self.sparks) < 8:
            self.spawn_spark()
            self.spawn_timer = 0
        self.player.step(self.grid, self.sparks)
        self.rival.step(self.grid, self.sparks)
        self.total_score = self.player.score + self.rival.score // 2
        if not self.player.alive and not self.rival.alive:
            self.reset()

    def draw(self):
        self.screen.fill(VOID)
        # subtle grid
        for x in range(0, W, CELL * 4):
            pygame.draw.line(self.screen, INK, (x, 0), (x, H), 1)
        for y in range(0, H, CELL * 4):
            pygame.draw.line(self.screen, INK, (0, y), (W, y), 1)
        # trails
        for cyc in (self.player, self.rival):
            if not cyc.trail:
                continue
            pts = [(p[0]*CELL + CELL//2, p[1]*CELL + CELL//2) for p in cyc.trail[-60:]]
            if len(pts) > 1:
                pygame.draw.lines(self.screen, cyc.color, False, pts, 6)
                pygame.draw.lines(self.screen, WHITE, False, pts, 2)
        # cycles
        for cyc in (self.player, self.rival):
            if cyc.alive:
                px, py = cyc.x * CELL + CELL//2, cyc.y * CELL + CELL//2
                pygame.draw.circle(self.screen, cyc.color, (px, py), 14)
                pygame.draw.circle(self.screen, WHITE, (px, py), 6)
        # sparks
        for sx, sy in self.sparks:
            cx, cy = sx * CELL + CELL//2, sy * CELL + CELL//2
            pygame.draw.circle(self.screen, GOLD, (cx, cy), 10)
            pygame.draw.circle(self.screen, WHITE, (cx, cy), 4)
        # overlays
        title_s = self.font_big.render(TITLE, True, CYAN)
        self.screen.blit(title_s, (W//2 - title_s.get_width()//2, 40))
        score_s = self.font_mid.render(f"SCORE {self.total_score}", True, GOLD)
        self.screen.blit(score_s, (W//2 - score_s.get_width()//2, 140))
        handle_s = self.font_sm.render(HANDLE, True, LIME)
        self.screen.blit(handle_s, (W//2 - handle_s.get_width()//2, H - 80))
        pygame.display.flip()

    def record(self):
        cmd = [
            "ffmpeg", "-y", "-f", "rawvideo", "-vcodec", "rawvideo",
            "-s", f"{W}x{H}", "-pix_fmt", "rgb24", "-r", str(FPS),
            "-i", "-", "-c:v", "libx264", "-pix_fmt", "yuv420p",
            "-crf", "20", "-preset", "fast", "-movflags", "+faststart",
            OUT
        ]
        proc = subprocess.Popen(cmd, stdin=subprocess.PIPE)
        frames = FPS * SECS
        for i in range(frames):
            self.update()
            self.draw()
            raw = pygame.image.tostring(self.screen, "RGB")
            proc.stdin.write(raw)
        proc.stdin.close()
        proc.wait()
        print(f"Wrote {OUT}")

    def play_interactive(self):
        clock = pygame.time.Clock()
        running = True
        self.player.is_ai = False
        while running:
            for ev in pygame.event.get():
                if ev.type == pygame.QUIT or (ev.type == pygame.KEYDOWN and ev.key == pygame.K_ESCAPE):
                    running = False
                if ev.type == pygame.KEYDOWN:
                    if ev.key in (pygame.K_LEFT, pygame.K_a):
                        self.player.dx, self.player.dy = -self.player.dy, self.player.dx
                    elif ev.key in (pygame.K_RIGHT, pygame.K_d):
                        self.player.dx, self.player.dy = self.player.dy, -self.player.dx
                    elif ev.key == pygame.K_r:
                        self.reset()
                        self.player.is_ai = False
            keys = pygame.key.get_pressed()
            self.update()
            self.draw()
            clock.tick(FPS)
        pygame.quit()

if __name__ == "__main__":
    g = Game()
    if RECORD:
        g.record()
    else:
        g.play_interactive()
