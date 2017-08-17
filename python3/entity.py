import libtcodpy as libtcod
import math

from render_functions import RenderOrder


class Entity:
    """
    A Generic object to represent players, enemies, items, etc.
    """
    def __init__(self, x, y, char, fore_color, back_color, name, blocks=False,
                 render_ord=RenderOrder.CORPSE, fighter=None, ai=None,
                 item=None, inventory=None):
        self.x = x
        self.y = y
        self.char = char
        self.fore_color = fore_color
        self.back_color = back_color
        self.name = name
        self.blocks = blocks
        self.render_ord = render_ord
        self.fighter = fighter
        self.ai = ai
        self.item = item
        self.inventory = inventory

        if self.fighter:
            self.fighter.owner = self

        if self.ai:
            self.ai.owner = self

        if self.item:
            self.item.owner = self

        if self.inventory:
            self.inventory.owner = self

    def move(self, dx, dy):
        # Move the entity by a given amount
        self.x += dx
        self.y += dy

    def move_towards(self, target_x, target_y, game_map, entities):
        dx = target_x - self.x
        dy = target_y - self.y
        distance = math.sqrt(dx ** 2 + dy ** 2)

        dx = int(round(dx / distance))
        dy = int(round(dy / distance))

        if not (game_map.is_blocked(self.x + dx, self.y + dy) or
                get_blocking_entities_at_location(entities, self.x + dx,
                                                  self.y + dy)):
            self.move(dx, dy)

    def move_astar(self, target, entities, game_map):
        # Create a FOV map that has the dimensions of the map
        fov = libtcod.map_new(game_map.width, game_map.height)

        # Scan the current map each turn and set all the walls as
        # unwalkable
        for y1 in range(game_map.height):
            for x1 in range(game_map.width):
                libtcod.map_set_properties(fov, x1, y1, not
                                            game_map.tiles[x1][y1].block_sight,
                                            not game_map.tiles[x1][y1].blocked)

        # Scan all the objects to see if there are objects that must
        # be  navigated around
        # Check also that the object isn't self or the target ( so
        # that the start and end points are free)
        # The AI class handles the situation if self is next to the
        # target so it will not use this A* function anyway
        for entity in entities:
            if entity.blocks and entity != self and entity != target:
                # Set the tile as a wall so it must be navigated
                # around
                libtcod.map_set_properties(fov, entity.x, entity.y,
                                           True, False)

        # Allocate a A* path
        # The 1.41 is the normal diagonal cost of moving, it can be
        # set as 0.0 if diagonal moves are prohibited
        my_path = libtcod.path_new_using_map(fov, 1.41)

        # Compute the path between self's coordinats and th target's
        # coordinates
        libtcod.path_compute(my_path, self.x, self.y, target.x, target.y)

        # Check if the path exist, and in this case, also the path
        # is shorter than 25 tiles
        # The path size matters if you want the monster to use
        # alernative longer paths(for example other rooms) if for
        # example the player is in a cooridor
        # It makes sense to keep path size relatively low to keep
        # the monsters from running around the map if there's an
        # alternative path really far away
        if not libtcod.path_is_empty(my_path) and libtcod.path_size(my_path) < 25:
            # find the next coordinates in the computed path
            x, y = libtcod.path_walk(my_path, True)
            if x or y:
                # Set self's coordinates to the next path tile
                self.x = x
                self.y = y
        else:
            # Keep the old move function as a backup so that if
            # there are no paths (for example another monster blocks
            # a corridor) it will still try to move towards the
            # player (closer to the corridor opening)
            self.move_towards(target.x, target.y, game_map, entities)

        # Delete the path to free memory
        libtcod.path_delete(my_path)

    def distance_to(self, other):
        dx = other.x - self.x
        dy = other.y - self.y
        return math.sqrt(dx ** 2 + dy ** 2)


def get_blocking_entities_at_location(entities, destination_x, destination_y):
    for entity in entities:
        if (entity.blocks and entity.x == destination_x and
                entity.y == destination_y):
            return entity

    return None