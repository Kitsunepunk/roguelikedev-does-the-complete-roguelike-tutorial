import libtcodpy as libtcod


def render_all(con0, con1, con2, con3, entities, game_map, sw, sh, iw, ih, lw,
               lh, mpw, mph, msw, msh, ix, iy, lx, ly, msx, msy, sprtites,
               colors):

    # Draw all the tiles in the game map
    for y in range(game_map.height):
        for x in range(game_map.width):
            wall = game_map.tiles[x][y].block_sight

            if wall:
                libtcod.console_set_char_background(con0, x, y,
                                                    colors.get('dark_wall'),
                                                    libtcod.BKGND_SET)
            else:
                libtcod.console_put_char_ex(con0, x, y, sprtites.get('floor'),
                                                    colors.get('dark_ground'),
                                                    colors.get('tile_back'))

    # Draw all entities in the list
    for entity in entities:
        draw_entity(con0, entity)

    blit_cons(con0, con1, con2, con3, mpw, mph, iw, ih, ix, iy, lw, lh, lx, ly,
              msw, msh, msx, msy)
    draw_frames(lw, lh, msw, msh, iw, ih)
    fill_rects(con1, con2, con3, lw, lh, iw, ih, msw, msh)


def clear_all(con0, entities):
    for entity in entities:
        clear_entity(con0, entity)


def draw_entity(con0, entity):
    libtcod.console_put_char_ex(con0, entity.x, entity.y, entity.char,
                                entity.fore_color, entity.back_color)


def clear_entity(con0, entity):
    # erase the character taht represents this object
    libtcod.console_put_char_ex(con0, entity.x, entity.y, '.',
                                libtcod.Color(50, 50, 150), libtcod.black)


def blit_cons(con0, con1, con2, con3, mpw, mph, iw, ih, ix, iy, lw, lh, lx, ly,
              msw, msh, msx, msy):
    libtcod.console_blit(con0, 0, 0, mpw, mph, 0, 0, 0)
    libtcod.console_blit(con1, 0, 0, iw, ih, 0, ix, iy)
    libtcod.console_blit(con2, 0, 0, lw, lh, 0, lx, ly)
    libtcod.console_blit(con3, 0, 0, msw, msh, 0, msx, msy)


def draw_frames(lw, lh, msw, msh, iw, ih):
    libtcod.console_print_frame(0, 0, 40, lw + 2, lh + 2,
                                False, libtcod.BKGND_NONE, 'Look')
    libtcod.console_print_frame(0, 0, 43, msw + 2, msh + 2,
                                False, libtcod.BKGND_NONE, 'Message Log')
    libtcod.console_print_frame(0, 60, 0, iw + 2, ih + 2,
                                False, libtcod.BKGND_NONE, 'Information')


def fill_rects(con1, con2, con3, lw, lh, iw, ih, msw, msh):
    libtcod.console_set_default_background(con2, libtcod.light_gray)
    libtcod.console_set_default_background(con3, libtcod.light_azure)
    libtcod.console_set_default_background(con1, libtcod.light_han)
    libtcod.console_rect(con2, 0, 0, lw, lh, True, libtcod.BKGND_SET)
    libtcod.console_rect(con1, 0, 0, iw, ih, True, libtcod.BKGND_SET)
    libtcod.console_rect(con3, 0, 0, msw, msh, True, libtcod.BKGND_SET)


def fix_wall_tiles(self, sprites):

    for i in range(1, game_map.width - 1):
        for j in range(1, game_map.height - 1):
            wall = game_map.tiles[i][j].block_sight

            if game_map.tiles[i][j] == wall:
                north = game_map.tiles[i][j - 1] == wall
                south = game_map.tiles[i][j + 1] == wall
                east = game_map.tiles[i + 1][j] == wall
                west = game_map.tiles[i - 1][j] == wall

                if north and east and south:
