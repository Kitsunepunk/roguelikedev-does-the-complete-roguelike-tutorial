class Level:
    """deals with levels and XP"""
    def __init__(
        self, current_lvl=1, current_xp=0, lvl_up_base=200, lvl_up_factor=150
    ):
        self.current_lvl = current_lvl
        self.current_xp = current_xp
        self.lvl_up_base = lvl_up_base
        self.lvl_up_factor = lvl_up_factor

    @property
    def experience_to_next_lvl(self):
        return self.lvl_up_base + self.current_lvl * self.lvl_up_factor

    def add_xp(self, xp):
        self.current_xp += xp

        if self.current_xp > self.experience_to_next_lvl:
            self.current_xp -= self.experience_to_next_lvl
            self.current_lvl += 1

            return True

        else:
            return False
