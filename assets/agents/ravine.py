from random import uniform, randrange
import shortuuid

class Ravine():
    """
    An obstacle in the environment. 
    Foragers with the right attributes can jump over them.
    Hunters, and foragers that cannot jump, have to walk around.
    """
    def __init__(self, grid_width: int) -> None:
        self.id = self.generate_id()
        self.skill_required = round(uniform(0.1, 0.7), 2) * 10
        self.width = randrange(1, grid_width//2)
        self.height = randrange(1, grid_width//2)
        
    def generate_id(self) -> str:
        """
        A unique ID for the ravine.
        """
        return shortuuid.random(length=4)
        
    def __str__(self) -> str:
        """
        Overload str method for more informative output when printing.
        """
        return f'Ravine {self.id} requires {self.skill_required} skill.\n'