import math
import random
from random import randrange, choice
import tomllib
import numpy as np
from typing import Tuple

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
        with open('assets/agents/forager_config.toml', 'rb') as f:
            self.config = tomllib.load(f)
            self.hunger = self.__validate(self.config['hunger'], 10.0)
            self.bravery = self.__validate(self.config['bravery'], 10.0)
            self.compat_diff = self.__validate(self.config['compat_diff'], 1)
            self.decay_factor = self.__validate(self.config['decay_factor'], 1)
            self.hunger_combin = self.__validate(self.config['hunger_combinator'], 1)
            self.boost1_threshold = self.__validate(self.config['boost1_threshold'], 10)
            self.boost2_threshold = self.__validate(self.config['boost2_threshold'], 10)
            self.positive_multiplier = self.__validate(self.config['positive_multiplier'], 1)
        
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
        # offspring evolve to have better abilities
        self.bonus_attributes = []
        # the weights of the foragers decisions aka foragers 'personality'
        self.motivation_weights = {
            'nearest food': random.uniform(0.01, 0.3),
            'furthest food': random.uniform(0.01, 0.3),
            'most sustaining food': random.uniform(0.01, 0.3),
            'nearest forager': random.uniform(0.01, 0.3),
            'furthest forager': random.uniform(0.01, 0.3),
            'most compatible forager': random.uniform(0.01, 0.3)
        }
        # attributes used for analysis
        self.steps_alive = 0
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
        self.atrributes_at_init = {
            'agility': agility,
            'perception': perception,
            'strength': strength,
            'endurance': endurance
        }
    
    # region GNS   
    def get_next_step(self, environment) -> Tuple[int, int]:
        """
        Gets the (x, y) coordinate to the next step on its path.

        Args:
            environment (Grid): The simulation environment.

        Returns:
            Tuple[int, int]: x, y coordinate to move the forager to.
        """
        def set_motivation():
            self.motivation = actions.set_motivation()
            self.log_statement(f'Forager {self.id} is going to find {self.motivation}.')
            self.motivation_metrics[self.motivation]['times chosen'] += 1
            environment.total_motivations[self.motivation] += 1
        
        actions = ForagerActions(environment, self)
        if self.motivation == None:
            set_motivation()
            
        # find the next step towards fulfilling motivation
        self.destination_coordinates = actions.get_destination_coordinates(self.motivation)
        
        # Get next step to destination 
        next_coordinate = actions.get_next_coordinate(self.current_coords, self.destination_coordinates)
        self.explored_coords.append(next_coordinate)
        
        if self.current_coords == self.destination_coordinates:
            self.log_statement(f'Forager {self.id} found {self.motivation}.')
            self.motivation_metrics[self.motivation]['successful outcomes'] += 1
            self.motivation_metrics[self.motivation]['total time'] += 1
            # used to influence next choice
            self.successful_motivations.append(self.motivation) 
            set_motivation()
        else:
            self.motivation_metrics[self.motivation]['total time'] += 1
            self.motivation_metrics[self.motivation]['average time'] = str(f"{(self.motivation_metrics[self.motivation]['total time'] / environment.num_steps)*100}%")
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
        
        self.agility = min((self.agility + (food.sustenance_granted * (self.positive_multiplier * 10)) / 4), 10.0)
        self.perception = min((self.perception + (food.sustenance_granted * (self.positive_multiplier * 10))  / 4), 10.0)
        self.strength = min((self.strength + (food.sustenance_granted * (self.positive_multiplier * 10))  / 4), 10.0)
        self.endurance = min((self.endurance + (food.sustenance_granted * (self.positive_multiplier * 10))  / 4), 10.0)
        self.log_statement(f'{self.id} ate the {food.name}.\n'
                              f'{self.id}\'s hunger decreased. ({self.old_hunger:.2f} -> {self.hunger:.2f}).')
        self.motivation_metrics['food encounters']['num encounters'] += 1
        self.motivation_metrics['food encounters']['total sustenance gained'] += food.sustenance_granted
        self.motivation_metrics['food encounters']['foods tasted'].append(food.name)
    
    def hunger_increase(self) -> bool:
        """
        Forager gets hungrier.
        
        Going up:
            - hunger
            - bravery
        """
        self.__check_death()
        self.old_hunger = self.hunger
        self.hunger = min((self.hunger + self.hunger_combin), 10)
        self.bravery = min((self.bravery + self.hunger_combin / 2), 10)
        
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
            decision, win = self.__fight_hunter(hunter)
            self.motivation_metrics['hunter encounters']['num encounters'] += 1
            self.motivation_metrics['hunter encounters']['times fought'] += 1
            if win:
                self.motivation_metrics['hunter encounters']['times won'] += 1
            else:
                self.motivation_metrics['hunter encounters']['times lost'] += 1
            return (decision, win)    
        else:
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
            self.log_statement(f'{self.id} successfully crossed ravine.')
            self.motivation_metrics['ravine encounters']['times jumped'] += 1
            self.motivation_metrics['ravine encounters']['times attempted'] += 1
            return True
        else:
            self.log_statement(f'{self.id} fails to cross ravine.')
            self.motivation_metrics['ravine encounters']['times attempted'] += 1
            return False
        
    def is_compatible_with(self, partner: 'Forager') -> bool:
        """
        Calculates comatilibity between two foragers using a combination
        of bravery, strength and perception and `compat_diff`. 
        The higher the compat_diff, the less "fussy"
        the forager is.

        Args:
            partner (Forager): Potential mate.
            max_diff (float): Acceptable difference between thresholds. 
            
        Returns:
            bool: True, if compatible otherwise false.
        """
        self.__check_death()
        try:
            partner.__check_death()
        except:
            return
        
        if partner in self.mated_with:
            return False
        # Recalculate thresholds as Foragers attributes adjust
        self.__get_compatibility()
        partner.__get_compatibility()
        if (self.sex == 'M' and partner.sex == 'F' or 
            self.sex == 'F' and partner.sex == 'M'):
            
            if math.isclose(self.compatability_threshold, 
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
                self.motivation_metrics[self.motivation]['times chosen'] += 1
                return False
        else:
            self.log_statement(f'{self.id} ({self.sex}) and {partner.id} '
                                 f'({partner.sex}) are not compatible.')
            self.incompatible_with.append(partner)
            self.motivation_metrics[self.motivation]['times chosen'] += 1
            return False
    
    def produce_offspring(self, partner: 'Forager') -> 'Forager':
        """
        Produces a new forager.
        """
        self.__check_death()
        partner.__check_death()
        
        # Get a combination of self and partners attributes
        offspring_dict = {
            'agility': ((self.agility + partner.agility) / 2) + 0.3,
            'perception': ((self.perception + partner.perception) / 2) + 0.3,
            'strength': ((self.strength + partner.strength) / 2) + 0.3,
            'endurance': ((self.endurance + partner.endurance) / 2) + 0.3,
        }
        offspring = Forager(attribute_dict=offspring_dict)
        
        self.log_statement(f'{self.id} and {partner.id} '
                          f'produced offspring {offspring.id}.')
        self.mated_with.append(partner)
        self.motivation_metrics['offspring produced'] += 1
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
            print('*' + '-' * 24 + '*')
            print(f'| Forager {forager_num + 1:<4}| {self.id:<9}|')
            print('*' + '-' * 24 + '*')
            # stdout attributes
            a = dict(self.attribute_log[-1][0])
            for key, value in a.items():
                if isinstance(value, str):
                    continue
                elif key == 'timestep':
                    continue
                elif key == 'current_coords':
                    label = '(x,y)'
                    x,y = value
                    print(f"| {label:<12}| {'('+f'{x:<2}'}, {f'{y:>2}' + ')'} |")
                else:
                    icon = ' '
                    if len(self.attribute_log) > 1:
                        if dict(self.attribute_log[-2][0])[key] > value:
                            icon = '-'
                        elif dict(self.attribute_log[-2][0])[key] < value:
                            icon = '+'
                        else:
                            icon = ''
                    print(f'| {key.title():<12}| {value:>6.2f} {icon:<1} |')
            print('*' + '-' * 24 + '*')
            
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
    
    def __fight_hunter(self, hunter: Hunter) -> Tuple[str, bool]:
        """
        A weighted sum of the foragers strength, endurance and agility 
        are compared to the hunters. The loser is made inactive.

        Args:
            hunter (Hunter): The hunter the forager is fighting

        Returns:
            Tuple[bool, str]: 
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
# appended here to avoid circular import error
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
    
    def set_motivation(self) -> str:
        """
        The forager decides on a motivation such as finding food or a mate.
        """
        # TODO document this
        def softmax(x):
            exp_values = [math.exp(value) for value in x]
            sum_values = sum(exp_values)
            return [exp_value / sum_values for exp_value in exp_values]
            
        choices = ['nearest food', 'furthest food', 'most sustaining food', 
                   'nearest forager', 'furthest forager', 'most compatible forager']

        # foragers gain better abilities as they evolve
        if self.forager.agility > 7:
            self.forager.bonus_attributes.append('zig zag past hunter')
        elif self.forager.perception > 5:
            self.forager.bonus_attributes.append('sniff food')
        elif self.forager.perception == 9 and self.forager.agility == 9:
            self.forager.bonus_attributes.append('camouflage')
        
        # Rate the choices, make a choice, set motivation
        novelty_values = [(self.novelty_value(choice)) for choice in choices]
        probabilities = softmax(novelty_values)
        choice_prob = list(zip(choices, probabilities))
        motivation = random.choices(choice_prob, weights=[prob for _, prob in choice_prob])[0][0]
        
        return motivation
    
    # region NV
    def novelty_value(self, choice):
        """
        Each choice is transformed into a novelty value.

        Args:
            choice (str): The motivation of the forager.
        """
        # number of steps to destination
        choice_weight = self.forager.motivation_weights[choice]
        
        # Lean towards novel motivations
        if choice not in self.forager.successful_motivations:
            choice_weight += math.log(self.forager.positive_multiplier + 1.2, 10)
        else:
            choice_weight *= self.forager.decay_factor
            
        if choice == 'nearest food' or choice == 'nearest forager':
            if (self.forager.perception > self.forager.boost1_threshold 
                or self.forager.agility > self.forager.boost1_threshold):
                choice_weight += math.log(self.forager.positive_multiplier + 1, 10)
        elif choice == 'furthest food' or choice == 'furthest forager':
            if (self.forager.strength > self.forager.boost1_threshold
                or self.forager.endurance > self.forager.boost1_threshold):
                choice_weight += math.log(self.forager.positive_multiplier + 1, 10)
        
        if choice == 'most sustaining food':
            if (self.forager.strength > self.forager.boost2_threshold
                or self.forager.perception > self.forager.boost2_threshold):
                choice_weight += math.log(self.forager.positive_multiplier + 1.1, 10)
                
        if choice == 'most compatible forager':
            if (self.forager.endurance > self.forager.boost2_threshold
                or self.forager.agility > self.forager.boost2_threshold):
                choice_weight += math.log(self.forager.positive_multiplier + 1.1, 10)
        
        # skilled foragers are more likely to explore     
        # if (len(self.forager.bonus_attributes) > 0
        #     and choice == 'furthest food'
        #     or choice == 'furthest forager'):
        #     choice_weight += math.log(self.forager.positive_multiplier + 1.2, 10)
        
        # add benefits from boosts in here
        if self.forager.hunger > 5:
            # forager is hungry so lean towards eating
            if choice == 'nearest food':
                choice_weight += math.log(self.forager.positive_multiplier + 1.1, 10)
            elif choice == 'most sustaining food' and 'sniff food' in self.forager.bonus_attributes:
                # forager knows the nearest food *is* is the most sustaining
                if self.steps_to_choice('nearest food') == self.steps_to_choice('most sustaining food'):
                    choice_weight += math.log(self.forager.positive_multiplier + 1.2, 10)
            elif choice == 'furthest food':
                choice_weight += math.log(self.forager.positive_multiplier + 1.1, 10)
         
        # # nudge slightly towards mating
        # if choice == 'most compatible forager':
        #     choice_weight = (choice_weight * (self.forager.positive_multiplier * 1.05)) * 10
        
        if choice_weight < 0:
            raise ValueError
        else:
            self.forager.motivation_weights[choice] = choice_weight
            return choice_weight
        
    def steps_to_choice(self, choice: str):
        """
        Calculates all steps to completing the foragers motivation.

        Args:
            choice (str): The motivation of the forager.

        Returns:
            list: list of (x,y) coordinates.
        """
        steps = []
        current_coords = self.forager.current_coords
        destination_coords = self.get_destination_coordinates(choice)
        while current_coords != destination_coords:
            next_coord = self.get_next_coordinate(current_coords, destination_coords)
            current_coords = next_coord
            steps.append(next_coord)
        return steps
        
    def find_all(self, object_class: Food | Forager | Hunter) -> list:
        """
        List of (x,y) coordinates for all objects of specified type.
        """
        objs = []
        for y in range(self.environment.height):
            for x in range(self.environment.width):
                if isinstance(self.environment.simulation[y][x], object_class):
                    simulation_obj = self.environment.simulation[y][x]
                    obj_dict = {}
                    if simulation_obj.id == self.forager.id:
                        continue
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
        Checks the foragers motivation and finds the (x,y) coordinate in the simulation
        

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
        