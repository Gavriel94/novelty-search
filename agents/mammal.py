class Mammal():
    def __init__(self, id: str, hunger: float, bravery: float, agility: float, 
                 perception: float , strength: float , endurance: float):
        self.id = id
        self.hunger = self.validate_arg(hunger, 'hunger')
        self.bravery = self.validate_arg(bravery, 'bravery')
        self.agility = self.validate_arg(agility, 'agility')
        self.perception = self.validate_arg(perception, 'perception')
        self.strength = self.validate_arg(strength, 'strength')
        self.endurance = self.validate_arg(endurance, 'endurance')
    
    def validate_arg(self, arg: float, arg_name: str) -> float:
        """
        Ensure attributes are the correct type and in the right range. 

        Args:
            arg (int|float): arg value
            arg_name (str): arg name
        """
        min_value = 0
        max_value = 10
        if not isinstance(arg, float):
            raise TypeError(f'{arg_name.title()} must be a floating point number.')
        if arg < min_value or arg > max_value:
            raise ValueError(f'{arg_name.title()} must be in range 0-10.')
        return arg
    
    def get_attributes(self) -> None:
        """
        Display all mammal attributes in a table
        """
        id_len = len(vars(self)['id'])
        v_length = max(12, id_len)
        t_length = 28 + v_length
        att = 'Attribute'
        val = 'Value'
        print('*' + '-' * t_length + '*')
        print(f'| {att:<23} | {val:>{v_length}} |')
        print('*' + '-' * t_length + '*')
        for key, value in vars(self).items():
            if isinstance(value, (float, int)) and key != 'alive':
                print(f'| {key.title():<23} | {str(round(value, 2)):>{v_length}} |')
            else:
                if key == 'alive':
                    if value == 1:
                        al = 'Yes'
                        print(f'| {key.title():<23} | {al:>{v_length}} |')
                    else:
                        al = 'No'
                        print(f'| {key.title():<23} | {al:>{v_length}} |')
                elif key == 'config':
                    continue
                else:
                    print(f'| {key.title():<23} | {str(value):>{v_length}} |')
        print('*' + '-' * t_length + '*' + '\n')
                