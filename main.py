"""RELAY PROTOCOL - Phase 3: flag objective, rounds, buy phase, economy.

    python main.py                 play
    python main.py --smoke DIR     automated smoke test: opens a window, saves
                                   screenshots to DIR, exercises movement,
                                   weapons, bots and full rounds, then exits
"""
from __future__ import annotations

import argparse

from ursina import Entity, Ursina, application, mouse, time

from game.settings import CFG

parser = argparse.ArgumentParser()
parser.add_argument("--smoke", metavar="DIR", help="run an automated smoke test and save screenshots")
args = parser.parse_args()

app = Ursina(
    title=CFG.window.title,
    fullscreen=CFG.window.fullscreen and not args.smoke,
    vsync=CFG.window.vsync,
    development_mode=False,
    size=(1280, 720) if args.smoke else None,
    window_type="onscreen",   # offscreen buffers mis-size the UI lens
)

# Imports that create entities must come after Ursina() exists.
from game.arsenal import Arsenal                              # noqa: E402
from game.bots import BotContext, BotDirector, ObjectiveBrain, spawn_bots  # noqa: E402
from game.buymenu import BuyMenu                              # noqa: E402
from game.combat import CombatWorld                           # noqa: E402
from game.economy import Economy                              # noqa: E402
from game.effects import Effects                              # noqa: E402
from game.flag_visual import FlagVisual                       # noqa: E402
from game.hud import HUD                                      # noqa: E402
from game.nav import NavGrid                                  # noqa: E402
from game.player import Player                                # noqa: E402
from game.rounds import ATTACKERS, FlagState, Phase, RoundManager  # noqa: E402
from game.weapons import load_definitions                     # noqa: E402
from game.world import World                                  # noqa: E402
import random                                                 # noqa: E402
from game.feature_settings import FeatureSettingsPanel       # noqa: E402

world = World(CFG)
combat = CombatWorld(world.collision, CFG.combat)
effects = Effects()
defs = load_definitions(CFG)

nav = NavGrid(world.collision, world.map.BOUNDS, CFG.nav.cell, CFG.nav.clearance_radius,
              CFG.player.stand_height, CFG.player.step_height, CFG.nav.max_drop)
for goal_name, point in world.map.NAV_POINTS.items():
    nav.build_field(goal_name, point)

player = Player(world, CFG, team=CFG.match.player_team)
hud = HUD(CFG)
arsenal = Arsenal(player, defs, combat, effects, hud, CFG)
ctx = BotContext(CFG, world, combat, nav, effects, defs)
bots = spawn_bots(ctx, player.team)
combat.combatants = [player, *bots]

economy = Economy(CFG)
rounds = RoundManager(CFG, world.map.PLANT_ZONES, world.map.NAV_POINTS["attacker_spawn"],
                      [player, *bots], economy, rng=random.Random())
ctx.rounds = rounds
for b in bots:
    b.brain = ObjectiveBrain()
director = BotDirector(ctx, random.Random())
flag_visual = FlagVisual(rounds)
buy_menu = BuyMenu(player, economy, rounds, arsenal)
feature_settings = FeatureSettingsPanel(hud, arsenal, buy_menu)

# wiring: kills -> economy/flag, damage -> plant/takedown interruption
combat.kill_listeners.append(lambda a, v, w, hs: rounds.on_kill(a, v))
combat.damage_listeners.append(lambda a, v, dmg: rounds.on_damaged(v))

if not args.smoke:          # the smoke test drives input itself
    mouse.locked = True


def team_name(team: str) -> str:
    return CFG.teams.attackers_name if team == ATTACKERS else CFG.teams.defenders_name


def site_short(zone_name: str) -> str:
    return world.map.SITE_KEYS.get(zone_name, zone_name).upper()


REASONS = {"takedown": "flag taken down", "flag_held": "planted flag held",
           "time": "time ran out", "elimination": "opposing side eliminated"}


class Session(Entity):
    """Phase 3 glue: drives the RoundManager, feeds the HUD, handles meta keys."""

    def __init__(self):
        super().__init__(name="session")
        self.spawn_index = 0
        self.fps_smooth = 60.0
        self.killer = ""
        player.on_damage_callbacks.append(lambda attacker, dmg: hud.damage_flash(dmg))
        player.on_death_callbacks.append(self._on_player_death)
        combat.kill_listeners.append(self._on_kill)
        rounds.listeners.append(self._on_round_event)
        rounds.start_match()

    def _on_player_death(self, attacker):
        self.killer = attacker.display_name if attacker else ""

    def _on_kill(self, attacker, victim, weapon_name, headshot):
        who = attacker.display_name if attacker else "?"
        hs = "  (head)" if headshot else ""
        hud.add_kill(f"{who} [{weapon_name}] {victim.display_name}{hs}")

    def _on_round_event(self, event, **data):
        if event == "round_start":
            nav.clear_dynamic()
            director.on_round_start(bots)
            self.killer = ""
        elif event == "plant":
            director.on_plant(bots, data["site"])
            hud.add_kill(f"{data['by'].display_name} planted the flag @ {site_short(data['site'])}")
        elif event == "takedown":
            hud.add_kill(f"{data['by'].display_name} took the flag down")
        elif event == "flag_drop":
            hud.add_kill("flag dropped")
        elif event == "flag_return":
            hud.add_kill("flag returned to base")

    # ------------------------------------------------------------ per frame
    def update(self):
        dt = time.dt
        rounds.tick(dt)
        phase = rounds.phase
        locked = rounds.movement_locked
        player.movement_locked = locked
        arsenal.weapons_locked = locked
        player.round_speed_multiplier = rounds.speed_multiplier(player)

        # clock + phase label
        post = rounds.post_plant_left()
        if phase == Phase.BUY_FREEZE:
            hud.set_clock(rounds.timer, f"BUY PHASE  -  press B  -  round {rounds.round_number}")
        elif post is not None:
            hud.set_clock(post, "FLAG PLANTED", urgent=True)
        elif phase == Phase.LIVE:
            hud.set_clock(rounds.timer, f"ROUND {rounds.round_number}")
        elif phase == Phase.ROUND_END:
            hud.set_clock(rounds.timer, "NEXT ROUND  (F5 to skip)" if not rounds.match_winner else "MATCH POINT REACHED")
        else:
            hud.set_clock(0, "MATCH OVER  -  F5 for a new match")

        # flag status
        f = rounds.flag
        if f.state == FlagState.CARRIED:
            who = "YOU" if f.carrier is player else f.carrier.display_name.upper()
            hud.set_flag_status(f"FLAG: CARRIED ({who})")
        elif f.state == FlagState.PLANTED:
            hud.set_flag_status(f"FLAG: PLANTED @ {site_short(f.site)}")
        else:
            hud.set_flag_status("FLAG: AT BASE" if f.at_home else "FLAG: DROPPED")
        hud.set_carrier(f.state == FlagState.CARRIED and f.carrier is player)

        # plant / takedown progress: mine, or a teammate's (never the enemy's)
        shown = None
        prog = rounds.progress_for(player)
        if prog:
            shown = (prog, "PLANTING FLAG" if prog[0] == "plant" else "TAKING DOWN FLAG")
        else:
            for b in bots:
                bp = rounds.progress_for(b)
                if bp and b.team == player.team:
                    verb = "PLANTING" if bp[0] == "plant" else "TAKING DOWN"
                    shown = (bp, f"{b.display_name.upper()} {verb}")
                    break
        hud.set_flag_progress(shown[0][1] if shown else None, shown[1] if shown else "")

        # banners
        if phase == Phase.MATCH_END:
            w = rounds.match_winner
            hud.set_banner(f"{team_name(w).upper()} WINS MATCH", hud.team_color(w),
                           f"{rounds.score['attackers']} - {rounds.score['defenders']}   press F5 for a new match")
        elif phase == Phase.ROUND_END:
            w = rounds.round_winner
            hud.set_banner(f"{team_name(w).upper()} WINS ROUND", hud.team_color(w), REASONS.get(rounds.round_reason, ""))
        else:
            hud.set_banner(None)

        # vitals, money, weapons, prompts
        x, y, z = player.body.pos
        v = player.vitals
        hud.set_location(world.callout(x, z))
        hud.set_credits(player.money)
        hud.set_score(rounds.score["attackers"], rounds.score["defenders"])
        hud.set_player_team(player.team)
        hud.set_vitals(v.health, v.armor, v.helmet)
        hud.set_weapon(arsenal.current, arsenal.owned_weapons())
        hud.set_speed(player.horizontal_speed, player.max_speed(),
                      player.speed_multiplier * player.round_speed_multiplier)
        hud.set_spread(arsenal.current.spread(arsenal.stance()) if not arsenal.current.d.is_melee else 0.0)
        banner_up = phase in (Phase.ROUND_END, Phase.MATCH_END)
        hud.set_death(None if (player.alive or banner_up) else float("inf"), self.killer)
        kind = None
        if player.alive and phase == Phase.LIVE:
            if f.state == FlagState.CARRIED and f.carrier is player and rounds.zone_for(player):
                kind = "hold E to plant"
            elif player.team != ATTACKERS and f.state == FlagState.PLANTED \
                    and rounds.distance_to_flag(player) <= CFG.flag.interact_radius:
                kind = "hold E to take the flag down"
        hud.set_prompt(kind.upper() if kind and not prog else "")
        hud.tick()

        if dt > 0:
            self.fps_smooth += (1.0 / dt - self.fps_smooth) * 0.05
        hud.fps.text = f"{self.fps_smooth:.0f} fps" if CFG.window.show_fps else ""
        if hud.debug.visible:
            b, w = player.body, arsenal.current
            hud.debug.text = (f"pos  {x:7.2f} {y:6.2f} {z:7.2f}\n"
                              f"vel  {player.horizontal_speed:5.2f} m/s  vy {b.vel[1]:5.2f}\n"
                              f"grounded {b.grounded}  crouch {player.crouching}\n"
                              f"spread {w.spread(arsenal.stance()):4.2f}  recoil {w.recoil_up:4.1f}/{w.recoil_side:4.1f}\n"
                              f"phase {phase.value}  site plan {director.target_site}")

    def handle_f5(self):
        """F5 is gated: buy phase = respawn at next spawn point; round end = skip
        to next round; match end = new match. Does nothing during LIVE."""
        phase = rounds.phase
        if phase == Phase.BUY_FREEZE:
            self.spawn_index += 1
            player.respawn(player.team, self.spawn_index)
        elif phase == Phase.ROUND_END:
            rounds.skip_round_end()
        elif phase == Phase.MATCH_END:
            rounds.start_match()

    def input(self, key):
        if key == "escape":
            if feature_settings.is_open:
                feature_settings.close(relock=False)
            else:
                mouse.locked = False
        elif key == "f4":
            if feature_settings.is_open:
                feature_settings.close()
            else:
                feature_settings.open()
        elif key == "left mouse down" and not mouse.locked and not buy_menu.is_open:
            mouse.locked = True
        elif key == "f1":
            hud.toggle_help()
        elif key == "f3":
            hud.debug.visible = not hud.debug.visible
        elif key == "f5":
            self.handle_f5()
        elif key == "f10":
            application.quit()


session = Session()

if args.smoke:
    from game.smoke import SmokeTest
    SmokeTest(app, args.smoke, CFG, world=world, player=player, arsenal=arsenal, bots=bots,
              combat=combat, hud=hud, rounds=rounds, session=session, buy_menu=buy_menu,
              economy=economy, director=director)

app.run()
