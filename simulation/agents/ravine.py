from random import uniform, randrange
import shortuuid

class Ravine():
    """
    The Ravine is an obstacle in the environment. 
    Foragers can only get around them with the right attributes.
    """
    def __init__(self, width: int = None, height: int = None):
        self.id = self.generate_id()
        self.skill_required = round(uniform(0.1, 0.7), 2)
        # Sizes can be set by user or initialised randomly
        if width == None and height == None:
            self.width = randrange(1, 4)
            self.height = randrange(1, 4)
        else:
            self.width = width
            self.height = height
        
    def generate_id(self) -> str:
        return shortuuid.random(length=4)
        
    def __str__(self) -> str:
        return f'Ravine {self.id} requires {self.skill_required} skill.\n'