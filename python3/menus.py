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
