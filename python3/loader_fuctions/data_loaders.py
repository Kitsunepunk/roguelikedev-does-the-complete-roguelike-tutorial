import os
import shelve


def check_dir_exist(path):

    if not os.path.exists(path):
        os.makedirs(path)

def save_game(player, entities, game_map, msg_log, game_state):

    check_dir_exist('./save')

    with shelve.open('./save/run', 'n') as data_file:
        data_file['player_index'] = entities.index(player)
        data_file['entities'] = entities
        data_file['game_map'] = game_map
        data_file['msg_log'] = msg_log
        data_file['game_state'] = game_state


def load_game():
    if not os.path.isfile('./save/run.dat'):
        raise FileNotFoundError

    with shelve.open('./save/run', 'r') as data_file:
        player_index = data_file['player_index']
        entities = data_file['entities']
        game_map = data_file['game_map']
        msg_log = data_file['msg_log']
        game_state = data_file['game_state']

    player = entities[player_index]

    return player, entities, game_map, msg_log, game_state
