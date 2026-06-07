# Space Invaders

A classic Space Invaders clone built with Python and Pygame. Features procedurally generated sound effects (no external audio files required), animated pixel-art aliens, destructible shields, a UFO, and a full main menu.

## Features

- 5 rows × 11 columns of animated aliens (3 types with unique shapes)
- Destructible shield bunkers
- Mystery UFO that crosses the screen periodically
- Enemy formation speeds up as aliens are eliminated
- Difficulty settings: Easy, Normal, Hard
- Procedurally synthesised sound effects (laser, explosions, march beat, UFO hum)
- High score tracking within the session
- Player invincibility frames after being hit

## Requirements

- Python 3.8+
- Pygame 2.x

## Installation

```bash
pip install pygame
python main.py
```

## Controls

| Key | Action |
|-----|--------|
| `←` / `→` or `A` / `D` | Move left / right |
| `Space` | Fire |
| `Esc` | Open menu |
| `↑` / `↓` | Navigate menu |
| `Enter` or `Space` | Select menu item |
| `←` / `→` | Change setting (Sound, Difficulty) |

## Difficulty

| Level | Enemy speed | Fire rate | Bullet speed |
|-------|-------------|-----------|--------------|
| Easy   | Slow | Low  | Slow |
| Normal | Medium | Medium | Medium |
| Hard   | Fast | High | Fast |

## Scoring

| Alien | Points |
|-------|--------|
| Top row (crab) | 30 |
| Middle rows (squid) | 20 |
| Bottom rows (octopus) | 10 |
| Mystery UFO | 150 |

## Screenshot

![Space Invaders gameplay](https://raw.githubusercontent.com/s2c97/space-invaders/master/screenshot.png)
