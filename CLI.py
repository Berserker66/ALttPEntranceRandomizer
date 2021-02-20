import argparse
import copy
import json
import os
import textwrap
import shlex
import sys

import source.classes.constants as CONST
from source.classes.BabelFish import BabelFish

from Utils import update_deprecated_args


class ArgumentDefaultsHelpFormatter(argparse.RawTextHelpFormatter):

    def _get_help_string(self, action):
        return textwrap.dedent(action.help)

def parse_cli(argv, no_defaults=False):
    def defval(value):
        return value if not no_defaults else None

    # get settings
    settings = parse_settings()

    lang = "en"
    fish = BabelFish(lang=lang)

    # we need to know how many players we have first
    parser = argparse.ArgumentParser(add_help=False)
    parser.add_argument('--multi', default=defval(settings["multi"]), type=lambda value: min(max(int(value), 1), 255))
    multiargs, _ = parser.parse_known_args(argv)

    parser = argparse.ArgumentParser(formatter_class=ArgumentDefaultsHelpFormatter)

    # get args
    args = []
    with open(os.path.join("resources","app","cli","args.json")) as argsFile:
      args = json.load(argsFile)
      for arg in args:
        argdata = args[arg]
        argname = "--" + arg
        argatts = {}
        argatts["help"] = "(default: %(default)s)"
        if "action" in argdata:
          argatts["action"] = argdata["action"]
        if "choices" in argdata:
          argatts["choices"] = argdata["choices"]
          argatts["const"] = argdata["choices"][0]
          argatts["default"] = argdata["choices"][0]
          argatts["nargs"] = "?"
        if arg in settings:
          default = settings[arg]
          if "type" in argdata and argdata["type"] == "bool":
              default = settings[arg] != 0
          argatts["default"] = defval(default)
        arghelp = fish.translate("cli","help",arg)
        if "help" in argdata and argdata["help"] == "suppress":
          argatts["help"] = argparse.SUPPRESS
        elif not isinstance(arghelp,str):
          argatts["help"] = '\n'.join(arghelp).replace("\\'","'")
        else:
          argatts["help"] = arghelp + " " + argatts["help"]
        parser.add_argument(argname,**argatts)

    parser.add_argument('--seed', default=defval(int(settings["seed"]) if settings["seed"] != "" and settings["seed"] is not None else None), help="\n".join(fish.translate("cli","help","seed")), type=int)
    parser.add_argument('--count', default=defval(int(settings["count"]) if settings["count"] != "" and settings["count"] is not None else 1), help="\n".join(fish.translate("cli","help","count")), type=int)
    parser.add_argument('--customitemarray', default={}, help=argparse.SUPPRESS)

    # included for backwards compatibility
    parser.add_argument('--beemizer', default=defval(settings["beemizer"]), type=lambda value: min(max(int(value), 0), 4))
    parser.add_argument('--multi', default=defval(settings["multi"]), type=lambda value: min(max(int(value), 1), 255))
    parser.add_argument('--teams', default=defval(1), type=lambda value: max(int(value), 1))

    if multiargs.multi:
        for player in range(1, multiargs.multi + 1):
            parser.add_argument(f'--p{player}', default=defval(''), help=argparse.SUPPRESS)

    ret = parser.parse_args(argv)

    # shuffle medallions

    ret.required_medallions = ("random", "random")
    # cannot be set through CLI currently
    ret.plando_items = []
    ret.plando_texts = {}
    ret.plando_connections = []
    ret.er_seeds = {}
    ret.dr_seeds = {}

    if ret.timer == "none":
        ret.timer = False
    if ret.dungeon_counters == 'on':
        ret.dungeon_counters = True
    elif ret.dungeon_counters == 'off':
        ret.dungeon_counters = False

    if ret.keysanity:
        ret.mapshuffle = ret.compassshuffle = ret.keyshuffle = ret.bigkeyshuffle = True
    elif ret.keyshuffle == "on":
        ret.keyshuffle = True
    elif ret.keyshuffle == "off":
        ret.keyshuffle = False

    if multiargs.multi:
        defaults = copy.deepcopy(ret)
        for player in range(1, multiargs.multi + 1):
            playerargs = parse_cli(shlex.split(getattr(ret, f"p{player}")), True)

            for name in ['logic', 'mode', 'swords', 'goal', 'difficulty', 'item_functionality',
                         'shuffle', 'door_shuffle', 'intensity', 'crystals_ganon', 'crystals_gt', 'open_pyramid',
                         'countdown_start_time', 'red_clock_time', 'blue_clock_time', 'green_clock_time',
                         'mapshuffle', 'compassshuffle', 'keyshuffle', 'bigkeyshuffle', 'startinventory',
                         'local_items', 'non_local_items', 'retro', 'accessibility', 'hints', 'beemizer', 'experimental', 'debug', 'dungeon_counters',
                         'shufflebosses', 'enemy_shuffle', 'enemy_health', 'enemy_damage', 'shufflepots',
                         'ow_palettes', 'uw_palettes', 'sprite', 'disablemusic', 'quickswap', 'fastmenu', 'heartcolor',
                         'heartbeep',  "skip_progression_balancing", "triforce_pieces_available", "triforce_pieces_required",
                         'remote_items', 'timer', 'progressive', "glitch_boots", 'killable_thieves', 'shuffle_prizes',
                         'tile_shuffle', 'bush_shuffle', 'shop_shuffle', 'sprite_pool', 'dark_room_logic', 'restrict_dungeon_item_on_boss',
                         'hud_palettes', 'sword_palettes', 'shield_palettes', 'link_palettes', 'keydropshuffle', 'mixed_travel',
                         'standardize_palettes', 'plando_items', 'plando_texts', 'plando_connections', 'required_medallions',
                         "shop_shuffle_slots", "reduceflashing", "er_seeds", "dr_seeds"]:
                value = getattr(defaults, name) if getattr(playerargs, name) is None else getattr(playerargs, name)
                if player == 1:
                    setattr(ret, name, {1: value})
                else:
                    getattr(ret, name)[player] = value

    return ret


def parse_settings():
    # set default settings
    settings = {
        "lang": "en",
        "retro": False,
        "mode": "open",
        "logic": "noglitches",
        "goal": "ganon",
        "crystals_gt": "7",
        "crystals_ganon": "7",
        "swords": "random",
        "triforce_pieces_available": 30,
        "triforce_pieces_required": 20,
        "difficulty": "normal",
        "item_functionality": "normal",
        "timer": "none",
        "progressive": "on",
        "accessibility": "items",
        "algorithm": "balanced",
        "glitch_boots": True,
        "skip_progression_balancing": False,

        # Shuffle Ganon defaults to TRUE
        "open_pyramid": "auto",
        "shuffleganon": True,
        "shuffle": "vanilla",

        "countdown_start_time": 10,
        "red_clock_time": -2,
        "blue_clock_time": 2,
        "green_clock_time": 4,

        "shufflepots": False,
        "enemy_shuffle": False,
        "killable_thieves": False,
        "tile_shuffle": False,
        "bush_shuffle": False,
        "shufflebosses": "none",
        "enemy_damage": "default",
        "enemy_health": "default",
        "enemizercli": os.path.join(".", "EnemizerCLI", "EnemizerCLI.Core"),

        "keydropshuffle": False,
        "mapshuffle": False,
        "compassshuffle": False,
        "keyshuffle": False,
        "bigkeyshuffle": False,
        "keysanity": False,
        "door_shuffle": "basic",
        "intensity": 2,
        "experimental": False,
        "debug": False,
        "dungeon_counters": "default",
        "shop_shuffle": "",
        "sprite_pool": [],
        "dark_room_logic": "lamp",
        "restrict_dungeon_item_on_boss": False,
        "mixed_travel": "prevent",
        "standardize_palettes": "standardize",

        "multi": 1,
        "names": "",

        # Hints default to TRUE
        "hints": True,
        "no_hints": False,
        "disablemusic": False,
        "quickswap": False,
        "heartcolor": "red",
        "heartbeep": "normal",
        "sprite": os.path.join(".","data","sprites","alttpr","001.link.1.zspr"),
        "fastmenu": "normal",
        "ow_palettes": "default",
        "uw_palettes": "default",
        "hud_palettes": "default",
        "shield_palettes": "default",
        "sword_palettes": "default",
        "link_palettes": "default",

        # Spoiler     defaults to FALSE
        # Playthrough defaults to TRUE
        # ROM         defaults to TRUE
        "create_spoiler": False,
        "calc_playthrough": True,
        "create_rom": True,
        "usestartinventory": False,
        "custom": False,
        "rom": os.path.join(".", "Zelda no Densetsu - Kamigami no Triforce (Japan).sfc"),

        "seed": "",
        "count": 1,
        "startinventory": "",
        "beemizer": 0,
        "remote_items": False,
        "race": False,
        "customitemarray": [
            0, 0, 1, 1, 1,    # bow, silverbow, boomerang, magicboomerang, hookshot,
            1, 1, 1, 1, 1,    # mushroom, magicpowder, firerod, icerod, bombos,

            1, 1, 1, 1, 1,    # ether, quake, lamp, hammer, shovel,
            1, 1, 1, 4, 1,    # flute, bugnet, book, bottle, somaria,

            1, 1, 1, 1, 0,    # byrna, cape, mirror, boots, powerglove,
            0, 2, 1, 1, 24,   # titansmitt, progglove, flippers, pearl, heartpiece,

            10, 1, 0, 0, 0,   # fullheart, sancheart, sword1, sword2, sword3,
            0, 4, 0, 0, 0,    # sword4, progsword, shield1, shield2, shield3,

            3, 0, 0, 2, 1,    # progshield, bluemail, redmail, progmail, halfmagic,
            0, 0, 0, 0, 0,    # quartermagic, bombupgrade5, bombupgrade10, arrowupgrade5, arrowupgrade10,

            1, 12, 0, 16, 2,  # arrow1, arrow10, bomb1, bomb3, rupee1,
            4, 28, 7, 1, 5,   # rupee5, rupee20, rupee50, rupee100, rupee300,

            0, 0, 0, 0, 2,    # rupoor, blueclock, greenclock, redclock, progbow,
            1, 0, 10, 0       # bomb10, triforce, rupoorcost, universalkey
        ],
        "randomSprite": False,
        "outputpath": os.path.join("."),
        "saveonexit": "ask",
        "outputname": "",
        "startinventoryarray": {},
    }

    if sys.platform.lower().find("windows"):
        settings["enemizercli"] += ".exe"

    # read saved settings file if it exists and set these
    settings_path = os.path.join(".", "resources", "user", "settings.json")
    if os.path.exists(settings_path):
        with(open(settings_path)) as json_file:
            data = json.load(json_file)
            for k, v in data.items():
                settings[k] = v
    return settings

# Priority fallback is:
#  1: CLI
#  2: Settings file
#  3: Canned defaults
def get_args_priority(settings_args, gui_args, cli_args):
    args = {}
    args["settings"] = parse_settings() if settings_args is None else settings_args
    args["gui"] = gui_args
    args["cli"] = cli_args

    args["load"] = args["settings"]
    if args["gui"] is not None:
        for k in args["gui"]:
            if k not in args["load"] or args["load"][k] != args["gui"]:
                args["load"][k] = args["gui"][k]

    if args["cli"] is None:
        args["cli"] = {}
        cli = vars(parse_cli(None))
        for k, v in cli.items():
            if isinstance(v, dict) and 1 in v:
                args["cli"][k] = v[1]
            else:
                args["cli"][k] = v
        args["cli"] = argparse.Namespace(**args["cli"])

    cli = vars(args["cli"])
    for k in vars(args["cli"]):
        load_doesnt_have_key = k not in args["load"]
        cli_val = cli[k]
        if isinstance(cli_val,dict) and 1 in cli_val:
            cli_val = cli_val[1]
        different_val = (k in args["load"] and k in cli) and (str(args["load"][k]) != str(cli_val))
        cli_has_empty_dict = k in cli and isinstance(cli_val, dict) and len(cli_val) == 0
        if load_doesnt_have_key or different_val:
            if not cli_has_empty_dict:
                args["load"][k] = cli_val

    newArgs = {}
    for key in [ "settings", "gui", "cli", "load" ]:
        if args[key]:
            if isinstance(args[key],dict):
                newArgs[key] = argparse.Namespace(**args[key])
            else:
                newArgs[key] = args[key]

        else:
            newArgs[key] = args[key]
        newArgs[key] = update_deprecated_args(newArgs[key])

    args = newArgs

    return args
