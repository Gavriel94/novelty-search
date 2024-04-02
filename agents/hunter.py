from .mammal import Mammal

class Hunter(Mammal):
    def __init__(self, id, hunger, bravery, agility, 
                 perception, strength, endurance):
        super().__init__(id, hunger, bravery, agility, 
                         perception, strength, endurance)
        
        self.sustenance_granted = self.calculate_sustenance()
    
    def calculate_sustenance(self) -> int:
        """
        Calculate how much sustenance the hunter gives the forgager if they lose the fight
        """
        pass  
    
    def sustenance(self) -> int:
        try:
            return self.sustenance_granted
        except:
            print(f'No sustenance value for Hunter {self.id}')
        
        