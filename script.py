from simulation.agents.forager import Forager
from simulation.agents.hunter import Hunter
from simulation.agents.food import Food
from simulation.agents.ravine import Ravine
from simulation.environment.grid import Grid

stuff = []
r1 = Ravine()
r2 = Ravine()
f1 = Forager(sex='M')
f2 = Forager(sex='F')
h1 = Hunter()
h2 = Hunter()
h3 = Hunter()
as1 = Food()
as2 = Food()
as3 = Food()

stuff.extend([r1, r2, f1, f2, h1, h2, h3, as1, as2, as3])

g = Grid(10, 10)
g.setup_environment(stuff)

# g.setup_environment(stuff)

g.display_grid()