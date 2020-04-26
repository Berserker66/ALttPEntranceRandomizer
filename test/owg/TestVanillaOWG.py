from BaseClasses import World
from Dungeons import create_dungeons, get_dungeon_item_pool
from EntranceShuffle import link_entrances
from InvertedRegions import mark_dark_world_regions
from ItemList import difficulties, generate_itempool
from Items import ItemFactory
from Regions import create_regions
from Rules import set_rules
from test.TestBase import TestBase


class TestVanillaOWG(TestBase):
    def setUp(self):
        self.world = World(1, 'vanilla', 'owglitches', 'open', 'random', 'normal', 'normal', 'none', 'on', 'ganon', 'balanced', 'items',
                           True, False, False, False, False, False, None, 'none', False)
        self.world.difficulty_requirements = difficulties['normal']
        create_regions(self.world, 1)
        create_dungeons(self.world, 1)
        link_entrances(self.world, 1)
        generate_itempool(self.world, 1)
        self.world.required_medallions[1] = ['Ether', 'Quake']
        self.world.itempool.extend(get_dungeon_item_pool(self.world))
        self.world.itempool.extend(ItemFactory(['Green Pendant', 'Red Pendant', 'Blue Pendant', 'Beat Agahnim 1', 'Beat Agahnim 2', 'Crystal 1', 'Crystal 2', 'Crystal 3', 'Crystal 4', 'Crystal 5', 'Crystal 6', 'Crystal 7'], 1))
        self.world.get_location('Agahnim 1', 1).item = None
        self.world.get_location('Agahnim 2', 1).item = None
        self.world.precollected_items.clear()
        self.world.itempool.append(ItemFactory('Pegasus Boots', 1))
        mark_dark_world_regions(self.world)
        set_rules(self.world, 1)