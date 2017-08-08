import libtcodpy as libtcod

from input_handlers import handle_keys

def main():
    game_title = 'Quest for the McGuffin'
    game_ver = ' 2017.08.08'

    # Window
    screen_width = 80
    screen_height = 50
    
    # Map
    map_width = 60
    map_height = 40

    # Look
    look_width = 58
    look_height = 1

    # Message Log
    msg_width = 58
    msg_height = 5

    # Information Pane
    info_width = 18
    info_height = 48

    player_x = int(screen_width / 2)
    player_y = int(screen_height / 2)

    libtcod.console_set_custom_font('cp437_8x8.png', libtcod.FONT_TYPE_GREYSCALE | libtcod.FONT_LAYOUT_ASCII_INROW)

    libtcod.console_init_root(screen_width, screen_height, game_title + game_ver, False)

    mapcon = libtcod.console_new(map_width, map_height)
    infocon = libtcod.console_new(info_width, info_height)
    msgcon = libtcod.console_new(msg_width, msg_height)
    lookcon = libtcod.console_new(look_width, look_height)

    key = libtcod.Key()
    mouse = libtcod.Mouse()

    while not libtcod.console_is_window_closed():

        libtcod.sys_check_for_event(libtcod.EVENT_KEY_PRESS, key, mouse)
        
        libtcod.console_set_default_foreground(0, libtcod.white)
        libtcod.console_put_char(0, player_x, player_y, '@', libtcod.BKGND_NONE)
        libtcod.console_flush()

        action = handle_keys(key)

        move = action.get('move')
        end = action.get('exit')
        fullscreen = action.get('fullscreen')

        if move:
            dx, dy = move
            player_x += dx
            player_y += dy

        if end:
            return True

        if fullscreen:
            libtcod.console_set_fullscreen(not libtcod.console_is_fullscreen())

if __name__ == '__main__':
    main()
