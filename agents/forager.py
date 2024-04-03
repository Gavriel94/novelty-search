from .mammal import Mammal
from .hunter import Hunter
from .food import Food
from .ravine import Ravine
from math import isclose
from random import choice as rdm_choice
import tomllib

class Forager(Mammal):
    def __init__(self, id: str, hunger: float, bravery: float, agility: float, 
                 perception: float, strength: float, endurance: float, sex: str):
        if sex not in ['M', 'F']:
            raise ValueError('Sex must be \'M\' or \'F\'')

        super().__init__(id, hunger, bravery, agility, 
                        perception, strength, endurance)
        self.sex = sex
        self.compatability_threshold = self.__calculate_compatibility_threshold()
        self.alive = True
        with open('agents/forager_config.toml', 'rb') as f:
            self.config = tomllib.load(f)
            if (self.config['compat_diff'] > 1.0 or 
                self.config['compat_diff'] < 0):
                raise ValueError('config: compat_diff out of range 0-1.')
            if (self.config['hunger_combinator'] > 1.0 or
                self.config['hunger_combinator'] < 0):
                raise ValueError('config: hunger_combinator out of range 0-1.')
                
    
    def eat(self, food: Food) -> None:
        """
        Satiates the forager and alters attributes.
        Going down:
            - hunger
            - bravery 
        Going up:
            - agility
            - perception
            - strength
            - endurance
        """
        self.__check_death()
        print(f'{self.id} ate the {food.name}\n')
        combinator = food.sustenance_granted
        
        self.hunger -= combinator
        self.bravery -= combinator / 2
        
        self.agility += combinator / 2
        self.perception += combinator / 2
        self.strength += combinator / 2
        self.endurance += combinator / 2
        
    def hunger_increase(self) -> None:
        """
        The forager gets hungrier and alters attributes.     
        Going up:
            - hunger
            - bravery 
        Going down:
            - agility
            - perception
            - strength
            - endurance
        """
        self.__check_death()
        combinator = self.config['hunger_combinator']
        
        self.hunger += combinator
        self.bravery += combinator / 2
        
        self.agility -= combinator / 2
        self.perception -= combinator / 2
        self.strength -= combinator / 2
        self.endurance -= combinator / 2
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
        self.__calculate_compatibility_threshold()
        partner.__calculate_compatibility_threshold()
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
        # ID is generated in relation to parents names 
        M_id = self.id if self.sex == 'M' else partner.id
        F_id = self.id if self.sex == 'F' else partner.id
        o_id = f'of_{M_id}{F_id}'
        # Choose attributes stochastically
        offspring = Forager(id=o_id, 
                            hunger=rdm_choice([1.0, 2.0, 3.0, 4.0, 5.0]), 
                            bravery=rdm_choice([0.0, 1.0, 2.0, 3.0, 4.0, 5.0, 
                                                6.0, 7.0, 8.0, 9.0, 10.0]), 
                            agility=rdm_choice([0.0, 1.0, 2.0, 3.0, 4.0, 5.0, 
                                                6.0, 7.0, 8.0, 9.0, 10.0]),  
                            perception=rdm_choice([0.0, 1.0, 2.0, 3.0, 4.0, 5.0, 
                                                6.0, 7.0, 8.0, 9.0, 10.0]),  
                            strength=rdm_choice([0.0, 1.0, 2.0, 3.0, 4.0, 5.0, 
                                                6.0, 7.0, 8.0, 9.0, 10.0]), 
                            endurance=rdm_choice([0.0, 1.0, 2.0, 3.0, 4.0, 5.0, 
                                                6.0, 7.0, 8.0, 9.0, 10.0]),  
                            sex=rdm_choice(['M', 'F']))
        print(f'{M_id} and {F_id} produced offspring {o_id}.\n')
        return offspring
    
    def engage_hunter(self, hunter: Hunter) -> bool:
        # if bravery > 5 then fight
        # if fight, calculate a value based on strength, endurance and agility
        # if flee, calculate a value based on endurance, agility and perception
        """
        if the forager has a 25% chance of winning the 
        rng has to get one number in the range of 4 (rng picks `1` from `1, 2, 3, 4`. 
        50% chance then the rng has two numbers: (`1, 2` from `1, 2, 3, 4`), 
        75% then rng has 3 numbers etc)
        have to use attribute values to find the initial chance of winning, then do the dice roll.
        """
        self.__check_death()
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
            return True
        else:
            return False
    
    def die(self) -> bool:
        """
        The forager did not survive.
        """
        self.alive = False
    
    def __check_death(self) -> 'InvalidForager':
        """
        Check to ensure dead foragers do not perform actions.
        """
        if self.alive == False:
            raise InvalidForager(self.id)
    
    def __calculate_compatibility_threshold(self) -> None:
        """
        The "attractiveness" of the forager.
        """
        self.compatability_threshold = (self.bravery + 
                                        self.strength + 
                                        (self.perception * 1.5))
        return self.compatability_threshold
    
    def __fight_hunter(self, hunter: Hunter) -> bool:
        """
        if the forager has a 25% chance of winning the 
        rng has to get one number in the range of 4 (rng picks `1` from `1, 2, 3, 4`. 
        50% chance then the rng has two numbers: (`1, 2` from `1, 2, 3, 4`), 
        75% then rng has 3 numbers etc)
        have to use attribute values to find the initial chance of winning, then do the dice roll.
        """
        # calculate a value based on strength, endurance and agility
        pass
    
    def __flee_hunter(self, hunter: Hunter) -> bool:
        """
        if the forager has a 25% chance of winning the 
        rng has to get one number in the range of 4 (rng picks `1` from `1, 2, 3, 4`. 
        50% chance then the rng has two numbers: (`1, 2` from `1, 2, 3, 4`), 
        75% then rng has 3 numbers etc)
        have to use attribute values to find the initial chance of winning, then do the dice roll.
        """
        # calculate a value based on endurance, agility and perception
        pass
        
    def __str__(self) -> str:
        return f'Forager {self.id}'
    
class InvalidForager(Exception):
    """
    Ensures dead foragers do not perform actions.
    Mainly used for testing.
    """
    def __init__(self, forager_id):
        self.message = f'Forager {forager_id} should not be performing any actions.'
        super().__init__(self.message)