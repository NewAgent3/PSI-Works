from character import Character


class Warrior(Character):
    def __init__(self, name, max_hp, attack_power, defense, shield_block):
        super().__init__(name, max_hp, attack_power, defense)
        self.shield_block = shield_block

    def block(self, damage_taken):
        if damage_taken <= self.shield_block:
            self.hp -= damage_taken / 2
            return True
        else:
            return False
