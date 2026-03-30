class Character:
    def __init__(self, name, max_hp, attack_power, defense):
        self.name = name
        self.max_hp = max_hp
        self.hp = max_hp
        self.attack_power = attack_power
        self.defense = defense

    def attack(self):
        return self.attack_power

    def take_damage(self, damage):
        self.hp -= damage

    def is_alive(self):
        if self.hp <= 0:
            return False
        else:
            return True

    def __str__(self):
        return f"\nName: {self.name}\nMax HP: {self.max_hp}\nHP: {self.hp}\nAttack Power: {self.attack_power}\nDefense: {self.defense}\n"
