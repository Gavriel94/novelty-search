import shortuuid

class Mammal():
    """
    Superclass for hunters and foragers.
    """
    def __init__(self, agility: float, 
                 perception: float , strength: float , endurance: float):
        self.id = self.generate_id()
        self.type = None
        self.agility = self.validate_arg(agility, 'agility')
        self.perception = self.validate_arg(perception, 'perception')
        self.strength = self.validate_arg(strength, 'strength')
        self.endurance = self.validate_arg(endurance, 'endurance')     
    
    def validate_arg(self, arg_value: float, arg_name: str) -> float:
        """
        Ensure attributes are the correct type and in the right range. 

        Args:
            arg (int|float): arg value
            arg_name (str): arg name
        """
        min_value = 0
        max_value = 10
        if not isinstance(arg_value, float):
            raise TypeError(
                f'{arg_name.title()} must be a floating point number.')
        if arg_value < min_value or arg_value > max_value:
            raise ValueError(f'{arg_name.title()} must be in range 0-10.')
        return arg_value
    
    def generate_id(self) -> str:
        return shortuuid.random(length=4)
    
    def display_attributes(self) -> None:
        """
        Display all mammal attributes in a table
        """
        id_len = len(vars(self)['id'])
        v_length = max(12, id_len)
        t_length = 28 + v_length
        att = 'Attribute'
        val = 'Value'
        h_line = '*' + '-' * t_length + '*'
        print(h_line)
        print(f'| {att:<23} | {val:>{v_length}} |')
        print(h_line)
        for key, value in vars(self).items():
            if isinstance(value, (float, int)) and key != 'alive':
                print(f'| {key.title():<23} | '
                      f'{str(round(value, 2)):>{v_length}} |')
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
                elif key == 'log':
                    continue
                elif key == 'attribute_log':
                    continue
                else:
                    print(f'| {key.title():<23} | {str(value):>{v_length}} |')
        print(h_line + '\n')
                