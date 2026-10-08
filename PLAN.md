# PLAN — agar.io clone

Тимлид: **Nibble**. Мёржит в master только владелец.
Все PR — только в форк `oshrvaleks-hub/agario`, база `master`.

## Цель
Играбельный клон, близкий к agar.io: модульная структура, честные механики
(поедание, рост, split/merge, выброс массы, вирусы), боты, лидерборд,
экран смерти и рестарт, стабильные 60 FPS, pytest на чистую логику.

## Roadmap

### Этап 0 — фундамент (последовательно)
| # | Задача | Исполнитель | Ветка / PR | Статус |
|---|--------|-------------|------------|--------|
| 0.1 | Скорость зависит от расстояния до мыши | Pixel (стажёр) | `fix/speed-by-mouse-distance` / #1 | ждёт мержа |
| 0.2 | Рефакторинг `agar.py` → пакет `agario/` (config, geometry, entities, world, physics, camera, render, game), `--frames N`, requirements.txt, README, первые тесты | Pixel (sonnet) | `refactor/modules` / #3 | ✅ проверено, ждёт мержа |
| 0.3 | PLAN.md | Nibble | `docs/plan` / #2 | ждёт мержа |

### Этап 1 — механики (параллельно, после 0.2)
| # | Задача | Файлы | Исполнитель |
|---|--------|-------|-------------|
| 1.1 | Поедание и рост: radius ∝ √mass, больший съедает меньшего при массе ≥ 1.25×, клетка-клетка между игроками, замедление с массой, зум камеры от размера, респаун еды, границы карты | `physics.py`, `geometry.py`, `camera.py`, `mechanics/eating.py` | Pixel (Claude sonnet) — `feat/eating-growth`, в работе |
| 1.2 | Split (пробел) и merge, выброс массы (W) | `mechanics/split.py`, `mechanics/eject.py`, `entities.py` | Byte (Codex) — `feat/split-eject`, в работе |
| 1.3 | Боты (ищут еду, убегают от больших, охотятся на меньших) + лидерборд с реальными данными | `ai.py`, `leaderboard.py`, `game.py` | Sprocket (Codex) — `feat/bots`, в работе |

### Этап 2 — после этапа 1
| # | Задача | Файлы |
|---|--------|-------|
| 2.1 | Вирусы: спавн, лопание крупных клеток, «кормление» вируса через W | `mechanics/virus.py` |
| 2.2 | Экран смерти, рестарт, счёт (макс. масса, время), стабильные 60 FPS (профилирование: отрисовка только видимого, spatial grid) | `game.py`, `render.py`, `spatial.py` |
| 2.3 | Добивка тестов (столкновения, поедание, split/merge, движение), CI-скрипт проверки | `tests/` |

## Архитектурный контракт (после 0.2)
- Логика (`config`, `geometry`, `entities`, `world`, `physics`, `camera`, `mechanics/*`, `ai`) **не импортирует pygame** — тестируется pytest без окна.
- `World.update(controls)` — единая точка шага симуляции; `Control(target, speed_factor, split, eject)` одинаков для человека и бота.
- Весь pygame — в `render.py` и `game.py`.
- Headless-проверка: `SDL_VIDEODRIVER=dummy python3 agar.py --frames 600`.

## Процесс ревью
Каждый PR тимлид проверяет: diff, `python3 -m pytest`, headless-прогон игры.
После проверки — комментарий «✅ проверено менеджером», затем PR ждёт владельца.

## Ждут мержа (порядок: #1 → #3 → #2)
- #1 — скорость от расстояния до мыши (Pixel-стажёр)
- #2 — этот PLAN.md
- #3 — рефакторинг в пакет `agario/` (Pixel)

## Смёржено
- —
