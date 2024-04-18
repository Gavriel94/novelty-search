from math import isclose
from random import randrange, choice
import tomllib
from typing import Tuple
import copy

from .mammal import Mammal
from .food import Food
from .hunter import Hunter
from .ravine import Ravine

# ForagerActions: class appended to bottom of file
# region Forager
class Forager(Mammal):
    def __init__(self, sex: str = None, attribute_dict: dict = None):
        # Super attributes
        if attribute_dict is not None:
            # Derives attributes from parents
            agility = attribute_dict['agility']
            perception = attribute_dict['perception']
            strength = attribute_dict['strength']
            endurance = attribute_dict['endurance']
        else:
            agility = float(randrange(1, 3))
            perception = float(randrange(1, 3))
            strength = float(randrange(1, 3))
            endurance = float(randrange(1, 3))
        super().__init__(agility, perception, strength, endurance)   
        
        if sex == None:
            self.sex = choice(['M', 'F'])
        else:
            self.sex = sex
        if self.sex != 'M' and self.sex != 'F':
            raise ValueError('Sex must be \'M\' or \'F\'')
        
        # Config file attributes
        with open('simulation/forager_config.toml', 'rb') as f:
            self.config = tomllib.load(f)
            self.hunger = self.__validate(self.config['hunger'], 10.0)
            self.bravery = self.__validate(self.config['bravery'], 10.0)
            self.compat_diff = self.__validate(self.config['compat_diff'], 1)
            self.hunger_combin = self.__validate(self.config['hunger_combinator'], 1)
        
        # Default attributes
        self.compatability_threshold = self.__get_compatibility()
        self.type = 'Forager'
        self.alive = True
        
        # Navigational attributes
        self.current_coords = None
        self.destination_coordinates = None
        
        # Persistent memory
        self.motivation = None # "nearest food"/"furthest forager" etc"
        self.successful_motivations = []
        self.previous_choices = []
        self.mated_with = []
        self.incompatible_with = []
        
        # store metrics
        self.log = [] # log of actions taken
        self.attribute_log = [] # log of dynamic attribute values
        # Unused attributes
        self.explored_coords = []
        # offspring can evolve to have better abilities
        self.bonus_attributes = []
        # Previous choices can influence the current one
        self.bias_to_choices = {
            'nearest food': 1,
            'furthest food': 1,
            'most sustaining food': 1,
            'nearest forager': 1,
            'furthest forager': 1,
            'most compatible forager': 1
        }
        
    def get_next_step(self, environment) -> Tuple[int, int]:
        """
        Gets the (x, y) coordinate to the next step on its path.

        Args:
            environment (Grid): The simulation environment.

        Returns:
            Tuple[int, int]: x, y coordinate to move the forager to.
        """
        actions = ForagerActions(environment, self)
        # region motivation
        if self.motivation == None:
            self.motivation = actions.set_motivation()
            self.log_statement(f'Forager {self.id} is going to find {self.motivation}.')
        
        # find the next step towards fulfilling motivation
        self.destination_coordinates = actions.get_destination_coordinates(self.motivation)
        
        # Get next step to destination 
        next_coordinate = actions.get_next_coordinate(self.current_coords, self.destination_coordinates)
        self.explored_coords.append(next_coordinate)
        
        if next_coordinate == self.destination_coordinates:
            self.log_statement(f'Forager {self.id} found {self.motivation}.')
            self.successful_motivations.append(self.motivation)
            self.motivation = None
        return next_coordinate
            
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
        self.log_statement(f'{self.id} ate the {food.name}.\n'
                              f'{self.id}\'s hunger decreased. ({self.old_hunger:.2f} -> {self.hunger:.2f}).')
    
    def hunger_increase(self) -> bool:
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
            self.log_statement(f'{self.id} starved.')
            self.alive = False
        # else:
            # self.log_statement(f'{self.id}\'s hunger increased. ({self.old_hunger:.2f} -> {self.hunger:.2f}).\n')
        return self.alive
    
    def engage_hunter(self, hunter: Hunter) -> Tuple[str, bool]:
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
            self.log_statement(f'{self.id} successfully '
                              f'crossed ravine.')
            return True
        else:
            self.log_statement(f'{self.id} fails to '
                              f'cross ravine.')
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
        try:
            partner.__check_death()
        except:
            return
        
        if partner in self.mated_with:
            return False
        # Recalculate thresholds as Foragers may have rebalanced attributes
        self.__get_compatibility()
        partner.__get_compatibility()
        if (self.sex == 'M' and partner.sex == 'F' or 
            self.sex == 'F' and partner.sex == 'M'):
            
            if isclose(self.compatability_threshold, 
                       partner.compatability_threshold, 
                       rel_tol=self.config['compat_diff']):
                self.log_statement(f'{self.id} ({self.sex}: {self.compatability_threshold:.2f}) '
                                     f'and {partner.id} ({partner.sex}: {partner.compatability_threshold:.2f}) are compatible.')
                return True
            else:
                self.log_statement(f'{self.id} ({self.compatability_threshold:.2f}) '
                                     f'and {partner.id} ({partner.compatability_threshold:.2f}) '
                                     'are not compatible.')
                self.incompatible_with.append(partner)
                return False
        else:
            self.log_statement(f'{self.id} ({self.sex}) and {partner.id} '
                                 f'({partner.sex}) are not compatible.')
            self.incompatible_with.append(partner)
            return False
    
    def produce_offspring(self, partner: 'Forager') -> 'Forager':
        """
        Calculate compatibility threshold using a combination of attributes
        """
        self.__check_death()
        partner.__check_death()
        # Get a combination of self and partners attributes
        
        offspring_dict = {
            'agility': (self.agility + partner.agility) / 2,
            'perception': (self.perception + partner.perception) / 2,
            'strength': (self.strength + partner.strength) / 2,
            'endurance': (self.endurance + partner.endurance) / 2,
        }
        offspring = Forager(attribute_dict=offspring_dict)
        
        # Choose attributes stochastically
        # offspring = Forager()
        
        self.log_statement(f'{self.id} and {partner.id} '
                          f'produced offspring {offspring.id}.')
        self.mated_with.append(partner)
        return offspring
    
    def log_dynamic_attributes(self, display: bool, forager_num: int) -> None:
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
            'current_coords': self.current_coords,
            'timestep': len(self.attribute_log)
        }
        self.attribute_log.append([attributes_at_timestep])
        if display:
            print()
            print('*' + '-' * 21 + '*')
            print(f'| Forager {forager_num + 1:<3}| {self.id:<7}|')
            print('*' + '-' * 21 + '*')
            # stdout attributes
            a = dict(self.attribute_log[-1][0])
            for key, value in a.items():
                if isinstance(value, str):
                    continue
                elif key == 'timestep':
                    continue
                elif key == 'current_coords':
                    label = '(x,y)'
                    print(f'| {label:<11}| {value} |')
                else:
                    icon = ' '
                    if len(self.attribute_log) > 1:
                        if dict(self.attribute_log[-2][0])[key] > value:
                            icon = '-'
                        else:
                            icon = '+'
                    print(f'| {key.title():<11}| {value:>4.2f} {icon} |')
            print('*' + '-' * 21 + '*')
            
    def log_statement(self, statement: str) -> None:
        """
        Saves and outputs forager actions to stdout.
        """
        print(statement)
        self.log.append(statement)
    
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
    # region private
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
            self.log_statement(f'{self.id} beat hunter {hunter.id}.')
        else:
            self.alive = False
            self.log_statement(f'{self.id} lost to hunter {hunter.id}.')
        return ('fight', self.alive)
    
    def __flee_hunter(self, hunter: Hunter) -> Tuple[str, bool]:
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
            self.log_statement(f'{self.id} fled hunter {hunter.id}.')
        else:
            self.alive = False
            self.log_statement(f'{self.id} was caught by hunter {hunter.id}.')
        return ('flee', self.alive)
    
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
        
    def __str__(self) -> str:
        return f'Forager {self.id}.\n'

# region Actions
# Kept in same .py file to avoid circular import error
class ForagerActions():
    """
    The "brain" of the Forager. 
    
    ForagerActions is responsible for setting the motivation of the 
    forager, and calculating the steps to reach it.
    """
    def __init__(self, environment, forager: Forager):
        self.environment = environment
        self.forager = forager
        # All foods and foragers in the environment
        self.foods = self.find_all(Food)
        self.foragers = self.find_all(Forager)
        self.hunters = self.find_all(Hunter)
    # region motivation
    
    def set_motivation(self) -> None:
        """
        The novelty search function.
        Right now it picks a motivation at random but this should be informed by attributes, 
        stochasticity and based somewhat off the last decision as well? 
        
        Does there need to be some mechanism for reward based on previous moves?
        """
        # ? There's a bunch of options here. 
        # ? should there be more ?
        choices = ['nearest food', 'furthest food', 'most sustaining food', 
                   'nearest forager', 'furthest forager', 'most compatible forager']

        # foragers gain better abilities as they evolve
        if self.forager.agility > 7:
            self.forager.bonus_attributes.append('zig zag past hunter')
        elif self.forager.perception > 7:
            self.forager.bonus_attributes('hide from hunter')
        elif self.forager.perception == 9 and self.forager.agility == 9:
            self.forager.bonus_attributes.append('camouflage')
            
        # motivation = random.choice(choices)
        
        # get choices and their weights
        weighted_choices = [(choice, self.novelty_value(choice)) for choice in choices]
        # find the choice with the highest weight
        best_choice = None
        max_weight = 0
        for choice, weight in weighted_choices:
            if weight > max_weight:
                max_weight = weight
                best_choice = choice

        for choice in weighted_choices:
            print(choice)
        print()
        # now at this stage, the forager shouldn't always do the best choice
        # there should be noise here
        # stochasticity
        
        return best_choice
    
    # region fixing
    def novelty_value(self, choice):
        """
        Each choice is transformed into a novelty value.

        Args:
            choice (str): The motivation of the forager.

        Returns:
            _type_: _description_
        """
        # * --- Helper methods begin-- *
        
        def step_count():
            steps = 0
            current_coords = self.forager.current_coords
            destination_coords = self.get_destination_coordinates(choice)
            while current_coords != destination_coords:
                next_coord = self.get_next_coordinate(current_coords, destination_coords)
                current_coords = next_coord
                steps += 1
            return steps
            
        def weight_nearest(choice_weight):
            """
            If the foragers perception is higher than the boost threshold,
            it now considers a destination is close if it is less than 
            8 steps. It's then nudged toward choosing 
            """
            if self.forager.perception > BOOST1_THRESHOLD:
                if num_steps < 8:
                    choice_weight *= POS_MULTIPLIER
                elif num_steps > 12:
                    choice_weight *= NEG_MULTIPLIER
                    
            # with higher endurance the forager considers more steps 
            if self.forager.endurance > BOOST2_THRESHOLD:
                if num_steps < 12:
                    choice_weight *= POS_MULTIPLIER
                elif num_steps > 16:
                    choice_weight *= NEG_MULTIPLIER
            return choice_weight
        
        def weight_furthest(choice_weight):
            # with higher perception the forager considers more steps
            if self.forager.agility > BOOST1_THRESHOLD:
                if num_steps < 8:
                    choice_weight *= POS_MULTIPLIER
                elif num_steps > 12:
                    choice_weight *= NEG_MULTIPLIER
            # with higher endurance the forager considers more steps
            if self.forager.endurance > BOOST2_THRESHOLD:
                if num_steps < 12:
                    choice_weight *= POS_MULTIPLIER
                elif num_steps < 16:
                    choice_weight *= NEG_MULTIPLIER
            return choice_weight
        
        def weight_best_key_attribute(choice_weight):
            # with higher endurance the forager considers more steps
            if self.forager.endurance > BOOST1_THRESHOLD:
                if num_steps < 8:
                    choice_weight *= POS_MULTIPLIER
                elif num_steps < 12:
                    choice_weight *= NEG_MULTIPLIER
            # with higher strength the forager considers more steps
            if self.forager.strength > BOOST2_THRESHOLD:
                if num_steps < 12:
                    choice_weight *= POS_MULTIPLIER
                elif num_steps > 16:
                    choice_weight *= NEG_MULTIPLIER
            return choice_weight
        
        # * -- Helper methods end --
        
        # what level an attribute is before it unlocks a small bost
        BOOST1_THRESHOLD = 2
        # what level an attribute is before it unlocks a significant boost
        BOOST2_THRESHOLD = 2 
        # Influence on choice_weight
        POS_MULTIPLIER = 1.2
        NEG_MULTIPLIER = 0.8
    
        # number of steps to destination
        num_steps = step_count()
        choice_weight = self.forager.bias_to_choices[choice]
        
        # weigh novel motivations higher 
        if choice in self.forager.successful_motivations:
            choice_weight = choice_weight * NEG_MULTIPLIER
        elif choice not in self.forager.successful_motivations:
            choice_weight = choice_weight * POS_MULTIPLIER
        
        print()
        print('Possible choices')
        print(choice, choice_weight)
        print('Forager', self.forager.id)
        print('initial choice_weight', choice_weight)
        print('successful motivations', self.forager.successful_motivations)
        print('third choice_weight', choice_weight)
        
        if choice == 'find nearest food' or choice == 'nearest forager':
            choice_weight = weight_nearest(choice_weight)
        elif choice == 'find furthest food' or choice == 'furthest forager':
            choice_weight = weight_furthest(choice_weight)
        elif choice == 'most sustaining food' or choice == 'most compatible forager':
            choice_weight = weight_best_key_attribute(choice_weight)
        print('fourth choice_weight', choice_weight)

        # stronger foragers are likely to explore more
        if (len(self.forager.bonus_attributes) > 0 
            and choice == 'find furthest food' 
            or choice == 'find furthest forager'): 
            choice_weight *= 1.1
        
        # forager is hungry so nudge towards eating
        if self.forager.hunger > 5:
            if choice == 'find nearest food':
                choice_weight *= 1.3
            elif choice == 'find furthest food':
                choice_weight *= 1.1
            elif choice_weight == 'most sustaining food':
                choice_weight *= 1.3
         
        # nudge towards mate
        if choice == 'most compatible forager':
            choice_weight *= 1.1
        
        print('fifth choice_weight', choice_weight)
        print()
        if choice_weight < 0:
            raise ValueError
        else:
            self.forager.bias_to_choices[choice] = choice_weight
            return choice_weight
        
    def find_all(self, object_class: Food | Forager | Hunter) -> list:
        """
        List of (x,y) coordinates for all objects of specified type.
        """
        objs = []
        for y in range(self.environment.height):
            for x in range(self.environment.width):
                if isinstance(self.environment.grid[y][x], object_class):
                    grid_obj = self.environment.grid[y][x]
                    obj_dict = {}
                    if grid_obj.id == self.forager.id:
                        continue
                    if object_class == Food:
                        obj_dict['id'] = grid_obj.id
                        obj_dict['type'] = 'Food'
                        obj_dict['key_attribute'] = grid_obj.sustenance_granted
                        obj_dict['location'] = (x,y)
                    elif object_class == Forager:
                        obj_dict['type'] = 'Forager'
                        obj_dict['key_attribute'] = grid_obj.compatability_threshold
                        obj_dict['location'] = (x,y)
                    elif object_class == Hunter:
                        obj_dict['id'] = grid_obj.id
                        obj_dict['type'] = 'Hunter'
                        obj_dict['key_attribute'] = grid_obj.strength
                        obj_dict['location'] = (x,y)
                    objs.append(obj_dict)
        return objs
        
    def find_nearest_food(self):
        """
        Finds the (x,y) coordinate of the nearest food.

        Returns:
            tuple: (x,y)
        """
        food_locations = []
        for food in self.foods:
            food_locations.append(food['location'])
        output = self.get_nearest(food_locations)
        if output == None:
            raise ValueError(f'Output: {output}')
        return output
    
    def find_furthest_food(self):
        """
        Finds the (x,y) coordinate of the furthest food.

        Returns:
            tuple: (x,y)
        """
        food_locations = []
        for food in self.foods:
            food_locations.append(food['location'])
        output = self.get_furthest(food_locations)
        if output == None:
            raise ValueError(f'Output: {output}')
        return output
    
    def find_most_sustenance(self):
        """
        Finds the (x,y) coordinate of the most sustaining food.

        Returns:
            tuple: (x,y)
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
                
    def find_nearest_forager(self):
        """
        Finds the (x,y) coordinate of the nearest forager.

        Returns:
            tuple: (x,y)
        """
        if len(self.foragers) == 0:
            print(self.forager)
            self.forager.log_statement(f'{self.forager.id} cannot find any potential mates.\n'
                                    'Looking for nearest food instead.')
            output = self.find_nearest_food()
            if output == None:
                raise ValueError(f'Output: {output}')
            return output
        else:
            forager_locations = []
            for forager in self.foragers:
                forager_locations.append(forager['location'])
            output = self.get_nearest(forager_locations)
            if output == None:
                raise ValueError(f'Output: {output}')
            return output
    
    def find_furthest_forager(self):
        """
        Finds the (x,y) coordinate of the furthest forager.

        Returns:
            tuple: (x,y)
        """
        if len(self.foragers) == 0:
            self.forager.log_statement(f'{self.forager.id} cannot find any potential mates.\n'
                                    'Looking for furthest food instead.')
            output = self.find_furthest_food()
            if output == None:
                raise ValueError(f'Output: {output}')
            return self.find_furthest_food()
        else:
            forager_locations = []
            for forager in self.foragers:
                forager_locations.append(forager['location'])
            output = self.get_furthest(forager_locations)
            if output == None:
                raise ValueError(f'Output: {output}')
            return self.get_furthest(forager_locations)
        
    def find_most_compatible_forager(self):
        """
        Finds the (x,y) coordinate of the forager with the most similar
        compatibility threshold.

        Returns:
            tuple: (x,y)
        """
        if len(self.foragers) == 0:
            # no potential mates
            # go and look for food
            self.forager.log_statement(f'{self.forager.id} cannot find any potential mates.\n'
                    'Looking for the most sustaining food instead.')
            return self.find_most_sustenance()
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
        
    def manhattan_distance(self, object_loc):
        """
        Manhattan distance between self.current_forager and object.

        Args:
            object_loc (tuple(int,int)): x, y coordinate of object.
        """
        return (abs(object_loc[0] - self.forager.current_coords[0]) + 
                abs(object_loc[1] - self.forager.current_coords[1]))
    
    def sort_by_nearest(self, locations):
        """
        Sort a list of food or forager objects in ascending order

        Args:
            locations (list): list of (x,y) coordinates

        Returns:
            list: ordered list of (x,y) coordinates
        """
        objs = []
        closest_obj = None
        shortest_distance = float('inf')    
        for obj_loc in locations:
            distance = self.manhattan_distance(obj_loc)
            if distance < shortest_distance:
                shortest_distance = distance
                closest_obj = obj_loc
                objs.append(closest_obj)
        return objs
    
    def sort_by_furthest(self, locations):
        """
        Sort a list of food or forager objects in descending order

        Args:
            locations (list): list of (x,y) coordinates

        Returns:
            list: ordered list of (x,y) coordinates
        """
        objs = self.sort_by_nearest(locations)
        objs.reverse()
        return objs
    
    def get_nearest(self, locations):
        """
        Get the nearest object

        Args:
            locations (list): list of (x,y) coordinates

        Returns:
            tuple: (x,y) coordinate of the nearest object
        """
        objs = self.sort_by_nearest(locations)
        return objs[0]
    
    def get_furthest(self, locations):
        """
        Get the furthest object

        Args:
            locations (list): list of (x,y) coordinates

        Returns:
            tuple: (x,y) coordinate of the furthest object
        """
        objs = self.sort_by_furthest(locations)
        return objs[0]

    def get_next_coordinate(self, current_coords, object_loc):
        """
        Get's the coordinates of the next step towards to object.
        
        Args:
            object_loc (tuple(int,int)): x, y coordinate of object.
        """
        # TODO document this properly
        new_x, new_y = 0, 0
        if (abs(object_loc[0] - current_coords[0]) > 
            abs(object_loc[1] - current_coords[1])):
            if object_loc[0] > current_coords[0]:
                new_x = 1
            elif object_loc[0] < current_coords[0]:
                new_x = -1
            new_x += current_coords[0]
            return new_x, current_coords[1]
        else:
            if object_loc[1] > current_coords[1]:
                new_y = 1
            elif object_loc[1] < current_coords[1]:
                new_y = -1
            new_y += current_coords[1]
            return current_coords[0], new_y
        
    def get_destination_coordinates(self, choice):
        # needs to set target_coords in the forager
        # * must return (x,y) coordinate
        """
        Checks the foragers motivation and finds the (x,y) coordinate in the grid
        

        Raises:
            TargetError: _description_

        Returns:
            _type_: _description_
        """
        target_coords = None
        if choice == 'nearest food':
            target_coords = self.find_nearest_food()
        elif choice == 'furthest food':
            target_coords = self.find_furthest_food()
        elif choice == 'most sustaining food':
            target_coords = self.find_most_sustenance()
        elif choice == 'nearest forager':
            target_coords = self.find_nearest_forager()
        elif choice == 'furthest forager':
            target_coords = self.find_furthest_forager()
        elif choice == 'most compatible forager':
            target_coords = self.find_most_compatible_forager()
        else:
            raise TargetError(f'Invalid motivation: {self.forager.motivation}')
        return target_coords
    
class InvalidForager(Exception):
    """
    Ensures dead foragers do not perform actions.
    """
    def __init__(self, forager_id):
        self.message = f'{forager_id} should be inactive.'
        super().__init__(self.message)
        
class TargetError(Exception):
    """
    Ensure the Forager has a motivation.
    """
    def __init__(self, message):
        super().__init__(message)
        