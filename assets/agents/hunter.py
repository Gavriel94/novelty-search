from .mammal import Mammal
import random
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
    
    def get_next_move(self, grid: list, grid_height: int, grid_width: int):
            """
            The hunter picks a direction to move in, and moves there if 
            the space is empty. If there are no empty spaces the hunter 
            stays still.
            
            Args:
                potential_moves (list): possible moves the hunter can make
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
        return f'Hunter {self.id}.\n'
    
class MoveError(Exception):
    def __init__(self, message):
        super().__init__(message)