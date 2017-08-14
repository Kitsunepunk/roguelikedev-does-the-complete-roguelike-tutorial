import libtcodpy as libtcod

from components.fighter import Fighter
from death_functions import kill_monster, kill_player
from entity import Entity, get_blocking_entities_at_location
from fov_functions import initialize_fov, recompute_fov
from game_states import GameStates
from image import take_screenshot
from input_handlers import handle_keys
from map_objects.game_map import GameMap
from render_functions import clear_all, render_all, RenderOrder


def main():
    game_title = 'Quest for the McGuffin'
    game_ver = ' py3_2017.08.11'

    # Window
    screen_width = 80
    screen_height = 50

    # Map
    map_width = 60
    map_height = 40

    room_max_size = 10
    room_min_size = 6
    max_rooms = 30

    fov_algo = libtcod.FOV_RESTRICTIVE
    fov_lw = True
    fov_r = 10

    max_monsters_per_room = 3

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

    # Interface
    bar_width = 16

    # Screenshot functions
    f_path = './screenshots'
    img_path = './screenshots/ss_0.png'
    rn_path = './screenshots/ss_%s.png'
    tmp_path = './screenshots/tmp.png'

    # future wall '206'
    sprites = {
        'death': '%',
        'floor': '.',
        'ne_tile': 178,
        'orc': 'o',
        'player': '@',
        'troll': 'T',
        'wall': '#',
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
        'wall_wne': 202
    }

    colors = {
        'death': libtcod.dark_red,
        'orc': libtcod.desaturated_green,
        'player_fore': libtcod.black,
        'player_back': libtcod.green,
        'troll': libtcod.darker_green,
        'dark_wall': libtcod.darker_grey,
        'light_wall': libtcod.light_sepia,
        'dark_ground': libtcod.dark_grey,
        'light_ground': libtcod.lighter_sepia,
        'tile_back': libtcod.black,
        'ofov_tile_back': libtcod.darkest_grey,
        'obj_back': libtcod.black,
        'ofov_obj_back': libtcod.darkest_grey
    }

    fighter_c = Fighter(hp=30, defense=2, power=5)
    player = Entity(0, 0, sprites.get('player'), colors.get('player_fore'),
                    colors.get('player_back'), 'Player', blocks=True,
                    render_ord=RenderOrder.ACTOR, fighter=fighter_c)
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
    game_map.make_map(max_rooms, room_min_size, room_max_size, map_width,
                      map_height, player, entities, sprites, colors,
                      max_monsters_per_room)

    fov_recompute = True

    fov_map = initialize_fov(game_map)

    key = libtcod.Key()
    mouse = libtcod.Mouse()

    game_state = GameStates.PLAYERS_TURN

    while not libtcod.console_is_window_closed():

        libtcod.sys_check_for_event(libtcod.EVENT_KEY_PRESS, key, mouse)

        if fov_recompute:
            recompute_fov(fov_map, player.x, player.y, fov_r, fov_lw, fov_algo)

        render_all(mapcon, infocon, lookcon, msgcon, entities, player,
                   game_map, fov_map, fov_r, screen_width, screen_height,
                   info_width, info_height, look_width, look_height, map_width,
                   map_height, msg_width, msg_height, info_x, info_y, look_x,
                   look_y, msg_x, msg_y, sprites, colors)

        fov_recompute = False
        # fill_rects()

        libtcod.console_flush()

        clear_all(mapcon, entities)

        action = handle_keys(key)

        move = action.get('move')
        end = action.get('exit')
        fullscreen = action.get('fullscreen')
        screenshot = action.get('screenshot')

        player_turn_results = []

        if move and game_state == GameStates.PLAYERS_TURN:
            dx, dy = move
            destination_x = player.x + dx
            destination_y = player.y + dy
            if not game_map.is_blocked(destination_x, destination_y):
                target = get_blocking_entities_at_location(entities,
                                                           destination_x,
                                                           destination_y)
                if target:
                    attack_results = player.fighter.attack(target)
                    player_turn_results.extend(attack_results)
                else:
                    player.move(dx, dy)

                    fov_recompute = True

                game_state = GameStates.ENEMY_TURN

        if end:
            return True

        if fullscreen:
            libtcod.console_set_fullscreen(not libtcod.console_is_fullscreen())

        if screenshot:
            take_screenshot(f_path, img_path, rn_path, tmp_path)

        for player_turn_result in player_turn_results:
            message = player_turn_result.get('message')
            dead_entity = player_turn_result.get('dead')

            if message:
                print(message)

            if dead_entity:
                if dead_entity == player:
                    message, game_state = kill_player(dead_entity, sprites,
                                                      colors)
                else:
                    message = kill_monster(dead_entity, sprites, colors)

                print(message)

        if game_state == GameStates.ENEMY_TURN:
            for entity in entities:
                if entity.ai:
                    enemy_turn_results = entity.ai.take_turn(player, fov_map,
                                                             game_map, entities
                                                             )

                    for enemy_turn_result in enemy_turn_results:
                        message = enemy_turn_result.get('message')
                        dead_entity = enemy_turn_result.get('dead')

                        if message:
                            print(message)

                        if dead_entity:
                            if dead_entity == player:
                                message, game_state = kill_player(
                                    dead_entity, sprites, colors)
                            else:
                                message = kill_monster(dead_entity, sprites,
                                                       colors)

                            print(message)

                            if game_state == GameStates.PLAYER_DEAD:
                                break
                    
                    if game_state == GameStates.PLAYER_DEAD:
                        break

            else:
                game_state = GameStates.PLAYERS_TURN


if __name__ == '__main__':
    main()
