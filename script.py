from agents.forager import Forager
from agents.hunter import Hunter
from agents.food import Food
from agents.ravine import Ravine

f1 = Forager(id='f1', hunger=3.0, bravery=3.0, agility=10.0, perception=3.0, strength=3.0, endurance=10.0, sex='M')
f2 = Forager('f2', 3.0, 3.0, 3.0, 3.0, 3.0, 3.0, 'F')
o = f1.produce_offspring(f2)
snack = Food()

print(snack)