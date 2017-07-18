class Entity:
    """
    A generic object to reresent players, enemies, items, etc.
    """
    def __init__(self, x, y, char, color1, color2):
        self.x = x
        self.y = y
        self.char = char
        self.color1 = color1
        self.color2 = color2

    def move(self, dx, dy):
        # move the entity by a given amount
        self.x += dx
        self.y += dy
