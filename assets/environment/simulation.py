import random
import matplotlib.pyplot as plt
import seaborn as sns
sns.set_theme()
import os 
import shutil

from ..agents.forager import Forager, ForagerActions
from ..agents.hunter import Hunter
from ..agents.food import Food
from ..agents.ravine import Ravine

# * class SimulationAnalytics is appended to the bottom of this file
# * This is to avoid a circular import error.

# region Simulation
class Simulation():
    """
    The environment in which foragers search for food.
    """
    def __init__(self, width: int, height: int) -> None:
        self.width = width
        self.height = height
        self.grid = [[None for _ in range(width)] for _ in range(height)]
        self.object_count = 0
        self.area = self.width * self.height
        self.foragers: list[Forager] = []
        self.hunters: list[Hunter] = []
        self.grid_history = []
        self.num_steps = 0
        self.forager_age_limit = 25
        
        # attributes used for analysis
        self.gene_trends = {
            'average agility': [],
            'average perception': [],
            'average strength': [],
            'average endurance': []
        }

        self.total_mating_attempts = 0
        self.total_offspring_produced = 0
        self.total_sustenance_gained = 0
        self.total_foragers_lost = 0
        self.total_hunters_lost = 0
        self.total_foragers_eol = 0
        
        self.simulation_metrics = {
            'total_mating_attempts' : [],
            'total_offspring_produced' : [],
            'total_sustenance_gained' : [],
            'total_foragers_lost' : [],
            'total_hunters_lost' : [],
            'total_foragers_eol': []
        }
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
            replace: bool, 
            display: bool) -> None:
        """
        Runs the simulation.
        
        - Hunters move before foragers
        - Hunters do not eat food
        - Hunters must walk around ravines

        Args:
            steps (int): Number of simulation steps.
            replace (bool): Replace objects that are removed. 
            display (bool): Output information to stdout at each time step.

        Raises:
            MoveError: Simulation ends if an invalid move has been made.
            GridFull: Simulation ends if the grid runs out of empty space.
        """

        self.num_steps = steps
        for i, step in enumerate(range(steps)):
            print('*' + '*' * 52 + '*')
            print(f"{'Step'} {step+1:<45}\n")
            self.__display_simulation()
            self.__gather_gene_trend_data()
            # hunters move
            for hunter in self.hunters:
                if not hunter.alive:
                    continue
                from_xy, to_xy = hunter.get_next_move(self.grid, self.height, self.width)
                if to_xy == from_xy:
                    continue
                else:
                    # print(f'Hunter {hunter.id} moved from {(from_xy)} to {(to_xy)}')
                    from_x = from_xy[0]
                    from_y = from_xy[1]
                    new_x = to_xy[0] 
                    new_y = to_xy[1]
                
                    self.grid[new_y][new_x] = self.grid[from_y][from_x]
                    self.grid[from_y][from_x] = None
            
            # foragers move
            for i, forager in enumerate(self.foragers):
                if step % 10 == 0:
                    forager.mated_with.clear()
                    forager.incompatible_with.clear()
                    # Analyse attribute trends

                if forager.steps_alive >= self.forager_age_limit:
                    # Forager dies of old age to make room for offspring
                    forager.alive = False
                self.total_foragers_lost += 1
                self.total_foragers_eol += 1
                self.simulation_metrics['total_foragers_lost'].append(
                    (step, self.total_foragers_lost)
                )
                self.simulation_metrics['total_foragers_eol'].append(
                    (step, self.total_foragers_eol)
                )
                
                if not forager.alive:
                    continue
                forager.simulation_step = step
                forager.log_genes(display, i)
                print()
                # Coordinates of next step
                to_x, to_y = forager.get_next_step(self)
                # Object at next step
                next_step_obj = self.grid[to_y][to_x]
                if isinstance(next_step_obj, Food):
                    # Forager eats food
                    self.__forager_finds_food(forager, to_x, to_y, replace, step)
                    forager.steps_alive += 1
                elif isinstance(next_step_obj, Hunter):
                    # Forager engages hunter
                    if forager.hunger_increase():
                        self.__forager_finds_hunter(forager, to_x, to_y, replace, step)
                        forager.steps_alive += 1
                    else:
                        self.__forager_starves(forager, replace, step)
                elif isinstance(next_step_obj, Ravine):
                    # Forager moves through or around ravine
                    if forager.hunger_increase():
                        self.__forager_finds_ravine(forager, to_x, to_y)
                        forager.steps_alive += 1
                    else:
                        self.__forager_starves(forager, replace, step)
                elif isinstance(next_step_obj, Forager):
                    # Forager meets another forager    
                    if forager.hunger_increase():
                        # Produce offspring, or wait for the other forager to move
                        self.__forager_finds_forager(forager, to_x, to_y, step)
                        forager.steps_alive += 1
                    else:
                        self.__forager_starves(forager, replace, step)
                elif next_step_obj == None:
                    # Forager moves from one spot to another   
                    if forager.hunger_increase():
                        self.__forager_step(forager, to_x, to_y)
                        forager.steps_alive += 1
                    else:
                        self.__forager_starves(forager, replace, step)
                else:
                    raise MoveError
            print('*' + '-' * 52 + '*')
            if step != steps - 1:                
                print() 
            
    def setup_environment(self, objects: list) -> None:
        """
        Distributes a collection of objects in the simulation. 

        Args:
            objects (list): Collection of objects.
        """
        if len(objects) > self.area:
            raise GridFull
        else:
            for object in objects:
                self.__place_object(object)
    
    def save_forager_logs(self, run_name: str) -> None:
        """
        Saves the log of each forager in a txt file.

        Args:
            run_name (str): Directory name.
        """
        try:
            os.mkdir(f'logs/{run_name}')
        except:
            shutil.rmtree(f'logs/{run_name}')
            os.mkdir(f'logs/{run_name}')
            
        for forager in self.foragers:
            forager.get_log(run_name)
                
    def __display_simulation(self) -> None:
        """
        Outputs simulation to stdout.
        """
        d = {
            Forager: 'F',
            Ravine: 'R',
            Hunter: 'H',
            Food: '*'
        }
        for row in self.grid:
            print(" ".join([d.get(type(cell), '.') for cell in row]))
    
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
            # If placing ravine, checks are in place to ensure it does
            # not go out of bounds
            width = object.width
            height = object.height
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
            # Otherwise if desired cell is in bounds
            if self.__get_cell(x, y) == None:
                # Desired cell is empty then place objects
                self.grid[y][x] = object
                if isinstance(object, Forager):
                    # Tell forager where it is
                    object.current_coords = (x, y)
                    # Simulation attribute to keep track of foragers
                    self.foragers.append(object)
                elif isinstance(object, Hunter):
                    # Simulation attribute to keep track of hunters
                    self.hunters.append(object)
            else:
                # Desired cell is not empty so find a new one
                x, y = self.__find_random_empty_cell()
                self.grid[y][x] = object
                if isinstance(object, Forager):
                    # Tell forager where it is
                    object.current_coords = (x, y)
                    # Simulation attribute to keep track of foragers
                    self.foragers.append(object)
                elif isinstance(object, Hunter):
                    # Simulation attribute to keep track of hunters
                    self.hunters.append(object)
            
    def __ravine_buffer(self, x: int, y: int, 
                        ravine_width: int, ravine_height: int) -> bool:
        """
        Checks if a ravine is in bounds when placed at (x,y).

        Args:
            x (int): x coordinate.
            y (int): x coordinate.
            ravine_width (int): Ravine x coordinate.
            ravine_height (int): Ravine y coordinate.

        Returns:
            bool: True if ravine can be placed here.
        """
        if (y + ravine_height < self.height) and (x + ravine_width < self.width):
            return True
        else:
            return False
    
    def __get_cell(self, 
                   x: int, 
                   y: int) -> Forager | Hunter | Food | Ravine | None:
        """
        Gets the object at coordinate.

        Returns:
            list | None: object or None.
        """
        if 0 <= x < self.width and 0 <= y < self.height:
            return self.grid[y][x]
        return None

    def __find_random_empty_cell(self) -> tuple[int, int]:
        """
        Finds a random empty cell.

        Returns:
            tuple(int, int): (x,y) coordinates.
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
        
    def __forager_finds_food(self, 
                             forager: Forager, 
                             to_x: int, 
                             to_y: int, 
                             replace: bool,
                             step: int) -> None:
        """
        Handles removing the food from (to_x, to_y) and moving
        the forager there. 
        """
        # Foragers current coordinates
        from_x = forager.current_coords[0]
        from_y = forager.current_coords[1]
        # Get food object
        food = self.grid[to_y][to_x]
        # Forager eats the food
        forager.eat(food)
        # Move forager to cell with food and tell it its new position
        self.grid[to_y][to_x] = self.grid[from_y][from_x]
        self.grid[from_y][from_x] = None
        forager.current_coords = (to_x, to_y)
        # Add for simulation metrics
        self.total_sustenance_gained += food.sustenance_granted
        self.simulation_metrics['total_sustenance_gained'].append(
            (step, self.total_sustenance_gained)
        )
        if replace:
            # Replace eaten food with another at a random location
            f = Food()
            self.__place_object(f)
            
    def __forager_finds_hunter(self, 
                               forager: Forager, 
                               to_x: int, 
                               to_y: int, 
                               replace: bool,
                               step: int) -> None:
        """
        The forager fights or flees the hunter.
        If the forager fights and wins it takes the place of the hunter
        and a new hunter appears at a random location. If the forager
        loses then it dies and a new forager appears at a random
        location.
        \n
        If the forager flees and wins it spawns somewhere in the simulation
        at random. If the forager loses, it "dies" and a new forager 
        appears at a random location.

        Args:
            forager (Forager): Forager finding the hunter.
            to_x (int): Desired x coordinate.
            to_y (int): Desired y coordinate.
            replace (bool): Replace lost foragers or hunters.
        """
        # Foragers current coordinates
        from_x = forager.current_coords[0]
        from_y = forager.current_coords[1]
        # Get hunter object
        hunter = self.grid[to_y][to_x]
        if 'hide from hunter' in forager.evolved_abilities:
            # Forager moves to a random location without danger
            self.grid[from_y][from_x] = None
            self.__place_object(forager)
            forager.motivation_metrics['hunter encounters']['times hidden'] += 1
        elif 'zig zag past hunter' in forager.evolved_abilities:
            fa = ForagerActions(environment=self, forager=forager)
            steps = fa.steps_to_motivation(forager.current_motivation)
            forager.motivation_metrics['hunter encounters']['times zig zagged'] += 1
            if len(steps) > 2:
                if self.grid[2] != None:
                    # Move three steps ahead
                    if self.grid[steps[2][1]][steps[2][0]] == None:
                        self.grid[steps[2][1]][steps[2][0]] = self.grid[from_y][from_x]
                        self.grid[from_y][from_x] = None
                        forager.current_coords = (steps[2][0], steps[2][1])
                elif self.grid[1] != None:
                    # move two steps ahead if 3 isn't valid
                    if self.grid[steps[1][1]][steps[1][0]] == None:
                        self.grid[steps[2][1]][steps[2][0]] = self.grid[from_y][from_x]
                        self.grid[from_y][from_x] = None
                        forager.current_coords = (steps[2][0], steps[2][1])
        else:
            if 'camouflage' in forager.evolved_abilities:
                self.grid[to_y][to_x] = self.grid[from_y][from_x]
                self.grid[from_y][from_x] = None
                forager.current_coords = (to_x, to_y)  
                forager.motivation_metrics['hunter encounters']['times camouflaged'] += 1
                return
            decision, win = forager.engage_hunter(hunter)
            if decision == 'fight' and win:
                # Move forager to hunters location
                self.grid[to_y][to_x] = self.grid[from_y][from_x]
                self.grid[from_y][from_x] = None
                forager.current_coords = (to_x, to_y)
                self.total_hunters_lost += 1
                self.simulation_metrics['total_hunters_lost'].append(
                    (step, self.total_hunters_lost)
                )
                if replace:
                    # Replace hunter 
                    h = Hunter()
                    self.__place_object(h)
            elif decision == 'fight' and not win:
                # Forager lost and is removed
                self.grid[from_y][from_x] = None
                self.foragers.remove(forager)
                self.total_foragers_lost += 1
                self.simulation_metrics['total_foragers_lost'].append(
                    (step, self.total_foragers_lost)
                )
            elif decision == 'flee' and win:
                # Forager is placed in a random location
                self.grid[from_y][from_x] = None
                self.__place_object(forager)
            elif decision == 'flee' and not win:
                # Forager is caught and removed
                self.grid[from_y][from_x] = None
                self.foragers.remove(forager)
                self.total_foragers_lost += 1
                self.simulation_metrics['total_foragers_lost'].append(
                    (step, self.total_foragers_lost)
                )
            if not win and replace:
                # add new forager back to the environment
                new_forager = Forager()
                print('adding new forager', new_forager.id)
                self.__place_object(new_forager)
                
    def __forager_starves(self, forager: Forager, replace: bool, step: int) -> None:
        """
        Foragers hunger has reached 10. 
        It is removed from the simulation.

        Args:
            forager (Forager): Forager to be removed.
            replace (bool): Replace with another forager.
        """
        from_x = forager.current_coords[0]
        from_y = forager.current_coords[1]
        self.grid[from_y][from_x] = None
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
        side of the ravine to continue its journey, otherwise 
        the forager walks around the ravine.
        """
        def horizontal_step():
            """
            Take a horizontal step around the ravine.
            """ 
            # Try to walk right. If that isn't possible, walk left.
            new_x = to_x + 1 if to_x + 1 < self.width else to_x - 1
            self.grid[from_y][new_x] = self.grid[from_y][from_x]
            self.grid[from_y][from_x] = None
            forager.current_coords = (new_x, from_y)
            
        def vertical_step():
            """
            Take a vertical step around the ravine.
            """
            # Try to walk up. If that isn't possible, walk down.
            new_y = to_y + 1 if to_y + 1 < self.height else to_y - 1
            self.grid[new_y][from_x] = self.grid[from_y][from_x]
            self.grid[from_y][from_x] = None
            forager.current_coords = (from_x, new_y)
            
        from_x = forager.current_coords[0]
        from_y = forager.current_coords[1]
        ravine = self.grid[to_y][to_x]

        can_traverse = forager.traverse_ravine(ravine)
        log_match1 = f'{forager.id} successfully crossed ravine.'
        log_match2 = f'{forager.id} fails to cross ravine.'
        
        if abs(to_x - from_x) > abs(to_y - from_y):
            # Forager is moving horizontally    
            if can_traverse:
                # determine if moving left-to-right or right-to-left
                new_x_coord = to_x + ravine.width + 1 if to_x > from_x else to_x - ravine.width - 1
                # use foragers log to see if it attempted this jump before
                # If it did, walk up/down instead of jumping
                if log_match1 == str(forager.log[-1]) or log_match2 == str(forager.log[-1]):
                    vertical_step()
                elif 0 <= new_x_coord < self.width and not isinstance(self.grid[to_y][new_x_coord], Ravine):
                    # Make horizontal jump
                    self.grid[to_y][new_x_coord] = self.grid[from_y][from_x]
                    self.grid[from_y][from_x] = None
                    forager.current_coords = (new_x_coord, to_y)
                else:
                    # ravine is on simulation edge so step up/down instead
                    # Take a vertical step instead
                    vertical_step()
            else:
                # attributes too low to traverse so walk around
                vertical_step()
        else:
            # forager is moving vertically
            if can_traverse:
                # determine if moving up or down
                new_y_coord = to_y + ravine.height + 1 if to_y > from_y else to_y - ravine.height - 1
                if log_match1 == str(forager.log[-1]) or log_match2 == str(forager.log[-1]):
                # use foragers log to see if it attempted this jump before
                # If it did, walk right/left instead of jumping
                    horizontal_step()
                elif 0 <= new_y_coord < self.height and not isinstance(self.grid[new_y_coord][to_x], Ravine):
                    # Make vertical jump
                    self.grid[new_y_coord][to_x] = self.grid[from_y][from_x]
                    self.grid[from_y][from_x] = None
                    forager.current_coords = (to_x, new_y_coord)
                else:
                    # Ravine is on simulation edge so step right/left instead
                    horizontal_step()
            else:
                # attributes too low to traverse so walk around
                horizontal_step()
                    
    def __forager_finds_forager(self, 
                                forager: Forager, 
                                to_x: int, 
                                to_y: int,
                                step: int) -> None:
        """
        A compatibilty check takes place and the foragers may produce
        offspring which appears at a random location.
        """
        potential_mate = self.grid[to_y][to_x]
        if forager.is_compatible_with(potential_mate):
            offspring = forager.produce_offspring(potential_mate)
            self.__place_object(offspring)
            self.total_mating_attempts += 1
            self.total_offspring_produced += 1
            self.simulation_metrics['total_offspring_produced'].append(
                (step, self.total_offspring_produced)
            )
            self.simulation_metrics['total_mating_attempts'].append(
                (step, self.total_mating_attempts)
            )
        else:
            # foragers are incompatible, decide on something else to do.
            forager.current_motivation = None
            self.total_mating_attempts += 1
            self.simulation_metrics['total_mating_attempts'].append(
                (step, self.total_mating_attempts)
            )
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
        self.grid[to_y][to_x] = self.grid[from_y][from_x]
        self.grid[from_y][from_x] = None
        forager.current_coords = (to_x, to_y)
    
    def __gather_gene_trend_data(self):
        agility = 0
        perception = 0
        strength = 0
        endurance = 0
        for fo in self.foragers:
            agility += fo.agility
            perception += fo.perception
            strength += fo.strength
            endurance += fo.endurance
        self.gene_trends['average agility'].append(
            round(agility / len(self.foragers), ndigits=2)
            )
        self.gene_trends['average perception'].append(
            round(perception / len(self.foragers), ndigits=2)
            )
        self.gene_trends['average strength'].append(
            round(strength / len(self.foragers), ndigits=2)
            )
        self.gene_trends['average endurance'].append(
            round(endurance / len(self.foragers), ndigits=2)
            )

class GridFull(Exception):
    def __init__(self):
        self.message = 'Grid is full.\n'
        super().__init__(self.message)
        
class MoveError(Exception):
    def __init__(self):
        self.message = 'Invalid forager move.\n'
        super().__init__(self.message)

# TODO document this
# region Analytics
class SimulationAnalytics:
    """
    Processes and plots data gathered while running the simulation.
    """
    def __init__(self, simulation: Simulation) -> None:
        self.__grid = simulation
        self.__foragers = [forager for forager in self.__grid.foragers]
        
    def chart_compare_decisions(self) -> None:
        """
        Bar chart displaying the number of novel decisions compared to
        repeated decisions.
        """
        num_novel = 0
        num_decisions = 0
        for forager in self.__foragers:
            num_novel += forager.num_novel_decisions
            num_decisions += forager.num_decisions
        num_decisions = num_decisions - num_novel
        plt.bar(['Novel Decisions', 'Repeated Decisions'], [num_novel, num_decisions])
        plt.show()
    
    def chart_simulation_metrics(self) -> None:
        """
        Displays overall metrics from the simulation:
        - total mating attempts
        - total offspring produced
        - total sustenace gained
        - total foragers lost
        - total hunters lost
        - total foragers lost after reaching their age limit
        """
        keys = list(self.__grid.simulation_metrics.keys())
        key_labels = [label.split('_').title() for label in keys]
        values = list(self.__grid.simulation_metrics.values())
        final_values = []
        for value in values:
            if len(value) > 1:
                final_values.append(value[-1][1])
            else:
                final_values.append(0)
        plt.bar(key_labels, final_values)
        plt.show()
        
    def chart_gene_changes(self) -> None:
        """
        Plots a chart showing the average growth in dynamic attributes.
        Measurements are taken every 10 steps.
        """
        legend_labels = []
        for k, v in self.__grid.gene_trends.items():
            # attribute name is in form 'average "attribute"'
            attribute_name = k.split()[1].title()
            legend_labels.append(attribute_name)
            plt.plot(range(self.__grid.num_steps), v)
        plt.title('Average Gene Trends')
        plt.xlabel('Step')
        plt.ylabel('Gene Value')
        plt.legend(legend_labels)
        plt.show()
    
    def chart_motivations(self) -> None:
        """
        A bar chart displaying how many times each motivation was chosen.
        """
        keys = list(self.__grid.total_motivations.keys())
        values  = list(self.__grid.total_motivations.values())
        plt.bar(keys, values)
        plt.show()
    
    def chart_lifetime_lengths(self) -> None:
        """
        A bar chart displaying the lifetime length of each forager.
        """
        lifetimes = [(forager.id, forager.steps_alive) for forager in self.__foragers]
        lifetimes_asc = sorted(lifetimes, key=lambda x: [1], reverse=True)
        print(lifetimes_asc)
        life_lengths = []
        for f in lifetimes_asc:
            life_lengths.append(f[1])
        plt.bar(range(len(self.__foragers)), life_lengths)
        plt.show()
    
    def stdout_eol_foragers(self) -> None:
        """
        Displays a list of key metrics from foragers who survived until
        their age limit.
        """
        best_foragers = [forager for forager in self.__foragers if forager.steps_alive >= self.__grid.forager_age_limit]
        print(f'{len(best_foragers)} foragers survived to old age.\n')
        for forager in best_foragers:
            self.__print_motivation_metrics(forager)
        
    def stdout_steps_and_actions(self) -> None:
        """
        Displays each change in metrics alongside the step that it happened.
        """
        for k, v in self.__grid.simulation_metrics.items():
            print(f"{k}:")
            for step, value in v:
                print(f"Step {step}: {value}")
            print()    
    
    def __print_motivation_metrics(self, forager) -> None:
        """
        Displays full motivation metrics dictionary.
        """
        print(f'Forager {forager.id}\n')
        for motivation, details in forager.motivation_metrics.items():
            print(f'{motivation.title()}')
            if not isinstance(details, dict):
                print(f'{motivation.title()}: {details}')
                print()
            else:
                for k, v in details.items():
                    print(f'{k.title()}: {v}')
                print()
        print()
        