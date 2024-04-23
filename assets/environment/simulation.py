import random
import matplotlib.pyplot as plt
import seaborn as sns
sns.set_theme()
from typing import Tuple
from ..agents.forager import Forager, ForagerActions
from ..agents.hunter import Hunter
from ..agents.food import Food
from ..agents.ravine import Ravine

class Simulation():
    """
    The environment in which foragers search for food.
    """
    def __init__(self, width: int, height: int):
        self.width = width
        self.height = height
        self.simulation = [[None for _ in range(width)] for _ in range(height)]
        self.object_count = 0
        self.area = self.width * self.height
        self.foragers: list[Forager] = []
        self.hunters: list[Hunter] = []
        self.simulation_history = []
        self.num_steps = 0
        
        # metrics for analysis
        self.attribute_trends = {
            'average agility / 10 steps': [],
            'average perception / 10 steps': [],
            'average strength / 10 steps': [],
            'average endurance / 10 steps': []
        }
        self.total_mating_attempts = 0
        self.total_offspring_produced = 0
        self.total_sustenance_gained = 0
        self.total_foragers_lost = 0
        self.total_hunters_lost = 0
        self.total_motivations = {
            'nearest food': 0,
            'furthest food': 0,
            'most sustaining food': 0,
            'nearest forager': 0,
            'furthest forager': 0,
            'most compatible forager': 0
        }
                    
    def run(self, 
            steps: int, 
            replace_agent: bool, 
            display_attributes: bool) -> None:
        """
        Runs the simulation.
        
        - Hunters move before foragers
        - Hunters do not eat food
        - Hunters must walk around ravines

        Args:
            steps (int): Number of simulation steps.
            replace_agent (bool): Replaces food, forager or hunters that 
                are removed from the simulation. 
            display_forager_attributes (bool): Output foragers attributes
                to stdout at each time step.

        Raises:
            MoveError: Simulation ends if an invalid move has been made.
            GridFull: Simulation ends if the grid runs out of empty space.
        """

        self.num_steps = steps
        for i, step in enumerate(range(steps)):
            print('*' + '*' * 52 + '*')
            print(f"{'Step'} {step+1:<45}\n")
            # print('*' + '*' * 52 + '*')
            self.display_simulation(step)
            # print('*' + '-' * 52 + '*')
            
            # hunters move
            for hunter in self.hunters:
                if not hunter.alive:
                    continue
                from_xy, to_xy = hunter.get_next_move(self.simulation, self.height, self.width)
                if to_xy == from_xy:
                    continue
                else:
                    # print(f'Hunter {hunter.id} moved from {(from_xy)} to {(to_xy)}')
                    from_x = from_xy[0]
                    from_y = from_xy[1]
                    new_x = to_xy[0] 
                    new_y = to_xy[1]
                
                    self.simulation[new_y][new_x] = self.simulation[from_y][from_x]
                    self.simulation[from_y][from_x] = None
            
            # foragers move
            for i, forager in enumerate(self.foragers):
                if step % 10 == 0:
                    forager.mated_with.clear()
                    forager.incompatible_with.clear()
                    # Get average attributes
                    agility = 0
                    perception = 0
                    strength = 0
                    endurance = 0
                    for fo in self.foragers:
                        agility += fo.agility
                        perception += fo.perception
                        strength += fo.strength
                        endurance += fo.endurance
                    self.attribute_trends['average agility / 10 steps'].append(round(agility / len(self.foragers), ndigits=2))
                    self.attribute_trends['average perception / 10 steps'].append(round(perception / len(self.foragers), ndigits=2))
                    self.attribute_trends['average strength / 10 steps'].append(round(strength / len(self.foragers), ndigits=2))
                    self.attribute_trends['average endurance / 10 steps'].append(round(endurance / len(self.foragers), ndigits=2))
                    
                if not forager.alive:
                    continue
                forager.log_dynamic_attributes(display_attributes, i)
                print()
                to_x, to_y = forager.get_next_step(self)
                target_loc = self.simulation[to_y][to_x]
                # Forager eats food
                if isinstance(target_loc, Food):
                    self.__forager_finds_food(forager, to_x, to_y, replace_agent)
                    forager.steps_alive += 1
                # Forager engages hunter
                elif isinstance(target_loc, Hunter):
                    if forager.hunger_increase():
                        self.__forager_finds_hunter(forager, to_x, to_y, replace_agent)
                        forager.steps_alive += 1
                    else:
                        self.__forager_starves(forager, replace_agent)
                # Forager moves through or around ravine
                elif isinstance(target_loc, Ravine):
                    if forager.hunger_increase():
                        self.__forager_finds_ravine(forager, to_x, to_y)
                        forager.steps_alive += 1
                    else:
                        self.__forager_starves(forager, replace_agent)
                # Forager meets another forager    
                elif isinstance(target_loc, Forager):
                    # Produce offspring, or wait for the other forager to move
                    if forager.hunger_increase():
                        self.__forager_finds_forager(forager, to_x, to_y)
                        forager.steps_alive += 1
                    else:
                        self.__forager_starves(forager, replace_agent)
                # Forager moves from one spot to another   
                elif target_loc == None:
                    if forager.hunger_increase():
                        self.__forager_step(forager, to_x, to_y)
                        forager.steps_alive += 1
                    else:
                        self.__forager_starves(forager, replace_agent)
                else:
                    raise MoveError
            # self.display_simulation(step)
            print('*' + '-' * 52 + '*')
            if step != steps - 1:                
                print() 
            
    def setup_environment(self, objects: list) -> None:
        """
        Distributes a collection of objects in the simulation. 

        Args:
            objects (list): Iterable collection of objects.
        """
        if len(objects) > self.area:
            raise GridFull
        for object in objects:
            self.__place_object(object)
            
    def display_simulation(self, step) -> None:
        """
        Outputs simulation to stdout.
        """
        d = {
            Forager: 'F',
            Ravine: 'R',
            Hunter: 'H',
            Food: '*'
        }
        simulation_copy = [row[:] for row in self.simulation]
        self.simulation_history.append(simulation_copy)
        if len(self.simulation_history) > 1:
            previous_simulation = self.simulation_history[-2]
            current_simulation = self.simulation
            print()
            # print(f'Step {step} Map\n')
            # print(f"{f'Step {len(self.simulation_history) - 1}':>12}     ------->     {f'Step {len(self.simulation_history)}':<8}")
            # print(f"{f'Step {len(self.simulation_history) - 1}':>12}")
            for prev_row, current_row in zip(previous_simulation, current_simulation):
                previous_row_str = " ".join([d.get(type(cell), '.') for cell in prev_row])
                # current_row_str = " ".join([d.get(type(cell), '.') for cell in current_row])
                print(f'{previous_row_str}')
        else:
            for row in self.simulation:
                print(" ".join([d.get(type(cell), '.') for cell in row]))
    
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
                    self.simulation[y - i][x + j] = ravine
                    
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
                self.simulation[y][x] = object
                if isinstance(object, Forager):
                    object.current_coords = (x, y)
                    self.foragers.append(object)
                elif isinstance(object, Hunter):
                    self.hunters.append(object)
            else:
                x, y = self.__find_random_empty_cell()
                self.simulation[y][x] = object
                if isinstance(object, Forager):
                    object.current_coords = (x, y)
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
            return self.simulation[y][x]
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
                if self.simulation[y][x] is None:
                    empty_cells.extend([(x,y)])
        if len(empty_cells) == 0:
            raise GridFull
        else:
            return random.choice(empty_cells)
        
    def __forager_finds_food(self, 
                             forager: Forager, 
                             to_x: int, 
                             to_y: int, 
                             replace: bool) -> None:
        """
        The forager eats and takes the place of the food in the simulation. 
        New food appears at a random location.
        """
        from_x = forager.current_coords[0]
        from_y = forager.current_coords[1]
        food = self.simulation[to_y][to_x]
        forager.eat(food)
        self.simulation[to_y][to_x] = self.simulation[from_y][from_x]
        self.simulation[from_y][from_x] = None
        forager.current_coords = (to_x, to_y)
        self.total_sustenance_gained += food.sustenance_granted
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
        If the forager flees and wins it spawns somewhere in the simulation
        at random. If the forager loses, it "dies" and a new forager 
        appears at a random location.
        """
        from_x = forager.current_coords[0]
        from_y = forager.current_coords[1]
        hunter = self.simulation[to_y][to_x]
        if 'hide from hunter' in forager.bonus_attributes:
            # Forager moves to a random location without danger
            self.simulation[from_y][from_x] = None
            self.__place_object(forager)
            forager.motivation_metrics['hunter encounters']['times hidden'] += 1
        elif 'zig zag past hunter' in forager.bonus_attributes:
            fa = ForagerActions(environment=self, forager=forager)
            steps = fa.steps_to_choice(forager.motivation)
            if self.simulation[2] != None:
                # Move three steps ahead
                if self.simulation[steps[2][1]][steps[2][0]] == None:
                    self.simulation[steps[2][1]][steps[2][0]] = self.simulation[from_y][from_x]
                    self.simulation[from_y][from_x] = None
                    forager.current_coords = (steps[2][0], steps[2][1])
                    forager.motivation_metrics['hunter encounters']['times zig zagged'] += 1
            elif self.simulation[1] != None:
                # move two steps ahead if 3 isn't valid
                if self.simulation[steps[1][1]][steps[1][0]] == None:
                    self.simulation[steps[2][1]][steps[2][0]] = self.simulation[from_y][from_x]
                    self.simulation[from_y][from_x] = None
                    forager.current_coords = (steps[2][0], steps[2][1])
        else:
            if 'camouflage' in forager.bonus_attributes:
                # self.simulation[to_y][to_x] = self.simulation[from_y][from_x]
                self.simulation[from_y][from_x] = None
                forager.current_coords = (to_x, to_y)  
                forager.motivation_metrics['hunter encounters']['times camouflaged'] += 1
                return
            decision, win = forager.engage_hunter(hunter)
            if decision == 'fight' and win:
                self.simulation[to_y][to_x] = self.simulation[from_y][from_x]
                self.simulation[from_y][from_x] = None
                forager.current_coords = (to_x, to_y)
                self.total_hunters_lost += 1
                if replace:
                    # replace hunter 
                    h = Hunter()
                    self.__place_object(h)
            elif decision == 'fight' and not win:
                # remove forager
                self.simulation[from_y][from_x] = None
                self.foragers.remove(forager)
                self.total_foragers_lost += 1
            elif decision == 'flee' and win:
                # forager is placed in a random location
                self.simulation[from_y][from_x] = None
                self.__place_object(forager)
            elif decision == 'flee' and not win:
                # remove forager
                self.simulation[from_y][from_x] = None
                self.foragers.remove(forager)
                self.total_foragers_lost += 1
            
            if not win and replace:
                # add new forager back to the environment
                new_forager = Forager()
                print('adding new forager', new_forager.id)
                self.__place_object(new_forager)
                
    def __forager_starves(self, forager: Forager, replace: bool) -> None:
        from_x = forager.current_coords[0]
        from_y = forager.current_coords[1]
        self.simulation[from_y][from_x] = None
        self.foragers.remove(forager)
        self.total_foragers_lost += 1
        if replace:
            # replace with new forager
            new_forager = Forager()
            self.__place_object(new_forager)
                
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
            self.simulation[from_y][new_x] = self.simulation[from_y][from_x]
            self.simulation[from_y][from_x] = None
            forager.current_coords = (new_x, from_y)
            
        def vertical_step():
            """
            Forager tries to go up to get around ravine.
            If this isn't possible, it goes down.
            """
            new_y = to_y + 1 if to_y + 1 < self.height else to_y - 1
            self.simulation[new_y][from_x] = self.simulation[from_y][from_x]
            self.simulation[from_y][from_x] = None
            forager.current_coords = (from_x, new_y)
            
        from_x = forager.current_coords[0]
        from_y = forager.current_coords[1]
        ravine = self.simulation[to_y][to_x]
        # true if ravine is within foragers ability to cross
        traverse = forager.traverse_ravine(ravine)
        log_match1 = f'{forager.id} successfully crossed ravine.'
        log_match2 = f'{forager.id} fails to cross ravine.'
        
        # forager is moving horizontally    
        if abs(to_x - from_x) > abs(to_y - from_y):
            if traverse:
                # determine if moving left-to-right or right-to-left
                new_x_coord = to_x + ravine.width + 1 if to_x > from_x else to_x - ravine.width - 1
                log_match1 = f'{forager.id} successfully crossed ravine.'
                log_match2 = f'{forager.id} fails to cross ravine.'
                # walk vertically instead of bouncing back 
                if log_match1 == str(forager.log[-1]) or log_match2 == str(forager.log[-1]):
                    vertical_step()
                elif 0 <= new_x_coord < self.width and not isinstance(self.simulation[to_y][new_x_coord], Ravine):
                    self.simulation[to_y][new_x_coord] = self.simulation[from_y][from_x]
                    self.simulation[from_y][from_x] = None
                    forager.current_coords = (new_x_coord, to_y)
                else:
                    # ravine is on simulation edge so can't jump over
                    vertical_step()
            else:
                # attributes too low to traverse so walk around
                vertical_step()
        # forager is moving vertically
        else:
            if traverse:
                # determine if moving up or down
                new_y_coord = to_y + ravine.height + 1 if to_y > from_y else to_y - ravine.height - 1
                if log_match1 == str(forager.log[-1]) or log_match2 == str(forager.log[-1]):
                    horizontal_step()
                    # forager already tried and failed to cross ravine
                    horizontal_step()
                elif 0 <= new_y_coord < self.height and not isinstance(self.simulation[new_y_coord][to_x], Ravine):
                    self.simulation[new_y_coord][to_x] = self.simulation[from_y][from_x]
                    self.simulation[from_y][from_x] = None
                    forager.current_coords = (to_x, new_y_coord)
                else:
                    # ravine is on simulation edge so can't jump over
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
        potential_mate = self.simulation[to_y][to_x]
        if forager.is_compatible_with(potential_mate):
            offspring = forager.produce_offspring(potential_mate)
            self.__place_object(offspring)
            self.total_mating_attempts += 1
            self.total_offspring_produced += 1
        else:
            # foragers are incompatible, decide on something else to do.
            forager.motivation = None
            self.total_mating_attempts += 1
    
    def __forager_step(self, 
                       forager: Forager, 
                       to_x: int, 
                       to_y: int) -> None:
        """
        There are no obstructions so the forager takes a step in the 
        direction it is heading.
        """
        from_x = forager.current_coords[0]
        from_y = forager.current_coords[1]
        self.simulation[to_y][to_x] = self.simulation[from_y][from_x]
        self.simulation[from_y][from_x] = None
        forager.current_coords = (to_x, to_y)

class GridFull(Exception):
    def __init__(self):
        self.message = 'Grid is full.\n'
        super().__init__(self.message)
        
class MoveError(Exception):
    def __init__(self):
        self.message = 'Invalid forager move.\n'
        super().__init__(self.message)

class SimulationAnalytics:
    def __init__(self, simulation: Simulation):
        self.simulation = simulation
        self.foragers = [forager for forager in self.simulation.foragers]
        
    def simulation_metrics(self):
        print(f'Total mating attempts: {self.simulation.total_mating_attempts}')
        print(f'Total offspring produced: {self.simulation.total_offspring_produced}')
        print(f'Total sustenance granted: {self.simulation.total_sustenance_gained}')
        print(f'Total foragers lost: {self.simulation.total_foragers_lost}')
        print(f'Total hunters lost: {self.simulation.total_hunters_lost}')
        
    def display_attribute_trends(self):
        legend_labels = []
        for k, v in self.simulation.attribute_trends.items():
            # attribute name from key in form 'average 'attribute' / 10 steps'
            attribute = k.split()[1].title()
            legend_labels.append(attribute)
            plt.plot(v)
            plt.xlabel('Generation')
            plt.ylabel('Attribute Level')
        plt.legend(legend_labels)
        plt.show()
    
    def display_motivations_trends(self):
        keys = list(self.simulation.total_motivations.keys())
        values  = list(self.simulation.total_motivations.values())
        plt.bar(keys, values)
        plt.show()
            
        
    def detailed_analysis(self, forager):
        print('Attribute Trends\n')
        self.forager_attribute_differences(forager)
        
        print('Motivation Metrics\n')
        self.print_motivation_metrics(forager)
    
    def forager_attribute_differences(self, forager):
        print(f"Difference in agility: {forager.agility - forager.atrributes_at_init['agility']}")
        print(f"Difference in agility: {forager.perception - forager.atrributes_at_init['perception']}")
        print(f"Difference in agility: {forager.strength - forager.atrributes_at_init['strength']}")
        print(f"Difference in agility: {forager.endurance - forager.atrributes_at_init['endurance']}")
    
    def print_motivation_metrics(self, forager) -> None:
        """
        Displays full motivation metrics dictionary.
        """
        print(f'Forager {forager.id}\n')
        for motivation, details in forager.motivation_metrics.items():
            print(f'{motivation.title()}')
            if not isinstance(details, dict):
                print(f'{motivation}: {details}')
                print()
            else:
                for k, v in details.items():
                    print(f'{k}: {v}')
                print()
        print()
    
    def get_best_survivors(self, steps_alive: int) -> None:
        """
        Returns a list of key metrics from foragers who survived more 
        than `steps_alive` steps.

        Args:
            steps_alive (int): Threshold of "best" survivor.
        """
        best_foragers = [forager for forager in self.foragers if forager.steps_alive > steps_alive]
        for forager in best_foragers:
            self.print_motivation_metrics(forager)
            
    def get_lifetimes(self, display=True) -> list:
        """
        Pairs a foragers ID with the amount of steps it has survived
        and sorts them in ascending order.

        Args:
            display (bool, optional): Details to stdout.

        Returns:
            list: (forager ID, steps alive)
        """
        lifetimes = [(forager.id, forager.steps_alive) for forager in self.foragers]
        lifetimes_asc = sorted(lifetimes, key= lambda x: [1], reverse=True)
        if display:
            for f in lifetimes_asc:
                print(f'Forager {f[0]} survived {f[1]} steps')
        return lifetimes_asc
        
    def plot_choices(self):
        pass
        