from .mammal import Mammal
from .hunter import Hunter
from .food import Food
from .ravine import Ravine
from math import isclose
from random import randrange, choice
import tomllib
from typing import Tuple

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
            self.hunger = self.__validate_cfg(self.config['hunger'], 10.0)
            self.bravery = self.__validate_cfg(self.config['bravery'], 10.0)
            self.compat_diff = self.__validate_cfg(self.config['compat_diff'], 1)
            self.hunger_combinator = self.__validate_cfg(self.config['hunger_combinator'], 1)
        
        # sex is either random or set on init
        if sex == None:
            self.sex = choice(['M', 'F'])
        elif sex != None and sex not in ['M', 'F']:
            raise ValueError('Sex must be \'M\' or \'F\'')
        # Set default attributes
        self.compatability_threshold = self.__get_compatibility()
        self.alive = True
        self.type = 'Forager'
        
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
        print(f'{self.id} ate the {food.name}\n')
        self.hunger = max((self.hunger - food.sustenance_granted), 0.0)
        self.bravery = max((self.hunger - food.sustenance_granted / 2), 0.0)
        
        self.agility = min((self.agility + food.sustenance_granted / 2), 10.0)
        self.perception = min((self.perception + food.sustenance_granted / 2), 10.0)
        self.strength = min((self.strength + food.sustenance_granted / 2), 10.0)
        self.endurance = min((self.endurance + food.sustenance_granted / 2), 10.0)
        
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
        
        self.hunger = min((self.hunger + self.hunger_combinator), 10)
        self.bravery = min((self.bravery + self.hunger_combinator / 2), 10)
        
        self.agility = max((self.agility - self.hunger_combinator / 2), 0)
        self.perception = max((self.perception - self.hunger_combinator / 2), 0)
        self.strength = max((self.strength - self.hunger_combinator / 2), 0)
        self.endurance = max((self.endurance - self.hunger_combinator / 2), 0)
        if self.hunger == 10:
            print(f'{self.id} starved.\n')
            self.alive = False
        else:
            print(f'{self.id}\'s hunger increased.\n')
        
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
        print(f'{self.id} and {partner.id} produced offspring {offspring.id}.\n')
        return offspring
    
    def engage_hunter(self, hunter: Hunter) -> bool:
        """
        Determines foragers action when coming across a hunter.

        Args:
            hunter (Hunter): The opposing hunter.

        Returns:
            bool: True if the forager 
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
            print(f'Forager {self.id} successfully crossed ravine {ravine.id}\n')
            return True
        else:
            print(f'Forager {self.id} fails to cross ravine {ravine.id}.\n')
            return False
    
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
        else:
            self.alive = False
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
            return (True, 'flee')    
        else:
            self.alive = False
            return (False, 'flee')
        
    def __str__(self) -> str:
        return f'Forager {self.id}.\n'
    
    def __validate_cfg(self, att: float, max: float) -> float | ValueError:
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
    
class InvalidForager(Exception):
    """
    Ensures dead foragers do not perform actions.
    """
    def __init__(self, forager_id):
        self.message = f'Forager {forager_id} should not be inactive.'
        super().__init__(self.message)