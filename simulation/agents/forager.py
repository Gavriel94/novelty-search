from math import isclose
import random
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
        self.current_coordinates = None
        self.target_coordinates = None
        self.current_target = None
        
        self.last_location = None
        self.explored_coordinates = []
        self.log = []
        self.attribute_log = []
    
    def get_next_step(self, environment) -> Tuple[int, int]:
        """
        The next step to food or a mate.
        """
        if self.current_target == None:
            self.set_target_coords(environment)
        # self.set_target_coords(environment)
        next_step = self.__get_next_coordinates(self.target_coordinates) 
        
        # If the next step is the target step, clear target coordinates
        # to be reset on next function call
        if next_step == self.target_coordinates:
            self.current_target = None
            self.target_coordinates = None
        
        # # if food at target step has been eaten, find a new target   
        # if 'food' in self.current_target or 'sustenance' in self.current_target and environment.grid[next_step[1]][next_step[0]] == None:
        #     self.target_coordinates = None
        #     self.set_target_coords(environment)
        #     next_step = self.__get_next_coordinates(self.target_coordinates)
            
        return next_step
    
    def set_target_coords(self, environment):
        """
        Can find food or foragers ordered by distance, 
        forager compatibility and food sustenance given
        
        Args:
            environment (Grid): current simulation state.
        """
        
        # * -- Beginning of helper methods -- * 
        
        def find_items(object_class: Food | Forager) -> list:
            """
            List of (x,y) coordinates for each Food object.
            """
            objs = []
            for y in range(environment.height):
                for x in range(environment.width):
                    if isinstance(environment.grid[y][x], object_class):
                        grid_obj = environment.grid[y][x]
                        if grid_obj.id == self.id:
                            continue
                        if object_class == Food:
                            obj_dict = {}
                            obj_dict['id'] = grid_obj.id
                            obj_dict['type'] = 'Food'
                            obj_dict['key_attribute'] = grid_obj.sustenance_granted
                            obj_dict['location'] = (x,y)
                            objs.append(obj_dict)
                        elif object_class == Forager:
                            obj_dict = {}
                            obj_dict['type'] = 'Forager'
                            obj_dict['key_attribute'] = grid_obj.compatability_threshold
                            obj_dict['location'] = (x,y)
                            objs.append(obj_dict)
            return objs
        
        def manhattan_distance(object_loc):
            """
            Manhattan distance between self and object.

            Args:
                object_loc (tuple(int,int)): x, y coordinate of object.
            """
            return (abs(object_loc[0] - self.current_coordinates[0]) + 
                    abs(object_loc[1] - self.current_coordinates[1]))
        
        def sort_by_nearest(locations):
            objs = []
            closest_obj = None
            shortest_distance = float('inf')    
            for obj_loc in locations:
                distance = manhattan_distance(obj_loc)
                if distance < shortest_distance:
                    shortest_distance = distance
                    closest_obj = obj_loc
                    objs.append(closest_obj)
            return objs
        
        def sort_by_furthest(locations):
            objs = sort_by_nearest(locations)
            objs.reverse()
            return objs
        
        def get_nearest(locations):
            objs = sort_by_nearest(locations)
            return objs[0]
        
        def get_furthest(locations):
            objs = sort_by_furthest(locations)
            return objs[0]
        
        def nearest_food():
            foods = find_items(Food)
            food_locations = []
            for food in foods:
                food_locations.append(food['location'])
            output = get_nearest(food_locations)
            if output == None:
                raise ValueError(f'Output: {output}')
            return output
        
        def furthest_food():
            foods = find_items(Food)
            food_locations = []
            for food in foods:
                food_locations.append(food['location'])
            output = get_furthest(food_locations)
            if output == None:
                raise ValueError(f'Output: {output}')
            return output
        
        def most_sustenance():
            foods = find_items(Food)
            food_locations = []
            food_sus = float('inf')
            for food in foods:
                if food['key_attribute'] < food_sus:
                    food_sus = food['key_attribute']
                    food_locations.append(food)
            output = food_locations[-1]['location']
            if output == None:
                raise ValueError(f'Output: {output}')
            return output
                    
        def nearest_forager():
            foragers = find_items(Forager)
            if len(foragers) == 0:
                self.__log_statement(f'{self.id} cannot find any potential mates.\n'
                                     'Looking for nearest food instead.')
                output = nearest_food()
                if output == None:
                    raise ValueError(f'Output: {output}')
                return output
            else:
                forager_locations = []
                for forager in foragers:
                    forager_locations.append(forager['location'])
                output = get_nearest(forager_locations)
                if output == None:
                    raise ValueError(f'Output: {output}')
                return output
        
        def furthest_forager():
            foragers = find_items(Forager)
            if len(foragers) == 0:
                self.__log_statement(f'{self.id} cannot find any potential mates.\n'
                                     'Looking for furthest food instead.')
                output = furthest_food()
                if output == None:
                    raise ValueError(f'Output: {output}')
                return furthest_food()
            else:
                forager_locations = []
                for forager in foragers:
                    forager_locations.append(forager['location'])
                output = get_furthest(forager_locations)
                if output == None:
                    raise ValueError(f'Output: {output}')
                return get_furthest(forager_locations)
            
        def most_compatible():
            # TODO change food in variable name to forager
            foods = find_items(Forager)
            if len(foods) == 0:
                self.__log_statement(f'{self.id} cannot find any potential mates.\n'
                        'Looking for most sustenance instead.')
                return most_sustenance()
            else:
                food_locations = []
                food_sus = float('inf')
                for food in foods:
                    if food['key_attribute'] < food_sus:
                        food_sus = food['key_attribute']
                        food_locations.append(food)
                output = food_locations[-1]['location']
                if output == None:
                    raise ValueError(f'Output: {output}')
                return output
            
        # * -- End of helper methods -- *
        
        self.current_target = random.choice(['nearest food', 'furthest food', 
                                                'nearest forager', 'furthest forager',
                                                'most sustenance', 'most compatible mate'])
        
        self.__log_statement(f'Forager {self.id} is looking for the {self.current_target}')
        
        if self.current_target == 'nearest food':
            self.target_coordinates = nearest_food()
        elif self.current_target == 'furthest food':
            self.target_coordinates = furthest_food()
        elif self.current_target == 'nearest forager':
            self.target_coordinates = nearest_forager()
        elif self.current_target == 'furthest forager':
            self.target_coordinates = furthest_forager()
        elif self.current_target == 'most sustenance':
            self.target_coordinates = most_sustenance()
        elif self.current_target == 'most compatible mate':
            self.target_coordinates = most_compatible()
        else:
            raise TargetError(f'Unrecognised target coordinates {self.target_coordinates}. Current target: {self.current_target}')
            
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
        self.__log_statement(f'{self.id} ate the {food.name}.\n'
                              f'{self.id}\'s hunger decreased. ({self.old_hunger:.2f} -> {self.hunger:.2f}).\n')
    
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
                self.__log_statement(f'{self.id} ({self.sex}: {self.compatability_threshold:.2f}) '
                                     f'and {partner.id} ({partner.sex}: {partner.compatability_threshold:.2f}) are compatible.\n')
                return True
            else:
                self.__log_statement(f'{self.id} ({self.compatability_threshold}) '
                                     f'and {partner.id} ({partner.compatability_threshold:.2f}) '
                                     'are not compatible.\n')
                return False
        else:
            self.__log_statement(f'{self.id} ({self.sex}) and {partner.id} '
                                 f'({partner.sex}) are not compatible.\n')
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
                    
    def __get_next_coordinates(self, object_loc):
            """
            Get's coordinates of step closer to object.
            
            Args:
                object_loc (tuple(int,int)): x, y coordinate of object.
            """
            # TODO document this properly
            new_x, new_y = 0, 0
            if (abs(object_loc[0] - self.current_coordinates[0]) > 
                abs(object_loc[1] - self.current_coordinates[1])):
                if object_loc[0] > self.current_coordinates[0]:
                    new_x = 1
                elif object_loc[0] < self.current_coordinates[0]:
                    new_x = -1
                new_x += self.current_coordinates[0]
                return new_x, self.current_coordinates[1]
            else:
                if object_loc[1] > self.current_coordinates[1]:
                    new_y = 1
                elif object_loc[1] < self.current_coordinates[1]:
                    new_y = -1
                new_y += self.current_coordinates[1]
                return self.current_coordinates[0], new_y
    
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
        
class TargetError(Exception):
    def __init__(self, message):
        super().__init__(message)