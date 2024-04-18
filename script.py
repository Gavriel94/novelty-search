import sys

from simulation.agents.forager import Forager
from simulation.agents.hunter import Hunter
from simulation.agents.food import Food
from simulation.agents.ravine import Ravine
from simulation.grid import Grid

def load_default_inhabitants():
    return [
        Ravine(),
        Ravine(),
        Forager(sex='M'),
        Forager(sex='F'),
        Hunter(),
        Hunter(),
        Hunter(),
        Food(),
        Food(),
        Food()
    ]

g = Grid(10, 10)
environment = []

if len(sys.argv) < 4:
    environment.extend(load_default_inhabitants())
else:
    num_foragers = int(sys.argv[1])
    num_hunters = int(sys.argv[2])
    num_ravines = int(sys.argv[3])
    num_food = int(sys.argv[4])

    for i in range(num_ravines):
        environment.append(Ravine())
    for i in range(num_foragers):
        if i % 2 == 0:
            environment.append(Forager(sex='M'))
        else:
            environment.append(Forager(sex='F'))
    for i in range(num_hunters):
        environment.append(Hunter())
    for i in range(num_food):
        environment.append(Food())

g.setup_environment(environment)
g.run_simulation(steps=10, replace_agent=True, display_attributes=True)
# g.get_forager_logs(save_as_txt=False)
