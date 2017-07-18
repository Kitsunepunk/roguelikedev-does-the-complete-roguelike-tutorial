import libtcodpy as libtcod

from entity import Entity
from fov_functions import initialize_fov, recompute_fov
from input_handlers import handle_keys
from map_objects.game_map import GameMap
from render_functions import clear_all, render_all


def main():

    game_title = 'Quest for the McGuffin'
    game_ver = '2017.07.18'

    screen_width = 80
    screen_height = 50

    map_width = 58
    map_height = 38
    map_c_width = 58
    map_c_height = 38
    cam_width = 58
    cam_height = 38
    left_f_width = 60
    map_f_height = 40

    look_f_height = 3

    msg_f_height = 7

    room_max_size = 10
    room_min_size = 6
    max_rooms = 30

    fov_algo = 0
    fov_lightwalls = True
    fov_radius = 10

    colors = {
        'root_back': libtcod.Color(0, 127, 255),
        'root_fore': libtcod.Color(255, 255, 255),
        'player_fore': libtcod.Color(0, 0, 0),
        'player_back': libtcod.Color(127, 255, 0),
        'light_wall': libtcod.Color(130, 110, 50),
        'dark_wall': libtcod.Color(0, 0, 100),
        'light_ground': libtcod.Color(200, 180, 50),
        'dark_ground': libtcod.Color(50, 50, 150),
        'back': libtcod.Color(0, 0, 0)
    }

    player = Entity(int(map_c_width / 2), int(map_c_height / 2), '@',
                    colors.get('player_fore'), colors.get('player_back'))
    entities = [player]

    libtcod.console_set_custom_font('cp437_12x12.png',
                                    libtcod.FONT_LAYOUT_ASCII_INROW |
                                    libtcod.FONT_TYPE_GREYSCALE)

    libtcod.sys_force_fullscreen_resolution(1440, 1080)
    libtcod.console_init_root(screen_width, screen_height, game_title + ' ' +
                              game_ver, False)

    libtcod.console_set_default_background(0, colors.get('root_back'))
    libtcod.console_set_default_foreground(0, colors.get('root_fore'))

    libtcod.console_rect(0, 0, 0, screen_width, screen_height, False,
                         libtcod.BKGND_SET)
    libtcod.console_print_frame(0, 0, 0, left_f_width, map_f_height, False,
                                libtcod.BKGND_SET, 'Map')
    libtcod.console_print_frame(0, 0, 40, left_f_width, look_f_height, False,
                                libtcod.BKGND_SET, 'Look')
    libtcod.console_print_frame(0, 0, 43, left_f_width, msg_f_height, False,
                                libtcod.BKGND_SET, 'MESSAGE LOG')

    mapcon = libtcod.console_new(map_c_width, map_c_height)

    game_map = GameMap(map_width, map_height)
    game_map.make_map(max_rooms, room_min_size, room_max_size, map_width,
                      map_height, player)

    fov_recompute = True

    fov_map = initialize_fov(game_map)

    key = libtcod.Key()
    mouse = libtcod.Mouse()

    while not libtcod.console_is_window_closed():

        libtcod.sys_check_for_event(libtcod.EVENT_KEY_PRESS, key, mouse)

        if fov_recompute:
            recompute_fov(fov_map, player.x, player.y, fov_radius,
                          fov_lightwalls, fov_algo)

        render_all(mapcon, entities, game_map, fov_map, fov_recompute,
                   map_c_width, map_c_height, colors)

        fov_recompute = False

        libtcod.console_flush()

        clear_all(mapcon, entities, fov_map)

        action = handle_keys(key)

        move = action.get('move')
        exit = action.get('exit')
        fullscreen = action.get('fullscreen')

        if move:
            dx, dy = move
            if not game_map.is_blocked(player.x + dx, player.y + dy):
                player.move(dx, dy)
                fov_recompute = True

        if exit:
            return True

        if fullscreen:
            libtcod.console_set_fullscreen(not libtcod.console_is_fullscreen())

if __name__ == '__main__':
    main()
