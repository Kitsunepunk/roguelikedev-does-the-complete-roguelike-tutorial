from random import randint
import libtcodpy as libtcod

from components.ai import BasicMonster
from components.fighter import Fighter
from components.item import Item
from components.stairs import Stairs
from entity import Entity
from game_messages import Message
from item_functions import cast_confuse, cast_fireball, cast_lightning, heal
from map_objects.rectangle import Rect
from map_objects.tile import Tile
from random_utils import from_dungeon_level, random_choice_from_dict
from render_functions import RenderOrder
from rng_functions import dice_roll


class GameMap:
    def __init__(self, width, height, dungeon_level=1):
        self.width = width
        self.height = height
        self.tiles = self.initialize_tiles()

        self.dungeon_level = dungeon_level

    def initialize_tiles(self):
        tiles = [[Tile(True) for y in range(self.height)]
                 for x in range(self.width)]

        return tiles

    def make_map(self, max_rooms, room_min_size, room_max_size, map_width,
                 map_height, player, entities, sprites, colors):

        rooms = []
        num_rooms = 0

        last_room_center_x = None
        last_room_center_y = None

        for r in range(max_rooms):

            # random width and height
            w = randint(room_min_size, room_max_size)
            h = randint(room_min_size, room_max_size)

            # random position without going out of the boundaries of the map
            x = randint(0, map_width - w - 1)
            y = randint(0, map_height - h - 1)

            # "Rect" class makes rectangles easier to work with
            new_room = Rect(x, y, w, h)

            # run through the other rooms and see if they intersect
            # with this one
            for other_room in rooms:
                if new_room.intersect(other_room):
                    break

            else:
                # this means there are no intersections, so this room
                # is valid

                # "paint" it to the map's tiles
                self.create_room(new_room)

                # center coordinates of new room, will be useful later
                (new_x, new_y) = new_room.center()

                last_room_center_x = new_x
                last_room_center_y = new_y

                if num_rooms == 0:
                    # this is the first room, where the player starts at
                    player.x = new_x
                    player.y = new_y
                else:
                    # all rooms after the first:
                    # connect it to the previous room with a tunnel

                    # center coordinates of previous room
                    (prev_x, prev_y) = rooms[num_rooms - 1].center()

                    # flip a coin (random number that is ether 0 or 1)
                    if randint(0, 1) == 1:
                        # first move horizontally, then vertically
                        self.create_h_tunnel(prev_x, new_x, prev_y)
                        self.create_v_tunnel(prev_y, new_y, new_x)
                    else:
                        # first move vertically, then horizontally
                        self.create_v_tunnel(prev_y, new_y, prev_x)
                        self.create_h_tunnel(prev_x, new_x, new_y)

                self.place_entities(new_room, entities, sprites, colors)

                # finally, append the new room to the list
                rooms.append(new_room)
                num_rooms += 1

        stairs_c = Stairs(self.dungeon_level + 1)
        down_stairs = Entity(
            last_room_center_x, last_room_center_y, sprites.get('d_stairs'),
            colors.get('stairs'), colors.get('obj_back'), 'Stairs',
            render_ord=RenderOrder.STAIRS, stairs=stairs_c
        )
        entities.append(down_stairs)

    def create_room(self, room):
        # go through the tiles in the rectangel and make them passable
        for x in range(room.x1 + 1, room.x2):
            for y in range(room.y1 + 1, room.y2):
                self.tiles[x][y].blocked = False
                self.tiles[x][y].block_sight = False

    def create_h_tunnel(self, x1, x2, y):
        for x in range(min(x1, x2), max(x1, x2) + 1):
            self.tiles[x][y].blocked = False
            self.tiles[x][y].block_sight = False

    def create_v_tunnel(self, y1, y2, x):
        for y in range(min(y1, y2), max(y1, y2) + 1):
            self.tiles[x][y].blocked = False
            self.tiles[x][y].block_sight = False

    def place_entities(self, room, entities, sprites, colors):
        # Get a random number of monsters
        max_monsters_per_room = from_dungeon_level(
            [[2, 1], [3, 4], [5, 6]],
            self.dungeon_level
        )
        max_items_per_room = from_dungeon_level(
            [[1, 1], [2, 4]],
            self.dungeon_level
        )

        number_of_monsters = randint(0, max_monsters_per_room)
        number_of_items = randint(0, max_items_per_room)

        monster_chances = {
            'orc': 80,
            'troll': from_dungeon_level(
                [[15, 3], [30, 5], [60, 7]],
                self.dungeon_level
            )
        }
        item_chances = {
            'healing_pot': 70,
            'lightning_scroll': from_dungeon_level(
                [[25, 4]], self.dungeon_level
            ),
            'fireball_scroll': from_dungeon_level(
                [[25, 6]], self.dungeon_level
            ),
            'confuse_scrol': from_dungeon_level(
                [[10, 2]], self.dungeon_level
            )
        }

        for i in range(number_of_monsters):
            # choose a random location in the room
            x = randint(room.x1 + 1, room.x2 - 1)
            y = randint(room.y1 + 1, room.y2 - 1)

            if not any([entity for entity in entities if entity.x == x and
                        entity.y == y]):
                monster_choice = random_choice_from_dict(monster_chances)
                
                if monster_choice == 'orc':
                    fighter_c = Fighter(hp=20, defense=0, power=4, xp=35)
                    ai_c = BasicMonster()
                    monster = Entity(x, y, sprites.get('orc'),
                                     colors.get('orc'), colors.get('obj_back'),
                                     'Orc', blocks=True,
                                     render_ord=RenderOrder.ACTOR,
                                     fighter=fighter_c,
                                     ai=ai_c)
                else:
                    fighter_c = Fighter(hp=30, defense=2, power=8, xp=100)
                    ai_c = BasicMonster()
                    monster = Entity(x, y, sprites.get('troll'),
                                     colors.get('troll'),
                                     colors.get('obj_back'), 'Troll',
                                     blocks=True,
                                     render_ord=RenderOrder.ACTOR,
                                     fighter=fighter_c, ai=ai_c)

                entities.append(monster)

        for i in range(number_of_items):
            x = randint(room.x1 + 1, room.x2 - 1)
            y = randint(room.y1 + 1, room.y2 - 1)

            if not any([entity for entity in entities if entity.x == x and
                        entity.y == y]):
                item_choice = random_choice_from_dict(item_chances)

                if item_choice == 'healing_pot':
                    item_c = Item(use_func=heal, amount=40)
                    item = Entity(x, y, sprites.get('potion'),
                                  colors.get('health_pot'),
                                  colors.get('obj_back'),
                                  'Potion of heals',
                                  render_ord=RenderOrder.ITEM,
                                  item=item_c)
                elif item_choice == 'fireball_scroll':
                    t_msg = Message(
                        'Left-Click a target tile for the fireball, or' +
                        ' Right-click to cancel', colors.get('msg_system')
                    )
                    item_c = Item(
                        use_func=cast_fireball, targeting=True,
                        targeting_msg=t_msg, damage=25, radius=3
                    )
                    item = Entity(
                        x, y, sprites.get('scroll'), colors.get('fireball'),
                        colors.get('obj_back'), 'Fireball Scroll',
                        render_ord=RenderOrder.ITEM, item=item_c
                    )
                elif item_choice == 'confusion_scroll':
                    t_msg = Message(
                        'Left-Click a enemy to confuse it, or' +
                        ' Right-click to cancel', colors.get('msg_system')
                    )
                    item_c = Item(
                        use_func=cast_confuse, targeting=True,
                        targeting_msg=t_msg
                    )
                    item = Entity(
                        x, y, sprites.get('scroll'), colors.get('confuse'),
                        colors.get('obj_back'), 'Confusion Scroll',
                        render_ord=RenderOrder.ITEM,
                        item=item_c
                    )
                else:
                    item_c = Item(use_func=cast_lightning,
                                  damage=40, maximum_range=5)
                    item = Entity(x, y, sprites.get('scroll'),
                                  colors.get('lightning_scroll'),
                                  colors.get('obj_back'), 'Lightning Scroll',
                                  render_ord=RenderOrder.ITEM,
                                  item=item_c)
                entities.append(item)

    def is_blocked(self, x, y):
        if self.tiles[x][y].blocked:
            return True
        return False

    def next_floor(self, player, msg_log, constants):
        self.dungeon_level += 1
        entities = [player]

        self.tiles = self.initialize_tiles()
        self.make_map(
            constants['max_rooms'], constants['room_min_size'],
            constants['room_max_size'], constants['map_width'],
            constants['map_height'], player, entities,
            constants['sprites'], constants['colors']
        )

        tmp = int(player.fighter.max_hp // 2)
        roll = dice_roll(1, tmp)
        base = int(tmp / 2)
        new_floor_heal = roll + base
        player.fighter.heal(new_floor_heal)
        msg_log.add_message(
            Message('You take a moment to rest, and recover your strength.',
                    libtcod.light_han)
        )
        msg_log.add_message(
            Message('regained 1d{0}+{1}(+{2} hp) of Health back'.format(
                tmp, base, new_floor_heal
            ), libtcod.light_han)
        )

        return entities
