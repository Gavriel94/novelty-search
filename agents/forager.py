from .mammal import Mammal
from .hunter import Hunter
from .plant import Plant
from typing import Union
from math import isclose
from random import choice as rdm_choice

class Forager(Mammal):
    def __init__(self, id: str, hunger: float, bravery: float, agility: float, 
                 perception: float, strength: float, endurance: float, sex: str):
        if sex not in ['M', 'F']:
            raise ValueError('Sex must be \'M\' or \'F\'')

        super().__init__(id, hunger, bravery, agility, 
                        perception, strength, endurance)
        self.sex = sex
        self.compatability_threshold = self.__compatibility_threshold()
        self.alive = True
    
    def eat(self, food: Plant) -> None:
        """
        Satiates the forager. Alters attributes.
        Going down:
            - hunger
            - bravery 
        Going up:
            - strength
            - agility
            - perception
            - endurance
        """
        sustenance = food.sustenance()
        self.hunger += sustenance
        self.__attribute_adjustment(sustenance=sustenance, eating=True)
        # TODO rebalance attributes using the amount of sustenance as a combinator
        # TODO This algorithm must also be applied to "get hungry", with the same combinator
        
    def is_compatible_with(self, partner: 'Forager', max_diff: float) -> bool:
        """
        Calculates comatilibity between two foragers.

        Args:
            partner (Forager): Potential mate.
            max_diff (float): Difference between foragers compatibility 
            thresholds. Larger max_diff means the forager is less "fussy". 
            
        Returns:
            bool: True, if compatible.
        """
        # Recalculate threshold as Forager may have rebalanced attributes
        self.__compatibility_threshold()
        if (self.sex == 'M' and partner.sex == 'F' or 
            self.sex == 'F' and partner.sex == 'M'):
            if isclose(self.compatability_threshold, 
                       partner.compatability_threshold, 
                       rel_tol=max_diff):
                return True
            else:
                return False
        else:
            return False
    
    def produce_offspring(self, partner: 'Forager') -> 'Forager':
        """
        Calculate compatibility threshold using a combination of attributes
        needs more thinking, to deal with male/female differently but this can wait
        """
        # ID is generated in relation to parents names 
        M_id = self.id if self.sex == 'M' else partner.id
        F_id = self.id if self.sex == 'F' else partner.id
        id = f'of_{M_id}{F_id}'
        # Choose attributes stochastically
        offspring = Forager(id=id, 
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
        return offspring

    def increase_hunger(self) -> None:
        """
        The forager gets hungrier. Alters attributes.     
        Going up:
            - hunger
            - bravery 
        Going down:
            - strength
            - agility
            - perception
            - endurance
            - agility
        """
        # Forager gets hungrier, and more brave
        self.hunger += 0.3
        
        
        pass
    
    def fight_or_flee(self, hunter: Hunter):
        """
        Determines if the forager will fight or flee. 
        Calculate value based on a combination of bravery, strength, endurance and agility
        """
        pass
    
    def fight(self, hunter: Hunter):
        """
        Fight the hunter. compare strength of forager and hunter
        imagining this like a dice roll, if the forager has a 25% chance of winning the rng has to get one number in the range of 4 (rng picks `1` from `1, 2, 3, 4`. 50% chance then the rng has two numbers: (`1, 2` from `1, 2, 3, 4`), 75% then rng has 3 numbers etc)
        have to use attribute values to find the initial chance of winning, then do the dice roll.
        """
        pass
    
    def flee(self, hunter: Hunter):
        """
        Can get caught if endurance/agility is low.
        Same logic as fight but forager ends up in a different place of the environment, the predator remains. 
        """
        pass
    
    def die(self) -> bool:
        """
        The forager did not survive.
        """
        self.alive = False
        return True
    
    def __attribute_adjustment(self, sustenance: int, eating: bool) -> None:
        if eating:
            """
            Going down:
                - hunger
                - bravery 
            Going up:
                - strength
                - agility
                - perception
                - endurance
                - agility
            """
            pass
        else:
            """
            Going up:
                - hunger
                - bravery 
            Going down:
                - strength
                - agility
                - perception
                - endurance
                - agility
            """
            pass
        pass
    
    def __compatibility_threshold(self) -> None:
        """
        The "attractiveness" of the forager. 
        """
        self.compatability_threshold = (self.bravery + 
                                        self.strength + 
                                        (self.perception * 1.5))
        return self.compatability_threshold
        
    def __str__(self) -> str:
        return f'Forager {self.id}'
    