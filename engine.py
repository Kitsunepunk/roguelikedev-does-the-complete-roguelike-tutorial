import libtcodpy as libtcod

from entity import Entity
from input_handlers import handle_keys
from render_functions import clear_all, render_all


def main():

    game_title = 'Quest for the McGuffin'
    game_ver = '2017.07.18'

    screen_width = 80
    screen_height = 50

    map_c_width = 58
    map_c_height = 38
    left_f_width = 60
    map_f_height = 40

    look_f_height = 3

    msg_f_height = 7

    colors = {
        'root_back': libtcod.Color(51, 51, 51),
        'root_fore': libtcod.Color(255, 255, 255),
        'player_fore': libtcod.Color(0, 0, 0),
        'player_back': libtcod.Color(0, 127, 255)
    }

    player = Entity(int(map_c_width / 2), int(map_c_height / 2), '@',
                    colors.get('player_fore'), colors.get('player_back'))
    entities = [player]

    libtcod.console_set_custom_font('terminal12x12_gs_ro.png',
                                    libtcod.FONT_LAYOUT_ASCII_INROW |
                                    libtcod.FONT_TYPE_GREYSCALE)

    libtcod.sys_force_fullscreen_resolution(800, 600)
    libtcod.console_init_root(screen_width, screen_height, game_title + ' ' +
                              game_ver, False)

    libtcod.console_set_default_background(0, colors.get('root_back'))
    libtcod.console_set_default_foreground(0, colors.get('root_fore'))

    mapcon = libtcod.console_new(map_c_width, map_c_height)

    key = libtcod.Key()
    mouse = libtcod.Mouse()

    while not libtcod.console_is_window_closed():

        libtcod.sys_check_for_event(libtcod.EVENT_KEY_PRESS, key, mouse)

        render_all(mapcon, entities, screen_width, screen_height, left_f_width,
                   map_f_height, look_f_height, msg_f_height, map_c_width,
                   map_c_height)

        libtcod.console_flush()

        clear_all(mapcon, entities)

        action = handle_keys(key)

        move = action.get('move')
        exit = action.get('exit')
        fullscreen = action.get('fullscreen')

        if move:
            dx, dy = move
            player.move(dx, dy)

        if exit:
            return True

        if fullscreen:
            libtcod.console_set_fullscreen(not libtcod.console_is_fullscreen())

if __name__ == '__main__':
    main()
