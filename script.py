from agents.forager import Forager
from agents.hunter import Hunter
from agents.food import Food
from agents.ravine import Ravine

f1 = Forager(sex='M')

f1.display_attributes()
food = Food()
print(food)

for i in range(100):
    f1.eat(food)
    
f1.display_attributes()

print('\n' + '-' * 50 + '\n')

f2 = Forager(sex='F')
f2.display_attributes()

for i in range(100):
    f2.hunger_increase()
f2.display_attributes()
