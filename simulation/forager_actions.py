from simulation.agents.forager import Forager
from simulation.agents.food import Food

class ForagerActions():
    def __init__(self, environment, forager):
        self.environment = environment
        self.foods = self.find(Food)
        self.foragers = self.find(Forager)
        self.current_forager = forager
    # """
    # This is like the brain of the forager. This determines the foragers actions.
    # * The definition for novel search should be in here!
    # gets the coordinates the forager needs to get food/a mate
    
    # Can find food or foragers ordered by distance, 
    # forager compatibility and food sustenance given
    
    # Args:
    #     environment (Grid): current simulation state.
    # """
    
    # # * -- Beginning of helper methods -- * 
        
    def find(self,object_class: Food | Forager) -> list:
        """
        List of (x,y) coordinates for each Food object.
        """
        objs = []
        for y in range(self.environment.height):
            for x in range(self.environment.width):
                if isinstance(self.environment.grid[y][x], object_class):
                    grid_obj = self.environment.grid[y][x]
                    if grid_obj.id == self.id:
                        continue
                    if object_class == Food:
                        obj_dict = {}
                        obj_dict['id'] = grid_obj.id
                        obj_dict['type'] = 'Food'
                        obj_dict['key_attribute'] = grid_obj.sustenance_granted
                        obj_dict['location'] = (x,y)
                        objs.append(obj_dict)
                    elif object_class == Forager:
                        obj_dict = {}
                        obj_dict['type'] = 'Forager'
                        obj_dict['key_attribute'] = grid_obj.compatability_threshold
                        obj_dict['location'] = (x,y)
                        objs.append(obj_dict)
        return objs
        
    def nearest_food(self):
        food_locations = []
        for food in self.foods:
            food_locations.append(food['location'])
        output = self.get_nearest(food_locations)
        if output == None:
            raise ValueError(f'Output: {output}')
        return output
    
    def furthest_food(self):
        food_locations = []
        for food in self.foods:
            food_locations.append(food['location'])
        output = self.get_furthest(food_locations)
        if output == None:
            raise ValueError(f'Output: {output}')
        return output
    
    def most_sustenance(self):
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
                
    def nearest_forager(self):
        if len(self.foragers) == 0:
            self.current_forager.__log_statement(f'{self.current_forager.id} cannot find any potential mates.\n'
                                    'Looking for nearest food instead.')
            output = self.nearest_food()
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
    
    def furthest_forager(self):
        if len(self.foragers) == 0:
            self.current_forager.__log_statement(f'{self.current_forager.id} cannot find any potential mates.\n'
                                    'Looking for furthest food instead.')
            output = self.furthest_food()
            if output == None:
                raise ValueError(f'Output: {output}')
            return self.furthest_food()
        else:
            forager_locations = []
            for forager in self.foragers:
                forager_locations.append(forager['location'])
            output = self.get_furthest(forager_locations)
            if output == None:
                raise ValueError(f'Output: {output}')
            return self.get_furthest(forager_locations)
        
    def most_compatible(self):
        # TODO change food in variable name to forager
        if len(self.foragers) == 0:
            self.current_forager.__log_statement(f'{self.current_forager.id} cannot find any potential mates.\n'
                    'Looking for most sustenance instead.')
            return self.most_sustenance()
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
        Manhattan distance between self and object.

        Args:
            object_loc (tuple(int,int)): x, y coordinate of object.
        """
        return (abs(object_loc[0] - self.current_forager.current_coords[0]) + 
                abs(object_loc[1] - self.current_forager.current_coords[1]))
    
    def sort_by_nearest(self, locations):
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
        objs = self.sort_by_nearest(locations)
        objs.reverse()
        return objs
    
    def get_nearest(self, locations):
        objs = self.sort_by_nearest(locations)
        return objs[0]
    
    def get_furthest(self, locations):
        objs = self.sort_by_furthest(locations)
        return objs[0]