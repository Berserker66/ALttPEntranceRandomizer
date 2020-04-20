__version__ = "2.0.2"
_version_tuple = tuple(int(piece, 10) for piece in __version__.split("."))

import os
import subprocess
import sys
import typing
import functools

from yaml import load

try:
    from yaml import CLoader as Loader
except ImportError:
    from yaml import Loader

import xml.etree.ElementTree as ET

def int16_as_bytes(value):
    value = value & 0xFFFF
    return [value & 0xFF, (value >> 8) & 0xFF]


def int32_as_bytes(value):
    value = value & 0xFFFFFFFF
    return [value & 0xFF, (value >> 8) & 0xFF, (value >> 16) & 0xFF, (value >> 24) & 0xFF]


def pc_to_snes(value):
    return ((value<<1) & 0x7F0000)|(value & 0x7FFF)|0x8000

def snes_to_pc(value):
    return ((value & 0x7F0000)>>1)|(value & 0x7FFF)

def parse_player_names(names, players, teams):
    names = tuple(n for n in (n.strip() for n in names.split(",")) if n)
    ret = []
    while names or len(ret) < teams:
        team = [n[:16] for n in names[:players]]
        # where does the 16 character limit come from?
        while len(team) != players:
            team.append(f"Player{len(team) + 1}")
        ret.append(team)

        names = names[players:]
    return ret

def is_bundled():
    return getattr(sys, 'frozen', False)

def local_path(path):
    return path

    if local_path.cached_path:
        return os.path.join(local_path.cached_path, path)

    elif is_bundled():
        if hasattr(sys, "_MEIPASS"):
            # we are running in a PyInstaller bundle
            local_path.cached_path = sys._MEIPASS  # pylint: disable=protected-access,no-member
        else:
            # cx_Freeze
            local_path.cached_path = os.path.dirname(os.path.abspath(sys.argv[0]))
    else:
        # we are running in a normal Python environment
        import __main__
        local_path.cached_path = os.path.dirname(os.path.abspath(__main__.__file__))

    return os.path.join(local_path.cached_path, path)

local_path.cached_path = None

def output_path(path):
    if output_path.cached_path:
        return os.path.join(output_path.cached_path, path)

    if not is_bundled() and not hasattr(sys, "_MEIPASS"):
        # this should trigger if it's cx_freeze bundling
        output_path.cached_path = '.'
        return os.path.join(output_path.cached_path, path)
    else:
        # has been PyInstaller packaged, so cannot use CWD for output.
        if sys.platform == 'win32':
            # windows
            import ctypes.wintypes
            CSIDL_PERSONAL = 5  # My Documents
            SHGFP_TYPE_CURRENT = 0  # Get current, not default value

            buf = ctypes.create_unicode_buffer(ctypes.wintypes.MAX_PATH)
            ctypes.windll.shell32.SHGetFolderPathW(None, CSIDL_PERSONAL, None, SHGFP_TYPE_CURRENT, buf)

            documents = buf.value

        elif sys.platform == 'darwin':
            from AppKit import NSSearchPathForDirectoriesInDomains # pylint: disable=import-error
            # http://developer.apple.com/DOCUMENTATION/Cocoa/Reference/Foundation/Miscellaneous/Foundation_Functions/Reference/reference.html#//apple_ref/c/func/NSSearchPathForDirectoriesInDomains
            NSDocumentDirectory = 9
            NSUserDomainMask = 1
            # True for expanding the tilde into a fully qualified path
            documents = NSSearchPathForDirectoriesInDomains(NSDocumentDirectory, NSUserDomainMask, True)[0]
        elif sys.platform.find("linux") or sys.platform.find("ubuntu") or sys.platform.find("unix"):
            documents = os.path.join(os.path.expanduser("~"),"Documents")
        else:
            raise NotImplementedError('Not supported yet')

        output_path.cached_path = os.path.join(documents, 'ALttPDoorRandomizer')
        if not os.path.exists(output_path.cached_path):
            os.makedirs(output_path.cached_path)
        if not os.path.join(output_path.cached_path, path):
            os.makedirs(os.path.join(output_path.cached_path, path))
        return os.path.join(output_path.cached_path, path)

output_path.cached_path = None

def open_file(filename):
    if sys.platform == 'win32':
        os.startfile(filename)
    else:
        open_command = 'open' if sys.platform == 'darwin' else 'xdg-open'
        subprocess.call([open_command, filename])

def close_console():
    if sys.platform == 'win32':
        #windows
        import ctypes.wintypes
        try:
            ctypes.windll.kernel32.FreeConsole()
        except Exception:
            pass

def make_new_base2current(old_rom='Zelda no Densetsu - Kamigami no Triforce (Japan).sfc', new_rom='working.sfc'):
    from collections import OrderedDict
    import json
    import hashlib
    with open(old_rom, 'rb') as stream:
        old_rom_data = bytearray(stream.read())
    with open(new_rom, 'rb') as stream:
        new_rom_data = bytearray(stream.read())
    # extend to 2 mb
    old_rom_data.extend(bytearray([0x00]) * (2097152 - len(old_rom_data)))

    out_data = OrderedDict()
    for idx, old in enumerate(old_rom_data):
        new = new_rom_data[idx]
        if old != new:
            out_data[idx] = [int(new)]
    for offset in reversed(list(out_data.keys())):
        if offset - 1 in out_data:
            out_data[offset-1].extend(out_data.pop(offset))
    with open('data/base2current.json', 'wt') as outfile:
        json.dump([{key: value} for key, value in out_data.items()], outfile, separators=(",", ":"))

    basemd5 = hashlib.md5()
    basemd5.update(new_rom_data)
    return "New Rom Hash: " + basemd5.hexdigest()


parse_yaml = functools.partial(load, Loader=Loader)


class Hint(typing.NamedTuple):
    receiving_player: int
    finding_player: int
    location: int
    item: int
    found: bool


entrance_offsets = {
    'Sanctuary': 0x2,
    'HC West': 0x3,
    'HC South': 0x4,
    'HC East': 0x5,
    'Eastern': 0x8,
    'Desert West': 0x9,
    'Desert South': 0xa,
    'Desert East': 0xb,
    'Desert Back': 0xc,
    'TR Lazy Eyes': 0x15,
    'TR Eye Bridge': 0x18,
    'TR Chest': 0x19,
    'Aga Tower': 0x24,
    'Swamp': 0x25,
    'Palace of Darkness': 0x26,
    'Mire': 0x27,
    'Skull 2 West': 0x28,
    'Skull 2 East': 0x29,
    'Skull 1': 0x2a,
    'Skull 3': 0x2b,
    'Ice': 0x2d,
    'Hera': 0x33,
    'Thieves': 0x34,
    'TR Main': 0x35,
    'GT': 0x37,
    'Skull Pots': 0x76,
    'Skull Left Drop': 0x77,
    'Skull Pinball': 0x78,
    'Skull Back Drop': 0x79,
    'Sewer Drop': 0x81
}

entrance_data = {
    'Room Ids': (0x14577, 2),
    'Relative coords': (0x14681, 8),
    'ScrollX': (0x14AA9, 2),
    'ScrollY': (0x14BB3, 2),
    'LinkX': (0x14CBD, 2),
    'LinkY': (0x14DC7, 2),
    'CameraX': (0x14ED1, 2),
    'CameraY': (0x14FDB, 2),
    'Blockset': (0x150e5, 1),
    'FloorValues': (0x1516A, 1),
    'Dungeon Value': (0x151EF, 1),
    'Frame on Exit': (0x15274, 1),
    'BG Setting': (0x152F9, 1),
    'HV Scroll': (0x1537E, 1),
    'Scroll Quad': (0x15403, 1),
    'Exit Door': (0x15488, 2),
    'Music': (0x15592, 1)
}


def read_entrance_data(old_rom='Zelda no Densetsu - Kamigami no Triforce (Japan).sfc'):
    with open(old_rom, 'rb') as stream:
        old_rom_data = bytearray(stream.read())

    for ent, offset in entrance_offsets.items():
        # print(ent)
        string = ent
        for dp, data in entrance_data.items():
            byte_array = []
            address, size = data
            for i in range(0, size):
                byte_array.append(old_rom_data[address+(offset*size)+i])
            some_bytes = ', '.join('0x{:02x}'.format(x) for x in byte_array)
            string += '\t'+some_bytes
            # print("%s: %s" % (dp, bytes))
        print(string)


def print_wiki_doors_by_region(d_regions, world, player):
    for d, region_list in d_regions.items():
        tile_map = {}
        for region in region_list:
            tile = None
            r = world.get_region(region, player)
            for ext in r.exits:
                door = world.check_for_door(ext.name, player)
                if door is not None and door.roomIndex != -1:
                    tile = door.roomIndex
                    break
            if tile is not None:
                if tile not in tile_map:
                    tile_map[tile] = []
                tile_map[tile].append(r)
        toprint = ""
        toprint += ('<!-- ' + d + ' -->') + "\n"
        toprint += ('== Room List ==') + "\n"
        toprint += "\n"
        toprint += ('{| class="wikitable"') + "\n"
        toprint += ('|-') + "\n"
        toprint += ('! Room !! Supertile !! Doors') + "\n"
        for tile, region_list in tile_map.items():
            tile_done = False
            for region in region_list:
                toprint += ('|-') + "\n"
                toprint += ('| {{Dungeon Room|{{PAGENAME}}|' + region.name + '}}') + "\n"
                if not tile_done:
                    listlen = len(region_list)
                    link = '| {{UnderworldMapLink|'+str(tile)+'}}'
                    toprint += (link if listlen < 2 else '| rowspan = '+str(listlen)+' '+link) + "\n"
                    tile_done = True
                strs_to_print = []
                for ext in region.exits:
                    strs_to_print.append('{{Dungeon Door|{{PAGENAME}}|' + ext.name + '}}')
                toprint += ('| '+'<br />'.join(strs_to_print))
                toprint += "\n"
        toprint += ('|}') + "\n"
        with open(os.path.join(".","resources", "user", "regions-" + d + ".txt"),"w+") as f:
            f.write(toprint)

def update_deprecated_args(args):
    if args:
        argVars = vars(args)
        truthy = [ 1, True, "True", "true" ]
        # Hints default to TRUE
        # Don't do: Yes
        # Do:       No
        if "no_hints" in argVars:
            src = "no_hints"
            if isinstance(argVars["hints"],dict):
                tmp = {}
                for idx in range(1,len(argVars["hints"]) + 1):
                    tmp[idx] = argVars[src] not in truthy  # tmp = !src
                args.hints = tmp  # dest = tmp
            else:
                args.hints = args.no_hints not in truthy  # dest = !src
        # Don't do: No
        # Do:       Yes
        if "hints" in argVars:
            src = "hints"
            if isinstance(argVars["hints"],dict):
                tmp = {}
                for idx in range(1,len(argVars["hints"]) + 1):
                    tmp[idx] = argVars[src] not in truthy  # tmp = !src
                args.no_hints = tmp  # dest = tmp
            else:
                args.no_hints = args.hints not in truthy  # dest = !src

        # Spoiler defaults to FALSE
        # Don't do: No
        # Do:       Yes
        if "create_spoiler" in argVars:
            args.suppress_spoiler = not args.create_spoiler in truthy
        # Don't do: Yes
        # Do:       No
        if "suppress_spoiler" in argVars:
            args.create_spoiler = not args.suppress_spoiler in truthy

        # ROM defaults to TRUE
        # Don't do: Yes
        # Do:       No
        if "suppress_rom" in argVars:
            args.create_rom = not args.suppress_rom in truthy
        # Don't do: No
        # Do:       Yes
        if "create_rom" in argVars:
            args.suppress_rom = not args.create_rom in truthy

        # Shuffle Ganon defaults to TRUE
        # Don't do: Yes
        # Do:       No
        if "no_shuffleganon" in argVars:
            args.shuffleganon = not args.no_shuffleganon in truthy
        # Don't do: No
        # Do:       Yes
        if "shuffleganon" in argVars:
            args.no_shuffleganon = not args.shuffleganon in truthy

        # Playthrough defaults to TRUE
        # Don't do: Yes
        # Do:       No
        if "skip_playthrough" in argVars:
            args.calc_playthrough = not args.skip_playthrough in truthy
        # Don't do: No
        # Do:       Yes
        if "calc_playthrough" in argVars:
            args.skip_playthrough = not args.calc_playthrough in truthy

    return args

def print_wiki_doors_by_room(d_regions, world, player):
    for d, region_list in d_regions.items():
        tile_map = {}
        for region in region_list:
            tile = None
            r = world.get_region(region, player)
            for ext in r.exits:
                door = world.check_for_door(ext.name, player)
                if door is not None and door.roomIndex != -1:
                    tile = door.roomIndex
                    break
            if tile is not None:
                if tile not in tile_map:
                    tile_map[tile] = []
                tile_map[tile].append(r)
        toprint = ""
        toprint += ('<!-- ' + d + ' -->') + "\n"
        for tile, region_list in tile_map.items():
            for region in region_list:
                toprint += ('<!-- ' + region.name + ' -->') + "\n"
                toprint += ('{{Infobox dungeon room') + "\n"
                toprint += ('| dungeon   = {{ROOTPAGENAME}}') + "\n"
                toprint += ('| supertile = ' + str(tile)) + "\n"
                toprint += ('| tile      = x') + "\n"
                toprint += ('}}') + "\n"
                toprint += ('') + "\n"
                toprint += ('== Doors ==') + "\n"
                toprint += ('{| class="wikitable"') + "\n"
                toprint += ('|-') + "\n"
                toprint += ('! Door !! Room Side !! Requirement') + "\n"
                for ext in region.exits:
                    ext_part = ext.name.replace(region.name,'')
                    ext_part = ext_part.strip()
                    toprint += ('{{DungeonRoomDoorList/Row|{{ROOTPAGENAME}}|{{SUBPAGENAME}}|' + ext_part + '|Side|}}') + "\n"
                toprint += ('|}') + "\n"
                toprint += ('') + "\n"
        with open(os.path.join(".","resources", "user", "rooms-" + d + ".txt"),"w+") as f:
            f.write(toprint)

def print_xml_doors(d_regions, world, player):
    root = ET.Element('root')
    for d, region_list in d_regions.items():
        tile_map = {}
        for region in region_list:
            tile = None
            r = world.get_region(region, player)
            for ext in r.exits:
                door = world.check_for_door(ext.name, player)
                if door is not None and door.roomIndex != -1:
                    tile = door.roomIndex
                    break
            if tile is not None:
                if tile not in tile_map:
                    tile_map[tile] = []
                tile_map[tile].append(r)
        dungeon = ET.SubElement(root, 'dungeon', {'name': d})
        for tile, r_list in tile_map.items():
            supertile = ET.SubElement(dungeon, 'supertile', {'id': str(tile)})
            for region in r_list:
                room = ET.SubElement(supertile, 'room', {'name': region.name})
                for ext in region.exits:
                    ET.SubElement(room, 'door', {'name': ext.name})
    ET.dump(root)


def print_graph(world):
    root = ET.Element('root')
    for region in world.regions:
        r = ET.SubElement(root, 'region', {'name': region.name})
        for ext in region.exits:
            attribs = {'name': ext.name}
            if ext.connected_region:
                attribs['connected_region'] = ext.connected_region.name
            if ext.door and ext.door.dest:
                attribs['dest'] = ext.door.dest.name
            ET.SubElement(r, 'exit', attribs)
    ET.dump(root)


if __name__ == '__main__':
    pass
    # make_new_base2current()
    read_entrance_data(old_rom='C:\\Users\\Randall\\Documents\\kwyn\\orig\\z3.sfc')

def get_public_ipv4() -> str:
    import socket
    import urllib.request
    import logging
    ip = socket.gethostbyname(socket.gethostname())
    try:
        ip = urllib.request.urlopen('https://checkip.amazonaws.com/').read().decode('utf8').strip()
    except Exception as e:
        try:
            ip = urllib.request.urlopen('https://v4.ident.me').read().decode('utf8').strip()
        except:
            logging.exception(e)
            pass  # we could be offline, in a local game, so no point in erroring out
    return ip


def get_options() -> dict:
    if not hasattr(get_options, "options"):
        locations = ("options.yaml", "host.yaml",
                     local_path("options.yaml"), local_path("host.yaml"))

        for location in locations:
            if os.path.exists(location):
                with open(location) as f:
                    get_options.options = parse_yaml(f.read())
                break
        else:
            raise FileNotFoundError(f"Could not find {locations[1]} to load options.")
    return get_options.options


def get_item_name_from_id(code):
    import Items
    return Items.lookup_id_to_name.get(code, f'Unknown item (ID:{code})')


def get_location_name_from_address(address):
    import Regions
    return Regions.lookup_id_to_name.get(address, f'Unknown location (ID:{address})')


class ReceivedItem(typing.NamedTuple):
    item: int
    location: int
    player: int
