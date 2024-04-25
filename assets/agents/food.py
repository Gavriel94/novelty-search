import random
import shortuuid

class Food():
    """
    Food for the foragers to find and eat.
    """
    def __init__(self):
        self.id = self.__generate_id()
        self.name, self.sustenance_granted = self.create_food()
    
    def create_food(self) -> tuple[str, float]:
        """
        Gets a food name and amount of sustenance granted.
        """
        food_dict = {
            'pumpkin': 0.8,
            'melon': 0.8,
            'carrot': 0.4,
            'apple': 0.3,
            'mushroom': 0.3,
            'shrub': 0.2,
            'flower': 0.1,
        }
        name, sus = random.choice(list(food_dict.items()))
        return name, sus
    
    def __generate_id(self) -> str:
        """
        A unique ID for the food.
        """
        return shortuuid.random(length=4)
        
    def __str__(self) -> str:
        """
        Overload str method for more informative output when printing.
        """
        return (f'{self.name.title()}: {self.sustenance_granted} sustenance.\n')
