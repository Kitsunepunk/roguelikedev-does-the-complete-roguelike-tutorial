import libtcodpy as libtcod

from components.fighter import Fighter
from components.inventory import Inventory
from components.level import Level
from entity import Entity
from game_messages import Message, MessageLog
from game_states import GameStates
from map_objects.game_map import GameMap
from render_functions import RenderOrder


def get_constants():
    game_title = 'McGuffin Quest'
    game_ver = ' py3_2017.08.19'
    window_title = game_title + game_ver

    limit_fps = 20

    # Window
    screen_width = 80
    screen_height = 50

    # Map
    map_width = 60
    map_height = 40

    room_max_size = 10
    room_min_size = 6
    max_rooms = 30

    fov_algo = libtcod.FOV_RESTRICTIVE
    fov_lw = True
    fov_r = 10

    max_monsters_per_room = 3
    max_items_per_room = 2

    # Look
    look_width = 60
    look_height = 3
    look_x = 0
    look_y = 40

    # Message Log
    msg_width = 60
    msg_height = 7
    msg_x = 0
    msg_y = 43

    # Information Pane
    info_width = 20
    info_height = 50
    info_x = 60
    info_y = 0

    # Interface
    bar_width = 16

    # Screenshot functions
    f_path = './screenshots'
    img_path = './screenshots/ss_0.png'
    rn_path = './screenshots/ss_%s.png'
    tmp_path = './screenshots/tmp.png'

    # future wall '206'
    sprites = {
        'death': '%',
        'floor': '.',
        'ne_tile': 178,
        'orc': 'o',
        'player': '@',
        'potion': 173,
        'scroll': 19,
        'd_stairs': 175,
        'troll': 'T',
        'wall': '#',
        'wall_w': 181,
        'wall_e': 198,
        'wall_n': 208,
        'wall_s': 210,
        'wall_we': 205,
        'wall_ns': 186,
        'wall_ne': 200,
        'wall_nw': 188,
        'wall_se': 201,
        'wall_sw': 187,
        'wall_nes': 204,
        'wall_nws': 185,
        'wall_wse': 203,
        'wall_wne': 202
    }

    colors = {
        'confuse': libtcod.light_green,
        'death': libtcod.dark_red,
        'health_pot': libtcod.red,
        'fireball': libtcod.flame,
        'lightning_scroll': libtcod.sky,
        'orc': libtcod.desaturated_green,
        'player_fore': libtcod.black,
        'player_back': libtcod.azure,
        'stairs': libtcod.white,
        'troll': libtcod.darker_green,
        'dark_wall': libtcod.darker_grey,
        'light_wall': libtcod.light_sepia,
        'dark_ground': libtcod.dark_grey,
        'light_ground': libtcod.lighter_sepia,
        'tile_back': libtcod.black,
        'ofov_tile_back': libtcod.darkest_grey,
        'obj_back': libtcod.black,
        'ofov_obj_back': libtcod.darkest_grey,
        'use_inventory': libtcod.azure,
        'drop_inventory': libtcod.red,
        'msg_default': libtcod.white,
        'msg_bad': libtcod.red,
        'msg_pickup': libtcod.azure,
        'msg_heal': libtcod.violet,
        'msg_lighning': libtcod.sky,
        'msg_drop': libtcod.crimson,
        'msg_system': libtcod.light_han,
        'msg_error': libtcod.pink,
        'msg_p_dead': libtcod.red,
        'msg_m_dead': libtcod.orange
    }

    constants = {
        'window_title': window_title,
        'limit_fps': limit_fps,
        'screen_width': screen_width,
        'screen_height': screen_height,
        'bar_width': bar_width,
        'map_width': map_width,
        'map_height': map_height,
        'room_max_size': room_max_size,
        'room_min_size': room_min_size,
        'max_rooms': max_rooms,
        'fov_algo': fov_algo,
        'fov_lw': fov_lw,
        'fov_r': fov_r,
        'max_monsters_per_room': max_monsters_per_room,
        'max_items_per_room': max_items_per_room,
        'look_width': look_width,
        'look_height': look_height,
        'look_x': look_x,
        'look_y': look_y,
        'msg_width': msg_width,
        'msg_height': msg_height,
        'msg_x': msg_x,
        'msg_y': msg_y,
        'info_width': info_width,
        'info_height': info_height,
        'info_x': info_x,
        'info_y':info_y,
        'f_path': f_path,
        'img_path': img_path,
        'rn_path': rn_path,
        'tmp_path': tmp_path,
        'sprites': sprites,
        'colors': colors
    }

    return constants


def get_game_vars(constants):

    fighter_c = Fighter(hp=100, defense=1, power=4)
    inventory_c = Inventory(26)
    level_c = Level()
    player = Entity(0, 0, '@', libtcod.black, libtcod.light_azure, 'Player',
                    blocks=True,
                    render_ord=RenderOrder.ACTOR, fighter=fighter_c,
                    inventory=inventory_c, level=level_c)
    entities = [player]

    game_map = GameMap(constants['map_width'], constants['map_height'])
    game_map.make_map(constants['max_rooms'], constants['room_min_size'],
                      constants['room_max_size'], constants['map_width'],
                      constants['map_height'], player, entities,
                      constants['sprites'], constants['colors'])

    msg_log = MessageLog(1, constants['msg_width'] - 5,
                         constants['msg_height'] - 2)

    msg_log.add_message(Message('test', libtcod.black))
    msg_log.add_message(Message('test', libtcod.black))
    msg_log.add_message(Message('test', libtcod.black))
    msg_log.add_message(Message('test', libtcod.black))
    msg_log.add_message(
        Message(
            'Your village is in danger find the McGuffin to save it!' +
            ' If you can...',
        )
    )

    game_state = GameStates.PLAYERS_TURN

    return player, entities, game_map, msg_log, game_state
