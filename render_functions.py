import libtcodpy as libtcod


def render_all(mapcon, entities, game_map, fov_map, fov_recompute, mcw, mch,
               colors):

    if fov_recompute:
        # Draw all the tiles in the game map
        for y in range(game_map.height):
            for x in range(game_map.width):
                visible = libtcod.map_is_in_fov(fov_map, x, y)
                wall = game_map.tiles[x][y].block_sight

                if visible:
                    if wall:
                        libtcod.console_put_char_ex(mapcon, x, y, '#', colors.
                                                    get('light_wall'), colors.
                                                    get('back'))
                    else:
                        libtcod.console_put_char_ex(mapcon, x, y, '.', colors.
                                                    get('light_ground'),
                                                    colors.get('back'))
                    game_map.tiles[x][y].explored = True
                elif game_map.tiles[x][y].explored:
                    if wall:
                        libtcod.console_put_char_ex(mapcon, x, y, '#', colors.
                                                    get('dark_wall'), colors.
                                                    get('back'))
                    else:
                        libtcod.console_put_char_ex(mapcon, x, y, '.', colors.
                                                    get('dark_ground'), colors.
                                                    get('back'))
                elif not visible:
                    libtcod.console_put_char_ex(mapcon, x, y, 176,
                                                libtcod.azure,
                                                libtcod.darkest_grey)

    # Draw all entities in the list
    for entity in entities:
        draw_entity(mapcon, entity, fov_map)

    blit_cons(mapcon, mcw, mch, 1, 1)


def clear_all(mapcon, entities, fov_map):
    for entity in entities:
        clear_entity(mapcon, entity, fov_map)


def draw_entity(mapcon, entity, fov_map):
    if libtcod.map_is_in_fov(fov_map, entity.x, entity.y):
        libtcod.console_put_char_ex(mapcon, entity.x, entity.y, entity.char,
                                    entity.color1, entity.color2)


def clear_entity(mapcon, entity, fov_map):
    if libtcod.map_is_in_fov(fov_map, entity.x, entity.y):
        # erase the character that represents this object
        libtcod.console_put_char_ex(mapcon, entity.x, entity.y, '.', libtcod.black,
                                    libtcod.Color(0, 0, 0))


def blit_cons(con, w, h, xdst, ydst):
    libtcod.console_blit(con, 0, 0, w, h, 0, xdst, ydst)
