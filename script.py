from agents.forager import Forager
from agents.hunter import Hunter
from agents.plant import Plant

f1 = Forager('f1', 3.0, 3.0, 3.0, 3.0, 3.0, 3.0, 'M')
f2 = Forager('f2', 3.0, 3.0, 3.0, 3.0, 3.0, 3.0, 'F')

shrub = Plant(name='shrub', sustenance_granted=0.8)

f1.get_attributes()
for i in range(3):
    f1.hunger_increase()
f1.get_attributes()

print('-'*50+'\n')

f2.get_attributes()
f2.eat(shrub)
f2.get_attributes()

f1.die()
f1.get_attributes()