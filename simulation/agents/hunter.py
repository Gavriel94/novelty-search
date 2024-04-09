from .mammal import Mammal
from random import randrange

class Hunter(Mammal):
    def __init__(self):
        attributes = self.create_hunter()
        super().__init__(
            agility=attributes['agility'],
            perception=attributes['perception'],
            strength=attributes['strength'],
            endurance=attributes['endurance']
        )
        self.type = 'Hunter'
        self.alive = True
        
    def create_hunter(self) -> dict:
        """
        Hunter attributes are initialised at random.

        Returns:
            dict: Dictionary containing name and value of attributes.
        """
        d = {}
        d['agility'] = float(randrange(4, 10))
        d['perception'] = float(randrange(4, 8))
        d['strength'] = float(randrange(6, 10))
        d['endurance'] = float(randrange(4, 8))
        return d
    
    def __str__(self) -> str:
        return f'Hunter {self.id}.\n'