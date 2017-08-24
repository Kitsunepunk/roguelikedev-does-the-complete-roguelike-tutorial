import libtcodpy as libtcod


def menu(con, title, header, options, width, sw, sh, color):
    if len(options) > 26:
        raise ValueError('Cannot have a menu with more than 26 options.')

    # calculate total height for the header (after auto-wrap) and one line/option
    if header == '':
        header_height = 0
    else:
        header_height = libtcod.console_get_height_rect(
            con, 0, 0, width, sh, header
        )
    height = len(options) + header_height + 4

    #create an offscreen console that represents the menu's window
    menucon = libtcod.console_new(width, height)

    # print the header, with auto-wrap
    libtcod.console_set_default_foreground(menucon, libtcod.white)

    if header != '':
        libtcod.console_set_default_background(menucon, color)
        libtcod.console_print_frame(
            menucon, 0, 0, width, height, True, libtcod.BKGND_SET, title
        )
        libtcod.console_hline(
            menucon, 1, 3, width - 2, libtcod.BKGND_SET,
        )
        libtcod.console_print_rect_ex(
            menucon, 1, 1, width, height, libtcod.BKGND_SET, libtcod.LEFT,
            header
        )
    else:
        libtcod.console_print_rect_ex(
            menucon, 1, 1, width, height, libtcod.BKGND_SET, libtcod.LEFT,
            header
        )

    y = header_height + 2
    letter_index = ord('a')
    for option_text in options:
        text = '(' + chr(letter_index) + ') ' + option_text
        libtcod.console_print_ex(
            menucon, 1, y, libtcod.BKGND_SET, libtcod.LEFT, text
        )
        y += 1
        letter_index += 1

    x = int(sw / 2 - width / 2)
    y = int(sh / 2 - height / 2)
    libtcod.console_blit(
        menucon, 0, 0, width, height, 0, x, y, 1.0, 0.7
    )


def inventory_menu(con, title, header, inventory, inventory_w, sw, sh, color):
    # show a menu with each item of the inventory as an option
    if len(inventory.items) == 0:
        options = ['Inventory is empty.']
    else:
        options = [item.name for item in inventory.items]

    menu(con, title, header, options, inventory_w, sw, sh, color)


def main_menu(con, background_img, screen_width, screen_height):
    libtcod.image_blit_2x(background_img, 0, 0, 0)

    libtcod.console_set_default_foreground(0, libtcod.light_yellow)
    libtcod.console_print_ex(
        0, int(screen_width / 2), int(screen_height / 2) - 5,
        libtcod.BKGND_NONE, libtcod.CENTER, 'McGuffin Quest'
    )
    libtcod.console_print_ex(
        0, int(screen_width / 2), int(screen_height - 2), libtcod.BKGND_NONE,
        libtcod.CENTER, 'By usrTaken'
    )

    menu(con, '', '', ['Play a new game', 'Continue last Game', 'Options',
                       'Quit'],
         24, screen_width, screen_height, libtcod.black)


def level_up_menu(con, header, player, menu_width, sw, sh):

    options = [
        'Constitution (+20 hp, from {0})'.format(player.fighter.max_hp),
        'Strength (+1 hp, from {0})'.format(player.fighter.power),
        'Agility (+1 hp, from {0})'.format(player.fighter.defense)
    ]
    menu(con, 'Level Up', header, options, menu_width, sw, sh,
         libtcod.dark_green)


def character_screen(title, player, char_sw, char_sh, sw, sh, color):
    window = libtcod.console_new(char_sw, char_sh)

    libtcod.console_set_default_foreground(window, libtcod.white)
    libtcod.console_set_default_background(window, color)

    libtcod.console_print_frame(window, 0, 0, char_sw, char_sh, True,
                                libtcod.BKGND_SET, title)
    libtcod.console_print_rect_ex(window, 2, 2, char_sw, char_sh,
                                  libtcod.BKGND_NONE, libtcod.LEFT,
                                  'Level: {0}'.format(
                                      player.level.current_lvl
                                  ))
    libtcod.console_print_rect_ex(window, 2, 4, char_sw, char_sh,
                                  libtcod.BKGND_NONE, libtcod.LEFT,
                                  'Experience: {0}'.format(
                                      player.level.current_xp
                                  ))
    libtcod.console_print_rect_ex(window, 2, 5, char_sw, char_sh,
                                  libtcod.BKGND_NONE, libtcod.LEFT,
                                  'Experience to next Level: {0}'.format(
                                      player.level.experience_to_next_lvl
                                  ))

    x = sw // 2 - char_sw // 2
    y = sh // 2 - char_sh // 2
    libtcod.console_blit(window, 0, 0, char_sw, char_sh, 0, x, y, 1.0, 0.7)


def help_screen(title, help_w, help_h, sw, sh, col1, col2, col3, col4):
    window = libtcod.console_new(help_w, help_h)

    libtcod.console_set_default_foreground(window, col2)
    libtcod.console_set_default_background(window, col1)
    libtcod.console_print_frame(window, 0, 0, help_w, help_h, True,
                                libtcod.BKGND_SET, title)

    libtcod.console_set_default_foreground(window, col1)
    libtcod.console_set_default_background(window, col2)

    libtcod.console_set_default_foreground(window, col1)
    libtcod.console_set_default_background(window, col3)
    libtcod.console_hline(window, 1, 1, help_w - 2, libtcod.BKGND_SET)
    libtcod.console_print_rect_ex(window, int(help_w / 2), 2,
                                  help_w, 1, libtcod.BKGND_SET,
                                  libtcod.CENTER,
                                  '                     ' +
                                  'Controls' +
                                  '                     ')
    libtcod.console_print_rect_ex(window, 1, 4, help_w, 1, libtcod.BKGND_SET,
                                  libtcod.LEFT, '  '+'Movement'+'  ')
    libtcod.console_vline(window, 13, 4, 1, libtcod.BKGND_SET)
    libtcod.console_print_rect_ex(window, 14, 4, help_w, 1, libtcod.BKGND_SET,
                                  libtcod.LEFT, ' '+'Abilities'+'  ')
    libtcod.console_vline(window, 26, 4, 1, libtcod.BKGND_SET)

    libtcod.console_print_rect_ex(window, 27, 4, help_w, 1, libtcod.BKGND_SET,
                                  libtcod.LEFT, ' '+'Interface'+'  ')
    libtcod.console_vline(window, 39, 4, 1, libtcod.BKGND_SET)
    libtcod.console_print_rect_ex(window, 40, 4, help_w, 1, libtcod.BKGND_SET,
                                  libtcod.LEFT, '   '+'Misc.'+'   ')

    libtcod.console_hline(window, 1, 3, help_w - 2, libtcod.BKGND_SET)
    libtcod.console_hline(window, 1, 5, help_w - 2, libtcod.BKGND_SET)

    libtcod.console_set_default_foreground(window, col2)
    libtcod.console_set_default_background(window, col1)
    libtcod.console_print_rect_ex(window, 2, 6, help_w, 1, libtcod.BKGND_SET,
                                  libtcod.LEFT, 'Up: ')
    libtcod.console_print_rect_ex(window, 2, 9, help_w, 1, libtcod.BKGND_SET,
                                  libtcod.LEFT, 'Down  : ')
    libtcod.console_print_rect_ex(window, 2, 12, help_w, 1, libtcod.BKGND_SET,
                                  libtcod.LEFT, 'Left  : ')
    libtcod.console_print_rect_ex(window, 2, 15, help_w, 1, libtcod.BKGND_SET,
                                  libtcod.LEFT, 'Right : ')
    libtcod.console_print_rect_ex(window, 2, 18, help_w, 1, libtcod.BKGND_SET,
                                  libtcod.LEFT, 'Daig.U.L.: ')
    libtcod.console_print_rect_ex(window, 2, 21, help_w, 1, libtcod.BKGND_SET,
                                  libtcod.LEFT, 'Daig.U.R.: ')
    libtcod.console_print_rect_ex(window, 2, 24, help_w, 1, libtcod.BKGND_SET,
                                  libtcod.LEFT, 'Daig.D.L.: ')
    libtcod.console_print_rect_ex(window, 2, 27, help_w, 1, libtcod.BKGND_SET,
                                  libtcod.LEFT, 'Daig.D.R.: ')
    libtcod.console_print_rect_ex(window, 2, 30, help_w, 1, libtcod.BKGND_SET,
                                  libtcod.LEFT, 'Pass : ')

    libtcod.console_print_rect_ex(window, 15, 6, help_w, 1, libtcod.BKGND_SET,
                                  libtcod.LEFT, 'Pick Up: ')
    libtcod.console_print_rect_ex(window, 15, 9, help_w, 1, libtcod.BKGND_SET,
                                  libtcod.LEFT, 'Use Item: ')
    libtcod.console_print_rect_ex(window, 15, 12, help_w, 1, libtcod.BKGND_SET,
                                  libtcod.LEFT, 'Drop Item: ')
    libtcod.console_print_rect_ex(window, 15, 15, help_w, 1, libtcod.BKGND_SET,
                                  libtcod.LEFT, 'Use Stairs:')
    libtcod.console_print_rect_ex(window, 15, 18, help_w, 1, libtcod.BKGND_SET,
                                  libtcod.LEFT, 'Char. Info:')
    libtcod.console_print_rect_ex(window, 15, 21, help_w, 1, libtcod.BKGND_SET,
                                  libtcod.LEFT, 'Use Spell:')

    libtcod.console_print_rect_ex(window, 28, 6, 10, 12, libtcod.BKGND_SET,
                                  libtcod.LEFT, 'Menu Selection: ')
    libtcod.console_print_rect_ex(window, 28, 11, 10, 2, libtcod.BKGND_SET,
                                  libtcod.LEFT, 'Close Menu:')
    libtcod.console_print_rect_ex(window, 28, 15, 10, 2, libtcod.BKGND_SET,
                                  libtcod.LEFT, 'Spell Cancel: ')
    libtcod.console_print_rect_ex(window, 28, 21, 10, 2, libtcod.BKGND_SET,
                                  libtcod.LEFT, 'Save Game: ')

    libtcod.console_print_rect_ex(window, 41, 6, 10, 12, libtcod.BKGND_SET,
                                  libtcod.LEFT, 'Screen Shot:')

    libtcod.console_print_rect_ex(window, 41, 10, 10, 12, libtcod.BKGND_SET,
                                  libtcod.LEFT, 'Help:')

    # libtcod.console_vline(window, 13, 4, 1, libtcod.BKGND_SET)
    libtcod.console_vline(window, 13, 6, 27, libtcod.BKGND_SET)
    libtcod.console_vline(window, 26, 6, 19, libtcod.BKGND_SET)
    libtcod.console_vline(window, 39, 6, 19, libtcod.BKGND_SET)

    libtcod.console_hline(window, 14, 25, 37, libtcod.BKGND_SET)

    libtcod.console_set_default_foreground(window, col3)
    libtcod.console_print_rect_ex(window, 2, 7, help_w, 1, libtcod.BKGND_SET,
                                  libtcod.LEFT, '{0}, {1}, {2}'.format(
                                      chr(24), 'NP_8', 'k'))

    libtcod.console_print_rect_ex(window, 2, 10, help_w, 1, libtcod.BKGND_SET,
                                  libtcod.LEFT, '{0}, {1}, {2}'.format(
                                      chr(25), 'NP_2', 'j'))

    libtcod.console_print_rect_ex(window, 2, 13, help_w, 1, libtcod.BKGND_SET,
                                  libtcod.LEFT, '{0}, {1}, {2}'.format(
                                      chr(27), 'NP_4', 'h'))

    libtcod.console_print_rect_ex(window, 2, 16, help_w, 1, libtcod.BKGND_SET,
                                  libtcod.LEFT, '{0}, {1}, {2}'.format(
                                      chr(26), 'NP_6', 'l'))

    libtcod.console_print_rect_ex(window, 2, 19, help_w, 1, libtcod.BKGND_SET,
                                  libtcod.LEFT, '{0}, {1}'.format(
                                      'NP_7', 'y'))

    libtcod.console_print_rect_ex(window, 2, 22, help_w, 1, libtcod.BKGND_SET,
                                  libtcod.LEFT, '{0}, {1}'.format(
                                      'NP_9', 'u'))

    libtcod.console_print_rect_ex(window, 2, 25, help_w, 1, libtcod.BKGND_SET,
                                  libtcod.LEFT, '{0}, {1}'.format(
                                      'NP_1', 'b'))

    libtcod.console_print_rect_ex(window, 2, 28, help_w, 1, libtcod.BKGND_SET,
                                  libtcod.LEFT, '{0}, {1}'.format(
                                      'NP_3', 'n'))

    libtcod.console_print_rect_ex(window, 2, 31, help_w, 1, libtcod.BKGND_SET,
                                  libtcod.LEFT, '{0}, {1}'.format(
                                      'NP_5', 'z'))

    libtcod.console_print_rect_ex(window, 15, 7, help_w, 1, libtcod.BKGND_SET,
                                  libtcod.LEFT, '{0}'.format('g'))

    libtcod.console_print_rect_ex(window, 15, 10, help_w, 1, libtcod.BKGND_SET,
                                  libtcod.LEFT, '{0}'.format(
                                      'i'))

    libtcod.console_print_rect_ex(window, 15, 13, help_w, 1, libtcod.BKGND_SET,
                                  libtcod.LEFT, '{0}'.format(
                                      'd'))

    libtcod.console_print_rect_ex(window, 15, 16, help_w, 1, libtcod.BKGND_SET,
                                  libtcod.LEFT, '{0}'.format(
                                      'Enter'))

    libtcod.console_print_rect_ex(window, 15, 19, help_w, 1, libtcod.BKGND_SET,
                                  libtcod.LEFT, '{0}'.format(
                                      'c'))

    libtcod.console_print_rect_ex(window, 15, 22, 10, 2, libtcod.BKGND_SET,
                                  libtcod.LEFT, '{0}'.format(
                                      'Left Mouse button'))

    libtcod.console_print_rect_ex(window, 28, 8, 10, 4, libtcod.BKGND_SET,
                                  libtcod.LEFT, '{0}'.format(
                                      '"a, b, c, etc"'))

    libtcod.console_print_rect_ex(window, 28, 13, help_w, 1, libtcod.BKGND_SET,
                                  libtcod.LEFT, '{0}'.format(
                                      'Esc/Escape'))

    libtcod.console_print_rect_ex(window, 28, 17, 10, 3, libtcod.BKGND_SET,
                                  libtcod.LEFT, '{0}'.format(
                                      'Right Mouse button'))

    libtcod.console_print_rect_ex(window, 28, 22, 10, 2, libtcod.BKGND_SET,
                                  libtcod.LEFT, '{0}'.format(
                                      'w'))

    libtcod.console_print_rect_ex(window, 41, 8, 10, 4, libtcod.BKGND_SET,
                                  libtcod.LEFT, '{0}'.format(
                                      'F1'))

    libtcod.console_print_rect_ex(window, 41, 11, 10, 4, libtcod.BKGND_SET,
                                  libtcod.LEFT, '{0}'.format(
                                      'F2'))

    x = sw // 2 - help_w // 2
    y = sh // 2 - help_h // 2
    libtcod.console_blit(window, 0, 0, help_w, help_h, 0, x, y, 1.0, 0.8)


def msg_box(con, title, header, width, sw, sh, color):
    menu(con, title, header, [], width, sw, sh, color)


def help_header(con, x, y, w, col1, col2):

    libtcod.console_set_default_foreground(con, col2)
    libtcod.console_set_default_background(con, col1)

    libtcod.console_print_rect_ex(window, int(w / 2), y,
                                  help_w, 1, libtcod.BKGND_SET,
                                  libtcod.CENTER, 'Controls')
    libtcod.console_print_rect_ex(window, x, y + 2, w, 1, libtcod.BKGND_SET,
                                  libtcod.LEFT, 'Movement')
