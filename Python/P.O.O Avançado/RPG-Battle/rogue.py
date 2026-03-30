from character import Character


class Rogue(Character):
    def __init__(self, name, max_hp, attack_power, defense, stealth):
        super().__init__(name, max_hp, attack_power, defense)
        self.stealth = stealth

    def backstab(self, stealth_check):
        if stealth_check >= self.stealth:
            return self.attack_power
        else:
            return False
