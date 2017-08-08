import libtcodpy as libtcod
import math
import os
import shelve
import textwrap


# game constants
GAME_TITLE = 'Quest of the McGuffin'

GAME_VER =  ' 2017.08.08'

# actual size of the window
SCREEN_WIDTH = 80
SCREEN_HEIGHT = 50

CAM_WIDTH = 60
CAM_HEIGHT = 40

# size of the map
MAP_MIN_SIZE = 70
MAP_MAX_SIZE = 100
MAP_WIDTH =60  # libtcod.random_get_int(0, MAP_MIN_SIZE, MAP_MAX_SIZE)
MAP_HEIGHT = 40 # libtcod.random_get_int(0, MAP_MIN_SIZE, MAP_MAX_SIZE)

# parameters for dungeon generator
ROOM_MAX_SIZE = 10
ROOM_MIN_SIZE = 6
MAX_ROOMS = 30

LEFT_F_WIDTH = 60
MAP_F_HEIGHT = 40

LOOK_WIDTH = 58
LOOK_HEIGHT = 1
LOOK_F_HEIGHT = 3

MSG_F_HEIGHT = 7
MSG_X = 0
MSG_L = 58 - 2
MSG_WIDTH = 58
MSG_HEIGHT = 5

INFO_WIDTH = 18
INFO_HEIGHT = 48

FOV_ALGO = libtcod.FOV_SHADOW  # libtcod.FOV_PERMISSIVE_1default FOV algorithm
FOV_LIGHT_WALLS = True  # light walls or not
TORCH_RADIUS = 10

LIMIT_FPS = 20  # 20 frames-per-second maximum

BAR_WIDTH = 16

INVENTORY_WIDTH = 50

LEVEL_UP_BASE = 200
LEVEL_UP_FACTOR = 150
LEVEL_SCREEN_WIDTH = 40

MENU_IMG = 'menu.png'

heal = 40
lightning = 40
fireball = 25
LIGHTNING_RANGE = 5
CONFUSE_NUM_TURNS = 10
CONFUSE_RANGE = 8
FIREBALL_RADIUS = 3

HEAD_SLOT = 'Head'
CHEST_SLOT = 'Chest'
RIGHT_ARM = 'R.Arm'
RIGHT_HAND = 'R.Hand'
LEFT_ARM = 'L.Arm'
LEFT_HAND = 'L.Hand'
LEG_SLOT = 'Legs'
BOOT_SLOT = 'Boots'

con_fore_color = libtcod.white
con_back_color = libtcod.black

color_dark_wall = libtcod.darker_grey
color_light_wall = libtcod.amber
color_dark_ground = libtcod.dark_grey
color_light_ground = libtcod.light_amber
color_dark_back = libtcod.darkest_grey

obj_back = libtcod.black
player_color = libtcod.black
player_back = libtcod.green

warning_color = libtcod.pink

wall_char = '#'  # 206


class Tile:
    # a tile of the map and its properties
    def __init__(self, blocked, block_sight=None):
        self.blocked = blocked

        # all tiles start unexplored
        self.explored = False

        # by default, if a tile is blocked, it also blocks sight
        if block_sight is None:
            block_sight = blocked
        self.block_sight = block_sight


class Rect:
    # a rectangle on the map. used to characterize a room.
    def __init__(self, x, y, w, h):
        self.x1 = x
        self.y1 = y
        self.x2 = x + w
        self.y2 = y + h

    def center(self):
        center_x = (self.x1 + self.x2) / 2
        center_y = (self.y1 + self.y2) / 2
        return (center_x, center_y)

    def intersect(self, other):
        # returns true if this rectangle intersects with another one
        return (self.x1 <= other.x2 and self.x2 >= other.x1 and
                self.y1 <= other.y2 and self.y2 >= other.y1)


class Object:
    # this is a generic object: the player, a monster, an item, the stairs...
    # it's always represented by a character on screen.
    def __init__(self, x, y, char, name, color, color2, blocks=False,
                 always_visible=False, fighter=None, ai=None, item=None,
                 equipment=None):
        self.x = x
        self.y = y
        self.char = char
        self.name = name
        self.color = color
        self.color2 = color2
        self.blocks = blocks
        self.always_visible = always_visible
        self.fighter = fighter
        if self.fighter:  # let the fighter component know who owns it
            self.fighter.owner = self

        self.ai = ai
        if self.ai:  # let the AI component know who wons it
            self.ai.owner = self

        self.item = item
        if self.item:  # let the Item component know who owns it
            self.item.owner = self

        self.equipment = equipment
        if self.equipment:
            self.equipment.owner = self

            self.item = Item()
            self.item.owner = self

    def move(self, dx, dy):
        # move by the given amount, if the destination is not blocked
        if not is_blocked(self.x + dx, self.y + dy):
            self.x += dx
            self.y += dy

    def move_towards(self, target_x, target_y):
        # vector from this object to the target, and distance
        dx = target_x - self.x
        dy = target_y - self.y
        distance = math.sqrt(dx ** 2 + dy ** 2)

        # normalize it to length 1 (preserving direction), then round
        # convert to integer so the movement is restricted to the map grid
        dx = int(round(dx / distance))
        dy = int(round(dy / distance))
        self.move(dx, dy)

    def move_astar(self, target):
        # create a FOV map that has the dimensions of the map
        fov = libtcod.map_new(MAP_WIDTH, MAP_HEIGHT)

        for y1 in range(MAP_HEIGHT):
            for x1 in range(MAP_WIDTH):
                libtcod.map_set_properties(fov, x1, y1,
                                           not map[x1][y1].block_sight,
                                           not map[x1][y1].blocked)
        for obj in objects:
            if obj.blocks and obj != self and obj != target:
                libtcod.map_set_properties(fov, obj.x, obj.y, True, False)

        my_path = libtcod.path_new_using_map(fov, 1.41)
        libtcod.path_compute(my_path, self.x, self.y, target.x, target.y)

        if not (libtcod.path_is_empty(my_path) and
                libtcod.path_size(my_path) < 25):
            x, y = libtcod.path_walk(my_path, True)
            if x or y:
                self.x = x
                self.y = y
        else:
            self.move_towards(target.x, target.y)

        libtcod.path_delete(my_path)

    def distance_to(self, other):
        # return the distance to another object
        dx = other.x - self.x
        dy = other.y - self.y
        return math.sqrt(dx ** 2 + dy ** 2)

    def distance(self, x, y):
        return math.sqrt((x - self.x) ** 2 + (y - self.y) ** 2)

    def send_to_back(self):
        # make this object be drawn first, so all others appear above
        # it if they're in the same tile
        global objects
        objects.remove(self)
        objects.insert(0, self)

    def draw(self):
        # only show if it's visible to the player
        if libtcod.map_is_in_fov(fov_map, self.x, self.y):
            (x, y) = to_camera_coordiantes(self.x, self.y)
            if x is not None:
                # set the color and then draw the character that
                # represents this object at its position
                libtcod.console_put_char_ex(mapcon, x, y, self.char,
                                            self.color, self.color2)
        elif (self.always_visible and map[self.x][self.y].explored):
            (x, y) = to_camera_coordiantes(self.x, self.y)
            if x is not None:
                libtcod.console_put_char_ex(mapcon, x, y, self.char, self.color,
                                            color_dark_back)

    def clear(self):
        if libtcod.map_is_in_fov(fov_map, self.x, self.y):
            (x, y) = to_camera_coordiantes(self.x, self.y)
            if x is not None:
                # erase the character that represents this object
                libtcod.console_put_char_ex(mapcon, x, y, '.',
                                            color_light_ground, libtcod.black)


class Fighter:
    # combat-related properties and methods(monster, player, NPC)
    def __init__(self, hp, defense, power, xp, death_function=None):
        self.base_max_hp = hp
        self.hp = hp
        self.base_defense = defense
        self.base_power = power
        self.xp = xp
        self.death_function = death_function

    @property
    def power(self):
        bonus = sum(equipment.power_bonus for equipment in get_all_equipped(self.owner))
        return self.base_power + bonus

    @property
    def defense(self):
        bonus = sum(equipment.defense_bonus for equipment in get_all_equipped(self.owner))
        return self.base_defense + bonus

    @property
    def max_hp(self):
        bonus = sum(equipment.max_hp_bonus for equipment in get_all_equipped(self.owner))
        return self.base_max_hp + bonus

    def attack(self, target):
        # a simple formula for attack damage
        damage = self.power - target.fighter.defense

        if damage > 0:
            # make the target take some damage
            if self.owner.name != 'Player':
                message(self.owner.name.capitalize() + ' attacks ' +
                        target.name +
                        ' for' + str(damage) + ' hit points.',
                        self.owner.color)
            else:
                message(self.owner.name.capitalize() + ' attacks ' +
                        target.name + ' for ' + str(damage) + ' hit points.',
                        libtcod.white)
            target.fighter.take_damage(damage)
        else:
            if self.owner.name != 'Player':
                message(self.owner.name.capitalize() + ' atttacks ' + target.name +
                        ' but it has no effect!', self.owner.color)
            else:
                message(self.owner.name.capitalize() + ' atttacks ' + target.name +
                        ' but it has no effect!', libtcod.white)

    def take_damage(self, damage):
        # apply damage if possible
        if damage > 0:
            self.hp -= damage

            if self.hp <= 0:
                self.hp = 0
                function = self.death_function
                if function is not None:
                    function(self.owner)

                if self.owner != player:
                    player.fighter.xp += self.xp

    def heal(self, amount):
        self.hp += amount
        if self.hp > self.max_hp:
            self.hp = self.max_hp


class BasicMonster:
    # AI for a basic monster.
    def take_turn(self):
        # a basic monster takes its turn. if you can see it, it cn see you
        monster = self.owner
        if libtcod.map_is_in_fov(fov_map, monster.x, monster.y):

            # move towards player if far away
            if monster.distance_to(player) >= 2:
                monster.move_astar(player)

            # close enough, attack! ( if the player is still alive)
            elif player.fighter.hp >= 0:
                monster.fighter.attack(player)


class ConfusedMonster:
    # AI for a temporarily confused monster (reverts to previous AI)

    def __init__(self, old_ai, num_turns=CONFUSE_NUM_TURNS):
        self.old_ai = old_ai
        self.num_turns = num_turns

    def take_turn(self):
        if self.num_turns > 0:
            self.owner.move(libtcod.random_get_int(0, -1, 1),
                            libtcod.random_get_int(0, -1, 1))
            self.num_turns -= 1

        else:
            self.owner.ai = self.old_ai
            message('The ' + self.owner.name + ' is no longer confused!',
                    libtcod.red)


class Item:
    # an item that can be picked up and used

    def __init__(self, use_function=None):
        self.use_function = use_function

    def pick_up(self):
        # add to the player's inventory and remove from the map
        if len(inventory) >= 26:
            message('Your inventory is full, cannot pick up ' +
                    self.owner.name + '.', warning_color)
        else:
            inventory.append(self.owner)
            objects.remove(self.owner)
            message('You picked up a ' + self.owner.name + '!',
                    self.owner.color)

            equipment = self.owner.equipment
            if equipment and get_equipped_in_slot(equipment.slot) is None:
                equipment.equip()

    def drop(self):

        if self.owner.equipment:
            self.owner.equipment.dequip()

        objects.append(self.owner)
        inventory.remove(self.owner)
        self.owner.x = player.x
        self.owner.y = player.y
        message('You dropped a ' + self.owner.name + '.', libtcod.yellow)

    def use(self):

        if self.owner.equipment:
            self.owner.equipment.toggle_equip()
            return

        if self.use_function is None:
            message('The ' + self.owner.name + ' cannot be used',
                    warning_color)
        else:
            if self.use_function() != 'cancelled':
                inventory.remove(self.owner)


class Equipment:

    def __init__(self, slot, power_bonus=0, defense_bonus=0, max_hp_bonus=0):
        self.power_bonus = power_bonus
        self.defense_bonus = defense_bonus
        self.max_hp_bonus = max_hp_bonus

        self.slot = slot
        self.is_equipped = False

    def toggle_equip(self):
        if self.is_equipped:
            self.dequip()
        else:
            self.equip()

    def equip(self):

        old_equipment = get_equipped_in_slot(self.slot)
        if old_equipment is not None:
            old_equipment.dequip()


        self.is_equipped = True
        message('Equipped ' + self.owner.name + ' on ' + self.slot + '.',
                libtcod.light_green)

    def dequip(self):
        if not self.is_equipped: return
        self.is_equipped = False
        message('Dequipped ' + self.owner.name + ' from ' + self.slot + '.',
                libtcod.light_yellow)


def get_equipped_in_slot(slot):
    for obj in inventory:
        if obj.equipment and obj.equipment.slot == slot and obj.equipment.is_equipped:
            return obj.equipment
    return None

def get_equipped(slot):
    for obj in inventory:
        if obj.equipment and obj.equipment.slot == slot and obj.equipment.is_equipped:
            return obj.name
    return 'empty'

def get_power_bonus(slot):
    for obj in inventory:
        if obj.equipment and obj.equipment.slot == slot and obj.equipment.is_equipped:
            return str(obj.equipment.power_bonus)
    return '0'

def get_defense_bonus(slot):
    for obj in inventory:
        if obj.equipment and obj.equipment.slot == slot and obj.equipment.is_equipped:
            return str(obj.equipment.defense_bonus)
    return '0'

def get_hp_bonus(slot):
    for obj in inventory:
        if obj.equipment and obj.equipment.slot == slot and obj.equipment.is_equipped:
            return str(obj.equipment.max_hp_bonus)
    return '0'

def get_all_equipped(obj):
    if obj == player:
        equipped_list = []
        for item in inventory:
            if item.equipment and item.equipment.is_equipped:
                equipped_list.append(item.equipment)
        return equipped_list
    else:
        return []


def is_blocked(x, y):
    # first test the map tile
    if map[x][y].blocked:
        return True

    # now check for any blocking objects
    for object in objects:
        if object.blocks and object.x == x and object.y == y:
            return True

    return False


def check_level_up():
    level_up_xp = level_formula()
    if player.fighter.xp >= level_up_xp:
        player.level += 1
        player.fighter.xp -= level_up_xp
        message('Your battle skills grow stronger! You reached level ' +
                str(player.level) + '!', libtcod.yellow)

        choice = None
        while choice == None:
            choice = menu('LEVEL UP', 'Choose a stat to raise:\n',
                          ['Constitution (+20 HP, from ' +
                           str(player.fighter.max_hp) + ')',
                           'Strength (+1 attack from ' +
                           str(player.fighter.power) + ')',
                           'Agility ( +1 defense, from ' +
                           str(player.fighter.defense) + ')'],
                          LEVEL_SCREEN_WIDTH)

        if choice == 0:
            player.fighter.base_max_hp += 20
            player.fighter.hp += 20
            if player.fighter.hp >= player.fighter.max_hp:
                player.fighter.hp = player.fighter.max_hp
        elif choice == 1:
            player.fighter.base_power += 1
        elif choice == 2:
            player.fighter.base_defense += 1


def level_formula():
    xp = LEVEL_UP_BASE + player.level * LEVEL_UP_FACTOR
    return xp


def create_room(room):
    global map
    # go through the tiles in the rectangle and make them passable
    for x in range(room.x1 + 1, room.x2):
        for y in range(room.y1 + 1, room.y2):
            map[x][y].blocked = False
            map[x][y].block_sight = False


def create_h_tunnel(x1, x2, y):
    global map
    # horizontal tunnel. min() and max() are used in case x1>x2
    for x in range(min(x1, x2), max(x1, x2) + 1):
        map[x][y].blocked = False
        map[x][y].block_sight = False


def create_v_tunnel(y1, y2, x):
    global map
    # vertical tunnel
    for y in range(min(y1, y2), max(y1, y2) + 1):
        map[x][y].blocked = False
        map[x][y].block_sight = False


def make_map():
    global map, objects, stairs

    objects = [player]

    # fill map with "blocked" tiles
    map = [[Tile(True) for y in range(MAP_HEIGHT)]
           for x in range(MAP_WIDTH)]

    rooms = []
    num_rooms = 0

    for r in range(MAX_ROOMS):
        # random width and height
        w = libtcod.random_get_int(0, ROOM_MIN_SIZE, ROOM_MAX_SIZE)
        h = libtcod.random_get_int(0, ROOM_MIN_SIZE, ROOM_MAX_SIZE)
        # random position without going out of the boundaries of the map
        x = libtcod.random_get_int(0, 1, MAP_WIDTH - w - 2)
        y = libtcod.random_get_int(0, 1, MAP_HEIGHT - h - 2)

        # "Rect" class makes rectangles easier to work with
        new_room = Rect(x, y, w, h)

        # run through the other rooms and see if they intersect with
        # this one
        failed = False
        for other_room in rooms:
            if new_room.intersect(other_room):
                failed = True
                break

        if not failed:
            # this means there are no intersections, so this room is
            # valid

            # "paint" it to the map's tiles
            create_room(new_room)

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
                (prev_x, prev_y) = rooms[num_rooms-1].center()

                # draw a coin (random number that is either 0 or 1)
                if libtcod.random_get_int(0, 0, 1) == 1:
                    # first move horizontally, then vertically
                    create_h_tunnel(prev_x, new_x, prev_y)
                    create_v_tunnel(prev_y, new_y, new_x)
                else:
                    # first move vertically, then horizontally
                    create_v_tunnel(prev_y, new_y, prev_x)
                    create_h_tunnel(prev_x, new_x, new_y)

            # add some contents to this room, such as monsters
            place_objects(new_room)

            # finally, append the new room to the list
            rooms.append(new_room)
            num_rooms += 1

    stairs = Object(new_x, new_y, '<', 'stairs', libtcod.white, libtcod.black,
                    always_visible=True)
    objects.append(stairs)
    stairs.send_to_back()


def place_objects(room):
    # choose random number of monsters
    max_monsters = from_dungeon_level([[2, 1], [3, 4], [5, 6]])

    monster_chances = {}
    monster_chances['orc']  = 80
    monster_chances['troll'] = from_dungeon_level([[15, 3], [30, 5], [60, 7]])

    max_items = from_dungeon_level([[1, 1],[2, 4]])

    item_chances = {}
    item_chances['heal'] = 35
    item_chances['lightning'] = from_dungeon_level([[25, 4]])
    item_chances['fireball'] =  from_dungeon_level([[25, 6]])
    item_chances['confuse'] =   from_dungeon_level([[10, 2]])
    item_chances['sword'] =     from_dungeon_level([[5, 4]])
    item_chances['shield'] =    from_dungeon_level([[15, 8]])

    num_monsters = libtcod.random_get_int(0, 0, max_monsters)

    for i in range(num_monsters):
        # choose random spot for this monster
        x = libtcod.random_get_int(0, room.x1 + 1, room.x2 - 1)
        y = libtcod.random_get_int(0, room.y1 + 1, room.y2 - 1)

        # only place it if the tile is not blocked
        if not is_blocked(x, y):
            choice = random_choice(monster_chances)
            # 80% chance of getting an orc
            if choice == 'orc':
                # create an orc
                fighter_component = Fighter(hp=20, defense=0, power=4, xp=35,
                                            death_function=monster_death)
                ai_component = BasicMonster()
                monster = Object(x, y, 'o', 'Orc', libtcod.desaturated_green,
                                 obj_back, blocks=True,
                                 fighter=fighter_component, ai=ai_component)
            elif choice == 'troll':
                # create a troll
                fighter_component = Fighter(hp=30, defense=2, power=4, xp=100,
                                            death_function=monster_death)
                ai_component = BasicMonster()
                monster = Object(x, y, 'T', 'Troll', libtcod.darker_green,
                                 obj_back, blocks=True,
                                 fighter=fighter_component, ai=ai_component)

            objects.append(monster)

    num_items = libtcod.random_get_int(0, 0, max_items)

    for i in range(num_items):
        # choose random number of items
        x = libtcod.random_get_int(0, room.x1 + 1, room.x2 - 1)
        y = libtcod.random_get_int(0, room.y1 + 1, room.y2 - 1)

        # only place it if the tile is not blocked
        if not is_blocked(x, y):
            choice = random_choice(item_chances)
            if choice == 'heal':
                # create a healing potion

                item_component = Item(cast_heal)
                item = Object(x, y, 173, 'Healing Potion', libtcod.violet,
                              obj_back, always_visible=True,
                              item=item_component)
            elif choice == 'lightning':
                # create a lightning bolt scroll (30% chance)
                item_component = Item(cast_lightning)

                item = Object(x, y, 19, 'scroll of lightning bolt',
                              libtcod.sky, obj_back, always_visible=True,
                              item=item_component)

            elif choice == 'fireball':
                item_component = Item(cast_fireball)
                item = Object(x, y, 19, 'Scroll of Fireball', libtcod.flame,
                              obj_back, always_visible=True,
                              item=item_component)

            elif choice == 'confuse':
                item_component = Item(cast_confuse)
                item = Object(x, y, 19, 'Scroll of Confusion', libtcod.green,
                              obj_back, always_visible=True,
                              item=item_component)

            elif choice == 'sword':
                equipment_component = Equipment(slot=RIGHT_HAND,
                                                power_bonus=3, defense_bonus=0,
                                                max_hp_bonus=0)
                item = Object(x, y, '/', 'Sword', libtcod.sky, obj_back,
                              always_visible=True,
                              equipment=equipment_component)

            elif choice == 'shield':
                equipment_component = Equipment(slot=LEFT_HAND,
                                                defense_bonus=1)
                item = Object(x, y, '[', 'Shield', libtcod.darker_orange, obj_back,
                              equipment=equipment_component)

            objects.append(item)
            item.send_to_back()  # items appear below other objects


def random_choice_index(chances):

    dice = libtcod.random_get_int(0, 1, sum(chances))

    running_sum = 0
    choice = 0
    for w in chances:
        running_sum += w

        if dice <= running_sum:
            return choice
        choice += 1

def random_choice(chances_dict):
    chances = chances_dict.values()
    strings = chances_dict.keys()

    return strings[random_choice_index(chances)]

def from_dungeon_level(table):

    for (value, level) in reversed(table):
        if dungeon_level >= level:
            return value
    return 0


def render_bar(con, x, y, total_width, name, value, max_value, text_color,
               bar_color, bar_back_color):

    # render a bar (HP, XP, MANA, etc.). first calculate teh widht of
    # the bar
    bar_width = int(float(value) / max_value * total_width)

    # render the background first
    libtcod.console_set_default_background(con, bar_back_color)
    libtcod.console_rect(con, x, y, total_width, 1, False,
                         libtcod.BKGND_SCREEN)

    # now render the bar on top
    libtcod.console_set_default_background(con, bar_color)
    if bar_width > 0:
        libtcod.console_rect(con, x, y, bar_width, 1, False,
                             libtcod.BKGND_SCREEN)

    # finally some centered text with the values
    libtcod.console_set_default_foreground(con, text_color)
    libtcod.console_print_ex(con, x, y - 1, libtcod.BKGND_NONE,
                             libtcod.LEFT, name + ': ' + str(value) + '/' +
                             str(max_value))


def get_names_under_mouse():
    global mouse

    # return a string with the names of all objects under the mouse
    (x, y) = (mouse.cx, mouse.cy)
    (x, y) = (camera_x + x, camera_y + y)

    # create a list with the names of all objects at the mouse's
    # coordinates and in FOV
    names = [obj.name for obj in objects
             if (obj.x == x and obj.y == y and
                 libtcod.map_is_in_fov(fov_map, obj.x, obj.y))]

    names = ', '.join(names)
    return names.capitalize()


def move_camera(target_x, target_y):
    global camera_x, camera_y, fov_recompute

    # new camera coordinates
    # (top-left corner of the screen releative to the map)
    x = target_x - CAM_WIDTH / 2
    y = target_y - CAM_HEIGHT / 2

    if x < 0:
        x = 0
    if y < 0:
        y = 0
    if x > MAP_WIDTH - CAM_WIDTH - 1:
        x = MAP_WIDTH - CAM_WIDTH - 1
    if y > MAP_HEIGHT - CAM_HEIGHT - 1:
        y = MAP_HEIGHT - CAM_HEIGHT - 1

    if x != camera_x or y != camera_y:
        fov_recompute = True

    (camera_x, camera_y) = (x, y)


def to_camera_coordiantes(x, y):
    (x, y) = (x - camera_x, y - camera_y)

    if x < 0 or y < 0 or x >= CAM_WIDTH or y >= CAM_HEIGHT:
        return (None, None)

    return (x, y)


def render_all():
    global fov_map, color_dark_wall, color_light_wall
    global color_dark_ground, color_light_ground
    global fov_recompute, debug

    move_camera(player.x, player.y)

    if fov_recompute:
        # recompute FOV if needed (the player moved or something)
        fov_recompute = False
        libtcod.map_compute_fov(fov_map, player.x, player.y, TORCH_RADIUS,
                                FOV_LIGHT_WALLS, FOV_ALGO)
        libtcod.console_clear(mapcon)

        # go through all tiles, and set their background color
        # according to the FOV
        for y in range(CAM_HEIGHT):
            for x in range(CAM_WIDTH):
                (map_x, map_y) = (camera_x + x, camera_y + y)
                visible = libtcod.map_is_in_fov(fov_map, map_x, map_y)
                wall = map[map_x][map_y].block_sight
                if not visible:
                    libtcod.console_put_char_ex(mapcon, x, y, 178,
                                                con_back_color,
                                                libtcod.darkest_grey)
                    # if it's not visible right now, the player can only
                    # see it if it's explored
                    if map[map_x][map_y].explored:
                        if wall:
                            libtcod.console_put_char_ex(mapcon, x, y, wall_char,
                                                        color_dark_wall,
                                                        color_dark_back)
                        else:
                            libtcod.console_put_char_ex(mapcon, x, y, '.',
                                                        color_dark_ground,
                                                        color_dark_back)
                else:
                    # it's visible
                    if wall:
                        libtcod.console_put_char_ex(mapcon, x, y, wall_char,
                                                    color_light_wall,
                                                    libtcod.black)
                    else:
                        libtcod.console_put_char_ex(mapcon, x, y, '.',
                                                    color_light_ground,
                                                    libtcod.black)
                    # since it's visible, explore it
                    map[map_x][map_y].explored = True

    # draw all objects in the list
    for object in objects:
        if object != player:
            object.draw()

    player.draw()

#    if debug is True:
#        libtcod.console_blit(debug, 0, 0, 40, 50, 0, 1, 1, 0.7, 0.5)

    # blit the contents of "con" to the root console
    libtcod.console_blit(mapcon, 0, 0, MAP_WIDTH, MAP_HEIGHT, 0, 0, 0)

    libtcod.console_set_default_foreground(lookcon, libtcod.white)
    libtcod.console_clear(lookcon)
    libtcod.console_print_ex(lookcon, 0, 0, libtcod.BKGND_NONE, libtcod.LEFT,
                             get_names_under_mouse())
    libtcod.console_blit(lookcon, 0, 0, LOOK_WIDTH, LOOK_HEIGHT, 0, 1, 41)

    libtcod.console_set_default_background(msgcon, con_back_color)
    libtcod.console_clear(msgcon)

    # print the game messages, one line at a time
    y = 0
    colorCoef = 0.4
    for (line, color) in game_msgs:
        libtcod.console_set_default_foreground(msgcon, color * colorCoef)
        libtcod.console_print_ex(msgcon, MSG_X, y, libtcod.BKGND_NONE,
                                 libtcod.LEFT, line)
        y += 1
        if colorCoef < 1.0:
            colorCoef += 0.2

    libtcod.console_blit(msgcon, 0, 0, MSG_WIDTH, MSG_HEIGHT, 0, 1, 44)

    # show the player's stats
    libtcod.console_set_default_background(infocon, con_back_color)
    libtcod.console_clear(infocon)

    # show the player's stats
    info_screen()
    libtcod.console_blit(infocon, 0, 0, INFO_WIDTH, INFO_HEIGHT, 0, 61, 1)

    draw_frames()


def message(new_msg, color=libtcod.white):
    # split the message if necessary, among multiple lines
    new_msg_lines = textwrap.wrap(new_msg, MSG_L)

    for line in new_msg_lines:
        # if the buffer is full, remove the first line to make room for
        # the new one
        if len(game_msgs) == MSG_HEIGHT:
            del game_msgs[0]

        # add the new line as a tuple, with the text and the color
        game_msgs.append((line, color))


def player_move_or_attack(dx, dy):
    global fov_recompute

    # the coordinates the player is moving to/attacking
    x = player.x + dx
    y = player.y + dy

    # try to find an attackable object there
    target = None
    for object in objects:
        if object.fighter and object.x == x and object.y == y:
            target = object
            break

    # attack if target found, move otherwise
    if target is not None:
        player.fighter.attack(target)
    else:
        player.move(dx, dy)
        fov_recompute = True


def menu(title, header, options, width):

    if len(options) > 26:
        raise ValueError('Cannot have a menu with more than 26 options.')

        # calculate total height for teh header (after auto-wrap) and
        # one line per option

    if header == '':
        header_height = 0
    else:
        header_height = libtcod.console_get_height_rect(mapcon, 0, 0, width,
                                                        SCREEN_HEIGHT, header)
    height = len(options) + header_height + 4

    # create an off-screen console that represents the menu's window
    window = libtcod.console_new(width, height)

    # print the header, with auto-wrap
    libtcod.console_set_default_foreground(window, con_fore_color)
    libtcod.console_set_default_background(window, con_back_color)

    if header != '':
        libtcod.console_print_frame(window, 0, 0, width, height, True,
                                    libtcod.BKGND_SET, title)
        libtcod.console_hline(window, 1, 3, width - 2, libtcod.BKGND_SET)
        libtcod.console_print_rect_ex(window, 1, 1, width, height,
                                      libtcod.BKGND_SET, libtcod.LEFT, header)

    else:
        libtcod.console_print_rect_ex(window, 1, 1, width, height,
                                      libtcod.BKGND_SET, libtcod.LEFT, header)

    y = header_height + 2
    letter_index = ord('a')
    for option_text in options:
        text = '(' + chr(letter_index) + ') ' + option_text
        libtcod.console_print_ex(window,  1, y, libtcod.BKGND_SET,
                                 libtcod.LEFT, text)
        y += 1
        letter_index += 1

    x = SCREEN_WIDTH / 2 - width / 2
    y = SCREEN_HEIGHT / 2 - height / 2
    libtcod.console_blit(window, 0, 0, width, height, 0, x, y, 1.0, 0.7)

    libtcod.console_flush()
    key = libtcod.console_wait_for_keypress(True)

    index = key.c - ord('a')
    if index >= 0 and index < len(options):
        return index
    return None


def debug():

    libtcod.console_print_ex(infocon, 1, 4, libtcod.BKGND_NONE, libtcod.LEFT,
                             'Pow: ' + str(player.fighter.power) + '(' +
                             str(player.fighter.power) + ')')
    libtcod.console_print_ex(infocon, 1, 5, libtcod.BKGND_NONE, libtcod.LEFT,
                             'Def: ' + str(player.fighter.defense) + '(' +
                             str(player.fighter.defense) + ')')
    libtcod.console_print_ex(debug, 1, 1, libtcod.BKGND_NONE, libtcod.LEFT,
                             'M.Pos.:(' + str((mouse.cx, mouse.cy)) + ')')
    libtcod.console_print_ex(debug, 1, 2, libtcod.BKGND_NONE, libtcod.LEFT,
                             'C.P.+M.P.:' +
                             str((camera_x + mouse.cx, camera_y + mouse.cy)))
    libtcod.console_print_ex(debug, 1, 3, libtcod.BKGND_NONE, libtcod.LEFT,
                             '@.Pos:' + str((player.x, player.y)))
    libtcod.console_print_ex(debug, 1, 4, libtcod.BKGND_NONE, libtcod.LEFT,
                             'C.P.+@.P.:' +
                             str((camera_x + player.x, camera_y + player.y)))
    libtcod.console_print_ex(debug, 1, 5, libtcod.BKGND_NONE, libtcod.LEFT,
                             'in FOV: ' +
                             str(libtcod.map_is_in_fov(fov_map, camera_x +
                                                       mouse.cx,
                                                       mouse.cy +
                                                       camera_y)))
    libtcod.console_print_ex(debug, 1, 6, libtcod.BKGND_NONE, libtcod.LEFT,
                             'L.b.click: ' + str(mouse.lbutton_pressed))
    libtcod.console_print_ex(debug, 1, 7, libtcod.BKGND_NONE, libtcod.LEFT,
                             'R.b.click: ' + str(mouse.rbutton_pressed))
    libtcod.console_print_ex(debug, 1, 8, libtcod.BKGND_NONE, libtcod.LEFT,
                             '@.dist(M.pos):' +
                             str(int(player.distance(mouse.cx, mouse.cy))))


def inventory_menu(title, header):

    if len(inventory) == 0:
        options = ['Inventory is empty.']
    else:
        options = []
        for item in inventory:
            text = item.name
            if item.equipment and item.equipment.is_equipped:
                text = text + ' (on ' + item.equipment.slot + ')'
            options.append(text)

    index = menu(title, header, options, INVENTORY_WIDTH)

    if index is None or len(inventory) == 0:
        return None
    return inventory[index].item


def handle_keys():
    global key, mouse, debug
    # key = libtcod.console_check_for_keypress()  # real-time
    # key = libtcod.console_wait_for_keypress(True)  # turn-based

    if key.vk == libtcod.KEY_ENTER and key.lalt:
        # Alt+Enter: toggle fullscreen
        libtcod.console_set_fullscreen(not libtcod.console_is_fullscreen())

    elif key.vk == libtcod.KEY_ESCAPE:
        return 'exit'  # exit game

    if game_state == 'playing':
        # movement keys
        if key.vk == libtcod.KEY_UP or key.vk == libtcod.KEY_KP8:
            player_move_or_attack(0, -1)

        elif key.vk == libtcod.KEY_DOWN or key.vk == libtcod.KEY_KP2:
            player_move_or_attack(0, 1)

        elif key.vk == libtcod.KEY_LEFT or key.vk == libtcod.KEY_KP4:
            player_move_or_attack(-1, 0)

        elif key.vk == libtcod.KEY_RIGHT or key.vk == libtcod.KEY_KP6:
            player_move_or_attack(1, 0)
        elif key.vk == libtcod.KEY_KP7:
            player_move_or_attack(-1, -1)

        elif key.vk == libtcod.KEY_KP9:
            player_move_or_attack(1, -1)

        elif key.vk == libtcod.KEY_KP1:
            player_move_or_attack(-1, 1)
        elif key.vk == libtcod.KEY_KP3:
            player_move_or_attack(1, 1)
        elif key.vk == libtcod.KEY_KP5:
            pass
        else:
            key_char = chr(key.c)

            if key_char == 'd':

                chosen_item = inventory_menu('Inventory Menu', 'Press the' +
                                             ' key next to an Item to drop' +
                                             ' it, or any other to cancel.\n')
                if chosen_item is not None:
                    chosen_item.drop()

            if key_char == 'i':
                # message('testing the inventory key', libtcod.azure)
                chosen_item = inventory_menu('Inventory Menu',
                                             'Press the key next to an item' +
                                             ' to use it, or any other to' +
                                             ' cancel.\n')
                if chosen_item is not None:
                    chosen_item.use()

            if key_char == 'g':
                # pick up an item..
                for object in objects:
                    if (object.x == player.x and object.y == player.y and
                            object.item):
                        object.item.pick_up()
                        break

            if key.vk == libtcod.KEY_TEXT:
                ch = key.text
                if ch == '<':
                    if stairs.x == player.x and stairs.y == player.y:
                        next_level()
            if key.vk == libtcod.KEY_F1:
                take_screenshot()
            return 'didnt-take-turn'


def next_level():
    global dungeon_level
    message('You take a moment to rest, and recover you strength.',
            libtcod.light_violet)
    player.fighter.heal(player.fighter.max_hp / 2)

    message('After a rare moment of peace, you decend deeper into the heart' +
            ' of the dungeon...', libtcod.red)
    dungeon_level += 1
    make_map()
    initialize_fov()
    save_game()

shot = 1


def take_screenshot():
    global shot
    test = libtcod.image_from_console(0)

    if not os.path.exists('screenshots/'):
        os.makedirs('screenshots/')

    if os.path.exists('screenshots/ss_0.png'):
        libtcod.image_save(test, 'screenshots/new.png')
        os.rename('screenshots/new.png', 'screenshots/ss_%s.png' % shot)
        shot += 1
    else:
        libtcod.image_save(test, 'screenshots/ss_0.png')

    if os.path.exists('screenshots/new.png'):
        os.remove('screenshots/new.png')

    message('Screenshot saved', libtcod.light_han)



def player_death(player):
    # the game ended!
    global game_state
    message('You DIED!', libtcod.red)
    game_state = 'dead'

    # for added effect, transform the player into a corpse
    player.char = '%'
    player.color = libtcod.dark_red
    player.color2 = libtcod.black
    save_game()


def monster_death(monster):
    # transform it into a nasty corpse! it doesn't block, can't be
    # attacked and doesn't move

    message(monster.name.capitalize() + ' is dead! You gain +' +
            str(monster.fighter.xp) + ' XP', libtcod.orange)
    monster.char = '%'
    monster.color = libtcod.dark_red
    monster.blocks = False
    monster.fighter = None
    monster.ai = None
    monster.name = 'remains of ' + monster.name
    monster.send_to_back()


def target_tile(max_range=None):
    global key, mouse

    while True:
        libtcod.console_flush()
        libtcod.sys_check_for_event(libtcod.EVENT_KEY_PRESS |
                                    libtcod.EVENT_MOUSE, key, mouse)
        render_all()

        (x, y) = (mouse.cx, mouse.cy)
        (x, y) = (camera_x + x, camera_y + y)

        if mouse.rbutton_pressed or key.vk == libtcod.KEY_ESCAPE:
            return (None, None)

        if (mouse.lbutton_pressed and libtcod.map_is_in_fov(fov_map, x, y) and
            (max_range is None or player.distance(x, y) <= max_range)):
            return (x, y)


def target_monster(max_range=None):
    while True:
        (x, y) = target_tile(max_range)
        if x is None:
            return None

        for obj in objects:
            if obj.x == x and obj.y == y and obj.fighter and obj != player:
                return obj


def roll_dice(num, sides):

    total = 0
    roll = 0
    run_total = 0

    for dice in range(num):
        # print '--'

        total = libtcod.random_get_int(0, 1, sides)
        run_total += total
        roll += 1
        # print str(num) + 'd' + str(sides)
        # print 'roll:' + str(roll) + ' running total:' +
        # str(run_total) + ' rolled:' + str(total)
        # print '--'

    # print run_total
    # message('your ' + str(num) + 'd' + str(sides) + ' rolled:' +
    #        str(run_total))
    return run_total


def closest_monster(max_range):

    closest_enemy = None
    closest_dist = max_range + 1

    for object in objects:
        if (object.fighter and not object == player and
                libtcod.map_is_in_fov(fov_map, object.x, object.y)):
            dist = player.distance_to(player)
            if dist < closest_dist:
                closest_enemy = object
                closest_dist = dist

    return closest_enemy


def cast_heal():

    if player.fighter.hp == player.fighter.max_hp:
        message('You are already at full health.', warning_color)
        return 'cancelled'

    # run_total = player.fighter.heal(roll_dice(1, heal) + heal / 2)
    die_roll = roll_dice(1, heal)
    base = heal / 2
    heal_total = die_roll + base
    player.fighter.heal(heal_total)
    message('The lesser potion heals 1d' + str(heal) + '+' + str(base) +
            '(' + str(heal_total) + ') of health', libtcod.violet)


def cast_lightning():

    monster = closest_monster(LIGHTNING_RANGE)
    if monster is None:
        message('No enemy is close enough to strike.', warning_color)
        return 'cancelled'

    die_roll = roll_dice(1, lightning)
    base = lightning / 2
    total = die_roll + base
    message('A lightning blolt strikes the ' + monster.name + ' with a loud' +
            ' thunder! The damage is 1d' + str(lightning) + '+' + str(base) +
            '(' + str((total)) +
            ') hit points.', libtcod.sky)
    monster.fighter.take_damage((total))


def cast_fireball():

    message('Left-click a target tile for the fireball, or right-click to' +
            ' cancel.', libtcod.light_cyan)

    (x, y) = target_tile()
    if x is None:
        return 'cancelled'
    message('The fireball explodes, burning everything within ' +
            str(FIREBALL_RADIUS) + ' tiles!', libtcod.flame)

    for obj in objects:
        if obj.distance(x, y) <= FIREBALL_RADIUS and obj.fighter:
            die_roll = roll_dice(1, fireball)
            base = fireball / 2
            fire_dmg = die_roll + base
            message('The ' + obj.name + ' gets burned for 1d' + str(fireball) +
                    '+' + str(base) + '(' + str(fire_dmg) + ') hit points.',
                    libtcod.flame)
            obj.fighter.take_damage(fire_dmg)


def cast_confuse():

    message('Left-click an enemy to confuse it, or right-click to cancel.',
            libtcod.green)

    monster = target_monster(CONFUSE_RANGE)
    if monster is None:
        return 'cancelled'

    old_ai = monster.ai
    monster.ai = ConfusedMonster(old_ai)
    monster.ai.owner = monster
    message('The eyes fo the ' + monster.name + ' look vacant, as he starts' +
            ' to stumble around!', libtcod.green)


#############################################
# Initialization & Main Loop
#############################################

# libtcod.console_rect(0, 0, 0, SCREEN_WIDTH, SCREEN_HEIGHT, False,
#                     libtcod.BKGND_SET)
def draw_frames():
    libtcod.console_set_default_foreground(0, con_fore_color)
    libtcod.console_set_default_background(0, con_back_color)
    # libtcod.console_clear(0)
#    libtcod.console_print_frame(0, 0, 0, 60, MAP_F_HEIGHT,
#                                False, libtcod.BKGND_SET, 'MAP')
    libtcod.console_print_frame(0, 0, 40, LEFT_F_WIDTH, LOOK_F_HEIGHT, False,
                                libtcod.BKGND_SET, 'LOOK')
    libtcod.console_print_frame(0, 0, 43, LEFT_F_WIDTH, MSG_F_HEIGHT, False,
                                libtcod.BKGND_SET, 'MESSAGE LOG')
    libtcod.console_print_frame(0, 60, 0, INFO_WIDTH + 2, INFO_HEIGHT + 2,
                                False, libtcod.BKGND_SET,
                                'INFORMATION')

debug = False
# the list of objects with just the player


def game_splash():
    libtcod.console_credits()


def msgbox(title, text, width=55):
    menu(title, text, [], width)


def info_screen():
    libtcod.console_set_default_foreground(infocon, libtcod.white)
    libtcod.console_print_ex(infocon, 1, 1, libtcod.BKGND_NONE, libtcod.LEFT,
                             player.name + ' level: ' + str(player.level))

    render_bar(infocon, 1, 3, BAR_WIDTH, 'HP', player.fighter.hp,
               player.fighter.max_hp, libtcod.white, libtcod.light_red,
               libtcod.darker_red)

    libtcod.console_print_ex(infocon, 1, 6, libtcod.BKGND_NONE, libtcod.LEFT,
                             'POW(MOD): ' + str(player.fighter.base_power) +
                             '(' + str(player.fighter.power) + ')')
    libtcod.console_print_ex(infocon, 1, 7, libtcod.BKGND_NONE, libtcod.LEFT,
                             'DEF(MOD): ' + str(player.fighter.base_defense) +
                             '(' + str(player.fighter.defense) + ')')
    render_bar(infocon, 1, 5, BAR_WIDTH, 'XP', player.fighter.xp,
               level_formula(), libtcod.white, libtcod.light_green,
               libtcod.darker_green)
    libtcod.console_print_ex(infocon, 1, 8, libtcod.BKGND_NONE, libtcod.LEFT,
                             'Dungeon Level: ' + str(dungeon_level))
    libtcod.console_print_ex(infocon, 1, INFO_HEIGHT - 2, libtcod.BKGND_NONE,
                             libtcod.LEFT, 'Inventory')
    libtcod.console_print_ex(infocon, 1, INFO_HEIGHT - 1, libtcod.BKGND_NONE,
                             libtcod.LEFT, 'Total Items: ' + str(len(inventory)
                                                                 ))
    libtcod.console_hline(infocon, 0, 9, INFO_WIDTH, libtcod.BKGND_NONE)
    libtcod.console_hline(infocon, 0, INFO_HEIGHT - 3, INFO_WIDTH,
                          libtcod.BKGND_NONE)

    libtcod.console_print_ex(infocon, 1, 10, libtcod.BKGND_NONE, libtcod.LEFT,
                             'Equipment:')
    display_slot(infocon, 1, 12, HEAD_SLOT)
    display_slot(infocon, 10, 12, CHEST_SLOT)
    display_slot(infocon, 1, 18, RIGHT_ARM)
    display_slot(infocon, 10, 18, RIGHT_HAND)
    display_slot(infocon, 1, 24, LEFT_ARM)
    display_slot(infocon, 10, 24, LEFT_HAND)
    display_slot(infocon, 1, 30, LEG_SLOT)
    display_slot(infocon, 10, 30, BOOT_SLOT)


def display_slot(con, x, y, slot, background=libtcod.BKGND_NONE,
                 alignment=libtcod.LEFT):
    libtcod.console_set_default_foreground(infocon, libtcod.white)

    libtcod.console_print_ex(con, x, y, background, alignment, slot.capitalize() + ':')
    if get_equipped(slot) == 'empty':
        libtcod.console_set_default_foreground(con, libtcod.dark_grey)
    else:
        libtcod.console_set_default_foreground(con, libtcod.light_han)
    libtcod.console_print_ex(con, x, y + 1, background, alignment,
                             get_equipped(slot))

    hp_plus = get_hp_bonus(slot)
    test = get_all_equipped(slot)
    if hp_plus == '0' or get_equipped(slot) == 'empty':
        libtcod.console_set_default_foreground(con, libtcod.dark_grey)
    elif hp_plus == 0 and get_equipped(slot) != 'empty':
        libtcod.console_set_default_foreground(con, libtcod.white)
    elif hp_plus > 0:
        libtcod.console_set_default_foreground(con, libtcod.light_red)
    else:
        libtcod.console_set_default_foreground(con, libtcod.red)

    libtcod.console_print_ex(con, x, y + 2, background, alignment,
                             'HP : ' + get_hp_bonus(slot))

    power_plus = get_power_bonus(slot)
    test = get_equipped(slot)
    if power_plus == 0 or get_equipped(slot) == 'empty':
        libtcod.console_set_default_foreground(con, libtcod.dark_grey)

    elif power_plus == '0' and get_equipped(slot) != 'empty':
        libtcod.console_set_default_foreground(con, libtcod.white)
    elif power_plus > 0:
        libtcod.console_set_default_foreground(con, libtcod.light_orange)
    else:
        libtcod.console_set_default_foreground(con, libtcod.red)

    libtcod.console_print_ex(con, x, y + 3, background, alignment,
                             'POW: ' + get_power_bonus(slot))

    if get_defense_bonus(slot) == '0' or get_equipped(slot) == 'empty':
        libtcod.console_set_default_foreground(con, libtcod.dark_grey)
    elif get_defense_bonus(slot) > 0 and get_equipped(slot) != 'empty':
        libtcod.console_set_default_foreground(con, libtcod.light_azure)
    else:
        libtcod.console_set_default_foreground(con, libtcod.red)

    libtcod.console_print_ex(con, x, y + 4, background, alignment,
                             'DEF: ' + get_defense_bonus(slot))


def save_game():
    file = shelve.open('sg', 'n')
    file['map'] = map
    file['objects'] = objects
    file['player_index'] = objects.index(player)
    file['stairs_index'] = objects.index(stairs)
    file['inventory'] = inventory
    file['game_msgs'] = game_msgs
    file['game_state'] = game_state
    file['dungeon_level'] = dungeon_level
    file.close()

    # message('Game saved', libtcod.light_han)


def load_game():
    global map, objects, player, stairs, inventory, game_msgs, game_state
    global dungeon_level
    # open the previously saved shelve and load the game data
    file = shelve.open('sg', 'r')
    map = file['map']
    objects = file['objects']
    player = objects[file['player_index']]
    stairs = objects[file['stairs_index']]
    inventory = file['inventory']
    game_msgs = file['game_msgs']
    game_state = file['game_state']
    dungeon_level = file['dungeon_level']
    file.close()

    initialize_fov()


def new_game():
    global player, inventory, game_msgs, game_state, dungeon_level

    # create object representing the player
    fighter_component = Fighter(hp=100, defense=1, power=2, xp=0,
                                death_function=player_death)
    player = Object(0, 0, '@', 'Player', player_color, player_back,
                    blocks=True, fighter=fighter_component)

    player.level = 1

    # generate map (at this point it's not drawn to the screen)
    dungeon_level = 1
    make_map()
    initialize_fov()

    game_state = 'playing'
    inventory = []

    game_msgs = []

    message('Your village is in danger find the McGuffin to save it!' +
            ' If you can...')

    equipment_component = Equipment(slot=RIGHT_HAND, power_bonus=2, defense_bonus=0, max_hp_bonus=0)
    obj = Object(0, 0, '-', 'dagger', libtcod.sky, obj_back,
                 equipment=equipment_component)
    inventory.append(obj)
    equipment_component.equip()
    obj.always_visible = True


def initialize_fov():
    global fov_recompute, fov_map

    fov_recompute = True

    # create the FOV map, according to the generated map
    fov_map = libtcod.map_new(MAP_WIDTH, MAP_HEIGHT)
    for y in range(MAP_HEIGHT):
        for x in range(MAP_WIDTH):
            libtcod.map_set_properties(fov_map, x, y,
                                       not map[x][y].block_sight,
                                       not map[x][y].blocked)


def play_game():
    global camera_x, camera_y, key, mouse

    player_action = None
    mouse = libtcod.Mouse()
    key = libtcod.Key()

    (camera_x, camera_y) = (0, 0)

    while not libtcod.console_is_window_closed():

        libtcod.sys_check_for_event(libtcod.EVENT_KEY_PRESS |
                                    libtcod.EVENT_MOUSE, key, mouse)

        # render the screen
        render_all()

        libtcod.console_flush()
        check_level_up()

        # erase all objects at their old locations, before they move
        for object in objects:
            object.clear()

        # handle keys and exit game if needed
        player_action = handle_keys()
        if player_action == 'exit':
            save_game()
            break

        # let monsters take their turn
        if game_state == 'playing' and player_action != 'didnt-take-turn':
            for object in objects:
                if object.ai:
                    object.ai.take_turn()


def main_menu():
    img = libtcod.image_load(MENU_IMG)

    while not libtcod.console_is_window_closed():
        libtcod.image_blit_2x(img, 0, 0, 0)

        libtcod.console_set_default_foreground(0, libtcod.white)
        libtcod.console_set_default_background(0, libtcod.black)
        libtcod.console_print_ex(0, SCREEN_WIDTH / 2, SCREEN_HEIGHT / 2 - 4,
                                 libtcod.BKGND_SET, libtcod.CENTER,
                                 GAME_TITLE)
        libtcod.console_print_ex(0, SCREEN_WIDTH / 2, SCREEN_HEIGHT - 2,
                                 libtcod.BKGND_SET, libtcod.CENTER,
                                 'by usrTaken')

        choice = menu('', '', ['Play a new game', 'Continue last game',
                               'Quit'], 24)

        if choice == 0:
            new_game()
            play_game()
        if choice == 1:
            try:
                load_game()
            except:
                msgbox('Loading Error', '\n No saved game to load.\n', 28)
                continue
            play_game()
        elif choice == 2:
            break


libtcod.console_set_custom_font('cp437_10x10.png',
                                libtcod.FONT_TYPE_GREYSCALE |
                                libtcod.FONT_LAYOUT_ASCII_INROW)

libtcod.console_init_root(SCREEN_WIDTH, SCREEN_HEIGHT, GAME_TITLE + ' ' +
                          GAME_VER, False)

libtcod.sys_set_fps(LIMIT_FPS)


libtcod.console_set_default_foreground(0, con_fore_color)
libtcod.console_set_default_background(0, con_back_color)

mapcon = libtcod.console_new(MAP_WIDTH, MAP_HEIGHT)

lookcon = libtcod.console_new(LOOK_WIDTH, LOOK_HEIGHT)
# libtcod.console_set_default_foreground(lookcon, con_fore_color)
# libtcod.console_set_default_background(lookcon, con_back_color)
# libtcod.console_rect(lookcon, 0, 0, LOOK_WIDTH, LOOK_HEIGHT, True,
#                     libtcod.BKGND_SET)

msgcon = libtcod.console_new(MSG_WIDTH, MSG_HEIGHT)
# libtcod.console_set_default_foreground(msgcon, con_fore_color)
# libtcod.console_set_default_background(msgcon, con_back_color)
# libtcod.console_rect(msgcon, 0, 0, MSG_WIDTH, MSG_HEIGHT, True,
#                     libtcod.BKGND_SET)

infocon = libtcod.console_new(INFO_WIDTH, INFO_HEIGHT)
# libtcod.console_set_default_foreground(infocon, con_fore_color)
# libtcod.console_set_default_background(infocon, con_back_color)
# libtcod.console_rect(infocon, 0, 0, INFO_WIDTH, INFO_HEIGHT, True,
#                     libtcod.BKGND_SET)

debug = libtcod.console_new(40, 50)
# game_splash()
main_menu()
