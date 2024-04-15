from math import isclose
from random import randrange, choice
import tomllib
from typing import Tuple

from .mammal import Mammal
from .food import Food
from .hunter import Hunter
from .ravine import Ravine
# from ..environment.grid import Grid


class Forager(Mammal):
    def __init__(self, sex: str = None):
        # Set superclass attributes
        agility = float(randrange(2, 9))
        perception = float(randrange(1, 6))
        strength = float(randrange(2, 8))
        endurance = float(randrange(2, 9))
        super().__init__(agility, 
                        perception, strength, endurance)
        # Set attributes from config file
        with open('simulation/agents/forager_config.toml', 'rb') as f:
            self.config = tomllib.load(f)
            self.hunger = self.__validate(self.config['hunger'], 10.0)
            self.bravery = self.__validate(self.config['bravery'], 10.0)
            self.compat_diff = self.__validate(self.config['compat_diff'], 1)
            self.hunger_combin = self.__validate(self.config['hunger_combinator'], 1)
        
        # sex is either random or set on init
        if sex == None:
            self.sex = choice(['M', 'F'])
        else:
            self.sex = sex
        if self.sex != 'M' and self.sex != 'F':
            raise ValueError('Sex must be \'M\' or \'F\'')
        # Set default attributes
        self.compatability_threshold = self.__get_compatibility()
        self.alive = True
        self.type = 'Forager'
        # Current coordinates of forager
        self.current_location = None
        self.last_location = None
        self.explored_coordinates = []
        self.log = []
        self.attribute_log = []
        
    # region get next move 
    def get_next_move(self, environment) -> Tuple[int, int]:
        # get vague idea of where food is
        # choice of explore or go for food
        # have a memory of places explored
        # needs to return current_location and x,y of where to go
        # then Grid.move_object can be used.
        # foragers can determine if exploring, eating or mating are priorities
        # ? maybe just have a "find_nearest_food()" function
        def get_layout():
            """
            Inspects the environment to find food.
            """
            food_locations = []
            for y in range(environment.height):
                for x in range(environment.width):
                    if isinstance(environment.grid[y][x], Food):
                        food_locations.append((x,y))
            return food_locations
        
        def get_distance(food_loc):
            """
            Gets the manhattan distance between the forager and food.
            """
            return (abs(food_loc[0] - self.current_location[0]) + 
                    abs(food_loc[1] - self.current_location[1]))
            
        def move_to_food(food_location):
            """
            Get's coordinates one step closer to food.
            """
            new_x, new_y = 0, 0
            if (abs(food_location[0] - self.current_location[0]) > 
                abs(food_location[1] - self.current_location[1])):
                if food_location[0] > self.current_location[0]:
                    new_x = 1
                elif food_location[0] < self.current_location[0]:
                    new_x = -1
                new_x += self.current_location[0]
                return new_x, self.current_location[1]
            else:
                if food_location[1] > self.current_location[1]:
                    new_y = 1
                elif food_location[1] < self.current_location[1]:
                    new_y = -1
                new_y += self.current_location[1]
                return self.current_location[0], new_y
        
        food_locations = get_layout()
        closest_food = None
        closest_distance = float('inf')
        for food_loc in food_locations:
            distance = get_distance(food_loc)
            if distance < closest_distance:
                closest_distance = distance
                closest_food = food_loc
        
        return move_to_food(closest_food)
        
    def eat(self, food: Food) -> None:
        """
        Alters attributes.\n
        Going down:
            - hunger
            - bravery \n
        Going up:
            - agility
            - perception
            - strength
            - endurance
        """
        self.__check_death()
        
        self.old_hunger = self.hunger
        self.hunger = max((self.hunger - food.sustenance_granted), 0.0)
        self.bravery = max((self.hunger - food.sustenance_granted / 2), 0.0)
        
        self.agility = min((self.agility + food.sustenance_granted / 2), 10.0)
        self.perception = min((self.perception + food.sustenance_granted / 2), 10.0)
        self.strength = min((self.strength + food.sustenance_granted / 2), 10.0)
        self.endurance = min((self.endurance + food.sustenance_granted / 2), 10.0)
        self.__log_statement(f'{self.id} ate the {food.name}.\n{self.id}\'s hunger decreased. ({self.old_hunger:.2f} -> {self.hunger:.2f}).\n')
    
    def hunger_increase(self) -> None:
        """
        Alters attributes.\n
        Going down:
            - agility
            - perception
            - strength
            - endurance\n
        Going up:
            - hunger
            - bravery
        """
        self.__check_death()
        self.old_hunger = self.hunger
        self.hunger = min((self.hunger + self.hunger_combin), 10)
        self.bravery = min((self.bravery + self.hunger_combin / 2), 10)
        
        self.agility = max((self.agility - self.hunger_combin / 2), 0)
        self.perception = max((self.perception - self.hunger_combin / 2), 0)
        self.strength = max((self.strength - self.hunger_combin / 2), 0)
        self.endurance = max((self.endurance - self.hunger_combin / 2), 0)
        if self.hunger == 10:
            self.__log_statement(f'{self.id} starved.\n')
            self.alive = False
        else:
            self.__log_statement(f'{self.id}\'s hunger increased. ({self.old_hunger:.2f} -> {self.hunger:.2f}).\n')
    
    def engage_hunter(self, hunter: Hunter) -> bool:
        """
        Determines foragers action when coming across a hunter.

        Args:
            hunter (Hunter): The opposing hunter.

        Returns:
            bool, str: Status of forager, and if it fought or fled.
        """
        self.__check_death()
        # ? This could probably be nicer
        if self.bravery > 5:
            return self.__fight_hunter(hunter)
        else:
            return self.__flee_hunter(hunter)
    
    def traverse_ravine(self, ravine: Ravine) -> bool:
        """
        Evaluates the chance of crossing the ravine.

        Args:
            ravine (Ravine): The ravine the forager must cross.

        Returns:
            bool: True if successful, False if not.
        """
        self.__check_death()
        weights = {
            'agility': 0.4,
            'endurance': 0.3,
            'perception': 0.3
        }
        weighted_sum = (self.agility * weights['agility'] + 
                        self.endurance * weights['endurance'] + 
                        self.perception * weights['perception'])
        crossing_probability = weighted_sum / 10
        if crossing_probability > ravine.skill_required:
            self.__log_statement(f'{self.id} successfully '
                              f'crossed ravine {ravine.id}\n')
            return True
        else:
            self.__log_statement(f'{self.id} fails to '
                              f'cross ravine {ravine.id}.\n')
            return False
        
    def is_compatible_with(self, partner: 'Forager') -> bool:
        """
        Calculates comatilibity between two foragers using a combination
        of bravery, strength and perception and `compat_diff` defined in
        the config file. The higher the compat_diff, the less "fussy"
        the forager is.

        Args:
            partner (Forager): Potential mate.
            max_diff (float): Acceptable difference between thresholds. 
            
        Returns:
            bool: True, if compatible.
        """
        self.__check_death()
        partner.__check_death()
        # Recalculate thresholds as Foragers may have rebalanced attributes
        self.__get_compatibility()
        partner.__get_compatibility()
        if (self.sex == 'M' and partner.sex == 'F' or 
            self.sex == 'F' and partner.sex == 'M'):
            if isclose(self.compatability_threshold, 
                       partner.compatability_threshold, 
                       rel_tol=self.config['compat_diff']):
                return True
            else:
                return False
        else:
            return False
    
    def produce_offspring(self, partner: 'Forager') -> 'Forager':
        """
        Calculate compatibility threshold using a combination of attributes
        """
        self.__check_death()
        partner.__check_death()
        # Choose attributes stochastically
        offspring = Forager()
        self.__log_statement(f'{self.id} and {partner.id} '
                          f'produced offspring {offspring.id}.\n')
        return offspring
    
    def log_dynamic_attributes(self, display: bool) -> None:
        """
        Saves dynamic attributes to analyse changes over time.
        """
        attributes_at_timestep = {
            'id': self.id,
            'hunger': self.hunger,
            'bravery': self.bravery,
            'agility': self.agility,
            'perception': self.perception,
            'strength': self.strength,
            'endurance': self.endurance,
            'timestep': len(self.attribute_log)
        }
        self.attribute_log.append([attributes_at_timestep])
        if display:
            a = dict(self.attribute_log[-1][0])
            for key, value in a.items():
                if isinstance(value, str):
                    print(f'{key.title()}: {value}')
                elif key == 'timestep':
                    continue
                else:
                    print(f'{key.title()}: {value:.2f} - ')
            print()
    
    def get_log(self, save_as_txt: bool) -> list | None:
        """
        Returns the actions of the forager as a list of strings or
        saves them in a txt file.

        Args:
            save_as_txt (bool): Save actions as a txt file

        Returns:
            list | None: List of strings or None if the file is saved as txt
        """
        if not save_as_txt:
            return self.log
        else: 
            with open(f'simulation/logs/{self.id}_log.txt', 'r') as f:
                for line in self.log:
                    f.write(line)
    
    def __check_death(self) -> 'InvalidForager':
        """
        Check to ensure dead foragers do not perform actions.
        """
        if self.alive == False:
            raise InvalidForager(self.id)
    
    def __get_compatibility(self) -> None:
        """
        The "attractiveness" of the forager.
        """
        self.compatability_threshold = (self.bravery + 
                                        self.strength + 
                                        (self.perception * 1.5))
        return self.compatability_threshold
    
    def __fight_hunter(self, hunter: Hunter) -> Tuple[bool, str]:
        """
        A weighted sum of the foragers strength, endurance and agility 
        are compared to the hunters. The loser is made inactive.
        """
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
            self.__log_statement(f'{self.id} beat hunter {hunter.id}.\n')
        else:
            self.alive = False
            self.__log_statement(f'{self.id} lost to hunter {hunter.id}.\n')
        return (self.alive, 'fight')
    
    def __flee_hunter(self, hunter: Hunter) -> Tuple[bool, str]:
        """
        A weighted sum of the foragers agility, endurance and perception
        are compared to the hunters. The loser is made inactive.
        """
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
            self.__log_statement(f'{self.id} fled hunter {hunter.id}.\n')
        else:
            self.alive = False
            self.__log_statement(f'{self.id} was caught by hunter {hunter.id}.\n')
        return (self.alive, 'flee')
    
    def __validate(self, att: float, max: float) -> float | ValueError:
        """
        Ensures attributes in configuration file are within range.
        """
        if max == 1:
            if att > 1 or att < 0:
                raise ValueError(f'config: Value {att} out of range 0-1. '
                                 'compat_diff or hunger_combinator?\n')
        if max == 10.0:
            if att > 10.0 or att < 0.0:
                raise ValueError(f'config: Value {att} out of range 0.0-10.0. '
                                 'hunger or bravery?')
        return att
    
    def __log_statement(self, statement: str) -> None:
        """
        Saves and outputs forager actions to stdout.
        """
        print(statement)
        self.log.append(statement)
        
    def __str__(self) -> str:
        return f'Forager {self.id}.\n'
    
class InvalidForager(Exception):
    """
    Ensures dead foragers do not perform actions.
    """
    def __init__(self, forager_id):
        self.message = f'{forager_id} should be inactive.'
        super().__init__(self.message)