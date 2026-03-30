from character import Character


class Mage(Character):
    def __init__(self, name, max_hp, attack_power, defense, max_mana):
        super().__init__(name, max_hp, attack_power, defense)
        self.max_mana = max_mana
        self.mana = max_mana

    def cast_spell(self, mana_cost):
        if mana_cost <= self.mana:
            self.mana -= mana_cost
            return True
        else:
            return False
