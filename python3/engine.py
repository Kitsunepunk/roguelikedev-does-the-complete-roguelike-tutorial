import libtcodpy as libtcod

from death_functions import kill_monster, kill_player
from entity import get_blocking_entities_at_location
from fov_functions import initialize_fov, recompute_fov
from game_messages import Message
from game_states import GameStates
from image import take_screenshot
from input_handlers import handle_keys, handle_mouse, handle_main_menu
from loader_fuctions.initialize_new_game import get_constants, get_game_vars
from loader_fuctions.data_loaders import load_game, save_game
from menus import main_menu, msg_box
from render_functions import clear_all, render_all


def play_game(player, entities, game_map, msg_log, game_state, mapcon, infocon,
              lookcon, msgcon, constants):
    """
    The game loop
    """

    fov_recompute = True

    fov_map = initialize_fov(game_map)

    key = libtcod.Key()
    mouse = libtcod.Mouse()

    game_state = GameStates.PLAYERS_TURN
    previous_game_state = game_state

    targeting_item = None

    libtcod.sys_set_fps(constants['limit_fps'])

    while not libtcod.console_is_window_closed():

        libtcod.sys_check_for_event(libtcod.EVENT_KEY_PRESS |
                                    libtcod.EVENT_MOUSE,
                                    key, mouse)

        if fov_recompute:
            recompute_fov(fov_map, player.x, player.y, constants['fov_r'],
                          constants['fov_lw'], constants['fov_algo'])

        render_all(mapcon, infocon, lookcon, msgcon, entities, player,
                   game_map, fov_map,
                   constants['fov_r'], constants['screen_width'],
                   constants['screen_height'], constants['info_width'],
                   constants['info_height'], constants['look_width'],
                   constants['look_height'], constants['map_width'],
                   constants['map_height'], constants['msg_width'],
                   constants['msg_height'], constants['info_x'],
                   constants['info_y'], constants['look_x'],
                   constants['look_y'], constants['msg_x'], constants['msg_y'],
                   msg_log, constants['bar_width'], mouse,
                   constants['sprites'], constants['colors'], game_state)

        fov_recompute = False

        libtcod.console_flush()

        clear_all(mapcon, entities)

        action = handle_keys(key, game_state)
        mouse_action = handle_mouse(mouse)

        move = action.get('move')
        wait = action.get('wait')
        pickup = action.get('pickup')
        show_inventory = action.get('show_inventory')
        drop_inventory = action.get('drop_inventory')
        inventory_index = action.get('inventory_index')
        take_stairs = action.get('take_stairs')
        level_up = action.get('level_up')
        show_character_screen = action.get('show_character_screen')
        end = action.get('exit')
        fullscreen = action.get('fullscreen')
        screenshot = action.get('screenshot')
        game_help = action.get('help')

        left_click = mouse_action.get('left_click')
        right_click = mouse_action.get('right_click')

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

        elif wait:
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
                    libtcod.pink
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

        if take_stairs and game_state == GameStates.PLAYERS_TURN:
            for entity in entities:
                if (entity.stairs and entity.x == player.x and
                        entity.y == player.y):
                    entities = game_map.next_floor(player, msg_log, constants)
                    fov_map = initialize_fov(game_map)
                    fov_recompute = True
                    libtcod.console_clear(mapcon)

                    break
            else:
                msg_log.add_message(Message('There are no stairs here',
                                            libtcod.pink))

        if level_up:
            if level_up == 'hp':
                player.fighter.max_hp += 20
                player.fighter.hp += 20
            elif level_up == 'str':
                player.fighter.power += 1
            elif level_up == 'def':
                player.fighter.defense += 1

            game_state = previous_game_state

        if show_character_screen:
            previous_game_state = game_state
            game_state = GameStates.CHARACTER_SCREEN

        if game_help:
            previous_game_state = game_state
            game_state = GameStates.GAME_HELP

        if game_state == GameStates.TARGETING:
            if left_click:
                target_x, target_y = left_click

                item_use_results = player.inventory.use(
                    targeting_item, entities=entities, fov_map=fov_map,
                    target_x=target_x, target_y=target_y
                )
                player_turn_results.extend(item_use_results)
            elif right_click:
                player_turn_results.append({
                    'targeting_cancelled': True
                })

        if end:
            if game_state in (GameStates.SHOW_INVENTORY,
                              GameStates.DROP_INVENTORY,
                              GameStates.CHARACTER_SCREEN,
                              GameStates.GAME_HELP):
                game_state = previous_game_state
            elif game_state == GameStates.TARGETING:
                player_turn_results.append({'targeting_cancelled': True})
            else:
                save_game(player, entities, game_map, msg_log, game_state)
                return True

        if fullscreen:
            libtcod.console_set_fullscreen(not libtcod.console_is_fullscreen())

        if screenshot:
            take_screenshot(constants['f_path'], constants['img_path'],
                            constants['rn_path'], constants['tmp_path'])

        for player_turn_result in player_turn_results:
            message = player_turn_result.get('message')
            dead_entity = player_turn_result.get('dead')
            item_added = player_turn_result.get('item_added')
            item_consumed = player_turn_result.get('consumed')
            item_dropped = player_turn_result.get('item_dropped')
            targeting = player_turn_result.get('targeting')
            targeting_cancelled = player_turn_result.get('targeting_cancelled')
            xp = player_turn_result.get('xp')

            if message:
                msg_log.add_message(message)

            if dead_entity:
                if dead_entity == player:
                    message, game_state = kill_player(dead_entity,
                                                      constants['sprites'],
                                                      constants['colors'])
                else:
                    message = kill_monster(dead_entity,
                                           constants['sprites'],
                                           constants['colors'])

                msg_log.add_message(message)

            if item_added:
                entities.remove(item_added)

                game_state = GameStates.ENEMY_TURN

            if item_consumed:
                game_state = GameStates.ENEMY_TURN

            if item_dropped:
                entities.append(item_dropped)

                game_state = GameStates.ENEMY_TURN

            if targeting:
                previous_game_state = GameStates.PLAYERS_TURN
                game_state = GameStates.TARGETING

                targeting_item = targeting

                msg_log.add_message(targeting_item.item.targeting_msg)

            if targeting_cancelled:
                game_state = previous_game_state

                msg_log.add_message(Message('Targeting cancelled'))

            if xp:
                leveled_up = player.level.add_xp(xp)
                msg_log.add_message(
                    Message('You gain {0} experience points.'.format(xp))
                )

                if leveled_up:
                    msg_log.add_message(Message(
                        'Your battle skills grow stronger! You reached' +
                        ' level {0}'.format(
                            player.level.current_lvl
                        ) + '!', libtcod.light_han
                    ))

                    previous_game_state = game_state
                    game_state = GameStates.LEVEL_UP

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
                                    dead_entity, constants['sprites'],
                                    constants['colors'])
                            else:
                                message = kill_monster(dead_entity,
                                                       constants['sprites'],
                                                       constants['colors'])

                            msg_log.add_message(message)

                            if game_state == GameStates.PLAYER_DEAD:
                                break

                    if game_state == GameStates.PLAYER_DEAD:
                        break

            else:
                game_state = GameStates.PLAYERS_TURN


def main():
    constants = get_constants()

    libtcod.console_set_custom_font('./assets/cp437_8x8.png',
                                    libtcod.FONT_TYPE_GREYSCALE |
                                    libtcod.FONT_LAYOUT_ASCII_INROW)

    libtcod.console_init_root(
        constants['screen_width'], constants['screen_height'],
        constants['window_title'], False
    )

    mapcon = libtcod.console_new(constants['map_width'],
                                 constants['map_height'])
    infocon = libtcod.console_new(constants['info_width'],
                                  constants['info_height'])
    msgcon = libtcod.console_new(constants['msg_width'],
                                 constants['msg_height'])
    lookcon = libtcod.console_new(constants['look_width'],
                                  constants['look_height'])

    player = None
    entities = []
    game_map = None
    msg_log = None
    game_state = None

    show_main_menu = True
    show_load_err_msg = False

    main_menu_background_img = libtcod.image_load(
        './assets/menu_background.png'
    )

    key_press = libtcod.EVENT_KEY_PRESS
    mouse_click = libtcod.EVENT_MOUSE
    key = libtcod.Key()
    mouse = libtcod.Mouse()

    libtcod.sys_set_fps(constants['limit_fps'])

    while not libtcod.console_is_window_closed():
        libtcod.sys_check_for_event(key_press | mouse_click, key, mouse)

        if show_main_menu:
            main_menu(mapcon, main_menu_background_img,
                      constants['screen_width'], constants['screen_height'])

            if show_load_err_msg:
                msg_box(mapcon, 'Error', 'No save game to load', 50,
                        constants['screen_width'], constants['screen_height'],
                        libtcod.red)

            libtcod.console_flush()

            action = handle_main_menu(key)

            new_game = action.get('new_game')
            load_saved_game = action.get('load_game')
            end_game = action.get('exit')

            if show_load_err_msg and (new_game or load_saved_game or end_game):
                show_load_err_msg = False
            elif new_game:
                player, entities, game_map, msg_log, game_state = get_game_vars(
                    constants
                )
                game_state = GameStates.PLAYERS_TURN

                show_main_menu = False
            elif load_saved_game:
                try:
                    player, entities, game_map, msg_log, game_state = load_game()
                    show_main_menu = False
                except FileNotFoundError:
                    show_load_err_msg = True
            elif end_game:
                break

        else:
            libtcod.console_clear(mapcon)
            play_game(player, entities, game_map, msg_log, game_state,
                      mapcon, infocon, lookcon, msgcon, constants
                      )
            show_main_menu = True

if __name__ == '__main__':
    main()
