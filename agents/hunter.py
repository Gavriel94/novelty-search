from .mammal import Mammal

class Hunter(Mammal):
    def __init__(self, id: str, hunger: float, bravery: float, agility: float, 
                 perception: float, strength: float, endurance: float,):
        super().__init__(id, hunger, bravery, agility, 
                         perception, strength, endurance)
    
    def __str__(self) -> str:
        return f'Hunter {self.id}'