import random
from typing import Union, Tuple

from ..agents.forager import Forager
from ..agents.hunter import Hunter
from ..agents.food import Food
from ..agents.ravine import Ravine

class Grid():
    """
    The environment in which foragers search for food.
    """
    def __init__(self, width: int, height: int):
        self.width = width
        self.height = height
        self.grid = [[None for _ in range(width)] for _ in range(height)]
        self.object_count = 0
        self.area = self.width * self.height
        
    def setup_environment(self, objects: list) -> None:
        """
        Distributes a collection of objects on the grid. 
        It's important to always put ravines first as there are no 
        checks in place for the area of the ravine yet.

        Args:
            objects (list): Iterable collection of objects.
        """
        if len(objects) > self.area:
            raise GridFull
        for object in objects:
            self.place_object(object)
            
    def display_grid(self) -> None:
        """
        Displays the grid and its inhabitants in the console.
        """
        d = {
            Forager: 'F',
            Ravine: 'R',
            Hunter: 'H',
            Food: '*'
        }
        for row in self.grid:
            print(" ".join([d.get(type(cell), '.') for cell in row]))
    
    def place_object(self, 
                     object: Union[Forager, Hunter, Food, Ravine], 
                     x: int = None, 
                     y: int = None) -> None:
        """
        Place an object in the environment.

        Args:
            object (Union[Forager, Hunter, Food, Ravine]): Agent.
            x (int, optional): X coordinate. Defaults to None.
            y (int, optional): Y coordinate. Defaults to None.
        """
        def place_ravine(x, y, ravine_x, ravine_y, ravine):
            """
            Iterate through coordinates and place ravine markers.
            """
            for i in range(ravine_y + 1):
                for j in range(ravine_x + 1):
                    self.grid[y + i][x + j] = ravine
                    
        if x == None and y == None:
            x, y = self.__find_random_empty_cell()
        if isinstance(object, Ravine):
            width = object.width
            height = object.height
            # Ensures ravine is in bounds before placing
            if self.__ravine_buffer(x, y, width, height):
                place_ravine(x, y, width, height, object)
            else:
                # Finds new coordinates if ravine is out of bounds
                while True:
                    if self.__ravine_buffer(x, y, width, height):
                        break
                    x, y = self.__find_random_empty_cell()
                place_ravine(x, y, width, height, object)
        elif 0 <= x < self.width and 0 <= y < self.height:
            if self.__get_cell(x, y) == None:
                self.grid[y][x] = object
            else:
                x, y = self.__find_random_empty_cell()
                self.grid[y][x] = object
    
    def __ravine_buffer(self, x: int, y: int, 
                        ravine_x: int, ravine_y: int) -> bool:
        """
        Checks if a ravine is in bounds if placed at (x,y).

        Args:
            x (int): X coordinate.
            y (int): Y coordinate.
            ravine_x (int): Ravine y coordinate.
            ravine_y (int): Ravine y coordinate.

        Returns:
            bool: True if ravine can be placed here.
        """
        if (y + ravine_y < self.height) and (x + ravine_x < self.width):
            return True
        else:
            return False
    
    def __move_object(self, from_x: int, from_y: int, to_x: int, to_y: int) -> None:
        """
        Moves an object from one cell to another.

        Args:
            from_x (int): from x coordinate.
            from_y (int): from y coordinate.
            to_x (int): to x coordinate.
            to_y (int): to y coordinate.
        """
        if 0 <= to_x < self.width and 0 <= to_y < self.height:
            self.grid[to_y][to_x] = self.grid[from_y][from_x]
            self.grid[from_y][from_x] = None
    
    def __get_cell(self, x: int, y: int) -> list | None:
        """
        Gets the object at the cell index specified by x and y.

        Args:
            x (int): x coordinate.
            y (int): y coordinate.

        Returns:
            list | None: object or None.
        """
        if 0 <= x < self.width and 0 <= y < self.height:
            return self.grid[y][x]
        return None
    
    def __find_empty_cell(self) -> Tuple[int, int] | None:
        """
        Iterates through the grid sequentially and returns the first
        empty cell.

        Returns:
            (int, int) | None: x,y of the cell or None if grid is full.
        """
        for y in range(self.height):
            for x in range(self.width):
                if self.grid[y][x] is None:
                    return x, y
        return None

    def __find_random_empty_cell(self) -> Tuple[int, int]:
        """
        Iterates through the grid to find empty cells and returns one at random.§

        Raises:
            GridFull: Grid is full so cannot find a random, empty cell.

        Returns:
            Tuple[int, int]: (x,y) coordinates.
        """
        empty_cells = []
        for y in range(self.height):
            for x in range(self.width):
                if self.grid[y][x] is None:
                    empty_cells.extend([(x,y)])
        if len(empty_cells) == 0:
            raise GridFull
        else:
            return random.choice(empty_cells)

class GridFull(Exception):
    def __init__(self):
        self.message = 'Grid is full. Cannot add more items.\n'
        super().__init__(self.message)