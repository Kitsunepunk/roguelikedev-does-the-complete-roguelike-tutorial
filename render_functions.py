import libtcodpy as libtcod


def render_all(mapcon, entities, sw, sh, lfw, mfh, lfh, msgfh, mcw, mch):

    libtcod.console_rect(0, 0, 0, sw, sh, False,
                         libtcod.BKGND_SET)
    libtcod.console_print_frame(0, 0, 0, lfw, mfh, False,
                                libtcod.BKGND_SET, 'Map')
    libtcod.console_print_frame(0, 0, 40, lfw, lfh, False,
                                libtcod.BKGND_SET, 'Look')
    libtcod.console_print_frame(0, 0, 43, lfw, msgfh, False,
                                libtcod.BKGND_SET, 'MESSAGE LOG')

    # Draw all entities in the list
    for entity in entities:
        draw_entity(mapcon, entity)

    blit_cons(mapcon, mcw, mch, 1, 1)


def clear_all(mapcon, entities):
    for entity in entities:
        clear_entity(mapcon, entity)


def draw_entity(mapcon, entity):
    libtcod.console_put_char_ex(mapcon, entity.x, entity.y, entity.char,
                                entity.color1, entity.color2)


def clear_entity(mapcon, entity):
    # erase the character that represents this object
    libtcod.console_put_char_ex(mapcon, entity.x, entity.y, ' ', libtcod.black,
                                libtcod.white)


def blit_cons(con, w, h, xdst, ydst):
    libtcod.console_blit(con, 0, 0, w, h, 0, xdst, ydst)
