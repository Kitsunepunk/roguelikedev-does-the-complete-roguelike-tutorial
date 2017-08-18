import libtcodpy as libtcod

from components.ai import ConfusedMonster
from game_messages import Message
from rng_functions import dice_roll


def heal(*args, **kwargs):
    entity = args[0]
    amount = kwargs.get('amount')

    results = []

    if entity.fighter.hp == entity.fighter.max_hp:
        results.append({
            'consumed': False,
            'message': Message(
                'You are already at full health',
                libtcod.pink
            )
        })
    else:
        roll = dice_roll(1, amount)
        base = int(amount / 2)
        heal_amt = roll + base
        entity.fighter.heal(heal_amt)
        results.append({
            'consumed': True,
            'message': Message(
                'Your wounds start to feel better! 1d{0}+{1}(+{2} hp)'.format(
                    amount, base, heal_amt
                ), libtcod.violet
            )
        })

    return results


def cast_lightning(*args, **kwargs):
    caster = args[0]
    entities = kwargs.get('entities')
    fov_map = kwargs.get('fov_map')
    damage = kwargs.get('damage')
    maximum_range = kwargs.get('maximum_range')

    results = []

    target = None
    closest_distance = maximum_range + 1

    for entity in entities:
        if (entity.fighter and entity != caster and
                libtcod.map_is_in_fov(fov_map, entity.x, entity.y)):
            distance = caster.distance_to(entity)

            if distance < closest_distance:
                target = entity
                closest_distance = distance

    if target:
        roll = dice_roll(1, damage)
        base = int(damage / 2)
        lightning_dmg = roll + base
        results.append({
            'consumed': True, 'target': target, 'message': Message(
                'A lightning bolt strikes {0}'.format(target.name) +
                ' with a loud thunder! 1d{0}+{1}(-{2} hp)'.format(
                    damage, base, lightning_dmg
                ), libtcod.sky
            )
        })
        results.extend(target.fighter.take_damage(lightning_dmg))
    else:
        results.append({
            'consumed': False, 'target': None, 'message': Message(
                'No enemy is close enough to strike.', libtcod.pink
            )
        })

    return results


def cast_fireball(*args, **kwargs):
    entities = kwargs.get('entities')
    fov_map = kwargs.get('fov_map')
    damage = kwargs.get('damage')
    radius = kwargs.get('radius')
    target_x = kwargs.get('target_x')
    target_y = kwargs.get('target_y')

    results = []

    if not libtcod.map_is_in_fov(fov_map, target_x, target_y):
        results.append({
            'consumed': False, 'message': Message(
                'You cannot target a tile outside of your field of view',
                libtcod.pink
            )
        })
        return results

    results.append({
        'consumed': True, 'message': Message(
            'The fireball explodes, burning eveything within {0} tiles!'.format(
                radius
            ), libtcod.flame
        )
    })

    for entity in entities:
        if entity.distance(target_x, target_y) <= radius and entity.fighter:
            roll = dice_roll(1, damage)
            base = int(damage / 2)
            fb_dmg = roll + base
            results.append({
                'message': Message(
                    'The {0} gets burned for 1d{1}+{2}(-{3} hp) damage.'.format(
                        entity.name, damage, base, fb_dmg
                    ), libtcod.flame
                )
            })
            results.extend(entity.fighter.take_damage(fb_dmg))

    return results


def cast_confuse(*args, **kwargs):
    entities = kwargs.get('entities')
    fov_map = kwargs.get('fov_map')
    target_x = kwargs.get('target_x')
    target_y = kwargs.get('target_y')

    results = []

    if not libtcod.map_is_in_fov(fov_map, target_x, target_y):
        results.append({
            'consumed': False, 'message': Message(
                'You cannot target a tile outside your field of view',
                libtcod.pink
            )
        })
        return results

    for entity in entities:
        if entity.x == target_x and entity.y == target_y and entity.ai:
            confused_ai = ConfusedMonster(entity.ai, 10)

            confused_ai.owner = entity
            entity.ai = confused_ai

            results.append({
                'consumed': True, 'message': Message(
                    'The eyes of the {0} look vacant, as the {0}'.format(
                        entity.name
                    ) + ' starts to stumble around!', libtcod.light_green
                )
            })
            break

    else:
        results.append({
            'consumed': False, 'message': Message(
                'There is no targetable enemy at that location',
                libtcod.pink
            )
        })
    return results
