import json
import os
import random
import textwrap
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Dict, List, Tuple

from content_tables import ENCOUNTER_DESCRIPTIONS, QUEST_OBJECTIVES, REGION_NAMES, TREASURE_PREFIXES

SAVE_DIR = Path(__file__).resolve().parent.parent / "saves"
SAVE_DIR.mkdir(parents=True, exist_ok=True)

STATS = ["strength", "dexterity", "constitution", "intelligence", "wisdom", "charisma"]

RACES = {
    "human": {"strength": 1, "dexterity": 1, "constitution": 1, "intelligence": 1, "wisdom": 1, "charisma": 1},
    "elf": {"strength": 0, "dexterity": 2, "constitution": 0, "intelligence": 2, "wisdom": 1, "charisma": 1},
    "dwarf": {"strength": 2, "dexterity": 0, "constitution": 2, "intelligence": 0, "wisdom": 1, "charisma": 0},
    "halfling": {"strength": 0, "dexterity": 2, "constitution": 1, "intelligence": 1, "wisdom": 1, "charisma": 2},
    "dragonborn": {"strength": 2, "dexterity": 0, "constitution": 1, "intelligence": 0, "wisdom": 0, "charisma": 2},
}

CLASSES = {
    "fighter": {
        "mods": {"strength": 4, "dexterity": 2, "constitution": 3, "intelligence": 1, "wisdom": 1, "charisma": 1},
        "resource": "stamina",
    },
    "wizard": {
        "mods": {"strength": 1, "dexterity": 2, "constitution": 1, "intelligence": 5, "wisdom": 3, "charisma": 1},
        "resource": "mana",
    },
    "rogue": {
        "mods": {"strength": 2, "dexterity": 5, "constitution": 2, "intelligence": 2, "wisdom": 1, "charisma": 2},
        "resource": "focus",
    },
    "cleric": {
        "mods": {"strength": 2, "dexterity": 1, "constitution": 3, "intelligence": 2, "wisdom": 5, "charisma": 2},
        "resource": "faith",
    },
    "ranger": {
        "mods": {"strength": 3, "dexterity": 4, "constitution": 2, "intelligence": 2, "wisdom": 2, "charisma": 1},
        "resource": "focus",
    },
}

ENEMIES = [
    ("Goblin Scout", 1.0), ("Bandit Marauder", 1.2), ("Cult Whisperer", 1.3), ("Wight Sentinel", 1.5),
    ("Iron Golem Fragment", 1.7), ("Void Hound", 1.8), ("Bone Drake", 2.0), ("Shadow Knight", 2.2),
]


@dataclass
class Player:
    username: str
    race: str
    role_class: str
    level: int
    xp: int
    gold: int
    hp: int
    max_hp: int
    resource: int
    max_resource: int
    region_index: int
    floor: int
    inventory: List[str]
    relics: List[str]
    stats: Dict[str, int]

    def to_json(self) -> Dict:
        return asdict(self)

    @classmethod
    def from_json(cls, payload: Dict) -> "Player":
        return cls(**payload)


def wrap(text: str) -> None:
    print("\n".join(textwrap.wrap(text, width=96)))


def save_path(username: str) -> Path:
    safe = "".join(ch for ch in username if ch.isalnum() or ch in "-_ ").strip().replace(" ", "_")
    return SAVE_DIR / f"{(safe or 'adventurer').lower()}.json"


def save_player(player: Player) -> None:
    save_path(player.username).write_text(json.dumps(player.to_json(), indent=2))


def load_player(username: str):
    path = save_path(username)
    return Player.from_json(json.loads(path.read_text())) if path.exists() else None


def ask_choice(prompt: str, options: List[str]) -> str:
    while True:
        print(f"\n{prompt}")
        for i, item in enumerate(options, start=1):
            print(f"  {i}. {item}")
        raw = input("> ").strip().lower()
        if raw.isdigit() and 1 <= int(raw) <= len(options):
            return options[int(raw) - 1]
        if raw in options:
            return raw
        print("Choose a listed option.")


def make_player(username: str) -> Player:
    race = ask_choice("Choose race", list(RACES.keys()))
    role_class = ask_choice("Choose class", list(CLASSES.keys()))
    stats = {stat: 8 + RACES[race][stat] + CLASSES[role_class]["mods"][stat] for stat in STATS}
    max_hp = 24 + stats["constitution"] * 2
    max_resource = 10 + stats["wisdom"] + stats["intelligence"] // 2
    return Player(
        username=username,
        race=race,
        role_class=role_class,
        level=1,
        xp=0,
        gold=30,
        hp=max_hp,
        max_hp=max_hp,
        resource=max_resource,
        max_resource=max_resource,
        region_index=0,
        floor=1,
        inventory=["Adventurer Pack", "Dented Buckler"],
        relics=[],
        stats=stats,
    )


def xp_to_next(level: int) -> int:
    return 120 + (level - 1) * 65


def regen(player: Player) -> None:
    player.resource = min(player.max_resource, player.resource + 2 + player.level // 2)


def class_attack_stat(player: Player) -> str:
    if player.role_class in {"wizard", "cleric"}:
        return "intelligence" if player.role_class == "wizard" else "wisdom"
    if player.role_class == "rogue":
        return "dexterity"
    return "strength"


def generate_enemy(player: Player, rng: random.Random) -> Dict[str, int | str]:
    region_scaling = 1 + player.region_index * 0.3 + player.floor * 0.08
    name, base = rng.choice(ENEMIES)
    level = max(1, int(player.level * 0.9 + rng.randint(0, 2) + player.floor * 0.35))
    hp = int((18 + level * 7) * base * region_scaling)
    attack = int((4 + level * 2) * base)
    defense = int((8 + level) * (0.8 + base / 3))
    return {"name": name, "level": level, "hp": hp, "attack": attack, "defense": defense}


def attack(player: Player, enemy: Dict[str, int | str], rng: random.Random, move: str) -> str:
    atk_stat = class_attack_stat(player)
    roll = rng.randint(1, 20) + player.stats[atk_stat] // 2 + player.level
    dmg = rng.randint(2, 8) + player.stats[atk_stat] // 3 + player.level
    resource_cost = 0
    if move == "skill":
        resource_cost = 5
        roll += 2
        dmg += rng.randint(5, 12)
    elif move == "ultimate":
        resource_cost = 9
        roll += 4
        dmg += rng.randint(10, 18)
    if player.resource < resource_cost:
        return "Not enough class resource."
    player.resource -= resource_cost
    if roll >= enemy["defense"]:
        enemy["hp"] -= dmg
        return f"Hit for {dmg}."
    return "Missed."


def enemy_turn(player: Player, enemy: Dict[str, int | str], rng: random.Random) -> str:
    evasion = player.stats["dexterity"] // 3 + player.level
    roll = rng.randint(1, 20) + enemy["level"]
    if roll < 10 + evasion:
        return f"{enemy['name']} misses."
    dmg = max(1, enemy["attack"] + rng.randint(-3, 4) - player.stats["constitution"] // 3)
    player.hp -= dmg
    return f"{enemy['name']} deals {dmg}."


def level_up(player: Player, rng: random.Random) -> List[str]:
    updates = []
    while player.xp >= xp_to_next(player.level):
        player.xp -= xp_to_next(player.level)
        player.level += 1
        chosen = rng.sample(STATS, k=2)
        for stat in chosen:
            player.stats[stat] += 1
        hp_gain = 8 + player.stats["constitution"] // 2
        res_gain = 3 + (player.stats["wisdom"] + player.stats["intelligence"]) // 8
        player.max_hp += hp_gain
        player.max_resource += res_gain
        player.hp = player.max_hp
        player.resource = player.max_resource
        updates.append(f"Level {player.level}! +1 {chosen[0]}, +1 {chosen[1]}, +{hp_gain} HP, +{res_gain} resource.")
    return updates


def reward_loot(player: Player, enemy: Dict[str, int | str], rng: random.Random) -> List[str]:
    notes = []
    gain_xp = 35 + enemy["level"] * 20 + player.floor * 4
    gain_gold = 10 + enemy["level"] * 6
    player.xp += gain_xp
    player.gold += gain_gold
    notes.append(f"+{gain_xp} XP, +{gain_gold} gold")
    if rng.random() < 0.55:
        item = f"{rng.choice(TREASURE_PREFIXES)} Relic +{1 + player.region_index}"
        player.inventory.append(item)
        notes.append(f"Loot: {item}")
    if rng.random() < 0.18:
        relic = f"Sigil of {rng.choice(['Dawn','Woe','Tides','Embers','Glass','Night'])}"
        player.relics.append(relic)
        notes.append(f"Major relic found: {relic}")
    return notes


def run_combat(player: Player, rng: random.Random) -> bool:
    enemy = generate_enemy(player, rng)
    wrap(f"Encounter: {enemy['name']} (lvl {enemy['level']}) in {REGION_NAMES[player.region_index]}.")
    while enemy["hp"] > 0 and player.hp > 0:
        print(f"\nYou HP {player.hp}/{player.max_hp} | Resource {player.resource}/{player.max_resource} | Enemy HP {enemy['hp']}")
        choice = ask_choice("Combat action", ["attack", "skill", "ultimate", "potion", "flee"])
        if choice == "flee":
            if rng.random() < 0.4:
                wrap("You escaped.")
                return True
            wrap("Escape failed.")
        elif choice == "potion":
            heal = min(player.max_hp - player.hp, 10 + player.level * 2)
            player.hp += heal
            wrap(f"You recover {heal} HP.")
        else:
            wrap(attack(player, enemy, rng, choice))
        if enemy["hp"] > 0:
            wrap(enemy_turn(player, enemy, rng))
            regen(player)
    if player.hp <= 0:
        wrap("Defeat. Temple healers rescue you and claim 20 gold tithe.")
        player.hp = max(1, player.max_hp // 2)
        player.gold = max(0, player.gold - 20)
        return False
    wrap("Victory: " + "; ".join(reward_loot(player, enemy, rng)))
    for message in level_up(player, rng):
        wrap(message)
    return True


def narrative_event(player: Player, rng: random.Random) -> None:
    event_idx = rng.randrange(len(ENCOUNTER_DESCRIPTIONS))
    objective_idx = rng.randrange(len(QUEST_OBJECTIVES))
    wrap(ENCOUNTER_DESCRIPTIONS[event_idx])
    wrap("Quest: " + QUEST_OBJECTIVES[objective_idx])
    option = ask_choice("Event action", ["investigate", "parley", "pray", "ignore"])
    if option == "investigate":
        score = rng.randint(1, 20) + player.stats["intelligence"] // 2
        if score >= 15:
            bonus = 12 + player.floor * 3
            player.gold += bonus
            wrap(f"You decode clues and recover {bonus} gold.")
        else:
            harm = 4 + player.floor
            player.hp = max(1, player.hp - harm)
            wrap(f"Trap backlash: {harm} HP lost.")
    elif option == "parley":
        score = rng.randint(1, 20) + player.stats["charisma"] // 2
        if score >= 14:
            xp = 25 + player.region_index * 8
            player.xp += xp
            wrap(f"Words win allies: +{xp} XP.")
            for message in level_up(player, rng):
                wrap(message)
        else:
            wrap("Talks collapse into violence.")
            run_combat(player, rng)
    elif option == "pray":
        restore = min(player.max_resource - player.resource, 7 + player.level)
        player.resource += restore
        wrap(f"Inner strength restored by {restore}.")
    else:
        wrap("You move on, guarding your strength.")


def visit_market(player: Player, rng: random.Random) -> None:
    print("\n=== Wayfarer Market ===")
    item_cost = 28 + player.level * 7
    training_cost = 44 + player.level * 10
    choice = ask_choice("Market option", ["buy potion", "train", "leave"])
    if choice == "buy potion":
        if player.gold < item_cost:
            wrap("Not enough gold.")
        else:
            player.gold -= item_cost
            heal = min(player.max_hp - player.hp, 22)
            player.hp += heal
            wrap(f"Potion consumed. Restored {heal} HP for {item_cost} gold.")
    elif choice == "train":
        if player.gold < training_cost:
            wrap("Not enough gold.")
        else:
            stat = rng.choice(STATS)
            player.gold -= training_cost
            player.stats[stat] += 1
            wrap(f"Training complete: +1 {stat}.")


def advance_floor(player: Player, rng: random.Random) -> None:
    player.floor += 1
    if player.floor % 4 == 0:
        player.region_index = min(player.region_index + 1, len(REGION_NAMES) - 1)
        wrap(f"You enter a new region: {REGION_NAMES[player.region_index]}.")
    if rng.random() < 0.35:
        player.max_hp += 2
        player.max_resource += 1
        wrap("Campfire boon: +2 max HP and +1 max resource.")


def show_sheet(player: Player) -> None:
    print("\n=== Hero Sheet ===")
    print(f"{player.username} the {player.race.title()} {player.role_class.title()}")
    print(
        f"Level {player.level} | XP {player.xp}/{xp_to_next(player.level)} | HP {player.hp}/{player.max_hp} | "
        f"{CLASSES[player.role_class]['resource'].title()} {player.resource}/{player.max_resource}"
    )
    print(f"Gold {player.gold} | Region {REGION_NAMES[player.region_index]} | Floor {player.floor}")
    print("Stats: " + ", ".join(f"{k[:3].upper()} {v}" for k, v in player.stats.items()))
    if player.relics:
        print("Relics: " + ", ".join(player.relics[-5:]))
    print("Inventory: " + ", ".join(player.inventory[-6:]))


def run_game(player: Player) -> None:
    seed = int.from_bytes(os.urandom(8), "big") ^ random.getrandbits(32)
    rng = random.Random(seed)
    wrap(f"Run seed {seed}. No two descents should feel alike.")
    while True:
        show_sheet(player)
        choice = ask_choice("Choose action", ["explore", "battle", "market", "camp", "save", "quit"])
        if choice == "explore":
            narrative_event(player, rng)
            if rng.random() < 0.45:
                run_combat(player, rng)
            advance_floor(player, rng)
        elif choice == "battle":
            run_combat(player, rng)
            if rng.random() < 0.2:
                advance_floor(player, rng)
        elif choice == "market":
            visit_market(player, rng)
        elif choice == "camp":
            heal = min(player.max_hp - player.hp, 8 + player.level)
            player.hp += heal
            regen(player)
            wrap(f"Camp rest recovers {heal} HP and some class resource.")
        elif choice == "save":
            save_player(player)
            wrap("Progress saved.")
        else:
            save_player(player)
            wrap("The chronicle is sealed until your return.")
            return


def main() -> None:
    print("== Emberdeep Reforged ==")
    username = input("Username: ").strip() or "adventurer"
    player = load_player(username)
    if player:
        decision = ask_choice("Save found. Continue or rebuild?", ["continue", "rebuild"])
        if decision == "rebuild":
            player = make_player(username)
    else:
        player = make_player(username)
    run_game(player)


if __name__ == "__main__":
    main()
