import libtcodpy as libtcod

from components.fighter import Fighter
from components.inventory import Inventory
from death_functions import kill_monster, kill_player
from entity import Entity, get_blocking_entities_at_location
from fov_functions import initialize_fov, recompute_fov
from game_messages import Message, MessageLog
from game_states import GameStates
from image import take_screenshot
from input_handlers import handle_keys
from map_objects.game_map import GameMap
from render_functions import clear_all, render_all, RenderOrder


def main():
    game_title = 'Quest for the McGuffin'
    game_ver = ' py3_2017.08.17'

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
    max_items_per_room = 2

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
    info_width = 20
    info_height = 50
    info_x = 60
    info_y = 0

    # Interface
    bar_width = 15

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
        'potion': 173,
        'scroll': 19,
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
        'health_pot': libtcod.red,
        'lightning_scroll': libtcod.sky,
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
        'ofov_obj_back': libtcod.darkest_grey,
        'use_inventory': libtcod.azure,
        'drop_inventory': libtcod.red,
        'msg_default': libtcod.white,
        'msg_pickup': libtcod.azure,
        'msg_heal': libtcod.violet,
        'msg_lighning': libtcod.sky,
        'msg_drop': libtcod.crimson,
        'msg_system': libtcod.light_han,
        'msg_error': libtcod.pink,
        'msg_p_dead': libtcod.red,
        'msg_m_dead': libtcod.orange
    }

    fighter_c = Fighter(hp=30, defense=2, power=5)
    inventory_c = Inventory(26)
    player = Entity(0, 0, sprites.get('player'), colors.get('player_fore'),
                    colors.get('player_back'), 'Player', blocks=True,
                    render_ord=RenderOrder.ACTOR, fighter=fighter_c,
                    inventory=inventory_c)
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
                      max_monsters_per_room, max_items_per_room)

    fov_recompute = True

    fov_map = initialize_fov(game_map)

    msg_log = MessageLog(0, msg_width, msg_height)

    key = libtcod.Key()
    mouse = libtcod.Mouse()

    game_state = GameStates.PLAYERS_TURN
    previous_game_state = game_state

    while not libtcod.console_is_window_closed():

        libtcod.sys_check_for_event(libtcod.EVENT_KEY_PRESS |
                                    libtcod.EVENT_MOUSE,
                                    key, mouse)

        if fov_recompute:
            recompute_fov(fov_map, player.x, player.y, fov_r, fov_lw, fov_algo)

#         libtcod.console_flush()
        render_all(mapcon, infocon, lookcon, msgcon, entities, player,
                   game_map, fov_map, fov_r, screen_width, screen_height,
                   info_width, info_height, look_width, look_height, map_width,
                   map_height, msg_width, msg_height, info_x, info_y, look_x,
                   look_y, msg_x, msg_y, msg_log, bar_width, mouse,
                   sprites, colors, game_state)

        fov_recompute = False
        # fill_rects()

        libtcod.console_flush()

        clear_all(mapcon, entities)

        action = handle_keys(key, game_state)

        move = action.get('move')
        pickup = action.get('pickup')
        show_inventory = action.get('show_inventory')
        drop_inventory = action.get('drop_inventory')
        inventory_index = action.get('inventory_index')
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

        elif pickup and game_state == GameStates.PLAYERS_TURN:
            for entity in entities:
                if entity.item and entity.x == player.x and entity.y == player.y:
                    pickup_results = player.inventory.add_item(entity)
                    player_turn_results.extend(pickup_results)

                    break
            else:
                msg_log.add_message(Message(
                    'There is nothing to pick up here.',
                    colors.get('msg_error')
                ))

        if show_inventory:
            previous_game_state = game_state
            game_state = GameStates.SHOW_INVENTORY

        if drop_inventory:
            previous_game_state = game_state
            game_state = GameStates.DROP_INVENTORY

        if (inventory_index is not None and previous_game_state !=
                GameStates.PLAYER_DEAD and inventory_index <
                len(player.inventory.items)):
            item = player.inventory.items[inventory_index]
            if game_state == GameStates.SHOW_INVENTORY:
                player_turn_results.extend(
                    player.inventory.use(
                        item, entities=entities, fov_map=fov_map
                    )
                )
            elif game_state == GameStates.DROP_INVENTORY:
                player_turn_results.extend(player.inventory.drop_item(item))

        if end:
            if game_state in (GameStates.SHOW_INVENTORY,
                              GameStates.DROP_INVENTORY):
                game_state = previous_game_state
            else:
                return True

        if fullscreen:
            libtcod.console_set_fullscreen(not libtcod.console_is_fullscreen())

        if screenshot:
            take_screenshot(f_path, img_path, rn_path, tmp_path)

        for player_turn_result in player_turn_results:
            message = player_turn_result.get('message')
            dead_entity = player_turn_result.get('dead')
            item_added = player_turn_result.get('item_added')
            item_consumed = player_turn_result.get('consumed')
            item_dropped = player_turn_result.get('item_dropped')

            if message:
                msg_log.add_message(message)

            if dead_entity:
                if dead_entity == player:
                    message, game_state = kill_player(dead_entity, sprites,
                                                      colors)
                else:
                    message = kill_monster(dead_entity, sprites, colors)

                msg_log.add_message(message)

            if item_added:
                entities.remove(item_added)

                game_state = GameStates.ENEMY_TURN

            if item_consumed:
                game_state = GameStates.ENEMY_TURN

            if item_dropped:
                entities.append(item_dropped)

                game_state = GameStates.ENEMY_TURN

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
                            msg_log.add_message(message)

                        if dead_entity:
                            if dead_entity == player:
                                message, game_state = kill_player(
                                    dead_entity, sprites, colors)
                            else:
                                message = kill_monster(dead_entity, sprites,
                                                       colors)

                            msg_log.add_message(message)

                            if game_state == GameStates.PLAYER_DEAD:
                                break

                    if game_state == GameStates.PLAYER_DEAD:
                        break

            else:
                game_state = GameStates.PLAYERS_TURN


if __name__ == '__main__':
    main()
