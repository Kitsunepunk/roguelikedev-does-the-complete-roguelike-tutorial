import libtcodpy as libtcod
from enum import Enum

from game_states import GameStates
from menus import character_screen, help_screen, inventory_menu, level_up_menu


class RenderOrder(Enum):
    STAIRS = 1
    CORPSE = 2
    ITEM = 3
    ACTOR = 4


def get_names_under_mouse(mouse, entities, fov_map):
    (x, y) = (mouse.cx, mouse.cy)

    names = [entity.name for entity in entities
             if entity.x == x and entity.y == y and
             libtcod.map_is_in_fov(fov_map, entity.x, entity.y)]
    names = ', '.join(names)

    return names.capitalize()


def render_bar(con, x, y, total_width, name, value, maximum, bf_col,
               b_col):
    bar_width = int(float(value) / maximum * total_width)

    libtcod.console_set_default_background(con, b_col)
    libtcod.console_rect(con, x, y + 1, total_width, 1, False,
                         libtcod.BKGND_SCREEN)

    libtcod.console_set_default_background(con, bf_col)
    if bar_width > 0:
        libtcod.console_rect(con, x, y + 1, bar_width, 1, False,
                             libtcod.BKGND_SCREEN)

    libtcod.console_set_default_foreground(con, libtcod.white)
    libtcod.console_print_ex(con, x, y,
                             libtcod.BKGND_NONE, libtcod.LEFT,
                             '{0}: {1}/{2}'.format(name, value, maximum))


def render_all(con0, con1, con2, con3, entities, player, game_map, fov_map,
               fov_recompute, sw, sh, iw, ih, lw, lh, mpw, mph, msw, msh, ix,
               iy, lx, ly, msx, msy, msg_log, bar_width, mouse,
               sprites, colors, game_state):

    if fov_recompute:
        # Draw all the tiles in the game map
        for y in range(game_map.height):
            for x in range(game_map.width):
                visible = libtcod.map_is_in_fov(fov_map, x, y)
                wall = game_map.tiles[x][y].block_sight

                if visible:
                    if wall:
                        libtcod.console_put_char_ex(con0, x, y,
                                                    sprites.get('wall'),
                                                    colors.get('light_wall'),
                                                    colors.get('tile_back'))
                    else:
                        libtcod.console_put_char_ex(con0, x, y,
                                                    sprites.get('floor'),
                                                    colors.get('light_ground'),
                                                    colors.get('tile_back'))
                    game_map.tiles[x][y].explored = True
                elif game_map.tiles[x][y].explored:
                    if wall:
                        libtcod.console_put_char_ex(con0, x, y,
                                                    sprites.get('wall'),
                                                    colors.get('dark_wall'),
                                                    colors.get('ofov_tile_back'
                                                               ))
                    else:
                        libtcod.console_put_char_ex(con0, x, y,
                                                    sprites.get('floor'),
                                                    colors.get('dark_ground'),
                                                    colors.get('ofov_tile_back'
                                                               ))
                elif not visible:
                    libtcod.console_put_char_ex(con0, x, y,
                                                sprites.get('ne_tile'),
                                                colors.get('tile_back'),
                                                colors.get('ofov_tile_back'))

    # Draw all entities in the list
    entities_in_render_ord = sorted(entities, key=lambda x: x.render_ord.value)
    for entity in entities_in_render_ord:
        draw_entity(con0, entity, fov_map, game_map)

    player_info(con1, game_map, 2, 2, iw, ih, player, bar_width)

    get_look(con2, lw, lh, mouse, entities, fov_map)

    # Print the game messages, one line at a time
    display_msgs(con3, msw, msh, 1, msg_log)

    blit_cons(con0, con1, con2, con3, mpw, mph, iw, ih, ix, iy, lw, lh, lx, ly,
              msw, msh, msx, msy)

    draw_frames(lw, lh, msw, msh, iw, ih)

    if game_state in (GameStates.SHOW_INVENTORY, GameStates.DROP_INVENTORY):
        if game_state == GameStates.SHOW_INVENTORY:
            inventory_title = 'Inventory: Use Menu'
            inventory_header = ('Press the Key next to an item to use it,' +
                                ' or Esc to cancel.\n')
            inventory_col = colors.get('use_inventory')
        else:
            inventory_title = 'Inventory: Drop Menu'
            inventory_header = ('Press the key next to an item to drop it,' +
                                'or Esc to cancel\n')
            inventory_col = colors.get('drop_inventory')
        inventory_menu(
            con0, inventory_title,
            inventory_header,
            player.inventory, 50, sw, sh, inventory_col
        )
    # fill_rects(con1, con2, con3, lw, lh, iw, ih, msw, msh)

    elif game_state == GameStates.LEVEL_UP:
        level_up_menu(con0, 'Choose a Stat to raise:\n ', player, 40, sw, sh)

    elif game_state == GameStates.CHARACTER_SCREEN:
        character_screen('character Screen', player, 30, 10, sw, sh,
                         libtcod.dark_sepia)

    elif game_state == GameStates.GAME_HELP:
        help_screen('Help Screen', 52, 34, sw, sh, libtcod.blue,
                    libtcod.white, libtcod.light_grey, libtcod.yellow)


def clear_all(con0, entities):
    for entity in entities:
        clear_entity(con0, entity)


def draw_entity(con0, entity, fov_map, game_map):
    if libtcod.map_is_in_fov(fov_map, entity.x, entity.y):
        libtcod.console_put_char_ex(con0, entity.x, entity.y, entity.char,
                                    entity.fore_color, entity.back_color)
    elif entity.stairs and game_map.tiles[entity.x][entity.y].explored:
        libtcod.console_put_char_ex(
            con0, entity.x, entity.y, entity.char, entity.fore_color,
            libtcod.darkest_grey
        )


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
    libtcod.console_set_default_foreground(0, libtcod.white)
    libtcod.console_set_default_background(0, libtcod.black)
    libtcod.console_print_frame(0, 0, 40, lw, lh,
                                False, libtcod.BKGND_NONE, 'Look')
    libtcod.console_print_frame(0, 0, 43, msw, msh,
                                False, libtcod.BKGND_NONE, 'Message Log')
    libtcod.console_print_frame(0, 60, 0, iw, ih,
                                False, libtcod.BKGND_NONE, 'Information')


def fill_rects(con1, con2, con3, lw, lh, iw, ih, msw, msh):
    libtcod.console_set_default_background(con2, libtcod.light_gray)
    libtcod.console_set_default_background(con3, libtcod.light_azure)
    libtcod.console_set_default_background(con1, libtcod.light_han)
    libtcod.console_rect(con2, 0, 0, lw, lh, True, libtcod.BKGND_SET)
    libtcod.console_rect(con1, 0, 0, iw, ih, True, libtcod.BKGND_SET)
    libtcod.console_rect(con3, 0, 0, msw, msh, True, libtcod.BKGND_SET)


def player_info(con1, game_map, x, y, iw, ih, player, bar_width):
    libtcod.console_set_default_foreground(con1, libtcod.white)
    libtcod.console_set_default_background(con1, libtcod.black)
    libtcod.console_clear(con1)
    libtcod.console_print_frame(con1, 0, 0, iw, ih, False, libtcod.BKGND_NONE,
                                'Information')
    libtcod.console_print_ex(con1, x, y, libtcod.BKGND_NONE, libtcod.LEFT,
                             player.name)

    render_bar(con1, x, y + 1, bar_width, 'HP', player.fighter.hp,
               player.fighter.max_hp, libtcod.light_red,
               libtcod.darker_red)
    render_bar(con1, x, y + 3, bar_width, 'XP', player.level.current_xp,
               player.level.experience_to_next_lvl, libtcod.light_green,
               libtcod.darker_green)
    libtcod.console_print_ex(con1, x, y + 6, libtcod.BKGND_NONE, libtcod.LEFT,
                             'POW(MOD): {0}({1})'.format(
                                 player.fighter.power,
                                 player.fighter.power))

    libtcod.console_print_ex(con1, x, y + 7, libtcod.BKGND_NONE, libtcod.LEFT,
                             'DEF(MOD): {0}({1})'.format(
                                 player.fighter.defense,
                                 player.fighter.defense))

    libtcod.console_print_ex(con1, x, y + 9, libtcod.BKGND_NONE, libtcod.LEFT,
                             'Dungeon Level: {0}'.format(
                                 str(game_map.dungeon_level)
                             ))

    libtcod.console_hline(con1, x - 1, y + 10, iw - 2, libtcod.BKGND_NONE)

    libtcod.console_print_ex(con1, x, y + 12, libtcod.BKGND_NONE, libtcod.LEFT,
                             'Equipment')

    libtcod.console_hline(con1, x - 1, ih - 8, iw - 2, libtcod.BKGND_NONE)
    libtcod.console_print_ex(con1, x, ih - 6, libtcod.BKGND_NONE, libtcod.LEFT,
                             'Inventory')
    libtcod.console_print_ex(con1, x, ih - 5, libtcod.BKGND_NONE, libtcod.LEFT,
                             'Total Items: {0}'.format(
                                 str(len(player.inventory.items))
                             ))
    libtcod.console_hline(con1, x - 1, ih - 3, iw - 2, libtcod.BKGND_NONE)
    libtcod.console_set_default_foreground(con1, libtcod.desaturated_han)
    libtcod.console_print_ex(con1, x, ih - 2, libtcod.BKGND_NONE, libtcod.LEFT,
                             'Hit F2 for help')


def display_msgs(con3, msw, msh, y, msg_log):
    libtcod.console_clear(con3)
    libtcod.console_print_frame(con3, 0, 43, msw, msh,
                                False, libtcod.BKGND_NONE, 'Message Log')

    y = 1
    colorCoef = 0.4
    for message in msg_log.messages:
        libtcod.console_set_default_foreground(con3, message.color * colorCoef)
        libtcod.console_print_ex(con3, msg_log.x, y, libtcod.BKGND_NONE,
                                 libtcod.LEFT, message.text)
        y += 1
        if colorCoef < 1.0:
            colorCoef += 0.2


def get_look(con2, lw, lh, mouse, entities, fov_map):
    libtcod.console_clear(con2)
    libtcod.console_print_frame(con2, 0, 40, lw, lh,
                                False, libtcod.BKGND_NONE, 'Look')
    libtcod.console_set_default_foreground(con2, libtcod.light_grey)
    libtcod.console_print_ex(con2, 1, 1, libtcod.BKGND_NONE, libtcod.LEFT,
                             get_names_under_mouse(mouse, entities, fov_map))

