from __future__ import annotations

import typing


def tuplize_version(version: str) -> typing.Tuple[int, ...]:
    return Version(*(int(piece, 10) for piece in version.split(".")))


class Version(typing.NamedTuple):
    major: int
    minor: int
    micro: int


__version__ = "4.1.2"
_version_tuple = tuplize_version(__version__)

import os
import subprocess
import sys
import pickle
import io
import builtins

import functools

from yaml import load, dump, safe_load

try:
    from yaml import CLoader as Loader
except ImportError:
    from yaml import Loader

import xml.etree.ElementTree as ET
from collections import defaultdict

def int16_as_bytes(value):
    value = value & 0xFFFF
    return [value & 0xFF, (value >> 8) & 0xFF]


def int32_as_bytes(value):
    value = value & 0xFFFFFFFF
    return [value & 0xFF, (value >> 8) & 0xFF, (value >> 16) & 0xFF, (value >> 24) & 0xFF]


def pc_to_snes(value):
    return ((value << 1) & 0x7F0000) | (value & 0x7FFF) | 0x8000


def snes_to_pc(value):
    return ((value & 0x7F0000) >> 1) | (value & 0x7FFF)


def parse_player_names(names, players, teams):
    names = tuple(n for n in (n.strip() for n in names.split(",")) if n)
    if len(names) != len(set(names)):
        import collections
        name_counter = collections.Counter(names)
        raise ValueError(f"Duplicate Player names is not supported, "
                         f'found multiple "{name_counter.most_common(1)[0][0]}".')
    ret = []
    while names or len(ret) < teams:
        team = [n[:16] for n in names[:players]]
        # 16 bytes in rom per player, which will map to more in unicode, but those characters later get filtered
        while len(team) != players:
            team.append(f"Player{len(team) + 1}")
        ret.append(team)

        names = names[players:]
    return ret


def is_bundled() -> bool:
    return getattr(sys, 'frozen', False)


def local_path(*path):
    if local_path.cached_path:
        return os.path.join(local_path.cached_path, *path)

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

    return os.path.join(local_path.cached_path, *path)


local_path.cached_path = None


def output_path(*path):
    if output_path.cached_path:
        return os.path.join(output_path.cached_path, *path)
    output_path.cached_path = local_path(get_options()["general_options"]["output_path"])
    path = os.path.join(output_path.cached_path, *path)
    os.makedirs(os.path.dirname(path), exist_ok=True)
    return path


output_path.cached_path = None


def open_file(filename):
    if sys.platform == 'win32':
        os.startfile(filename)
    else:
        open_command = 'open' if sys.platform == 'darwin' else 'xdg-open'
        subprocess.call([open_command, filename])


def close_console():
    if sys.platform == 'win32':
        # windows
        import ctypes.wintypes
        try:
            ctypes.windll.kernel32.FreeConsole()
        except Exception:
            pass


parse_yaml = safe_load
unsafe_parse_yaml = functools.partial(load, Loader=Loader)


class Hint(typing.NamedTuple):
    receiving_player: int
    finding_player: int
    location: int
    item: int
    found: bool
    entrance: str = ""

    def re_check(self, ctx, team) -> Hint:
        if self.found:
            return self
        found = self.location in ctx.location_checks[team, self.finding_player]
        if found:
            return Hint(self.receiving_player, self.finding_player, self.location, self.item, found, self.entrance)
        return self

    def as_legacy(self) -> tuple:
        return self.receiving_player, self.finding_player, self.location, self.item, self.found

    def __hash__(self):
        return hash((self.receiving_player, self.finding_player, self.location, self.item, self.entrance))
    
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


def read_layout_data(old_rom='Zelda no Densetsu - Kamigami no Triforce (Japan).sfc'):
    with open(old_rom, 'rb') as stream:
        old_rom_data = bytearray(stream.read())

    string = ''
    for room in range(0, 0xff+1):
        # print(ent)
        pointer_start = 0xf8000+room*3
        highbyte = old_rom_data[pointer_start+2]
        midbyte = old_rom_data[pointer_start+1]
        midbyte = midbyte - 0x80 if highbyte % 2 == 0 else midbyte
        pointer = highbyte // 2 * 0x10000
        pointer += midbyte * 0x100
        pointer += old_rom_data[pointer_start]
        layout_byte = old_rom_data[pointer+1]
        layout = (layout_byte & 0x1c) >> 2
        string += hex(room) + ':' + str(layout) + '\n'
    print(string)


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


def room_palette_data(old_rom):
    with open(old_rom, 'rb') as stream:
        old_rom_data = bytearray(stream.read())

    offset = defaultdict(list)
    for i in range(0, 256):
        pointer_offset = 0x0271e2+i*2
        header_offset = old_rom_data[pointer_offset + 1] << 8
        header_offset += old_rom_data[pointer_offset]
        header_offset -= 0x8000
        header_offset += 0x020000
        offset[header_offset].append(i)
        # print(f'{hex(i)}: {hex(old_rom_data[header_offset+1])}')
    for header_offset, rooms in offset.items():
        print(f'{hex(header_offset)}: {[hex(x) for x in rooms]}')



# Palette notes:
# HC: 0
# Sewer/Dungeon: 1
# AT: 0xc near boss, 0x0 (other) 26 (f4, f1)
# Sanc: 0x1d
# Hera: 0x6
# Desert: 0x4 (boss and near boss), 0x9 (desert tiles 1 + desert main)
# Eastern: 0xb
# Pod: 0xf, x10 (boss)
# Swamp: 0x8 (boss), 0xa (other)
# Skull: 0xe (boss), 0xd (other)
# TT: 0x17, 0x23 (attic)
# Ice: 0x13, 0x14 (boss)
# Mire: 0x11 (other) , 0x12 (boss/preroom)
# TR: 0x18, 0x19 (boss+pre)
# GT: 0x28 (entrance + B1), 0x1a (other) 0x24 (Gauntlet - Lanmo) 0x25 (conveyor-torch-wizzrode moldorm pit f5?)
# Aga2: 0x1b, 0x1b (Pre aga2)
# Caves: 0x7, 0x20
# Uncle: 0x1
# Ganon: 0x21
# Houses: 0x2


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

        # Multiworld progression balancing defaults to TRUE
        # Don't do: No
        # Do:       Yes
        if "progression_balancing" in argVars:
            args.skip_progression_balancing = not args.progression_balancing in truthy
        # Don't do: Yes
        # Do:       No
        if "skip_progression_balancing" in argVars:
            args.progression_balancing = not args.skip_progression_balancing in truthy

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


def extract_data_from_us_rom(rom):
    with open(rom, 'rb') as stream:
        rom_data = bytearray(stream.read())

    rooms = [0x9a, 0x69, 0x78, 0x79, 0x7a, 0x88, 0x8a, 0xad]
    for room in rooms:
        b2idx = room*2
        b3idx = room*3
        headerptr = 0x110000 + b2idx  # zscream specific
        headerloc = rom_data[headerptr] + rom_data[headerptr+1]*0x100 + 0x108000  # zscream specific
        header, objectdata, spritedata, secretdata = [], [], [], []
        for i in range(0, 14):
            header.append(rom_data[headerloc+i])
        objectptr = 0xF8000 + b3idx
        objectloc = rom_data[objectptr] + rom_data[objectptr+1]*0x100 + rom_data[objectptr+2]*0x10000
        objectloc -= 0x100000
        stop, idx = False,  0
        ffcnt = 0
        mode = 0
        while ffcnt < 2:
            b1 = rom_data[objectloc+idx]
            b2 = rom_data[objectloc+idx+1]
            b3 = rom_data[objectloc+idx+2]
            objectdata.append(b1)
            objectdata.append(b2)
            if b1 == 0xff and b2 == 0xff:
                ffcnt += 1
                mode = 0
            if b1 == 0xf0 and b2 == 0xff:
                mode = 1
            if not mode and ffcnt < 2:
                objectdata.append(b3)
                idx += 3
            else:
                idx += 2
        spriteptr = 0x4d62e + b2idx
        spriteloc = rom_data[spriteptr] + rom_data[spriteptr+1]*0x100 + 0x40000
        done, idx = False, 0
        while not done:
            b1 = rom_data[spriteloc+idx]
            spritedata.append(b1)
            if b1 == 0xff:
                done = True
            idx += 1
        secretptr = 0xdb69 + b2idx
        secretloc = rom_data[secretptr] + rom_data[secretptr+1]*0x100
        done, idx = False, 0
        while not done:
            b1 = rom_data[secretloc+idx]
            b2 = rom_data[secretloc+idx+1]
            b3 = rom_data[secretloc+idx+2]
            secretdata.append(b1)
            secretdata.append(b2)
            if b1 == 0xff and b2 == 0xff:
                done = True
            else:
                secretdata.append(b3)
            idx += 3

        print(f'Room {room:02x}')
        print(f'db {",".join([f"${x:02x}" for x in header])}')
        print(f'Obj Length: {len(objectdata)}')
        print_data_block(objectdata)
        print('Sprites')
        print_data_block(spritedata)
        print('Secrets')
        print_data_block(secretdata)

    blockdata, torchdata = [], []
    blockloc = 0x271de
    for i in range(0, 128):
        idx = i*4
        b1 = rom_data[blockloc+idx]
        b2 = rom_data[blockloc+idx+1]
        room_idx = b1 + b2*0x100
        if room_idx in rooms:
            blockdata.append(b1)
            blockdata.append(b2)
            blockdata.append(rom_data[blockloc+idx+2])
            blockdata.append(rom_data[blockloc+idx+3])
    torchloc = 0x2736A
    nomatch = False
    append = False
    for i in range(0, 192):
        idx = i*2
        b1 = rom_data[torchloc+idx]
        b2 = rom_data[torchloc+idx+1]
        if nomatch:
            if b1 == 0xff and b2 == 0xff:
                nomatch = False
        elif not append:
            room_idx = b1 + b2*0x100
            if room_idx in rooms:
                append = True
            else:
                nomatch = True
        if append:
            torchdata.append(b1)
            torchdata.append(b2)
            if b1 == 0xff and b2 == 0xff:
                append = False
    print('Blocks')
    print_data_block(blockdata)
    print('Torches')
    print_data_block(torchdata)
    print()


def print_data_block(block):
    for i in range(0, len(block)//16 + 1):
        slice = block[i*16:i*16+16]
        print(f'db {",".join([f"${x:02x}" for x in slice])}')


def extract_data_from_jp_rom(rom):
    with open(rom, 'rb') as stream:
        rom_data = bytearray(stream.read())

    # rooms = [0x7b, 0x7c, 0x7d, 0x8b, 0x8c, 0x8d, 0x9b, 0x9c, 0x9d]
    rooms = [0x1a, 0x2a, 0xd1]
    for room in rooms:
        b2idx = room*2
        b3idx = room*3
        headerptr = 0x271e2 + b2idx
        headerloc = rom_data[headerptr] + rom_data[headerptr+1]*0x100 + 0x18000
        header, objectdata, spritedata, secretdata = [], [], [], []
        for i in range(0, 14):
            header.append(rom_data[headerloc+i])
        objectptr = 0xF8000 + b3idx
        objectloc = rom_data[objectptr] + rom_data[objectptr+1]*0x100 + rom_data[objectptr+2]*0x10000
        objectloc -= 0x100000
        stop, idx = False,  0
        ffcnt = 0
        mode = 0
        while ffcnt < 2:
            b1 = rom_data[objectloc+idx]
            b2 = rom_data[objectloc+idx+1]
            b3 = rom_data[objectloc+idx+2]
            objectdata.append(b1)
            objectdata.append(b2)
            if b1 == 0xff and b2 == 0xff:
                ffcnt += 1
                mode = 0
            if b1 == 0xf0 and b2 == 0xff:
                mode = 1
            if not mode and ffcnt < 2:
                objectdata.append(b3)
                idx += 3
            else:
                idx += 2
        spriteptr = 0x4d62e + b2idx
        spriteloc = rom_data[spriteptr] + rom_data[spriteptr+1]*0x100 + 0x40000
        secretptr = 0xdb67 + b2idx
        secretloc = rom_data[secretptr] + rom_data[secretptr+1]*0x100
        done, idx = False, 0
        while not done:
            b1 = rom_data[spriteloc+idx]
            spritedata.append(b1)
            if b1 == 0xff:
                done = True
            idx += 1
        done, idx = False, 0
        while not done:
            b1 = rom_data[secretloc+idx]
            b2 = rom_data[secretloc+idx+1]
            b3 = rom_data[secretloc+idx+2]
            secretdata.append(b1)
            secretdata.append(b2)
            if b1 == 0xff and b2 == 0xff:
                done = True
            else:
                secretdata.append(b3)
            idx += 3
        print(f'Room {room:02x}')
        print(f'HeaderPtr {headerptr:06x}')
        print(f'HeaderLoc {headerloc:06x}')
        print(f'db {",".join([f"${x:02x}" for x in header])}')
        print(f'Obj Length: {len(objectdata)}')
        print(f'ObjectPtr {objectptr:06x}')
        print(f'ObjectLoc {objectloc:06x}')
        for i in range(0, len(objectdata)//16 + 1):
            slice = objectdata[i*16:i*16+16]
            print(f'db {",".join([f"${x:02x}" for x in slice])}')
        print(f'SpritePtr {spriteptr:06x}')
        print(f'SpriteLoc {spriteloc:06x}')
        print_data_block(spritedata)
        print(f'SecretPtr {secretptr:06x}')
        print(f'SecretLoc {secretloc:06x}')
        print_data_block(secretdata)
        print()


if __name__ == '__main__':
    # make_new_base2current()
    # read_entrance_data(old_rom=sys.argv[1])
    # room_palette_data(old_rom=sys.argv[1])
    # extract_data_from_us_rom(sys.argv[1])
    extract_data_from_jp_rom(sys.argv[1])



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


def get_public_ipv6() -> str:
    import socket
    import urllib.request
    import logging
    ip = socket.gethostbyname(socket.gethostname())
    try:
        ip = urllib.request.urlopen('https://v6.ident.me').read().decode('utf8').strip()
    except Exception as e:
        logging.exception(e)
        pass  # we could be offline, in a local game, or ipv6 may not be available
    return ip


def get_default_options() -> dict:
    if not hasattr(get_default_options, "options"):
        # Refer to host.yaml for comments as to what all these options mean.
        options = {
            "general_options": {
                "rom_file": "Zelda no Densetsu - Kamigami no Triforce (Japan).sfc",
                "qusb2snes": "QUsb2Snes\\QUsb2Snes.exe",
                "rom_start": True,
                "output_path": "output",
            },
            "server_options": {
                "host": None,
                "port": 38281,
                "password": None,
                "multidata": None,
                "savefile": None,
                "disable_save": False,
                "loglevel": "info",
                "server_password": None,
                "disable_item_cheat": False,
                "location_check_points": 1,
                "hint_cost": 1000,
                "forfeit_mode": "goal",
                "remaining_mode": "goal",
                "auto_shutdown": 0,
                "compatibility": 2,
            },
            "multi_mystery_options": {
                "teams": 1,
                "enemizer_path": "EnemizerCLI/EnemizerCLI.Core.exe",
                "player_files_path": "Players",
                "players": 0,
                "weights_file_path": "weights.yaml",
                "meta_file_path": "meta.yaml",
                "pre_roll": False,
                "player_name": "",
                "create_spoiler": 1,
                "zip_roms": 0,
                "zip_diffs": 2,
                "zip_spoiler": 0,
                "zip_multidata": 1,
                "zip_format": 1,
                "glitch_triforce_room": 1,
                "race": 0,
                "cpu_threads": 0,
                "max_attempts": 0,
                "take_first_working": False,
                "keep_all_seeds": False,
                "log_output_path": "Output Logs",
                "log_level": None,
                "plando_options": "bosses",
            }
        }

        get_default_options.options = options
    return get_default_options.options

def update_options(src: dict, dest: dict, filename: str, keys: list) -> dict:
    import logging
    for key, value in src.items():
        new_keys = keys.copy()
        new_keys.append(key)
        if key not in dest:
            dest[key] = value
            if filename.endswith("options.yaml"):
                logging.info(f"Warning: {filename} is missing {'.'.join(new_keys)}")
        elif isinstance(value, dict):
            if not isinstance(dest.get(key, None), dict):
                if filename.endswith("options.yaml"):
                    logging.info(f"Warning: {filename} has {'.'.join(new_keys)}, but it is not a dictionary. overwriting.")
                dest[key] = value
            else:
                dest[key] = update_options(value, dest[key], filename, new_keys)
    return dest


def get_options() -> dict:
    if not hasattr(get_options, "options"):
        locations = ("options.yaml", "host.yaml",
                     local_path("options.yaml"), local_path("host.yaml"))

        for location in locations:
            if os.path.exists(location):
                with open(location) as f:
                    options = parse_yaml(f.read())

                get_options.options = update_options(get_default_options(), options, location, list())
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


def persistent_store(category, key, value):
    path = local_path("_persistent_storage.yaml")
    storage: dict = persistent_load()
    category = storage.setdefault(category, {})
    category[key] = value
    with open(path, "wt") as f:
        f.write(dump(storage))


def persistent_load() -> typing.Dict[dict]:
    storage = getattr(persistent_load, "storage", None)
    if storage:
        return storage
    path = local_path("_persistent_storage.yaml")
    storage: dict = {}
    if os.path.exists(path):
        try:
            with open(path, "r") as f:
                storage = unsafe_parse_yaml(f.read())
        except Exception as e:
            import logging
            logging.debug(f"Could not read store: {e}")
    if storage is None:
        storage = {}
    persistent_load.storage = storage
    return storage


def get_adjuster_settings(romfile: str) -> typing.Tuple[str, bool]:
    if hasattr(get_adjuster_settings, "adjuster_settings"):
        adjuster_settings = getattr(get_adjuster_settings, "adjuster_settings")
    else:
        adjuster_settings = persistent_load().get("adjuster", {}).get("last_settings_3", {})

    if adjuster_settings:
        import pprint
        import Patch
        adjuster_settings.rom = romfile
        adjuster_settings.baserom = Patch.get_base_rom_path()
        adjuster_settings.world = None
        whitelist = {"disablemusic", "fastmenu", "heartbeep", "heartcolor", "ow_palettes", "quickswap",
                     "uw_palettes", "sprite"}
        printed_options = {name: value for name, value in vars(adjuster_settings).items() if name in whitelist}
        if hasattr(adjuster_settings, "sprite_pool"):
            sprite_pool = {}
            for sprite in getattr(adjuster_settings, "sprite_pool"):
                if sprite in sprite_pool:
                    sprite_pool[sprite] += 1
                else:
                    sprite_pool[sprite] = 1
            if sprite_pool:
                printed_options["sprite_pool"] = sprite_pool


        if hasattr(get_adjuster_settings, "adjust_wanted"):
            adjust_wanted = getattr(get_adjuster_settings, "adjust_wanted")
        elif persistent_load().get("adjuster", {}).get("never_adjust", False):  # never adjust, per user request
            return romfile, False
        else:
            adjust_wanted = input(f"Last used adjuster settings were found. Would you like to apply these? \n"
                                  f"{pprint.pformat(printed_options)}\n"
                                  f"Enter yes, no or never: ")
        if adjust_wanted and adjust_wanted.startswith("y"):
            if hasattr(adjuster_settings, "sprite_pool"):
                from Adjuster import AdjusterWorld
                adjuster_settings.world = AdjusterWorld(getattr(adjuster_settings, "sprite_pool"))

            adjusted = True
            import Adjuster
            _, romfile = Adjuster.adjust(adjuster_settings)

            if hasattr(adjuster_settings, "world"):
                delattr(adjuster_settings, "world")
        elif adjust_wanted and "never" in adjust_wanted:
            persistent_store("adjuster", "never_adjust", True)
            return romfile, False
        else:
            adjusted = False
            import logging
            if not hasattr(get_adjuster_settings, "adjust_wanted"):
                logging.info(f"Skipping post-patch adjustment")
        get_adjuster_settings.adjuster_settings = adjuster_settings
        get_adjuster_settings.adjust_wanted = adjust_wanted
        return romfile, adjusted
    return romfile, False


class ReceivedItem(typing.NamedTuple):
    item: int
    location: int
    player: int


def get_unique_identifier():
    uuid = persistent_load().get("client", {}).get("uuid", None)
    if uuid:
        return uuid

    import uuid
    uuid = uuid.getnode()
    persistent_store("client", "uuid", uuid)
    return uuid


safe_builtins = {
    'set',
    'frozenset',
}


class RestrictedUnpickler(pickle.Unpickler):
    def find_class(self, module, name):
        if module == "builtins" and name in safe_builtins:
            return getattr(builtins, name)
        # Forbid everything else.
        raise pickle.UnpicklingError("global '%s.%s' is forbidden" %
                                     (module, name))


def restricted_loads(s):
    """Helper function analogous to pickle.loads()."""
    return RestrictedUnpickler(io.BytesIO(s)).load()
