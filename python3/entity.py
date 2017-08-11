class Entity:
    """
    A Generic object to represent players, enemies, items, etc.
    """
    def __init__(self, x, y, char, fore_color, back_color, name, blocks=False):
        self.x = x
        self.y = y
        self.char = char
        self.fore_color = fore_color
        self.back_color = back_color
        self.name = name
        self.blocks = blocks

    def move(self, dx, dy):
        # Move the entity by a given amount
        self.x += dx
        self.y += dy


def get_blocking_entities_at_location(entities, destination_x, destination_y):
    for entity in entities:
        if (entity.blocks and entity.x == destination_x and
                entity.y == destination_y):
            return entity

    return None
