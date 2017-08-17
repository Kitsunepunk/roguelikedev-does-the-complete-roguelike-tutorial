import libtcodpy as libtcod

from game_messages import Message
from rng_functions import dice_roll

class Fighter:
    def __init__(self, hp, defense, power):
        self.max_hp = hp
        self.hp = hp
        self.defense = defense
        self.power = power

    def take_damage(self, amount):
        results = []

        self.hp -= amount

        if self.hp <= 0:
            self.hp = 0
            results.append({'dead': self.owner})

        return results

    def attack(self, target):

        results = []

        attack_roll = dice_roll(1, self.power)
        base = int(self.power / 2)
        damage = int(attack_roll + base)

        to_hit = dice_roll(1, 20)

        if to_hit >= target.fighter.defense:
            results.append({'message': Message('{0} to hit vs. {1} AC'.format(
                str(to_hit), str(target.fighter.defense)),libtcod.light_han)})
            if self.owner.name != 'Player':
                results.append({'message':
                                Message('{0} attacks {1} for 1d{2}+{3}({4}) hit points'.format(
                                    self.owner.name.capitalize(), target.name.capitalize(),
                                    str(self.power), str(base), str(damage)
                                ), self.owner.fore_color)})
            else:
                results.append({'message':
                                Message('{0} attacks {1} for 1d{2}+{3}({4}) hit points'.format(
                                    self.owner.name.capitalize(), target.name.capitalize(),
                                    str(self.power), str(base), str(damage)
                                ), libtcod.white)})
            results.extend(target.fighter.take_damage(damage))
        else:
            results.append({'message': Message('{0} to hit vs. {1} AC'.format(
                str(to_hit), str(target.fighter.defense)), libtcod.light_han)})
            results.append({'message': Message('{0} tries to attacks {1} but misses'.format(
                self.owner.name.capitalize(), target.name,
                str(to_hit), str(target.fighter.defense)
            ), libtcod.white)})

        return results
