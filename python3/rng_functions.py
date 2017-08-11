from random import randint


def dice_roll(num, sides):
    """ test"""

    run_total = 0
    roll = 0
    total = 0

    for dice in range(num):
        run_total = randint(1, sides)
        total += run_total
        roll += 1

    return total
