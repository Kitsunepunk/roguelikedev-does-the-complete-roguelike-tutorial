import libtcodpy as libtcod

from entity import Entity
from input_handlers import handle_keys
from map_objects.game_map import GameMap
from render_functions import clear_all, render_all

def main():
    game_title = 'Quest for the McGuffin'
    game_ver = ' py3_2017.08.08'

    # Window
    screen_width = 80
    screen_height = 50

    # Map
    map_width = 60
    map_height = 40

    # Look
    look_width = 58
    look_height = 1
    look_x = 1
    look_y = 41

    # Message Log
    msg_width = 58
    msg_height = 5
    msg_x = 1
    msg_y = 44

    # Information Pane
    info_width = 18
    info_height = 48
    info_x = 61
    info_y = 1

    sprites = {
        'player': '@',
        'wall': 206,
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
        'wall_wne': 202,
        'floor': '.'
    }

    colors = {
        'player_fore': libtcod.black,
        'player_back': libtcod.green,
        'dark_wall': libtcod.Color(190, 170, 140),
        'dark_ground': libtcod.Color(50, 50, 150),
        'tile_back': libtcod.black,
        'obj_back': libtcod.black
    }

    player = Entity(int(map_width / 2), int(map_width / 2), 210,
                    colors.get('player_fore'), colors.get('player_back'))
    entities = [player]

    libtcod.console_set_custom_font('cp437_8x8.png',
                                    libtcod.FONT_TYPE_GREYSCALE |
                                    libtcod.FONT_LAYOUT_ASCII_INROW)

    libtcod.console_init_root(screen_width, screen_height, game_title +
                              game_ver, False)

    mapcon = libtcod.console_new(map_width, map_height)
    infocon = libtcod.console_new(info_width, info_height)
    msgcon = libtcod.console_new(msg_width, msg_height)
    lookcon = libtcod.console_new(look_width, look_height)

    game_map = GameMap(map_width, map_height)

    key = libtcod.Key()
    mouse = libtcod.Mouse()

    while not libtcod.console_is_window_closed():

        libtcod.sys_check_for_event(libtcod.EVENT_KEY_PRESS, key, mouse)

        render_all(mapcon, infocon, lookcon, msgcon, entities, game_map,
                   screen_width, screen_height, info_width, info_height,
                   look_width, look_height, map_width, map_height, msg_width,
                   msg_height, info_x, info_y, look_x, look_y, msg_x, msg_y,
                   sprites, colors)

        # fill_rects()

        libtcod.console_flush()

        clear_all(mapcon, entities)

        action = handle_keys(key)

        move = action.get('move')
        end = action.get('exit')
        fullscreen = action.get('fullscreen')

        if move:
            dx, dy = move
            if not game_map.is_blocked(player.x + dx, player.y + dy):
                player.move(dx, dy)

        if end:
            return True

        if fullscreen:
            libtcod.console_set_fullscreen(not libtcod.console_is_fullscreen())


if __name__ == '__main__':
    main()
