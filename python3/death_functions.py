import libtcodpy as libtcod

from game_states import GameStates
from render_functions import RenderOrder


def kill_player(player, sprites, colors):
    player.char = sprites.get('death')
    player.fore_color = colors.get('obj_back')
    player.back_color = colors.get('death')

    return 'You died', GameStates.PLAYER_DEAD


def kill_monster(monster, sprites, colors):
    death_message = '{0} is dead'.format(monster.name.capitalize())

    monster.char = sprites.get('death')
    monster.fore_color = colors.get('death')
    monster.blocks = False
    monster.fighter = None
    monster.ai = None
    monster.name = 'remains of ' + monster.name
    monster.render_ord = RenderOrder.CORPSE

    return death_message
