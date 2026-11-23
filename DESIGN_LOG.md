# Design Log: Relay Protocol

This log records design decisions and where they came from. Mechanics were implemented from
general genre knowledge and first-principles maths. No files, code, assets or data from
any existing game were opened, copied or referenced.

## Phase 1: controller, map, HUD (2026-11-23)

**Engine.** Ursina 8.3 (MIT) on Panda3D. Collision and movement are written in plain Python
(`game/physics.py`), not Ursina's built-in controller, so the movement feel is fully
tunable and the physics can be tested headless.

**Movement model.** This is a standard kinematic character model:

- Speed-proportional ground friction with a minimum "stop speed".
- Acceleration toward a wish direction, capped at a wish speed.
- Weak air acceleration with a cap.
- Gravity and a jump impulse.
- Automatic step-up onto ledges up to 0.55 m, and snap-down onto lower steps.

This family of techniques is widely documented in general game-programming material. All
values are original and live in `config.toml`.

The simulation runs in fixed 120 Hz sub-steps, and the camera is interpolated between
them. Crouching shrinks the collision box. Crouching mid-air tucks the legs up so you can
clear higher ledges.

**Collision.** Boxes are resolved one axis at a time. A per-step broad phase keeps only
nearby boxes. This is simple and robust, and fast enough for about 150 boxes.

**Map: Relay Station.** It was designed on paper as a "signal relay facility" premise
before any geometry was placed. The design goals were:

1. Two sites with contrasting character: an open, elevated outdoor pad (Alpha) and an
   enclosed hall with a catwalk (Bravo).
2. A central tower that breaks the spawn-to-spawn sightline.
3. A shared crossing point (Pump Corridor) that both teams contest.
4. Verticality through the Overlook, the Gantry bridge, the Bravo catwalk and the Loading
   Dock platform.

Every route was then checked with a 2.5D reachability flood-fill (`tools/check_map.py`).

**HUD.** The goal was a minimal readout with a distinctive identity:

- Location callout and credits at top-left.
- A compact score card at top-right, with the round clock between the two tallies.
- Health and armor as slim labelled bars at bottom-centre.
- Ammo tucked beside the crosshair.
- An X-shaped tick crosshair.

The palette is ink-navy panels with mint, periwinkle and amber accents, and teal versus
coral for the two teams.

**Naming.**

- The objective is a "flag" that is planted and taken down.
- Team display names come from config. The defaults follow the brief, and the README
  flags their overlap with existing gaming brands.
- The spawn areas use neutral names: South Muster and North Post.

**Assets.**

- All geometry is cubes, planes and spheres.
- The floor and zone-hatch textures are drawn with PIL at startup.
- There is no audio.
- The fonts are the ones Ursina ships (Bitstream Vera Sans Mono, OpenSans).

## Phase 2: weapons, armor, bots (2026-11-23)

**Weapons.** Weapons are data-driven: each one is a `[weapons.<id>]` table in
`config.toml`, loaded into a frozen `WeaponDefinition`. The three weapons (RK-9 Rifle,
SD-4 Sidearm, Field Knife) and all their numbers were chosen for this project's own
pacing. With a helmet, an RK-9 kills in 4 body hits. Without one, a single head hit kills.

**Spread.** Accuracy is a cone that grows with stance and bloom: crouched is best, then
standing, moving and airborne. These are standard genre ideas, written from first
principles. The crosshair gap follows the spread live.

**Recoil.** Recoil is generated in code, not taken from data tables:

- The vertical kick grows linearly over the first 8 shots, up to a cap.
- The horizontal drift follows a sine wave with a per-weapon phase, plus a little jitter.
- After a short rest, both recover exponentially.

The camera shows `view_kick_ratio` of the kick. No recoil pattern files from any game were
used or referenced.

**Hit detection.** Hit detection uses slab-test ray casts against the map's own boxes and
two hitboxes per combatant (body and head). Engine colliders are not used, so the maths
can be tested headless in `tools/check_map.py`.

**Armor.** A single `compute_damage` function holds the whole damage model. It covers
falloff, the headshot multiplier, the helmet's lower multiplier, armor absorption and wear.

**Bots.**

- *Navigation.* Bots use a 2.5D grid with several standing levels per cell, plus a
  reverse-Dijkstra flow field per named goal. Fields are computed once at startup (about
  0.4 s for 12 goals), and bots walk downhill. Look-ahead stops at height changes so bots
  don't cut corners on stairs.
- *Behaviour.* Perception is throttled to run every 0.15 s and checks range, view cone and
  line of sight. Bots wait out a reaction delay, then turn at a capped rate with
  re-rolled Gaussian aim error. They fire in bursts, partly control recoil, and hold fire
  when a teammate is in the line of fire.
- *Modularity.* Goal choice sits behind `PatrolBrain.next_goal()`, so Phase 3 can swap in
  objective play.

**Visual placeholders.**

- The viewmodels are original box assemblies with an orange stripe matching the map trim.
  They are scaled to 0.3× close to the camera so they can't clip into walls.
- Tracers, impact puffs and a diamond-shaped flash are drawn as unlit primitives.
- The hitmarker uses orthogonal ticks so it stands apart from the diagonal crosshair. It
  is white for a hit, amber for a head hit and red for a kill.


## Phase 3: flag objective, rounds, economy (2026-11-23)

**Structure.** Two engine-independent modules hold all the rules, so they are tested
headless in `tools/check_map.py`:

- `game/rounds.py`: the `RoundManager` state machine (BUY_FREEZE → LIVE → ROUND_END →
  MATCH_END) and the `Flag` (CARRIED, DROPPED, PLANTED).
- `game/economy.py`: money, the loss ladder, purchases and bot auto-buy.

The Ursina side only reads these and feeds them input.

**Flag rules.**

- Plant and takedown use one interaction routine, `_tick_interactions`. Moving faster
  than `interrupt_speed`, taking damage or releasing E resets progress to 0. Bots and the
  player go through exactly the same code.
- A dropped flag can be picked up by walking over it, and returns home after
  `flag_return_time`.
- Carrying the flag multiplies movement speed by `carrier_speed_multiplier`. The
  multiplier stacks with the weapon's.

**Elimination rule (an addition).** With respawns disabled during LIVE, a round where
every attacker died before planting would otherwise run out its full 1:45. I added
`[round] elimination_wins = true`:

- If a whole side is down, the other side wins.
- If the flag is planted, the defenders still have to take it down.

Set it to false for the strict "timers only" rule set.

**Loadout between rounds.**

- Survivors keep their weapons (`keep_weapons_if_alive`). Anyone who died drops back to
  `free_loadout`, which is the Field Knife.
- Armor and helmet are cleared every round, as the brief asks.

This makes the sidearm price meaningful, since nobody gets a free gun.

**Economy numbers.** These are original:

- Start money: 1,000. Kill: 250. Round win: 3,000.
- Loss ladder: 1,000, 1,500, 2,000, 2,500, 3,000. A win resets it.
- Cap: 12,000.
- Prices: RK-9 2,800, SD-4 450, armor 600, helmet 400.

Losers' bonuses are paid from their streak *before* it advances, so the first loss pays
the first rung.

**Bots.**

- `BotDirector` assigns a `BotRole` (CARRIER, ESCORT, SITE_HOLDER, RETAKER) at round start
  and on plant.
- `ObjectiveBrain` turns role and flag state into an `Order`: a field to follow, an
  arrival distance, and whether to hold E.
- Moving targets (dropped flag, carrier, planted flag) use shared *dynamic* flow fields.
  A field is rebuilt only when its target moves more than 1.5 m or is older than 2 s.
- Combat code from Phase 2 is unchanged. Fighting takes priority over the objective.

**HUD.**

- The round clock moved to top-centre, as the brief requested. It sits on its own ink
  card, with the phase label and a flag status line below.
- The score card (top-right) shows both team names.
- The plant/takedown progress bar sits at bottom-centre. It shows your own progress, or a
  teammate bot's, and never the enemy's.
- The round/match banner is a full-width ink band in the winning team's colour.
- The buy menu ("Requisition") is a narrow ledger at the left edge.

**Knife speed label (tuning-pass decision).** The Field Knife's ×1.25 was already
correct. It is measured against base run speed (`movement.run_speed`, 6.2 m/s), giving
7.75 m/s. The "≈1.42×" figure was knife compared with the RK-9 (1.25 ÷ 0.88). There is no
separate knife `max_speed` value. **Choice:** keep the gameplay numbers and relabel the HUD
readout as `x1.25 of base`, so it can't be misread as relative to another weapon. Config
and HUD now agree by construction: the HUD prints the configured multiplier, times the
flag-carrier multiplier when you carry the flag.

## [tuning]: values a designer is expected to tweak

Everything is in `config.toml`. None of these are hardcoded.

| Area | Keys |
|---|---|
| Flag timings | `[flag] plant_time`, `takedown_time`, `post_plant_time`, `flag_return_time`, `interrupt_speed`, `pickup_radius`, `interact_radius`, `carrier_speed_multiplier` |
| Round timings | `[round] freeze_time`, `round_time`, `round_end_delay`, `elimination_wins` |
| Match | `[match] rounds_to_win`, `player_team` |
| Economy | `[economy] start_money`, `max_money`, `kill_reward`, `round_win_reward`, `loss_bonus_ladder`, `rk9_price`, `sd4_price`, `armor_price`, `helmet_price`, `free_loadout`, `keep_weapons_if_alive` |
| Weapon movement | `[weapons.*] speed_multiplier` (knife 1.25, sidearm 0.97, rifle 0.88), `[movement] run_speed`, `walk_speed`, `crouch_speed` |
| Recoil / spread | `[weapons.*] recoil_vertical`, `recoil_vertical_growth`, `recoil_vertical_max`, `recoil_horizontal`, `recoil_recovery`, `view_kick_ratio`, `spread_stand`, `spread_crouch`, `spread_move`, `spread_air`, `bloom_per_shot`, `bloom_max`, `bloom_recovery` |
| Damage | `[weapons.*] damage`, `rpm`, `falloff_per_10m`; `[combat] headshot_multiplier`, `helmet_headshot_multiplier`, `armor_absorption`, `armor_wear` |
| Bot skill | `[bots] reaction_time`, `aim_error_deg`, `turn_speed`, `recoil_control`, `vision_range`, `vision_fov`, `burst_min`, `burst_max`, `hold_min`, `hold_max`, `allies`, `enemies` |