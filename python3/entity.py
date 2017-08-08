class Entity:
    """
    A Generic object to represent players, enemies, items, etc.
    """
    def __init__(self, x, y, char, fore_color, back_color):
        self.x = x
        self.y = y
        self.char = char
        self.fore_color = fore_color
        self.back_color = back_color

    def move(self, dx, dy):
        # Move the entity by a given amount
        self.x += dx
        self.y += dy
