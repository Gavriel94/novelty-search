import random

class Food():
    def __init__(self):
        self.name, self.sustenance_granted = self.create_food()
    
    def create_food(self) -> None:
        """
        The food this object will emulate.

        Returns:
            tuple: The name of the food and sustenance granted. 
        """
        food_dict = {
            'pumpkin': 0.8,
            'peach': 0.4,
            'yucca': 0.3,
            'mushroom': 0.3,
            'shrub': 0.2,
            'flower': 0.1,
            'berry': 0.1,
            'seeds': 0.2,
        }
        name, sus = random.choice(list(food_dict.items()))
        return name, sus
        
    def __str__(self) -> str:
        return (f'{self.name.title()}: '
    f'{self.sustenance_granted} sustenance.\n')
        