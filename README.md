# Relay Protocol

An original, round-based tactical first-person shooter prototype, written in Python with
[Ursina](https://www.ursinaengine.org/) (MIT-licensed engine).

> **⚠ Consult a qualified lawyer before commercial release.**
> This project was designed to avoid infringing third-party IP, but this README is not legal
> advice. Before selling, monetising or publicly distributing it, get a professional review,
> including a trademark search on the game's title and team names.

## Status

| Phase | Scope | State |
|---|---|---|
| 1 | Controller, movement, original map, minimal HUD | **done** |
| 2 | Weapons (recoil/spread), Field Knife speed boost, armor, bots | **done** |
| 3 | Flag plant/takedown, round flow, buy phase/economy, first-to-5 | **done** |
| 4 | Cosmetic skin/crate stubs (no store), final originality docs | not started |

## Running

Requires Python 3.11+.

```bash
pip install -r requirements.txt
python main.py
```

| Action | Key |
|---|---|
| Move | W A S D |
| Jump | Space (buffered briefly, so an early press still jumps on landing) |
| Crouch | Ctrl or C (crouching mid-air tucks your legs up to clear higher ledges) |
| Walk | Shift |
| Fire / melee | Left mouse |
| Reload | R (also reloads automatically when the magazine runs dry) |
| Select weapon | 1 / 2 / 3, or the mouse wheel |
| Plant the flag (attackers, inside a site) / take it down (defenders, next to it) | **hold E** |
| Buy menu (buy phase only) | **B**. Inside the menu, 1–4 or a click buys; B or Esc closes |
| F5 | Buy phase: respawn at the next spawn point. Round end: skip to the next round. Match end: start a new match. **Does nothing while the round is live.** |
| Release / recapture mouse | Esc / left click |
| Controls overlay / debug readout | F1 / F3 |
| Crosshair and screen settings | F4 |
| Inspect weapon | F |
| Quit | F10 |

Tab no longer switches sides; sides are fixed for each match. To play the other side, set
`[match] player_team` in config.

All tuning lives in [config.toml](config.toml): movement, weapons, spread, recoil, armor,
headshot multipliers, bot skill, navigation, flag timings, round timings, match length and
economy.

## Match rules

- **Format.** A match is first to `rounds_to_win` (5) rounds. **Vanguard** always
  attacks and **Sentinel** always defends. `swap_sides_at_halftime` is in config but not
  implemented yet.
- **Round phases.**
  1. Buy phase: 15 s. Movement is locked and the buy menu is open.
  2. Live: 1:45.
  3. Round end: 5 s with a winner banner. Then the next round starts, or the match ends.
- **The flag.**
  - At the start of each round, a Vanguard bot carries the flag. The player carries it
    only when there are no Vanguard bots.
  - The carrier moves at ×0.85.
  - If the carrier dies, the flag drops. Any Vanguard who walks over it picks it up. If
    nobody touches it for 20 s, it returns to the Vanguard spawn.
- **Plant.** Hold E inside Site Alpha or Site Bravo for 3 s while carrying the flag. A
  25 s countdown then starts.
- **Takedown.** Hold E within 2 m of the planted flag for 5 s. Moving, taking damage or
  releasing E resets the progress to 0. Progress is shown to you and your team only.
- **Winning a round.**

  | Situation | Winner |
  |---|---|
  | Takedown completed | Sentinel |
  | Planted flag's countdown runs out | Vanguard |
  | Round time runs out before a plant | Sentinel |
  | One side fully eliminated | The other side. A planted flag still has to be taken down. Set `elimination_wins = false` to turn this off. |

- **Loadout between rounds.** Survivors keep their weapons. Anyone who died goes back to
  the Field Knife. Armor and helmet are cleared every round.

## Economy (original numbers)

All values are in `[economy]`:

- **Starting money:** 1,000. Money is capped at 12,000 and never goes below 0.
- **Rewards:** a kill pays 250. Winning a round pays 3,000.
- **Loss bonus:** a losing team's bonus climbs with each consecutive loss: 1,000 → 1,500
  → 2,000 → 2,500 → 3,000. A win resets the climb.
- **Prices:**
  - RK-9 Rifle: 2,800
  - SD-4 Sidearm: 450
  - Armor Vest: 600
  - Helmet: 400
  - Field Knife: free, always owned
- **Owned items:** buying something you already own costs nothing.
- **Bots** buy automatically during each buy phase. They take a rifle and armor when they
  can afford both, and a sidearm and armor otherwise.

## Weapons

| Slot | Name | Type | Damage | Rate | Mag / reserve | Movement |
|---|---|---|---|---|---|---|
| 1 | RK-9 Rifle | automatic hitscan | 31 | 600 rpm | 30 / 90 | ×0.88 |
| 2 | SD-4 Sidearm | semi-auto hitscan | 24 | 380 rpm | 12 / 36 | ×0.97 |
| 3 | Field Knife | melee, 1.9 m, 40° arc | 45 | 80 rpm | — | **×1.25** |

How shooting works (all values are set in `[weapons.*]` and `[combat]` in config):

- **Spread cone.** Shots land inside a cone. Crouching is most accurate, then standing,
  then moving (scaled by speed), and jumping is least accurate. The first shot after a
  pause has no bloom, so it is accurate. Sustained fire widens the cone, and the
  crosshair gap widens with it.
- **Recoil.** Each shot kicks the aim upward. The kick grows over the first shots of a
  spray, up to a cap, and the aim drifts sideways along a smooth wave unique to each
  weapon. The camera shows part of the kick, so bullets land above the crosshair. Recoil
  recovers once you stop firing.
- **Damage falloff.** Damage is multiplied by `falloff_per_10m` for every 10 m travelled.
- **Armor and helmet.** Armor absorbs `armor_absorption` of each body hit and loses
  `armor_wear` points per point absorbed. Head hits use the headshot multiplier (3.6×). A
  helmet lowers it to 2.2× and lets armor absorb head hits as well.
- **Reload.** Switching weapons cancels a reload that is in progress.

Phase 2 has no audio; all effects are silent placeholders. Muzzle flashes, tracers and
impacts are simple primitive shapes.

## Bots

There are 3 allies and 4 enemies by default (`[bots]` in config). Each bot has an original
callsign (Kestrel, Basalt, Juniper and others). Bots:

- Move by following precomputed flow fields on a navigation grid. Moving targets, such as
  a dropped flag, the flag carrier or a planted flag, get fields that are rebuilt as the
  target moves.
- Spot enemies within their view cone and range, provided line of sight is clear.
- After a reaction delay, turn toward the enemy at a limited turn rate, with some random
  aim error, and fire in bursts.
- Stand still while firing for accuracy, and hold fire when a teammate is in the way.
- Fight first. Once no enemy is in sight, they go back to the objective.
- Stay dead until the next round, like the player.

Each round, the **BotDirector** picks Site Alpha or Site Bravo for Vanguard and gives
every bot a **BotRole**:

| Role | Behaviour |
|---|---|
| CARRIER | A Vanguard bot with the flag. Walks to the chosen site and holds E to plant. |
| ESCORT | A Vanguard bot that stays within about 5 m of the carrier, whether the carrier is a bot or you. |
| SITE_HOLDER | Before the plant, a Sentinel bot rotates between guard spots on its assigned site, and some Vanguard bots push the target site. After the plant, Vanguard bots guard the planted site. |
| RETAKER | After the plant, every Sentinel bot heads for the flag and holds E to take it down. If it is interrupted, it tries again. |

Other rules:

- If the flag drops, Vanguard bots go to pick it up.
- If you carry the flag, Sentinel bots chase you.

The **ObjectiveBrain** turns each bot's role and the flag's state into an order: where to
go, how close to get, and whether to hold E on arrival.

### Checks

```bash
python tools/check_map.py          # headless: map, physics, nav, weapons/damage, rounds, flag, economy
python main.py --smoke OUT_DIR     # opens a window ~4 min: weapons, buy menu, F5 gating, 3 bot-played rounds, match end
```

## Project layout

```
main.py                     entry point + session glue (HUD feed, respawns, meta keys)
config.toml                 every tunable value
game/settings.py            config loader
game/physics.py             engine-independent AABB collision + movement maths
game/player.py              first-person controller (fixed-step, interpolated camera), combatant
game/weapons.py             WeaponDefinition (from config) + WeaponState: ammo, spread, recoil
game/combat.py              ray casts, hitboxes, damage model (armor/helmet/falloff)
game/shooting.py            hitscan + melee shot resolution shared by player and bots
game/arsenal.py             the player's weapons: switching, trigger, reload
game/viewmodel.py           first-person weapon placeholders built from boxes
game/effects.py             tracers, impact puffs, muzzle flashes
game/nav.py                 bot navigation grid + flow fields (static and moving targets)
game/bots.py                BotDirector / BotRole / ObjectiveBrain + bot body (sense, aim, shoot, move)
game/rounds.py              RoundManager state machine + flag (engine-independent)
game/economy.py             money, loss ladder, purchases, bot auto-buy (engine-independent)
game/buymenu.py             the "Requisition" buy menu
game/flag_visual.py         the flag's in-world model
game/smoke.py               in-engine automated smoke test
game/world.py               builds the visible scene from map data
game/maps/relay_station.py  the original map (pure data: boxes, zones, spawns)
game/hud.py                 the original HUD
game/textures.py            procedurally generated textures
tools/check_map.py          headless map/physics validation
DESIGN_LOG.md               design decisions and their sources
```

## The map: Relay Station

A hill-top signal relay facility at dusk, built on a 120 m × 96 m grid from primitive boxes.

- **Site Alpha: Antenna Yard.** An open-air raised pad with a dish mast. It can be reached on
  foot from the yard (via Cable Run, the Switch Gate or the Ridge Door) or by dropping off
  the elevated **Gantry** that runs from the Switchyard's **Overlook**.
- **Site Bravo: Generator Hall.** An enclosed hall with generator blocks and a high catwalk,
  entered through three doors: Dock Door from Loading Dock, Hall Door from Pump Corridor, and
  Back Door from Back Hall.
- **Switchyard:** the central plaza. A 12 m relay tower blocks the long sightline between the
  two spawns.
- **Spawns:** South Muster (attackers) and North Post (defenders).

**The map is original.** It was laid out from scratch for this project, with its own
premise, routes, structures and callout names. It is not derived from the layout,
sightlines, geometry or callouts of any existing game's map. See the ASCII plan at the
top of [game/maps/relay_station.py](game/maps/relay_station.py).

## Originality Statement

Everything below was invented for this project:

- **Title:** "Relay Protocol".
- **Map:** "Relay Station": its layout, premise, structures (relay tower, Gantry, Overlook,
  Antenna Yard pad, Generator Hall catwalk, Loading Dock) and every callout name.
- **Objective vocabulary:** a "flag" is planted and taken down. The project does not use
  terms associated with other games' objectives.
- **Teams:** attackers and defenders, with display names set in `config.toml`.
- **Weapons:** the names, the box-built viewmodels and every stat (damage, rate, spread,
  recoil wave, falloff, speed) were invented for this project. No recoil pattern data
  from any game was used.
- **Bots:** callsigns, silhouettes and behaviour were designed here.
- **Objective and economy:**
  - The flag's design was made for this project: an orange pennant on a mast with a
    beacon.
  - The "Requisition" buy menu layout is original.
  - Every economy number (starting money, kill and win rewards, the loss-bonus ladder,
    prices) and every flag and round timing was set for this project. None were copied
    from another game.
- **UI:** the HUD layout, X-tick crosshair, colour palette, bar style and score card were
  designed here.
- **Assets:** no image, model, sound or music files are bundled. All geometry is engine
  primitives (cubes, planes, spheres). The floor and zone textures are generated in code at
  startup (`game/textures.py`). There is no audio yet; later phases will use silence or
  procedurally generated tones.
- **Code:** written for this project. The mechanics (acceleration/friction movement,
  step-up, buy phase, economy and so on) are general genre conventions, implemented from
  first principles. No other game's code, data files or assets were consulted or copied.

**Third-party components** (all permissively licensed):

- The Ursina engine (MIT) and Panda3D (BSD).
- Two fonts bundled with Ursina: Bitstream Vera Sans Mono (Bitstream Vera licence) and
  OpenSans (Apache 2.0).
- The default window icon is Ursina's. Replace it with an original icon before
  distribution.

**No Valve assets, trademarks, names, maps, sounds, UI or code are used.**

## Legal Safety Checklist

| # | Principle | Status (Phase 3) |
|---|---|---|
| 1 | Mechanics only, no copied expression | ✅ Movement, spread, recoil, armor, rounds and economy use generic rules with original values. Nothing reproduces another game's art, audio, maps, UI, recoil data or price/bonus tables. |
| 2 | No Valve/Counter-Strike IP | ✅ No Valve names, trademarks or terms in code, UI or docs, except this checklist naming what is avoided. "Flag", "plant" and "takedown" are used for the objective, and "Requisition" and "credits" for buying. |
| 3 | Original names and branding | ✅ Title, map, sites and callouts are original. ⚠ The default team names "Vanguard"/"Sentinel" overlap with Riot's anti-cheat name and a well-known esports team. They are configurable; consider changing them before release. |
| 4 | Original assets only | ✅ Primitives and code-generated textures only, including the weapon and bot shapes. No downloaded assets. No audio. |
| 5 | Original map design | ✅ Relay Station was designed from scratch (see the map section). |
| 6 | Original UI / trade dress | ✅ Own layout, palette, crosshair, buy ledger and banner. Phase 3 moved the round clock to top-centre, as requested; it is a generic convention, and the surrounding card, colours and fonts remain this project's own. |
| 7 | Originality documented | ✅ This README and [DESIGN_LOG.md](DESIGN_LOG.md). |
| 8 | No monetisation | ✅ No store, payments or crates. Cosmetic-only stubs are planned for Phase 4, with no store. |

**Before publishing:** the project folder is named `counter-alien`, and the "Counter-"
prefix echoes a Valve trademark. Don't use that name for the game, the repository or any
store listing. "Relay Protocol" is the in-game title.
