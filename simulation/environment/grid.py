import random
from typing import Tuple
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
        self.foragers = []
        self.hunters = []
        self.grid_history = []
        
    def setup_environment(self, objects: list) -> None:
        """
        Distributes a collection of objects on the grid. 

        Args:
            objects (list): Iterable collection of objects.
        """
        if len(objects) > self.area:
            raise GridFull
        for object in objects:
            self.__place_object(object)
            
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
        grid_copy = [row[:] for row in self.grid]
        self.grid_history.append(grid_copy)
        
        if len(self.grid_history) > 1:
            previous_grid = self.grid_history[-2]
            current_grid = self.grid_history[-1]
            print(f"{'Previous Timestep':>8}      {'Current Timestep':<8}")
            for prev_row, current_row in zip(previous_grid, current_grid):
                previous_row_str = " ".join([d.get(type(cell), '.') for cell in prev_row])
                current_row_str = " ".join([d.get(type(cell), '.') for cell in current_row])
                print(f'{previous_row_str}    {current_row_str}')
        else:
            for row in self.grid:
                print(" ".join([d.get(type(cell), '.') for cell in row]))
                    
    def run_simulation(self, 
                       steps: int, 
                       replace_agent: bool, 
                       display_attributes: bool) -> None:
        """
        Runs the simulation.
        Hunters move before foragers do. 
        Hunters do not engage with any objects.

        Args:
            steps (int): Number of simulation steps.
            replace_agent (bool): Replaces food, forager or hunters that 
                are removed from the simulation. 
            display_forager_attributes (bool): Output foragers attributes
                to stdout at each time step.

        Raises:
            MoveError: Simulation ends if an invalid move has been made.
        """
        for step in range(steps):
            print('*' + '-' * 52 + '*')
            print(f"| {'Time':>26} {step:<24}|")
            print('*' + '-' * 52 + '*')
            self.display_grid()
            print('*' + '-' * 52 + '*')
            
            for hunter in self.hunters:
                if not hunter.alive:
                    continue
                from_xy, to_xy = hunter.get_next_move(self.grid, self.height, self.width)
                if to_xy == from_xy:
                    print(f'Hunter {hunter.id} stayed still')
                    continue
                else:
                    print(f'Hunter {hunter.id} moved from {(from_xy)} to {(to_xy)}')
                    from_x = from_xy[0]
                    from_y = from_xy[1]
                    new_x = to_xy[0] 
                    new_y = to_xy[1]
                
                    self.grid[new_y][new_x] = self.grid[from_y][from_x]
                    self.grid[from_y][from_x] = None
                
            for forager in self.foragers:
                if not forager.alive:
                    continue
                forager.log_dynamic_attributes(display_attributes)
                to_x, to_y = forager.get_next_move(self)
                target_loc = self.grid[to_y][to_x]
                # Forager eats food and new food appears somewhere randomly
                # ! this chain of events for steps can be changed!
                if isinstance(target_loc, Food):
                    self.__forager_finds_food(forager, to_x, to_y, replace_agent)
                # Forager engages hunter
                elif isinstance(target_loc, Hunter):
                    forager.hunger_increase()
                    self.__forager_finds_hunter(forager, to_x, to_y, replace_agent)
                # Forager moves through or around ravine
                elif isinstance(target_loc, Ravine):
                    forager.hunger_increase()
                    self.__forager_finds_ravine(forager, to_x, to_y)
                # Forager meets another forager    
                elif isinstance(target_loc, Forager):
                    # Produce offspring, or wait for the other forager to move
                    forager.hunger_increase()
                    self.__forager_finds_forager(forager, to_x, to_y)
                # Forager moves from one spot to another   
                elif target_loc == None:
                    forager.hunger_increase()
                    self.__forager_step(forager, to_x, to_y)
                else:
                    raise MoveError
                print('*' + '-' * 52 + '*')
            print('\n'*3) 
    
    def get_forager_logs(self, save_as_txt: bool):
        print('-' * 72, '\n')
        if not save_as_txt:
            for forager in self.foragers:
                log = forager.get_log(save_as_txt)
                print(f'Forager {forager.id}')
                for line in log:
                    print(line)
                print('\n')
        else:
            for forager in self.foragers:
                forager.get_log(save_as_txt)
    
    def __place_object(self, object: Forager | Hunter | Food | Ravine) -> None:
        """
        Place an object in the environment. 
        """
        def place_ravine(x, y, ravine_x, ravine_y, ravine):
            """
            Iterate through coordinates and place ravine markers.
            """
            for i in range(ravine_y + 1):
                for j in range(ravine_x + 1):
                    # markers are placed up and to the right
                    self.grid[y - i][x + j] = ravine
                    
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
                if isinstance(object, Forager):
                    object.current_coordinates = (x, y)
                    self.foragers.append(object)
                elif isinstance(object, Hunter):
                    self.hunters.append(object)
            else:
                x, y = self.__find_random_empty_cell()
                self.grid[y][x] = object
                if isinstance(object, Forager):
                    object.current_coordinates = (x, y)
                    self.foragers.append(object)
                elif isinstance(object, Hunter):
                    self.hunters.append(object)
            
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
    
    def __get_cell(self, x: int, y: int) -> list | None:
        """
        Gets the object at the cell index specified by x and y.

        Returns:
            list | None: object or None.
        """
        if 0 <= x < self.width and 0 <= y < self.height:
            return self.grid[y][x]
        return None

    def __find_random_empty_cell(self) -> Tuple[int, int]:
        """
        Finds a random empty cell.

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
        
    # region handle forager actions
    def __forager_finds_food(self, 
                             forager: Forager, 
                             to_x: int, 
                             to_y: int, 
                             replace: bool) -> None:
        """
        The forager eats and takes the place of the food on the grid. 
        New food appears at a random location.
        """
        from_x = forager.current_coordinates[0]
        from_y = forager.current_coordinates[1]
        food = self.grid[to_y][to_x]
        forager.eat(food)
        self.grid[to_y][to_x] = self.grid[from_y][from_x]
        self.grid[from_y][from_x] = None
        forager.current_coordinates = (to_x, to_y)
        if replace:
            f = Food()
            self.__place_object(f)
            
    def __forager_finds_hunter(self, 
                               forager: Forager, 
                               to_x: int, 
                               to_y: int, 
                               replace: bool) -> None:
        """
        The forager fights or flees the hunter.
        If the forager fights and wins it takes the place of the hunter
        and a new hunter appears at a random location. If the forager
        loses then it "dies" and a new forager appears at a random
        location.
        \n
        If the forager flees and wins it spawns somewhere on the grid
        at random. If the forager loses, it "dies" and a new forager 
        appears at a random location.
        """
        from_x = forager.current_coordinates[0]
        from_y = forager.current_coordinates[1]
        hunter = self.grid[to_y][to_x]
        win, decision = forager.engage_hunter(hunter)
        if decision == 'fight' and win:
            self.grid[to_y][to_x] = self.grid[from_y][from_x]
            self.grid[from_y][from_x] = None
            forager.current_coordinates = (to_x, to_y)
            h = Hunter()
            self.__place_object(h)
        elif decision == 'fight' and not win:
            # remove forager
            self.grid[from_y][from_x] = None
            self.foragers.remove(forager)
            if replace:
                # replace with new forager
                new_forager = Forager()
                self.__place_object(new_forager)
                self.foragers.append(new_forager)
        elif decision == 'flee' and win:
            # forager is placed in a random location
            self.grid[from_y][from_x] = None
            self.__place_object(forager)
        elif decision == 'flee' and not win:
            # replace with new forager
            self.grid[from_y][from_x] = None
            self.foragers.remove(forager)
            if replace:
                new_forager = Forager()
                self.__place_object(new_forager)
                self.foragers.append(new_forager)
                
    def __forager_finds_ravine(self, 
                               forager: Forager, 
                               to_x: int, 
                               to_y: int) -> None:
        """
        If the foragers attributes allow, it appears on the other
        side of the ravine in the direction it was
        heading (vertical/horizontal), otherwise the forager walks
        around the ravine.
        """
        def horizontal_step():
            """
            Forager tries to go around the right side of the ravine.
            If this isn't possible, it goes left.
            """ 
            new_x = to_x + 1 if to_x + 1 < self.width else to_x - 1
            self.grid[from_y][new_x] = self.grid[from_y][from_x]
            self.grid[from_y][from_x] = None
            forager.current_coordinates = (new_x, from_y)
            
        def vertical_step():
            """
            Forager tries to go up to get around ravine.
            If this isn't possible, it goes down.
            """
            new_y = to_y + 1 if to_y + 1 < self.height else to_y - 1
            self.grid[new_y][from_x] = self.grid[from_y][from_x]
            self.grid[from_y][from_x] = None
            forager.current_coordinates = (from_x, new_y)
            
        from_x = forager.current_coordinates[0]
        from_y = forager.current_coordinates[1]
        ravine = self.grid[to_y][to_x]
        traverse = forager.traverse_ravine(ravine)
        
        # forager is moving horizontally
        if abs(to_x - from_x) > abs(to_y - from_y):
            if traverse:
                # determine if moving left-to-right or right-to-left
                new_x_coord = to_x + ravine.width + 1 if to_x > from_x else to_x - ravine.width - 1
                if 0 <= new_x_coord < self.width and not isinstance(self.grid[to_y][new_x_coord], Ravine):
                    self.grid[to_y][new_x_coord] = self.grid[from_y][from_x]
                    self.grid[from_y][from_x] = None
                    forager.current_coordinates = (new_x_coord, to_y)
                else:
                    # ravine is on grid edge so can't jump over
                    vertical_step()
            else:
                # attributes too low to traverse so walk around
                vertical_step()
        # forager is moving vertically
        else:
            if traverse:
                # determine if moving up or down
                new_y_coord = to_y + ravine.height + 1 if to_y > from_y else to_y - ravine.height - 1
                if 0 <= new_y_coord < self.height and not isinstance(self.grid[new_y_coord][to_x], Ravine):
                    self.grid[new_y_coord][to_x] = self.grid[from_y][from_x]
                    self.grid[from_y][from_x] = None
                    forager.current_coordinates = (to_x, new_y_coord)
                else:
                    # ravine is on grid edge so can't jump over
                    horizontal_step()
            else:
                # attributes too low to traverse so walk around
                horizontal_step()
                    
    def __forager_finds_forager(self, 
                                forager: Forager, 
                                to_x: int, 
                                to_y: int) -> None:
        """
        A compatibilty check takes place and the foragers may produce
        offspring which appears at a random location, otherwise the 
        forager remains still so the other one can move.
        """
        potential_mate = self.grid[to_y][to_x]
        if forager.is_compatible_with(potential_mate):
            offspring = forager.produce_offspring(potential_mate)
            print(f'Forager {forager.id} and {potential_mate.id} produced offspring {offspring.id}.\n')
            self.__place_object(offspring)
        else:
            print(f'Forager {forager.id} and {potential_mate.id} are incompatible.\n')
    
    def __forager_step(self, 
                       forager: Forager, 
                       to_x: int, 
                       to_y: int) -> None:
        """
        There are no obstructions so the forager takes a step in the 
        direction it is heading.
        """
        from_x = forager.current_coordinates[0]
        from_y = forager.current_coordinates[1]
        self.grid[to_y][to_x] = self.grid[from_y][from_x]
        self.grid[from_y][from_x] = None
        forager.current_coordinates = (to_x, to_y)

class GridFull(Exception):
    def __init__(self):
        self.message = 'Grid is full.\n'
        super().__init__(self.message)
        
class MoveError(Exception):
    def __init__(self):
        self.message = 'Invalid forager move.\n'
        super().__init__(self.message)