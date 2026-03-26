"""
NEAT Dinosaur Game  —  Chrome-style pixel art, no external assets
=================================================================
Dependencies:
    pip install pygame neat-python

Run:
    python main.py   (both files must be in the same folder)
"""

import pygame
import neat
import os
import random

# ---------------------------------------------------------------------------
# CONSTANTS
# ---------------------------------------------------------------------------

SCREEN_W   = 1000
SCREEN_H   = 300
FPS        = 75

# Chrome palette
WHITE      = (255, 255, 255)
BG_COLOR   = (247, 247, 247)
DINO_COLOR = ( 83,  83,  83)
CLOUD_COL  = (209, 209, 209)
GROUND_COL = (209, 209, 209)
TEXT_COL   = ( 83,  83,  83)
DEAD_COL   = (200,  80,  80)

GROUND_Y   = 230          # y where the ground surface sits

# Dino physics
GRAVITY    = 0.9
JUMP_VEL   = -17.5

# Obstacle speed
SPD_INIT   = 7.0
SPD_MAX    = 15.0
SPD_INC    = 0.003

# NEAT
CONFIG_PATH = os.path.join(os.path.dirname(__file__), "config-feedforward.txt")
MAX_GENS    = 0            # 0 = run forever

# ---------------------------------------------------------------------------
# PIXEL-ART SPRITE DATA
# ---------------------------------------------------------------------------
# Each sprite = list of (x, y, w, h) in "logical pixels".
# We render each logical pixel as a SCALE×SCALE real square.

SCALE = 3

def _surf(rects, lw, lh, color=DINO_COLOR):
    """Build a transparent Surface from a list of logical-pixel rectangles."""
    s = pygame.Surface((lw * SCALE, lh * SCALE), pygame.SRCALPHA)
    s.fill((0, 0, 0, 0))
    for (x, y, w, h) in rects:
        pygame.draw.rect(s, color,
                         (x * SCALE, y * SCALE, w * SCALE, h * SCALE))
    return s


# ---- Dinosaur body (shared across frames) ----------------------------------
# 17 × 18 logical pixels
_BODY = [
    (4, 0, 9, 1),
    (4, 1, 11, 1),
    (4, 2, 13, 1),
    # row 3: eye gap at col 8
    (4, 3, 4, 1), (9, 3, 8, 1),
    (4, 4, 13, 1),
    (4, 5, 13, 1),
    (4, 6, 13, 1),
    # neck / back
    (0, 7, 17, 1),
    (0, 8, 17, 1),
    (2, 9, 13, 1),
    (4, 10, 9, 1),
    # torso
    (4, 11, 9, 1),
    (4, 12, 9, 1),
    (4, 13, 7, 1),
    (4, 14, 5, 1),
]

_LEGS_RUN1 = [         # left leg forward
    (4, 15, 2, 1), (9, 15, 2, 1),
    (4, 16, 2, 1), (10, 16, 1, 1),
    (4, 17, 2, 1),
]
_LEGS_RUN2 = [         # legs swapped
    (5, 15, 2, 1), (8, 15, 2, 1),
    (6, 16, 1, 1), (8, 16, 2, 1),
    (8, 17, 2, 1),
]
_LEGS_JUMP = [         # tucked
    (4, 15, 9, 1),
    (4, 16, 9, 1),
    (4, 17, 9, 1),
]

DINO_LW, DINO_LH = 17, 18
DINO_W = DINO_LW * SCALE
DINO_H = DINO_LH * SCALE


# ---- Small cactus  (17 × 35 logical px) ------------------------------------
_CACT_S = [
    (7, 0, 3, 2),
    (5, 2, 7, 2),
    (0, 4, 17, 3),
    (0, 7, 2, 1), (7, 7, 3, 1), (15, 7, 2, 1),
    (7, 8, 3, 18),
    (6, 11, 5, 2),
    (6, 13, 5, 22),
]

# ---- Large cactus  (25 × 50 logical px) ------------------------------------
_CACT_L = [
    (10, 0,  5, 2),
    ( 8, 2,  9, 3),
    ( 0, 5, 25, 4),
    ( 0, 9,  4, 3), (10, 9, 5, 3), (21, 9, 4, 3),
    (10, 12, 5, 38),
    ( 8, 14, 9,  2),
    ( 8, 16, 9, 34),
]

# ---- Cloud  (24 × 11 logical px) -------------------------------------------
_CLOUD = [
    ( 7, 0, 13, 1),
    ( 4, 1, 19, 2),
    ( 1, 3, 22, 2),
    ( 0, 5, 24, 2),
    ( 1, 7, 22, 2),
    ( 4, 9, 19, 1),
]

# ---------------------------------------------------------------------------
# SPRITE CACHE  (populated after pygame.init())
# ---------------------------------------------------------------------------

SP = {}

def build_sprites():
    SP["run1"]     = _surf(_BODY + _LEGS_RUN1, DINO_LW, DINO_LH)
    SP["run2"]     = _surf(_BODY + _LEGS_RUN2, DINO_LW, DINO_LH)
    SP["jump"]     = _surf(_BODY + _LEGS_JUMP, DINO_LW, DINO_LH)
    SP["dead"]     = _surf(_BODY + _LEGS_RUN1, DINO_LW, DINO_LH, DEAD_COL)
    SP["cact_s"]   = _surf(_CACT_S, 17, 35)
    SP["cact_l"]   = _surf(_CACT_L, 25, 50)
    SP["cloud"]    = _surf(_CLOUD,  24, 11, CLOUD_COL)


# ---------------------------------------------------------------------------
# GAME OBJECTS
# ---------------------------------------------------------------------------

class Dinosaur:
    DINO_X = 80

    def __init__(self):
        self.x          = self.DINO_X
        self.y          = float(GROUND_Y - DINO_H)
        self.vy         = 0.0
        self.on_ground  = True
        self.alive      = True
        self.score      = 0.0
        self._atick     = 0
        self._fidx      = 0

    def jump(self):
        if self.on_ground:
            self.vy        = JUMP_VEL
            self.on_ground = False

    def update(self):
        self.vy += GRAVITY
        self.y  += self.vy
        rest     = float(GROUND_Y - DINO_H)
        if self.y >= rest:
            self.y = rest; self.vy = 0.0; self.on_ground = True
        self._atick += 1
        if self._atick >= 6:
            self._atick = 0; self._fidx ^= 1

    def get_rect(self):
        return pygame.Rect(int(self.x) + 5, int(self.y) + 2,
                           DINO_W - 10, DINO_H - 2)

    def draw(self, surf):
        if not self.alive:
            key = "dead"
        elif not self.on_ground:
            key = "jump"
        else:
            key = "run1" if self._fidx == 0 else "run2"
        surf.blit(SP[key], (int(self.x), int(self.y)))

    def draw_ghost(self, surf):
        g = SP["dead"].copy(); g.set_alpha(35)
        surf.blit(g, (int(self.x), int(self.y)))


class Obstacle:
    # FIX 1: double-cactus logical width corrected to 17+7=24 offset → full
    #        span is 17 lw + 7 gap + 17 lw = 41 lw, so pw covers both cacti.
    #        Also get_rect() now returns a union rect for "ss" obstacles so
    #        collision detection covers the entire double-cactus footprint.
    _SS_LW = 41   # 17 + 7-px gap + 17

    def __init__(self):
        t = random.choice(["s", "s", "l", "ss"])
        self.kind = t
        if t == "s":
            self.lw, self.lh, self.key = 17, 35, "cact_s"
        elif t == "l":
            self.lw, self.lh, self.key = 25, 50, "cact_l"
        else:   # double small — wide enough to cover both sprites
            self.lw, self.lh, self.key = self._SS_LW, 35, "cact_s"
        self.pw = self.lw * SCALE
        self.ph = self.lh * SCALE
        self.x  = float(SCREEN_W + 20)
        self.y  = float(GROUND_Y - self.ph)

    def update(self, speed):
        self.x -= speed

    def get_rect(self):
        # FIX 2: for "ss" the hitbox must span both cacti, not just one.
        if self.kind == "ss":
            single_pw = 17 * SCALE
            total_w   = self.pw - 8   # full span minus small margin
            return pygame.Rect(int(self.x) + 4, int(self.y) + 2,
                               total_w, self.ph - 2)
        return pygame.Rect(int(self.x) + 4, int(self.y) + 2,
                           self.pw - 8, self.ph - 2)

    def is_off(self):
        return self.x + self.pw < 0

    def draw(self, surf):
        if self.kind == "ss":
            surf.blit(SP["cact_s"], (int(self.x), int(self.y)))
            surf.blit(SP["cact_s"], (int(self.x) + 24 * SCALE, int(self.y)))
        else:
            surf.blit(SP[self.key], (int(self.x), int(self.y)))


class Cloud:
    def __init__(self, x=None):
        self.x   = float(x if x is not None else SCREEN_W + 50)
        self.y   = random.randint(30, 100)
        self.spd = random.uniform(1.0, 2.0)

    def update(self):     self.x -= self.spd
    def is_off(self):     return self.x + 24 * SCALE < 0
    def draw(self, surf): surf.blit(SP["cloud"], (int(self.x), self.y))


# ---------------------------------------------------------------------------
# NEURAL NET INPUTS
# ---------------------------------------------------------------------------

def get_inputs(dino, obstacles, speed):
    nxt = None
    for o in obstacles:
        if o.x + o.pw > dino.x:
            if nxt is None or o.x < nxt.x:
                nxt = o

    # FIX 3: guard against division-by-zero when GROUND_Y == DINO_H
    denom = max(1., float(GROUND_Y - DINO_H))
    dy_n  = max(0., min(1., (GROUND_Y - DINO_H - dino.y) / denom))
    d_n   = (min(1., max(0., nxt.x - (dino.x + DINO_W)) / SCREEN_W)
             if nxt else 1.)
    h_n   = min(1., nxt.ph / (50 * SCALE)) if nxt else 0.
    sp_n  = max(0., min(1., (speed - SPD_INIT) / (SPD_MAX - SPD_INIT)))
    # FIX 5: vy input — NN-ин tujem en ar dinoron mid-air en
    # normalize: JUMP_VEL(-16.5) -> -1.0, falling -> positive
    vy_n  = max(-1., min(1., dino.vy / abs(JUMP_VEL)))
    return [dy_n, d_n, h_n, sp_n, vy_n]


# ---------------------------------------------------------------------------
# RENDERING HELPERS
# ---------------------------------------------------------------------------

def draw_ground(surf):
    pygame.draw.line(surf, GROUND_COL, (0, GROUND_Y),     (SCREEN_W, GROUND_Y),     2)
    pygame.draw.line(surf, GROUND_COL, (0, GROUND_Y + 5), (SCREEN_W, GROUND_Y + 5), 1)


def draw_score(surf, font, score, hi):
    t = font.render(f"HI {int(hi):05d}   {int(score):05d}", True, TEXT_COL)
    surf.blit(t, (SCREEN_W - t.get_width() - 20, 18))


def draw_hud(surf, font, gen, alive, speed):
    for i, txt in enumerate([f"GEN {gen}", f"ALIVE {alive}", f"SPD {speed:.1f}"]):
        s = font.render(txt, True, TEXT_COL)
        surf.blit(s, (20, 18 + i * 22))


def draw_nn_bar(surf, dino, v):
    bx, by, bw, bh = int(dino.x), int(dino.y) - 13, DINO_W, 5
    pygame.draw.rect(surf, GROUND_COL, (bx, by, bw, bh))
    fill = max(0, min(bw, int(v * bw)))
    col  = (52, 152, 219) if v <= 0.5 else (241, 196, 15)
    if fill:
        pygame.draw.rect(surf, col, (bx, by, fill, bh))


# ---------------------------------------------------------------------------
# NEAT EVALUATION
# FIX 4: pygame.init() / display setup moved OUTSIDE eval_genomes so they
#        are called only once, not on every generation.  eval_genomes now
#        receives the already-created screen, clock, and font as arguments.
# ---------------------------------------------------------------------------

def eval_genomes(genomes, config, screen, clock, font):
    pygame.display.set_caption(
        f"NEAT Dinosaur  —  Generation {eval_genomes.generation}")

    nets, dinos, ge = [], [], []
    for _, genome in genomes:
        genome.fitness = 0.
        nets.append(neat.nn.FeedForwardNetwork.create(genome, config))
        dinos.append(Dinosaur())
        ge.append(genome)

    obstacles   = []
    clouds      = [Cloud(random.randint(80, SCREEN_W - 100)) for _ in range(4)]
    speed       = SPD_INIT
    frame       = 0
    spawn_timer = -100
    hi          = eval_genomes.hi_score

    while any(d.alive for d in dinos):
        clock.tick(FPS)
        frame += 1

        for ev in pygame.event.get():
            if ev.type == pygame.QUIT:
                pygame.quit(); raise SystemExit
            if ev.type == pygame.KEYDOWN and ev.key == pygame.K_ESCAPE:
                pygame.quit(); raise SystemExit

        speed = min(SPD_MAX, SPD_INIT + frame * SPD_INC)

        # spawn obstacles
        spawn_timer += 1
        gap = max(50, int(400 / speed))
        if spawn_timer >= 0 and (not obstacles or spawn_timer >= gap):
            obstacles.append(Obstacle())
            spawn_timer = -180

        for o in obstacles: o.update(speed)
        obstacles = [o for o in obstacles if not o.is_off()]
        for c in clouds:    c.update()
        clouds = [c for c in clouds if not c.is_off()]
        if random.random() < 0.005:
            clouds.append(Cloud())

        alive_cnt  = 0
        best_score = 0.
        lead_dino  = None
        lead_out   = 0.

        for i, (dino, net, genome) in enumerate(zip(dinos, nets, ge)):
            if not dino.alive:
                continue
            alive_cnt += 1
            genome.fitness += 0.1
            dino.score     += 0.1

            inputs = get_inputs(dino, obstacles, speed)
            out = net.activate(inputs)[0]

            if out > 0.5:
                if inputs[1] > 0.8:
                    genome.fitness -= 0.05
                dino.jump()

            dino.update()

            dr = dino.get_rect()
            for o in obstacles:
                if dr.colliderect(o.get_rect()):
                    genome.fitness -= 5.0
                    dino.alive = False
                    break
                elif o.x + o.pw < dino.x and not getattr(o, '_passed', False):
                    o._passed = True
                    genome.fitness += 40.0

            if dino.score > best_score:
                best_score = dino.score
                lead_dino  = dino
                lead_out   = out

        if best_score > hi:
            hi = best_score

        if best_score >= config.fitness_threshold:
            print(f"\n🏆 Threshold reached! Best score: {best_score}")
            break

            # ---- draw ----------------------------------------------------------
        screen.fill(BG_COLOR)

        for c in clouds:  c.draw(screen)
        draw_ground(screen)
        for o in obstacles: o.draw(screen)

        for d in dinos:
            if not d.alive:
                d.draw_ghost(screen)
        for d in dinos:
            if d.alive:
                d.draw(screen)

        if lead_dino and lead_dino.alive:
            draw_nn_bar(screen, lead_dino, lead_out)

        draw_hud(screen, font, eval_genomes.generation, alive_cnt, speed)
        draw_score(screen, font, best_score, hi)

        hint = font.render("ESC = quit", True, GROUND_COL)
        screen.blit(hint, (SCREEN_W - hint.get_width() - 14,
                           SCREEN_H - hint.get_height() - 8))

        pygame.display.flip()

    eval_genomes.hi_score = hi
    pygame.time.wait(350)


eval_genomes.generation = 0
eval_genomes.hi_score   = 0.


# ---------------------------------------------------------------------------
# ENTRY POINT
# ---------------------------------------------------------------------------

def run():
    if not os.path.exists(CONFIG_PATH):
        raise FileNotFoundError(
            f"Config not found: {CONFIG_PATH}\n"
            "Put 'config-feedforward.txt' next to main.py."
        )
    config = neat.Config(
        neat.DefaultGenome, neat.DefaultReproduction,
        neat.DefaultSpeciesSet, neat.DefaultStagnation,
        CONFIG_PATH,
    )
    pop = neat.Population(config)
    pop.add_reporter(neat.StdOutReporter(True))
    pop.add_reporter(neat.StatisticsReporter())

    # FIX 4 (cont.): init pygame once here, pass shared objects into eval_genomes
    pygame.init()
    build_sprites()   # FIX 3: build sprites once, not every generation
    screen = pygame.display.set_mode((SCREEN_W, SCREEN_H))
    clock  = pygame.time.Clock()
    font   = pygame.font.SysFont("Courier New", 16, bold=True)

    def _run(genomes, cfg):
        eval_genomes.generation += 1
        eval_genomes(genomes, cfg, screen, clock, font)

    winner = pop.run(_run, MAX_GENS if MAX_GENS else 10_000)

    import pickle
    with open("champion.pkl", "wb") as f:
        pickle.dump(winner, f)
    print("✅ The champion was retained. → champion.pkl")

    pygame.quit()


if __name__ == "__main__":
    # 1. Start training
    run()

    # 2. Training complete — load champion and play
    print("\n=============================================")
    print("Training complete! Now only the Champion is playing.")
    print("=============================================\n")

    import pickle

    config = neat.Config(
        neat.DefaultGenome, neat.DefaultReproduction,
        neat.DefaultSpeciesSet, neat.DefaultStagnation,
        CONFIG_PATH,
    )

    with open("champion.pkl", "rb") as f:
        winner = pickle.load(f)

    # FIX 4 (cont.): re-init pygame for the champion playback session
    pygame.init()
    screen = pygame.display.set_mode((SCREEN_W, SCREEN_H))
    clock  = pygame.time.Clock()
    font   = pygame.font.SysFont("Courier New", 16, bold=True)

    eval_genomes.generation = "CHAMPION"
    eval_genomes([(1, winner)], config, screen, clock, font)

    pygame.quit()