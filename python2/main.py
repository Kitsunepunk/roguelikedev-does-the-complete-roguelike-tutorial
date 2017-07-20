import libtcodpy as libtcod
import math
import textwrap

# game constants
GAME_TITLE = 'Quest of the McGuffin'
GAME_VER = '2017.07.19'

# actual size of the window
SCREEN_WIDTH = 80
SCREEN_HEIGHT = 50

CAM_WIDTH = 58
CAM_HEIGHT = 38

# size of the map
MAP_MIN_SIZE = 70
MAP_MAX_SIZE = 100
MAP_WIDTH = 100  # libtcod.random_get_int(0, MAP_MIN_SIZE, MAP_MAX_SIZE)
MAP_HEIGHT = 100  # libtcod.random_get_int(0, MAP_MIN_SIZE, MAP_MAX_SIZE)

# parameters for dungeon generator
ROOM_MAX_SIZE = 10
ROOM_MIN_SIZE = 6
MAX_ROOMS = 30
MAX_ROOM_MONSTERS = 3

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

FOV_ALGO = 0  # libtcod.FOV_PERMISSIVE_1  # default FOV algorithm
FOV_LIGHT_WALLS = True  # light walls or not
TORCH_RADIUS = 10

LIMIT_FPS = 20  # 20 frames-per-second maximum

BAR_WIDTH = 16


con_back_color = libtcod.Color(51, 51, 51)

color_dark_wall = libtcod.darker_grey
color_light_wall = libtcod.amber
color_dark_ground = libtcod.dark_grey
color_light_ground = libtcod.light_amber
color_dark_back = libtcod.darkest_grey

obj_back = libtcod.black
player_color = libtcod.black
player_back = libtcod.green


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
                 fighter=None, ai=None):
        self.x = x
        self.y = y
        self.char = char
        self.name = name
        self.color = color
        self.color2 = color2
        self.blocks = blocks
        self.fighter = fighter
        if self.fighter:  # let the fighter component know who owns it
            self.fighter.owner = self

        self.ai = ai
        if self.ai:  # let the AI component know who wons it
            self.ai.owner = self

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

    def distance_to(self, other):
        # return the distance to another object
        dx = other.x - self.x
        dy = other.y - self.y
        return math.sqrt(dx ** 2 + dy ** 2)

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

    def clear(self):
        if libtcod.map_is_in_fov(fov_map, self.x, self.y):
            (x, y) = to_camera_coordiantes(self.x, self.y)
            if x is not None:
                # erase the character that represents this object
                libtcod.console_put_char_ex(mapcon, x, y, '.',
                                            color_light_ground, libtcod.black)


class Fighter:
    # combat-related properties and methods(monster, player, NPC)
    def __init__(self, hp, defense, power, death_function=None):
        self.max_hp = hp
        self.hp = hp
        self.defense = defense
        self.power = power
        self.death_function = death_function

    def attack(self, target):
        # a simple formula for attack damage
        damage = self.power - target.fighter.defense

        if damage > 0:
            # make the target take some damage
            if self.owner.name != 'Player':
                message(self.owner.name.capitalize() + ' attacks ' +
                        target.name +
                        ' for ' + str(damage) + ' hit points.',
                        self.owner.color)
            else:
                message(self.owner.name.capitalize() + ' attacks ' +
                        target.name + ' for ' + str(damage) + ' hit points.',
                        libtcod.white)
            target.fighter.take_damage(damage)
        else:
            message(self.owner.name.capitalize() + ' atttacks ' + target.name +
                    ' but it has no effect!', self.owner.color)

    def take_damage(self, damage):
        # apply damage if possible
        if damage > 0:
            self.hp -= damage

            if self.hp <= 0:
                self.hp = 0
                function = self.death_function
                if function is not None:
                    function(self.owner)


class BasicMonster:
    # AI for a basic monster.
    def take_turn(self):
        # a basic monster takes its turn. if you can see it, it cn see you
        monster = self.owner
        if libtcod.map_is_in_fov(fov_map, monster.x, monster.y):

            # move towards player if far away
            if monster.distance_to(player) >= 2:
                monster.move_towards(player.x, player.y)

            # close enough, attack! ( if the player is still alive)
            elif player.fighter.hp >= 0:
                monster.fighter.attack(player)


def is_blocked(x, y):
    # first test the map tile
    if map[x][y].blocked:
        return True

    # now check for any blocking objects
    for object in objects:
        if object.blocks and object.x == x and object.y == y:
            return True

    return False


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
    global map, player

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


def place_objects(room):
    # choose random number of monsters
    num_monsters = libtcod.random_get_int(0, 0, MAX_ROOM_MONSTERS)

    for i in range(num_monsters):
        # choose random spot for this monster
        x = libtcod.random_get_int(0, room.x1, room.x2)
        y = libtcod.random_get_int(0, room.y1, room.y2)

        # only place it if the tile is not blocked
        if not is_blocked(x, y):
            # 80% chance of getting an orc
            if libtcod.random_get_int(0, 0, 100) < 80:
                # create an orc
                fighter_component = Fighter(hp=10, defense=0, power=3,
                                            death_function=monster_death)
                ai_component = BasicMonster()
                monster = Object(x, y, 'o', 'Orc', libtcod.desaturated_green,
                                 obj_back, blocks=True,
                                 fighter=fighter_component, ai=ai_component)
            else:
                # create a troll
                fighter_component = Fighter(hp=16, defense=1, power=4,
                                            death_function=monster_death)
                ai_component = BasicMonster()
                monster = Object(x, y, 'T', 'Troll', libtcod.darker_green,
                                 obj_back, blocks=True,
                                 fighter=fighter_component, ai=ai_component)

            objects.append(monster)


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
    libtcod.console_print_ex(con, x + total_width / 2, y, libtcod.BKGND_NONE,
                             libtcod.CENTER, name + ': ' + str(value) + '/' +
                             str(max_value))


def get_names_under_mouse():
    global mouse

    # return a string with the names of all objects under the mouse
    (x, y) = (mouse.cx, mouse.cy)
    (x, y) = (camera_x + x - 1, camera_y + y - 1)

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
    global fov_recompute

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
                            libtcod.console_put_char_ex(mapcon, x, y, '#',
                                                        color_dark_wall,
                                                        color_dark_back)
                        else:
                            libtcod.console_put_char_ex(mapcon, x, y, '.',
                                                        color_dark_ground,
                                                        color_dark_back)
                else:
                    # it's visible
                    if wall:
                        libtcod.console_put_char_ex(mapcon, x, y, '#',
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

    # blit the contents of "con" to the root console
    libtcod.console_blit(mapcon, 0, 0, MAP_WIDTH, MAP_HEIGHT, 0, 1, 1)

    libtcod.console_set_default_foreground(lookcon, libtcod.white)
    libtcod.console_clear(lookcon)
    libtcod.console_print_ex(lookcon, 0, 0, libtcod.BKGND_NONE, libtcod.LEFT,
                             get_names_under_mouse())
                             # ('mp:' + str((mouse.cx, mouse.cy)) +
                             # 'cp+mp:' + str((camera_x + mouse.cx,
                             # camera_y + mouse.cy)) +
                             # 'pp:' +str((player.x, player.y)) + 'cp+pp'
                             # + str((camera_x + player.x, camera_y +
                             #  player.y))
                             # + ' ' + str(libtcod.map_is_in_fov(fov_map,
                             # mouse.cx, mouse.cy)) + ' ' + ))
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
    render_bar(infocon, 1, 1, BAR_WIDTH, 'HP', player.fighter.hp,
               player.fighter.max_hp, libtcod.white, libtcod.light_red,
               libtcod.darker_red)

    libtcod.console_blit(infocon, 0, 0, INFO_WIDTH, INFO_HEIGHT, 0, 61, 1)


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


def handle_keys():
    # key = libtcod.console_check_for_keypress()  # real-time
    # key = libtcod.console_wait_for_keypress(True)  # turn-based

    if key.vk == libtcod.KEY_ENTER and key.lalt:
        # Alt+Enter: toggle fullscreen
        libtcod.console_set_fullscreen(not libtcod.console_is_fullscreen())

    elif key.vk == libtcod.KEY_ESCAPE:
        return 'exit'  # exit game

    if game_state == 'playing':
        # movement keys
        if libtcod.console_is_key_pressed(libtcod.KEY_UP):
            player_move_or_attack(0, -1)

        elif libtcod.console_is_key_pressed(libtcod.KEY_DOWN):
            player_move_or_attack(0, 1)

        elif libtcod.console_is_key_pressed(libtcod.KEY_LEFT):
            player_move_or_attack(-1, 0)

        elif libtcod.console_is_key_pressed(libtcod.KEY_RIGHT):
            player_move_or_attack(1, 0)

        else:
            return 'didnt-take-turn'


def player_death(player):
    # the game ended!
    global game_state
    message('You DIED!', libtcod.red)
    game_state = 'dead'

    # for added effect, transform the player into a corpse
    player.char = '%'
    player.color = libtcod.dark_red
    player.color2 = libtcod.black


def monster_death(monster):
    # transform it into a nasty corpse! it doesn't block, can't be
    # attacked and doesn't move

    message(monster.name.capitalize() + ' is dead', libtcod.orange)
    monster.char = '%'
    monster.color = libtcod.dark_red
    monster.blocks = False
    monster.fighter = None
    monster.ai = None
    monster.name = 'remains of ' + monster.name
    monster.send_to_back()


#############################################
# Initialization & Main Loop
#############################################

libtcod.console_set_custom_font('cp437_12x12.png',
                                libtcod.FONT_TYPE_GREYSCALE |
                                libtcod.FONT_LAYOUT_ASCII_INROW)
libtcod.console_init_root(SCREEN_WIDTH, SCREEN_HEIGHT, GAME_TITLE + ' ' +
                          GAME_VER, False)
libtcod.sys_set_fps(LIMIT_FPS)

libtcod.console_set_default_foreground(0, libtcod.white)
libtcod.console_set_default_background(0, libtcod.Color(51, 51, 51))

libtcod.console_rect(0, 0, 0, SCREEN_WIDTH, SCREEN_HEIGHT, False,
                     libtcod.BKGND_SET)
libtcod.console_print_frame(0, 0, 0, LEFT_F_WIDTH, MAP_F_HEIGHT,
                            False, libtcod.BKGND_SET, 'MAP')
libtcod.console_print_frame(0, 0, 40, LEFT_F_WIDTH, LOOK_F_HEIGHT, False,
                            libtcod.BKGND_SET, 'LOOK')
libtcod.console_print_frame(0, 0, 43, LEFT_F_WIDTH, MSG_F_HEIGHT, False,
                            libtcod.BKGND_SET, 'MESSAGE LOG')
libtcod.console_print_frame(0, 60, 0, 20, 50, False, libtcod.BKGND_SET,
                            'PLAYER')


mapcon = libtcod.console_new(CAM_WIDTH, CAM_HEIGHT)

lookcon = libtcod.console_new(LOOK_WIDTH, LOOK_HEIGHT)
libtcod.console_set_default_foreground(lookcon, libtcod.Color(255, 255, 255))
libtcod.console_set_default_background(lookcon, libtcod.Color(51, 51, 51))
libtcod.console_rect(lookcon, 0, 0, LOOK_WIDTH, LOOK_HEIGHT, True,
                     libtcod.BKGND_SET)

msgcon = libtcod.console_new(MSG_WIDTH, MSG_HEIGHT)
libtcod.console_set_default_foreground(msgcon, libtcod.Color(255, 255, 255))
libtcod.console_set_default_background(msgcon, libtcod.Color(51, 0, 51))
libtcod.console_rect(msgcon, 0, 0, MSG_WIDTH, MSG_HEIGHT, True,
                     libtcod.BKGND_SET)

infocon = libtcod.console_new(INFO_WIDTH, INFO_HEIGHT)
libtcod.console_set_default_foreground(infocon, libtcod.Color(255, 255, 255))
libtcod.console_set_default_background(infocon, libtcod.Color(51, 51, 51))
libtcod.console_rect(infocon, 0, 0, INFO_WIDTH, INFO_HEIGHT, True,
                     libtcod.BKGND_SET)

# create object representing the player
fighter_component = Fighter(hp=30, defense=2, power=5,
                            death_function=player_death)
player = Object(0, 0, '@', 'Player', player_color, player_back, blocks=True,
                fighter=fighter_component)

# the list of objects with just the player
objects = [player]

# generate map (at this point it's not drawn to the screen)
make_map()

# create the FOV map, according to the generated map
fov_map = libtcod.map_new(MAP_WIDTH, MAP_HEIGHT)
for y in range(MAP_HEIGHT):
    for x in range(MAP_WIDTH):
        libtcod.map_set_properties(fov_map, x, y, not map[x][y].block_sight,
                                   not map[x][y].blocked)

fov_recompute = True
game_state = 'playing'
player_action = None

game_msgs = []

message('Your village is in danger find the McGuffin to save it!' +
        ' If you can...')

mouse = libtcod.Mouse()
key = libtcod.Key()

(camera_x, camera_y) = (0, 0)

while not libtcod.console_is_window_closed():

    libtcod.sys_check_for_event(libtcod.EVENT_KEY_PRESS | libtcod.EVENT_MOUSE,
                                key, mouse)

    # render the screen
    render_all()

    libtcod.console_flush()

    # erase all objects at their old locations, before they move
    for object in objects:
        object.clear()

    # handle keys and exit game if needed
    player_action = handle_keys()
    if player_action == 'exit':
        break

    # let monsters take their turn
    if game_state == 'playing' and player_action != 'didnt-take-turn':
        for object in objects:
            if object.ai:
                object.ai.take_turn()
