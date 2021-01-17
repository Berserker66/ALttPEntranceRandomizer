# A Link to the Past Randomizer Plando Guide

## Configuration
1. Plando features have to be enabled first, before they can be used (opt-in).
2. To do so, go to your installation directory (Windows default: C:\ProgramData\BerserkerMultiWorld), 
   then open the host.yaml file therein with a text editor.
3. In it, you're looking for the option key "plando_options", 
   to enable all plando modules you can set the value to "bosses, items, texts, connections"

## Modules

### Bosses

- This module is enabled by default and available to be used on 
  [https://archipelago.gg/generate](https://archipelago.gg/generate)
- Plando versions of boss shuffles can be added like any other boss shuffle option in a yaml and weighted.
- Boss Plando works as a list of instructions from left to right, if any arenas are empty at the end, 
  it defaults to vanilla
- Instructions are separated by a semicolon
- Available Instructions:
    -  Direct Placement:
        - Example: "Eastern Palace-Trinexx"
        - Takes a particular Arena and particular boss, then places that boss into that arena
        - Ganons Tower has 3 placements, "Ganons Tower Top", "Ganons Tower Middle" and "Ganons Tower Bottom"
    - Boss Placement:
        - Example: "Trinexx"
        - Takes a particular boss and places that boss in any remaining slots in which this boss can function.
        - In this example, it would fill Desert Palace, but not Tower of Hera.
    - Boss Shuffle:
        - Example: "simple"
        - Runs a particular boss shuffle mode to finish construction instead of vanilla placement, typically used as a last instruction.
- [Available Bosses](https://github.com/Berserker66/MultiWorld-Utilities/blob/65fa39df95c90c9b66141aee8b16b7e560d00819/Bosses.py#L135)
- [Available Arenas](https://github.com/Berserker66/MultiWorld-Utilities/blob/65fa39df95c90c9b66141aee8b16b7e560d00819/Bosses.py#L186)

#### Examples:
```yaml
boss_shuffle:
  Turtle Rock-Trinexx;basic: 1
  full: 2
  Mothula: 3
  Ganons Tower Bottom-Kholdstare;Trinexx;Kholdstare: 4
```
1. Would be basic boss shuffle but prevent Trinexx from appearing outside of Turtle Rock, 
   as there's only one Trinexx in the pool
2. Regular full boss shuffle. With a 2 in 10 chance to occur.
3. A Mothula Singularity, as Mothula works in any arena.
4. A Trinexx -> Kholdstare Singularity that prevents ice Trinexx in GT


### Items
- This module is disabled by default.
- Has the options from_pool, world, percentage and either item and location or items and locations
- All of these options support subweights
- percentage is the percentage chance for this block to trigger
    - is a number in the range [0, 100], can be omitted entirely for 100%
- from_pool denotes if the item should be taken from the item pool, or be an additional item entirely.
    - can be true or false, defaults to true when omitted
- world is the target world to place the item
    - ignored if only one world is generated
    - can be a number, to target that slot in the multiworld
    - can be a name, to target that player's world
    - can be true, to target any other player's world
    - can be false, to target own world
    - can be null, to target a random world
- Single Placement
    - place a single item at a single location
    - item denotes the Item to place
    - location denotes the Location to place it into
- Multi Placement
    - place multiple items into multiple locations, until either list is exhausted.
    - items denotes the items to use, can be given a number to have multiple of that item
    - locations lists the possible locations those items can be placed in
    - placements are picked randomly, not sorted in any way
- [Available Items](https://github.com/Berserker66/MultiWorld-Utilities/blob/3b5ba161dea223b96e9b1fc890e03469d9c6eb59/Items.py#L26)
- [Available Locations](https://github.com/Berserker66/MultiWorld-Utilities/blob/3b5ba161dea223b96e9b1fc890e03469d9c6eb59/Regions.py#L418)

#### Examples
```yaml
plando_items:
  - item:
      Lamp: 1
      Fire Rod: 1
    location: Link's House
    from_pool: true
    world: true
    percentage: 50
  - items:
      Progressive Sword: 4
      Progressive Bow: 1
      Progressive Bow (Alt): 1
    locations:
      - Desert Palace - Big Chest
      - Eastern Palace - Big Chest
      - Tower of Hera - Big Chest
      - Swamp Palace - Big Chest
      - Thieves' Town - Big Chest
      - Skull Woods - Big Chest
      - Ice Palace - Big Chest
      - Misery Mire - Big Chest
      - Turtle Rock - Big Chest
      - Palace of Darkness - Big Chest
    world: false
```

The first example has a 50% chance to occur, which if it does places either the Lamp or Fire Rod in one's own 
Link's House and removes the picked item from the item pool.

The second example always triggers and places the Swords and Bows into one's own Big Chests

### Texts
- This module is disabled by default.
- Has the options "text", "at" and "percentage"
- percentage is the percentage chance for this text to be placed, can be omitted entirely for 100%
- text is the text to be placed.
    - can be weighted.
    - \n is a newline. 
    - @ is the entered player's name.
    - Warning: Text Mapper does not support full unicode.
    - [Alphabet](https://github.com/Berserker66/MultiWorld-Utilities/blob/65fa39df95c90c9b66141aee8b16b7e560d00819/Text.py#L756)
- at is the location within the game to attach the text to.
    - can be weighted.
    - [List of targets](https://github.com/Berserker66/MultiWorld-Utilities/blob/65fa39df95c90c9b66141aee8b16b7e560d00819/Text.py#L1498)
   
#### Example
```yaml
plando_texts:
  - text: "This is a plando.\nYou've been warned."
    at:
      uncle_leaving_text: 1
      uncle_dying_sewer: 1
    percentage: 50
```
![Uncle Example](https://cdn.discordapp.com/attachments/731214280439103580/794953870903083058/unknown.png)
This has a 50% chance to trigger at all, if it does, 
it throws a coin between "uncle_leaving_text" and "uncle_dying_sewer", then places the text 
"This is a plando.\nYou've been warned." at that location.

### Connections
- This module is disabled by default.
- Has the options "percentage", "entrance", "exit" and "direction".
- All options support subweights
- percentage is the percentage chance for this to be connected, can be omitted entirely for 100%
- Any Door has 4 total directions, as a door can be unlinked like in insanity ER
- entrance is the overworld door
- exit is the underworld exit
- direction can be "both", "entrance" or "exit"
- doors can be found in [this file](https://github.com/Berserker66/MultiWorld-Utilities/blob/main/EntranceShuffle.py)


#### Example
```yaml
plando_connections:
  - entrance: Links House
    exit: Hyrule Castle Exit (West)
    direction: both
  - entrance: Hyrule Castle Entrance (West)
    exit: Links House Exit
    direction: both
```

The first block connects the overworld entrance that normally leads to Link's House
to put you into the HC West Wing instead, exiting from within there will put you at the Overworld exiting Link's House.

Without the second block, you'd still exit from within Link's House to outside Link's House and the left side 
Balcony Entrance would still lead into HC West Wing