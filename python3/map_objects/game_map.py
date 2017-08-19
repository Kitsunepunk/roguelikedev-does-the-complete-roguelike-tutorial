from random import randint
import libtcodpy as libtcod

from components.ai import BasicMonster
from components.fighter import Fighter
from components.item import Item
from entity import Entity
from game_messages import Message
from item_functions import cast_confuse, cast_fireball, cast_lightning, heal
from map_objects.rectangle import Rect
from map_objects.tile import Tile
from render_functions import RenderOrder


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
                 map_height, player, entities, sprites, colors,
                 max_monsters_per_room, max_items_per_room):

        rooms = []
        num_rooms = 0

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

                self.place_entities(new_room, entities, max_monsters_per_room,
                                    max_items_per_room, sprites, colors)

                # finally, append the new room to the list
                rooms.append(new_room)
                num_rooms += 1

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

    def place_entities(self, room, entities, max_monsters_per_room,
                       max_items_per_room, sprites, colors):
        # Get a random number of monsters
        number_of_monsters = randint(0, max_monsters_per_room)
        number_of_items = randint(0, max_items_per_room)

        for i in range(number_of_monsters):
            # choose a random location in the room
            x = randint(room.x1 + 1, room.x2 - 1)
            y = randint(room.y1 + 1, room.y2 - 1)

            if not any([entity for entity in entities if entity.x == x and
                        entity.y == y]):
                if randint(0, 100) < 80:
                    fighter_c = Fighter(hp=10, defense=0, power=3)
                    ai_c = BasicMonster()
                    monster = Entity(x, y, sprites.get('orc'),
                                     colors.get('orc'), colors.get('obj_back'),
                                     'Orc', blocks=True,
                                     render_ord=RenderOrder.ACTOR,
                                     fighter=fighter_c,
                                     ai=ai_c)
                else:
                    fighter_c = Fighter(hp=16, defense=1, power=4)
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
                item_chance = randint(0, 100)

                if item_chance < 70:
                    item_c = Item(use_func=heal, amount=4)
                    item = Entity(x, y, sprites.get('potion'),
                                  colors.get('health_pot'),
                                  colors.get('obj_back'),
                                  'Potion of heals',
                                  render_ord=RenderOrder.ITEM,
                                  item=item_c)
                elif item_chance < 80:
                    t_msg = Message(
                        'Left-Click a target tile for the fireball, or' +
                        ' Right-click to cancel', colors.get('msg_system')
                    )
                    item_c = Item(
                        use_func=cast_fireball, targeting=True,
                        targeting_msg=t_msg, damage=12, radius=3
                    )
                    item = Entity(
                        x, y, sprites.get('scroll'), colors.get('fireball'),
                        colors.get('obj_back'), 'Fireball Scroll',
                        render_ord=RenderOrder.ITEM, item=item_c
                    )
                elif item_chance < 90:
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
                                  damage=20, maximum_range=5)
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
