import math
import random
from random import randrange, choice
import tomllib
import numpy as np

from .mammal import Mammal
from .food import Food
from .hunter import Hunter
from .ravine import Ravine

# * class ForagerActions is appended to the bottom of this file
# * This is to avoid a circular import error.

# region Forager
class Forager(Mammal):
    """
    Agents who navigate the environment to eat, mate, adapt and evolve.
    """
    def __init__(self, sex: str = None, parents_genes: dict = None):
        if parents_genes is not None:
            # Derives genes from parents
            agility = parents_genes['agility']
            perception = parents_genes['perception']
            strength = parents_genes['strength']
            endurance = parents_genes['endurance']
        else:
            # Forager has no parents so genes init at random
            agility = float(randrange(1, 3))
            perception = float(randrange(1, 3))
            strength = float(randrange(1, 3))
            endurance = float(randrange(1, 3))
        super().__init__(agility, perception, strength, endurance)   
        self.type = 'Forager'
        self.alive = True
        
        if sex == None:
            self.sex = choice(['M', 'F'])
        else:
            self.sex = sex            
        if self.sex != 'M' and self.sex != 'F':
            raise ValueError('Sex must be \'M\' or \'F\'')
        
        with open('assets/agents/forager_config.toml', 'rb') as f:
            self.config = tomllib.load(f)
            self.hunger = self.__validate(self.config['hunger'], 'hunger', 10.0)
            self.bravery = self.__validate(self.config['bravery'], 'bravery', 10.0)
            self.compat_diff = self.__validate(self.config['compat_diff'], 'compat_diff', 1)
            self.decay_factor = self.__validate(self.config['decay_factor'], 'decay_factor', 1)
            self.hunger_combin = self.__validate(self.config['hunger_combinator'], 'hunger_combinator', 1)
            self.boost1_threshold = self.__validate(self.config['boost1_threshold'], 'boost1_threshold', 10)
            self.boost2_threshold = self.__validate(self.config['boost2_threshold'], 'boost2_threshold', 10)
            self.positive_multiplier = self.__validate(self.config['positive_multiplier'], 'positive_multiplier', 1)
        
        self.compatability_threshold = self.__get_compatibility()
        
        # Offspring born with better genes have better abilities 
        self.evolved_abilities = []
        # Random weights enable foragers to have unique 'personalities'
        self.motivation_weights = {
            'nearest food': random.uniform(0.01, 0.3),
            'furthest food': random.uniform(0.01, 0.3),
            'most sustaining food': random.uniform(0.01, 0.3),
            'nearest forager': random.uniform(0.01, 0.3),
            'furthest forager': random.uniform(0.01, 0.3),
            'most compatible forager': random.uniform(0.01, 0.3)
        }
        
        # * Attributes necessary for navigation
        self.current_coords = None
        self.destination_coordinates = None
        
        # * Attributes emulating persistent memory
        self.current_motivation = None 
        self.successful_motivations = []
        self.mated_with = [] # Foragers mated with
        self.incompatible_with = [] # Foragers unable to mate with
        self.explored_coords = [] # Explored coordinates
        self.log = [] # Log of actions
        self.gene_log = [] # Log of gene updates

        # * Attributes for analysis
        self.steps_alive = 0 # Number of simulation steps survived
        self.motivation_metrics = {
            'food encounters': {
                'num encounters': 0,
                'total sustenance gained': 0,
                'foods tasted': []
            },
            'offspring produced': 0,
            'nearest food': {
                'times chosen': 0,
                'successful outcomes': 0,
                'total time': 0,
                'average time': 0,
            },
            'furthest food': {
                'times chosen': 0,
                'successful outcomes': 0,
                'total time': 0,
                'average time': 0,
            },
            'most sustaining food': {
                'times chosen': 0,
                'successful outcomes': 0,
                'total time': 0,
                'average time': 0,
            },
            'nearest forager': {
                'times chosen': 0,
                'successful outcomes': 0,
                'total time': 0,
                'average time': 0,
            },
            'furthest forager': {
                'times chosen': 0,
                'successful outcomes': 0,
                'total time': 0,
                'average time': 0,
            },
            'most compatible forager': {
                'times chosen': 0,
                'successful outcomes': 0,
                'total time': 0,
                'average time': 0,
            },  
            'hunter encounters': {
                'num encounters': 0,
                'times fought': 0,
                'times fled': 0,
                'times hidden': 0,
                'times zig zagged': 0,
                'times camouflaged': 0,
                'times won': 0,
                'times lost': 0
            },
            'ravine encounters': {
                'times jumped': 0,
                'times attempted': 0,
            }
        }
    
    def set_motivation(self, environment, actions) -> str:
        """
        Set a motivation and store metrics.
        """
        self.current_motivation = actions.set_motivation()
        self.__log_statement(f'Forager {self.id} is going to find {self.current_motivation}.')
        self.motivation_metrics[self.current_motivation]['times chosen'] += 1
        environment.total_motivations[self.current_motivation] += 1
    
    def get_next_step(self, environment) -> tuple[int, int]:
        """
        Sets a motivation and gets the coordinates to be one step closer 
        to fulfilling it.

        Args:
            environment (Grid): The simulation environment.

        Returns:
            Tuple[int, int]: (x, y) coordinate to move the forager to.
        """
        self.__alive()
        actions = ForagerActions(environment, self)
        if self.current_motivation == None:
            self.set_motivation(environment, actions)

        # Get coordinates of destination to find coordinate of next step
        self.destination_coordinates = actions.get_destination_coordinates(self.current_motivation)
        next_coordinate = actions.get_next_coordinate(self.current_coords, self.destination_coordinates)
        self.explored_coords.append(next_coordinate)
        
        if self.current_coords == self.destination_coordinates:
            # Motivation has been fulfilled
            self.__log_statement(f'Forager {self.id} found {self.current_motivation}.')
            self.motivation_metrics[self.current_motivation]['successful outcomes'] += 1
            self.motivation_metrics[self.current_motivation]['total time'] += 1
            self.successful_motivations.append(self.current_motivation) 
            # Set new motivation
            self.set_motivation(environment, actions)
        else:
            self.motivation_metrics[self.current_motivation]['total time'] += 1
            self.motivation_metrics[self.current_motivation]['average time'] = str(
                f"{(self.motivation_metrics[self.current_motivation]['total time'] / environment.num_steps)*100}%"
            )
        return next_coordinate
            
    def eat(self, food: Food) -> None:
        """
        Forager eats food.
        
        Reduces:
            - hunger
            - bravery 
        """
        # Reduce attributes
        self.hunger = max((self.hunger - food.sustenance_granted), 0.0)
        self.bravery = max((self.hunger - food.sustenance_granted / 2), 0.0)
        # Log data
        self.__log_statement(f'{self.id} ate the {food.name}.\n')
        self.motivation_metrics['food encounters']['num encounters'] += 1
        self.motivation_metrics['food encounters']['total sustenance gained'] += food.sustenance_granted
        self.motivation_metrics['food encounters']['foods tasted'].append(food.name)
    
    def hunger_increase(self) -> bool:
        """
        Forager gets hungrier.
        
        Increases:
            - hunger
            - bravery
        """
        # Reduce attributes
        self.hunger = min((self.hunger + self.hunger_combin), 10)
        self.bravery = min((self.bravery + self.hunger_combin / 2), 10)
        
        if self.hunger == 10:
            self.__log_statement(f'{self.id} starved.')
            self.alive = False

        return self.alive
    
    def engage_hunter(self, hunter: Hunter) -> tuple[str, bool]:
        """
        If the forager is brave (and hungry) it will fight the hunter,
        otherwise it will try to run away.

        Args:
            hunter (Hunter): The hunter in the foragers path.

        Returns:
            tuple[str, bool]: The foragers decision and outcome.
        """
        if self.bravery > 5:
            # Forager is fighting the hunter
            decision, win = self.__fight_hunter(hunter)
            self.motivation_metrics['hunter encounters']['num encounters'] += 1
            self.motivation_metrics['hunter encounters']['times fought'] += 1
            if win:
                self.motivation_metrics['hunter encounters']['times won'] += 1
            else:
                self.motivation_metrics['hunter encounters']['times lost'] += 1
            return (decision, win)    
        else:
            # Forager tries to flee
            decision, win = self.__flee_hunter(hunter)
            self.motivation_metrics['hunter encounters']['num encounters'] += 1
            self.motivation_metrics['hunter encounters']['times fought'] += 1
            if win:
                self.motivation_metrics['hunter encounters']['times won'] += 1
            else:
                self.motivation_metrics['hunter encounters']['times lost'] += 1
            return (decision, win)    
    
    def traverse_ravine(self, ravine: Ravine) -> bool:
        """
        Evaluates the chance of crossing the ravine.

        Args:
            ravine (Ravine): The ravine the forager must cross.

        Returns:
            bool: True if successful, False if not.
        """
        # Importance of attributes for crossing ravines
        weights = {
            'agility': 0.4,
            'endurance': 0.3,
            'perception': 0.3
        }
        weighted_sum = (self.agility * weights['agility'] + 
                        self.endurance * weights['endurance'] + 
                        self.perception * weights['perception'])
        
        if weighted_sum > ravine.skill_required:
            self.__log_statement(f'{self.id} successfully crossed ravine.')
            self.motivation_metrics['ravine encounters']['times jumped'] += 1
            self.motivation_metrics['ravine encounters']['times attempted'] += 1
            return True
        else:
            self.__log_statement(f'{self.id} fails to cross ravine.')
            self.motivation_metrics['ravine encounters']['times attempted'] += 1
            return False
        
    def is_compatible_with(self, partner: 'Forager') -> bool:
        """
        Compares the compatability threshold of self and another forager.
        If the difference between two foragers compat thresholds are 
        within compat_diff, they produce offspring.

        Args:
            partner (Forager): Potential mate.
            max_diff (float): Acceptable difference between thresholds. 
            
        Returns:
            bool: True, if compatible otherwise false.
        """
        if partner in self.mated_with:
            # Don't mate with any forager more than once
            return False
        # Recalculate compatibility as attributes may have changed
        self.__get_compatibility()
        partner.__get_compatibility()
        # Determine if foragers are compatible and produce offspring
        if (self.sex == 'M' and partner.sex == 'F' or 
            self.sex == 'F' and partner.sex == 'M'):
            # Foragers are sexually compatible
            if math.isclose(self.compatability_threshold, 
                       partner.compatability_threshold, 
                       rel_tol=self.config['compat_diff']):
                # Foragers compatibility thresholds are within compat_diff
                self.__log_statement(f'{self.id} ({self.sex}: {self.compatability_threshold:.2f}) '
                                     f'and {partner.id} ({partner.sex}: {partner.compatability_threshold:.2f}) are compatible.')
                return True
            else:
                # Foragers are not compatible
                self.__log_statement(f'{self.id} ({self.compatability_threshold:.2f}) '
                                     f'and {partner.id} ({partner.compatability_threshold:.2f}) '
                                     'are not compatible.')
                self.incompatible_with.append(partner)
                self.motivation_metrics[self.current_motivation]['times chosen'] += 1
                return False
        else:
            # Foragers are not compatible
            self.__log_statement(f'{self.id} ({self.sex}) and {partner.id} '
                                 f'({partner.sex}) are not compatible.')
            self.incompatible_with.append(partner)
            self.motivation_metrics[self.current_motivation]['times chosen'] += 1
            return False
    
    def produce_offspring(self, partner: 'Forager') -> 'Forager':
        """
        Produces a new forager, with genes dervied from its parents.
        """
        # Get a combination of self and partners genes
        offspring_dict = {
            'agility': min(10.0, ((self.agility + partner.agility) / 2 + random.uniform(1.5, 3))),
            'perception': min(10.0, ((self.perception + partner.perception) / 2 + random.uniform(1.5, 3))),
            'strength': min(10.0, ((self.strength + partner.strength) / 2 + random.uniform(1.5, 3))),
            'endurance': min(10.0, ((self.endurance + partner.endurance) / 2 + random.uniform(1.5, 3))),
        }
        # Create offspring
        offspring = Forager(parents_genes=offspring_dict)
        
        self.__log_statement(f'{self.id} and {partner.id} '
                          f'produced offspring {offspring.id}.')
        self.mated_with.append(partner)
        self.motivation_metrics['offspring produced'] += 1
        
        return offspring
    
    def log_genes(self, display: bool, forager_num: int) -> None:
        """
        Logs changes in genes throughout the simulation.

        Args:
            display (bool): Display changes in stdout.
            forager_num (int): Forager number out of total in simulation.
        """
        genes = {
            'id': self.id,
            'hunger': self.hunger,
            'bravery': self.bravery,
            'agility': self.agility,
            'perception': self.perception,
            'strength': self.strength,
            'endurance': self.endurance,
            'current_coords': self.current_coords,
            'timestep': len(self.gene_log)
        }
        self.gene_log.append([genes])
        if display:
            print()
            print('*' + '-' * 24 + '*')
            print(f'| Forager {forager_num + 1:<4}| {self.id:<9}|')
            print('*' + '-' * 24 + '*')
            # stdout genes
            a = dict(self.gene_log[-1][0])
            for key, value in a.items():
                if isinstance(value, str):
                    # Don't display attribute
                    continue
                elif key == 'timestep':
                    # Don't display attribute
                    continue
                elif key == 'current_coords':
                    # Format output for even width
                    label = '(x,y)'
                    x,y = value
                    print(f"| {label:<12}| {'('+f'{x:<2}'}, {f'{y:>2}' + ')'} |")
                else:
                    # Display a '+' or '-' next to changed attributes
                    icon = ' '
                    if len(self.gene_log) > 1:
                        if dict(self.gene_log[-2][0])[key] > value:
                            icon = '-'
                        elif dict(self.gene_log[-2][0])[key] < value:
                            icon = '+'
                        else:
                            icon = ''
                    print(f'| {key.title():<12}| {value:>6.2f} {icon:<1} |')
            print('*' + '-' * 24 + '*')
    
    def get_log(self, save_as_txt: bool) -> list | None:
        """
        Returns the actions of the forager as a list of strings or
        saves them in a txt file.

        Args:
            save_as_txt (bool): If true, save actions as a txt file

        Returns:
            list | None: List of strings or None if txt files are saved.
        """
        if not save_as_txt:
            return self.log
        else: 
            with open(f'simulation/logs/{self.id}_log.txt', 'r') as f:
                for line in self.log:
                    f.write(line)
    
    def __get_compatibility(self) -> float:
        """
        Uses bravery, strength and perception to determine the 
        "attractiveness" of the forager.
        """
        compatibility = (self.bravery + self.strength + (self.perception * 1.5))
        return compatibility
    
    def __fight_hunter(self, hunter: Hunter) -> tuple[str, bool]:
        """
        A weighted sum of the foragers strength, endurance and agility 
        are compared to the hunters. The loser is made inactive.

        Args:
            hunter (Hunter): The hunter the forager is fighting

        Returns:
            tuple[str, bool]: The foragers decision to fight, and the
                outcome.
        """
        # Importance of attributes for fighting hunter
        weights = {
            'agility': 0.3,
            'strength': 0.4,
            'endurance': 0.2
        }
        self_weighted_sum = (self.agility * weights['agility'] + 
                             self.strength * weights['strength'] + 
                             self.endurance * weights['endurance'])
        
        hunter_weighted_sum = (hunter.agility * weights['agility'] + 
                               hunter.strength * weights['strength'] + 
                               hunter.endurance * weights['endurance'])
        
        if self_weighted_sum > hunter_weighted_sum:
            hunter.alive = False
            self.__log_statement(f'{self.id} beat hunter {hunter.id}.')
        else:
            self.alive = False
            self.__log_statement(f'{self.id} lost to hunter {hunter.id}.')
        return ('fight', self.alive)
    
    def __flee_hunter(self, hunter: Hunter) -> tuple[str, bool]:
        """
        A weighted sum of the foragers agility, endurance and perception
        are compared to the hunters. The loser is made inactive.
        """
        # Importance of attributes for fleeing hunter
        weights = {
            'agility': 0.3,
            'endurance': 0.4,
            'perception': 0.2
        }
        self_weighted_sum = (self.agility * weights['agility'] +
                             self.endurance * weights['endurance'] +
                             self.perception * weights['perception'])
        
        hunter_weighted_sum = (hunter.agility * weights['agility'] +
                               hunter.endurance * weights['endurance'] +
                               hunter.perception * weights['perception'])
        
        if self_weighted_sum > hunter_weighted_sum:
            self.__log_statement(f'{self.id} fled hunter {hunter.id}.')
        else:
            self.alive = False
            self.__log_statement(f'{self.id} was caught by hunter {hunter.id}.')
        return ('flee', self.alive)
    
    def __validate(self, 
                   att: float, 
                   att_name: str, 
                   max: float) -> float | ValueError:
        """
        Validates configuration file attributes.
        """
        if max == 1:
            if att > 1 or att < 0:
                raise ValueError(f'config: Value {att} out of range 0-1 '
                                 f'for {att_name}.\n')
        if max == 10.0:
            if att > 10.0 or att < 0.0:
                raise ValueError(f'config: Value {att} out of range 0.0-10.0 '
                                 f'for {att_name}.\n')
        return att
    
    def __log_statement(self, statement: str) -> None:
        """
        Saves and outputs forager actions to stdout.
        """
        print(statement)
        self.log.append(statement)
                    
    def __alive(self) -> 'InvalidForager':
        """
        Check to ensure dead foragers do not perform actions.
        """
        if self.alive == False:
            raise InvalidForager(self.id)
        
    def __str__(self) -> str:
        return f'Forager {self.id}.\n'

class InvalidForager(Exception):
    """
    Ensures dead foragers do not perform actions.
    """
    def __init__(self, forager_id):
        self.message = f'{forager_id} should be inactive.'
        super().__init__(self.message)
        
# region Actions
class ForagerActions():
    """
    Responsible for setting the foragers motivation and finding the 
    steps to fulfil it.
    """
    def __init__(self, environment, forager: Forager):
        self.environment = environment
        self.forager = forager
        # All foods and foragers in the environment
        self.foods = self.__find_all(Food)
        self.foragers = self.__find_all(Forager)
        self.hunters = self.__find_all(Hunter)
    
    def set_motivation(self) -> str:
        """
        Gets a motivation such as finding food or a mate.

        Returns:
            str: The motivation.
        """
        def softmax(values: list):
            """
            Applies softmax to a list of novelty values to transform
            them into probabilities.

            Args:
                values (list): List of novelty values.

            Returns:
                list: List of probabilities.
            """
            exp_values = [math.exp(value) for value in values]
            sum_values = sum(exp_values)
            return [exp_value / sum_values for exp_value in exp_values]
            
        motivations = ['nearest food', 'furthest food', 'most sustaining food', 
                   'nearest forager', 'furthest forager', 'most compatible forager']

        # Abilities granted to foragers after evolution
        if self.forager.agility > 7:
            self.forager.evolved_abilities.append('zig zag past hunter')
        elif self.forager.perception > 5:
            self.forager.evolved_abilities.append('sniff food')
        elif self.forager.perception == 9 and self.forager.agility == 9:
            self.forager.evolved_abilities.append('camouflage')
        
        # Give each choice a novelty value
        novelty_values = [(self.novelty_value(motivation)) for motivation in motivations]
        # Softmax normalised probabilities for novelty values
        probabilities = softmax(novelty_values)
        # Combine each motivation with its probability of being selected
        motiv_prob = list(zip(motivations, probabilities))
        # Choose a motivation based on probability and extract str
        chosen_motivation = random.choices(motiv_prob, weights=[prob for _, prob in motiv_prob])[0][0]
        return chosen_motivation
    
    def novelty_value(self, motivation) -> float:
        """
        Transforms a motivation into a score.

        Args:
            motivation (str): The motivation of the forager.
        Returns:
            float: A value that allows comparison to other motivations.
        """
        # Get initial novelty value
        novelty_value = self.forager.motivation_weights[motivation]
        
        # Add bias towards novel motivations
        if motivation not in self.forager.successful_motivations:
            novelty_value += math.log(self.forager.positive_multiplier + 1.2, 10)
        else:
            novelty_value *= self.forager.decay_factor
        # Check if level 1 boosts can be applied
        if motivation == 'nearest food' or motivation == 'nearest forager':
            if (self.forager.perception > self.forager.boost1_threshold 
                or self.forager.agility > self.forager.boost1_threshold):
                novelty_value += math.log(self.forager.positive_multiplier + 1, 10)
        elif motivation == 'furthest food' or motivation == 'furthest forager':
            if (self.forager.strength > self.forager.boost1_threshold
                or self.forager.endurance > self.forager.boost1_threshold):
                novelty_value += math.log(self.forager.positive_multiplier + 1, 10)
        # Check if level 2 boosts can be applied
        if motivation == 'most sustaining food':
            if (self.forager.strength > self.forager.boost2_threshold
                or self.forager.perception > self.forager.boost2_threshold):
                novelty_value += math.log(self.forager.positive_multiplier + 1.1, 10)        
        if motivation == 'most compatible forager':
            if (self.forager.endurance > self.forager.boost2_threshold
                or self.forager.agility > self.forager.boost2_threshold):
                novelty_value += math.log(self.forager.positive_multiplier + 1.1, 10)
        
        # Skilled foragers are more likely to explore     
        if (len(self.forager.evolved_abilities) > 0
            and choice == 'furthest food'
            or choice == 'furthest forager'):
            choice_weight += math.log(self.forager.positive_multiplier + 1.2, 10)
        
        # add benefits from boosts in here
        if self.forager.hunger > 4:
            # forager is hungry so lean towards eating
            if motivation == 'nearest food':
                novelty_value += math.log(self.forager.positive_multiplier + 1.1, 10)
            elif motivation == 'most sustaining food' and 'sniff food' in self.forager.evolved_abilities:
                # forager knows the nearest food *is* is the most sustaining
                if self.steps_to_motivation('nearest food') == self.steps_to_motivation('most sustaining food'):
                    novelty_value += math.log(self.forager.positive_multiplier + 1.2, 10)
            elif motivation == 'furthest food':
                novelty_value += math.log(self.forager.positive_multiplier + 1.1, 10)
        
        if novelty_value < 0:
            raise ValueError
        else:
            self.forager.motivation_weights[motivation] = novelty_value
            return novelty_value

    def get_destination_coordinates(self, motivation: str) -> tuple[int, int]:
        # needs to set target_coords in the forager
        # * must return (x,y) coordinate
        """
        Finds the coordinates that mark the destination of the foragers
        motivation.
        

        Raises:
            TargetError: Unrecognised motivation.

        Returns:
            tuple: (x,y) coordinates of destination.
        """
        target_coords = None
        if motivation == 'nearest food':
            target_coords = self.__find_nearest_food()
        elif motivation == 'furthest food':
            target_coords = self.__find_furthest_food()
        elif motivation == 'most sustaining food':
            target_coords = self.__find_most_sustenance()
        elif motivation == 'nearest forager':
            target_coords = self.__find_nearest_forager()
        elif motivation == 'furthest forager':
            target_coords = self.__find_furthest_forager()
        elif motivation == 'most compatible forager':
            target_coords = self.__find_most_compatible_forager()
        else:
            raise TargetError(f'Invalid motivation: {self.forager.current_motivation}')
        return target_coords

    def get_next_coordinate(self, current_coords, object_loc) -> tuple[int, int]:
        """
        Get's the coordinates of the next step towards to object.
        
        Args:
            object_loc (tuple(int,int)): Destination coordinates.
        """
        new_x, new_y = 0, 0
        # Compare the abs difference between current and dest. x and y coords
        if (abs(object_loc[0] - current_coords[0]) > 
            abs(object_loc[1] - current_coords[1])):
            # abs diff of x coordinates is greater so move horizontally
            if object_loc[0] > current_coords[0]:
                # Move one step to the right
                new_x = 1
            elif object_loc[0] < current_coords[0]:
                # Move one step to the left
                new_x = -1
            new_x += current_coords[0]
            # Return new x and current y coord
            return new_x, current_coords[1]
        else:
            # abs diff of y coordinates is greater so move vertically
            if object_loc[1] > current_coords[1]:
                # Move one step up
                new_y = 1
            elif object_loc[1] < current_coords[1]:
                # Move one step down
                new_y = -1
            new_y += current_coords[1]
            # Return x and new y coord
            return current_coords[0], new_y
        
    def steps_to_motivation(self, motivation: str) -> list:
        """
        Gets steps from the foragers current location to a destination.

        Args:
            choice (str): The motivation of the forager.

        Returns:
            list: list of (x,y) coordinates.
        """
        steps = []
        current_coords = self.forager.current_coords
        destination_coords = self.get_destination_coordinates(motivation)
        while current_coords != destination_coords:
            next_coord = self.get_next_coordinate(current_coords, destination_coords)
            current_coords = next_coord
            steps.append(next_coord)
        return steps
    
    def __find_all(self, object_class: Food | Forager | Hunter) -> list:
        """
        Finds all coordinates of food, foragers or hunters in the
        simulation.

        Args:
            object_class (Food | Forager | Hunter): Object class.

        Returns:
            list: List of coordinates where objects reside.
        """
        objs = []
        # Iterate through environment
        for y in range(self.environment.height):
            for x in range(self.environment.width):
                if isinstance(self.environment.grid[y][x], object_class):
                    simulation_obj = self.environment.grid[y][x]
                    obj_dict = {}
                    if simulation_obj.id == self.forager.id:
                        # Ignore own location
                        continue
                    # Gets details about objects
                    if object_class == Food:
                        obj_dict['id'] = simulation_obj.id
                        obj_dict['type'] = 'Food'
                        obj_dict['key_attribute'] = simulation_obj.sustenance_granted
                        obj_dict['location'] = (x,y)
                    elif object_class == Forager:
                        obj_dict['type'] = 'Forager'
                        obj_dict['key_attribute'] = simulation_obj.compatability_threshold
                        obj_dict['location'] = (x,y)
                    elif object_class == Hunter:
                        obj_dict['id'] = simulation_obj.id
                        obj_dict['type'] = 'Hunter'
                        obj_dict['key_attribute'] = simulation_obj.strength
                        obj_dict['location'] = (x,y)
                    objs.append(obj_dict)
        return objs
        
    def __find_nearest_food(self) -> tuple[int, int]:
        """
        Finds the (x,y) coordinate of the nearest food.
        """
        food_locations = []
        for food in self.foods:
            food_locations.append(food['location'])
        output = self.__get_nearest(food_locations)
        if output == None:
            raise ValueError(f'Output: {output}')
        return output
    
    def __find_furthest_food(self) -> tuple[int, int]:
        """
        Finds the (x,y) coordinate of the furthest food.
        """
        food_locations = []
        for food in self.foods:
            food_locations.append(food['location'])
        output = self.get_furthest(food_locations)
        if output == None:
            raise ValueError(f'Output: {output}')
        return output
    
    def __find_most_sustenance(self) -> tuple[int, int]:
        """
        Finds the (x,y) coordinate of the most sustaining food.
        """
        food_locations = []
        food_sus = float('inf')
        for food in self.foods:
            if food['key_attribute'] < food_sus:
                food_sus = food['key_attribute']
                food_locations.append(food)
        output = food_locations[-1]['location']
        if output == None:
            raise ValueError(f'Output: {output}')
        return output
                
    def __find_nearest_forager(self) -> tuple[int, int]:
        """
        Finds the (x,y) coordinate of the nearest forager.
        """
        if len(self.foragers) == 0:
            output = self.__find_nearest_food()
            if output == None:
                raise ValueError(f'Output: {output}')
            return output
        else:
            forager_locations = []
            for forager in self.foragers:
                forager_locations.append(forager['location'])
            output = self.__get_nearest(forager_locations)
            if output == None:
                raise ValueError(f'Output: {output}')
            return output
    
    def __find_furthest_forager(self) -> tuple[int, int]:
        """
        Finds the (x,y) coordinate of the furthest forager.
        """
        if len(self.foragers) == 0:
            output = self.__find_furthest_food()
            if output == None:
                raise ValueError(f'Output: {output}')
            return self.__find_furthest_food()
        else:
            forager_locations = []
            for forager in self.foragers:
                forager_locations.append(forager['location'])
            output = self.get_furthest(forager_locations)
            if output == None:
                raise ValueError(f'Output: {output}')
            return self.get_furthest(forager_locations)
        
    def __find_most_compatible_forager(self) -> tuple[int, int]:
        """
        Finds the (x,y) coordinate of the forager with the most similar
        compatibility threshold.
        """
        if len(self.foragers) == 0:
            # no potential mates
            # go and look for food
            return self.__find_most_sustenance()
        else:
            forager_locations = []
            compatibility = float('inf')
            for forager in self.foragers:
                if forager['key_attribute'] < compatibility:
                    compatibility = forager['key_attribute']
                    forager_locations.append(forager)
            output = forager_locations[-1]['location']
            if output == None:
                raise ValueError(f'Output: {output}')
            return output
        
    def __manhattan_distance(self, object_loc: tuple[int, int]) -> int:
        """
        Manhattan distance between self.current_forager and object.

        Args:
            object_loc (tuple(int,int)): x, y coordinate of object.
        """
        return (abs(object_loc[0] - self.forager.current_coords[0]) + 
                abs(object_loc[1] - self.forager.current_coords[1]))
    
    def __sort_by_nearest(self, locations: list) -> list:
        """
        Sort distance of food or foragers in ascending order.

        Args:
            locations (list): List of (x,y) coordinates.

        Returns:
            list: Sorted list of (x,y) coordinates.
        """
        objs = []
        closest_obj = None
        shortest_distance = float('inf')    
        for obj_loc in locations:
            distance = self.__manhattan_distance(obj_loc)
            if distance < shortest_distance:
                shortest_distance = distance
                closest_obj = obj_loc
                objs.append(closest_obj)
        return objs
    
    def __sort_by_furthest(self, locations: list) -> list:
        """
        Sort a list of food or forager objects in descending order.

        Args:
            locations (list): List of (x,y) coordinates.

        Returns:
            list: Sorted list of (x,y) coordinates.
        """
        objs = self.__sort_by_nearest(locations)
        objs.reverse()
        return objs
    
    def __get_nearest(self, locations: list) -> tuple[int, int]:
        """
        Get the coordinates of the nearest food or forager.

        Args:
            locations (list): list of (x,y) coordinates

        Returns:
            tuple: (x,y) coordinate of the nearest object
        """
        objs = self.__sort_by_nearest(locations)
        return objs[0]
    
    def get_furthest(self, locations: list) -> tuple[int, int]:
        """
        Gets the coordinates of the furthest food or forager.

        Args:
            locations (list): list of (x,y) coordinates.

        Returns:
            tuple: (x,y) coordinate of the furthest object.
        """
        objs = self.__sort_by_furthest(locations)
        return objs[0]
        
class TargetError(Exception):
    """
    Ensure the Forager has a motivation.
    """
    def __init__(self, message):
        super().__init__(message)