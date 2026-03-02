# Emberdeep Reforged (CLI RPG)

A single-player, D&D-inspired terminal RPG with character progression, tactical combat, procedural encounters, and username-based save files.

## What changed
- Deeper character system with 5 races and 5 classes.
- Class resources (`mana`, `faith`, `focus`, `stamina`) and distinct combat actions.
- Regional progression system (floors and biome shifts).
- Event checks (investigate/parley/pray/ignore) that alter survival and growth.
- Procedural content libraries with 10,000+ encounter prompts and 1,300 quest prompts.
- Per-user JSON saves in `saves/<username>.json`.

## Run
```bash
python src/game.py
```

## Notes
- Every run uses a cryptographic seed source (`os.urandom`) plus runtime entropy.
- The game auto-saves on quit and can manually save mid-run.
