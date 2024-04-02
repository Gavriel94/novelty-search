from .mammal import Mammal
from .hunter import Hunter

class Forager(Mammal):
    def __init__(self, id: str, hunger: float, bravery: int, agility: int, perception: int, strength: int, endurance: int, sex: str):
        super().__init__(id, hunger, bravery, agility, perception, strength, endurance)
        self.sex = sex
        self.compatability_threshold = None
    
    def eat(self, sustenance: int) -> None:
        """
        Calculate value in the same way as `increase_hunger` and negate it.
        """
        pass
    
    def mate(self) -> Mammal:
        """
        Calculate compatibility threshold using a combination of attributes
        needs more thinking, to deal with male/female differently but this can wait
        """
        pass
    
    def increase_hunger(self) -> None:
        """
        Time has passed, you haven't eaten.        
        Going up:
            - hunger
            - bravery 
        Going down:
            - strength
            - agility
            - perception
            - endurance
            - agility
        """
        pass
    
    def fight_or_flee(self, hunter: Hunter):
        """
        Determines if the forager will fight or flee. 
        Calculate value based on a combination of bravery, strength, endurance and agility
        """
        pass
    
    def fight(self, hunter: Hunter):
        """
        Fight the hunter. If the forager wins they also eat so hunger does down.
        """
        pass
    
    def flee(self, hunter: Hunter):
        """
        Can get caught if endurance/agility is low.
        """
        pass
    
    def die(self) -> bool:
        """
        The forager did not survive.
        """
        pass