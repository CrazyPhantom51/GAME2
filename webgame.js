const races = {
  human: { strength: 1, dexterity: 1, constitution: 1, intelligence: 1, wisdom: 1, charisma: 1 },
  elf: { strength: 0, dexterity: 2, constitution: 0, intelligence: 2, wisdom: 1, charisma: 1 },
  dwarf: { strength: 2, dexterity: 0, constitution: 2, intelligence: 0, wisdom: 1, charisma: 0 },
  halfling: { strength: 0, dexterity: 2, constitution: 1, intelligence: 1, wisdom: 1, charisma: 2 },
};

const classes = {
  fighter: { strength: 4, dexterity: 2, constitution: 3, intelligence: 1, wisdom: 1, charisma: 1 },
  wizard: { strength: 1, dexterity: 2, constitution: 1, intelligence: 5, wisdom: 3, charisma: 1 },
  rogue: { strength: 2, dexterity: 5, constitution: 2, intelligence: 2, wisdom: 1, charisma: 2 },
  cleric: { strength: 2, dexterity: 1, constitution: 3, intelligence: 2, wisdom: 5, charisma: 2 },
};

const regions = ["Ashen Warrens", "Silverfen March", "Clockwork Basilica", "Stormvault Peaks", "Starfall Catacombs"];
const encounters = Array.from({ length: 300 }, (_, i) =>
  `Encounter ${i + 1}: The corridor shifts and strange sigils react to your steps.`
);

let game = null;
const byId = (id) => document.getElementById(id);

function rng(seed) {
  let x = seed >>> 0;
  return () => {
    x ^= x << 13;
    x ^= x >>> 17;
    x ^= x << 5;
    return ((x >>> 0) / 4294967296);
  };
}

function randomInt(rand, min, max) {
  return Math.floor(rand() * (max - min + 1)) + min;
}

function saveKey(user) {
  return `emberdeep_save_${user.toLowerCase().replace(/[^a-z0-9_-]/g, "_")}`;
}

function log(msg, good = false) {
  const p = document.createElement("p");
  if (good) p.className = "good";
  p.textContent = msg;
  byId("log").prepend(p);
}

function render() {
  if (!game) return;
  const s = game.player.stats;
  byId("sheet").innerHTML = `
    <p><strong>${game.player.username}</strong> the ${game.player.race} ${game.player.roleClass}</p>
    <p>Level ${game.player.level} | XP ${game.player.xp}/${game.player.level * 100}</p>
    <p>HP ${game.player.hp}/${game.player.maxHp} | Gold ${game.player.gold}</p>
    <p>Floor ${game.player.floor} | Region ${regions[game.player.region]}</p>
    <p>STR ${s.strength} DEX ${s.dexterity} CON ${s.constitution} INT ${s.intelligence} WIS ${s.wisdom} CHA ${s.charisma}</p>
    <p>Inventory: ${game.player.inventory.slice(-5).join(", ")}</p>
  `;
}

function makeNewPlayer(username) {
  const raceNames = Object.keys(races);
  const classNames = Object.keys(classes);
  const race = raceNames[Math.floor(Math.random() * raceNames.length)];
  const roleClass = classNames[Math.floor(Math.random() * classNames.length)];
  const stats = {};
  Object.keys(races[race]).forEach((k) => stats[k] = 8 + races[race][k] + classes[roleClass][k]);
  const maxHp = 24 + stats.constitution * 2;
  return {
    username,
    race,
    roleClass,
    level: 1,
    xp: 0,
    gold: 30,
    hp: maxHp,
    maxHp,
    floor: 1,
    region: 0,
    inventory: ["Traveler's Kit", "Bronze Dagger"],
    stats,
  };
}

function startGame() {
  const username = (byId("username").value.trim() || "adventurer");
  const stored = localStorage.getItem(saveKey(username));
  if (stored && confirm("Load existing save for this username?")) {
    game = JSON.parse(stored);
  } else {
    const seed = (crypto.getRandomValues(new Uint32Array(1))[0] ^ Date.now()) >>> 0;
    game = { seed, randState: seed, player: makeNewPlayer(username) };
  }
  byId("auth").classList.add("hidden");
  byId("game").classList.remove("hidden");
  byId("log").innerHTML = "";
  log(`Run seed: ${game.seed}. Every run changes with random encounters.`);
  render();
}

function stepRand() {
  game.randState = (game.randState * 1664525 + 1013904223) >>> 0;
  return game.randState / 4294967296;
}

function battle() {
  const p = game.player;
  const enemyLevel = Math.max(1, p.level + randomInt(stepRand, -1, 2) + Math.floor(p.floor / 2));
  let enemyHp = 16 + enemyLevel * randomInt(stepRand, 5, 9);
  const enemyAtk = 3 + enemyLevel * randomInt(stepRand, 1, 2);
  log(`A level ${enemyLevel} foe appears in ${regions[p.region]}.`);

  while (enemyHp > 0 && p.hp > 0) {
    const heroHit = randomInt(stepRand, 1, 20) + Math.floor(p.stats.strength / 2) + p.level;
    if (heroHit >= 11 + enemyLevel) {
      const dmg = randomInt(stepRand, 3, 10) + p.level;
      enemyHp -= dmg;
      log(`You hit for ${dmg}. Enemy HP: ${Math.max(0, enemyHp)}`);
    } else log("You miss.");

    if (enemyHp <= 0) break;

    const enemyHit = randomInt(stepRand, 1, 20) + enemyLevel;
    if (enemyHit >= 10 + Math.floor(p.stats.dexterity / 3)) {
      const dmg = Math.max(1, enemyAtk - Math.floor(p.stats.constitution / 4));
      p.hp -= dmg;
      log(`Enemy hits you for ${dmg}. HP: ${Math.max(0, p.hp)}`);
    } else log("Enemy misses.");
  }

  if (p.hp <= 0) {
    p.hp = Math.max(1, Math.floor(p.maxHp / 2));
    p.gold = Math.max(0, p.gold - 15);
    log("You were rescued and lose 15 gold.");
  } else {
    const xp = 30 + enemyLevel * 14;
    const gold = 8 + enemyLevel * 6;
    p.xp += xp;
    p.gold += gold;
    if (stepRand() < 0.6) p.inventory.push("Recovered Relic");
    log(`Victory! +${xp} XP, +${gold} gold.`, true);
    while (p.xp >= p.level * 100) {
      p.xp -= p.level * 100;
      p.level++;
      p.maxHp += 8;
      p.hp = p.maxHp;
      log(`Level up! You are now level ${p.level}.`, true);
    }
  }
}

function explore() {
  const p = game.player;
  log(encounters[randomInt(stepRand, 0, encounters.length - 1)]);
  if (stepRand() < 0.45) battle();
  if (stepRand() < 0.35) {
    p.floor++;
    if (p.floor % 4 === 0) p.region = Math.min(regions.length - 1, p.region + 1);
    log(`You descend to floor ${p.floor}.`);
  }
}

function act(action) {
  if (!game) return;
  const p = game.player;
  if (action === "explore") explore();
  if (action === "battle") battle();
  if (action === "rest") {
    const heal = Math.min(p.maxHp - p.hp, 12 + p.level);
    p.hp += heal;
    log(`You rest and recover ${heal} HP.`);
  }
  if (action === "shop") {
    const cost = 20 + p.level * 6;
    if (p.gold >= cost) {
      p.gold -= cost;
      p.maxHp += 4;
      p.hp = Math.min(p.maxHp, p.hp + 10);
      log(`You buy supplies for ${cost} gold. +4 max HP.`, true);
    } else log("Not enough gold.");
  }
  if (action === "save") {
    localStorage.setItem(saveKey(p.username), JSON.stringify(game));
    log("Game saved.", true);
  }
  if (action === "newrun") {
    if (confirm("Start a fresh random run? Current unsaved progress will be lost.")) {
      game = { seed: crypto.getRandomValues(new Uint32Array(1))[0], randState: crypto.getRandomValues(new Uint32Array(1))[0], player: makeNewPlayer(p.username) };
      byId("log").innerHTML = "";
      log(`New run seed: ${game.seed}`);
    }
  }
  render();
}

byId("startBtn").addEventListener("click", startGame);
document.querySelectorAll("[data-action]").forEach(btn => btn.addEventListener("click", () => act(btn.dataset.action)));
