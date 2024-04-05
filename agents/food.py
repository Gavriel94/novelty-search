import random

class Food():
    def __init__(self):
        self.name = None
        self.sustenance_granted = None
        self.create_food()
    
    def create_food(self) -> None:
        """
        Dictionary of possible plants.
        Each plant is instantiated and initialised at random.
        Close to emulating nature.
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
        self.name = name
        self.sustenance_granted = sus
        
    def __str__(self) -> str:
        return (f'{self.name.title()}: '
    f'{self.sustenance_granted} sustenance.')
        