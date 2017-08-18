import libtcodpy as libtcod
from random import randint

from game_messages import Message


class BasicMonster:
    def take_turn(self, target, fov_map, game_map, entities):
        results = []

        monster = self.owner
        if libtcod.map_is_in_fov(fov_map, monster.x, monster.y):

            if monster.distance_to(target) >= 2:
                monster.move_astar(target, entities, game_map)

            elif target.fighter.hp > 0:
                attack_results = monster.fighter.attack(target)
                results.extend(attack_results)

        return results


class ConfusedMonster:
    def __init__(self, prev_ai, num_turns=10):
        self.prev_ai = prev_ai
        self.num_turns = num_turns

    def take_turn(self, target, fov_map, game_map, entities):
        results = []

        if self.num_turns > 0:
            rand_x = self.owner.x + randint(0, 2) - 1
            rand_y = self.owner.y + randint(0, 2) - 1

            if rand_x != self.owner.x and rand_y != self.owner.y:
                self.owner.move_towards(rand_x, rand_y, game_map, entities)

            self.num_turns -= 1
        else:
            self.owner.ai = self.prev_ai
            results.append({
                'message': Message(
                    'The {0} is no longer confused!'.format(
                        self.owner.name
                    ), libtcod.red
                )
            })

        return results
