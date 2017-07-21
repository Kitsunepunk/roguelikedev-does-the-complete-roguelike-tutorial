import libtcodpy as libtcod

def roll_dice(num, sides):

    total = 0
    roll = 0
    run_total = 0

    for dice in range(num):
        print '--'

        total = libtcod.random_get_int(0, 1, sides)
        run_total += total
        roll += 1
        print str(num) + 'd' + str(sides)
        print 'roll:' + str(roll) + ' running total:' +  str(run_total) + ' rolled:' + str(total)
        print '--'

    print run_total
    return run_total

roll_dice(4, 20)
roll_dice(3, 6)
roll_dice(2, 100)
roll_dice(2, 8)
roll_dice(5, 12)
roll_dice(6, 4)
