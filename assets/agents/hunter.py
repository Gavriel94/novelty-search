from .mammal import Mammal
import random
from random import randrange

class Hunter(Mammal):
    """
    Predators that fight foragers, or cause them to flee.
    """
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
        Hunter attributes, initialised at random.
        The range of values is high, forcing foragers to evolve.

        Returns:
            dict: Dictionary containing name and value of attributes.
        """
        d = {}
        d['agility'] = float(randrange(4, 10))
        d['perception'] = float(randrange(4, 8))
        d['strength'] = float(randrange(6, 10))
        d['endurance'] = float(randrange(4, 8))
        return d
    
    def get_next_move(self, 
                      grid: list, 
                      grid_height: int, 
                      grid_width: int) -> tuple[tuple, tuple]:
            """
            Finds an empty space directly around itself, and moves to it. 
            If there are no empty spaces, the hunter remains still.
            
            Args:
                grid (list): The simulation and its contents
                grid_height (int): Height of grid
                grid_width (int): Width of grid
            """
            current_position = None
            potential_moves = []
            for y in range(grid_height-1):
                for x in range(grid_width-1):
                        if isinstance(grid[y][x], Hunter):
                            hunter = grid[y][x]
                            if hunter.id != self.id:
                                continue
                            # save current position
                            current_position = (x,y)
                            # cell above is empty
                            if 0 <= y - 1 <= grid_height and grid[y - 1][x] == None:
                                potential_moves.append((x, y - 1))
                            # cell below is empty
                            elif 0 <= y + 1 <= grid_height and grid[y + 1][x] == None:
                                potential_moves.append((x, y + 1))
                            # cell to the left is empty
                            elif 0 <= x - 1 <= grid_width and grid[y][x - 1] == None:
                                potential_moves.append((x - 1, y))
                            # cell to the right is empty
                            elif 0 <= x + 1 <= grid_width and grid[y][x + 1] == None:
                                potential_moves.append((x + 1, y))
                new_position = (random.choice(potential_moves) 
                                if len(potential_moves) > 0 else current_position)
            return current_position, new_position
        
    def __str__(self) -> str:
        """
        Overload str method for more informative output when printing.
        """
        return f'Hunter {self.id}.\n'
    