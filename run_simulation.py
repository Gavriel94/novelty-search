import sys

from simulation.agents.forager import Forager
from simulation.agents.hunter import Hunter
from simulation.agents.food import Food
from simulation.agents.ravine import Ravine
from simulation.grid import Grid

def load_default_inhabitants():
    return [
        Ravine(grid_width=GRID_WIDTH, grid_height=GRID_HEIGHT),
        Ravine(grid_width=GRID_WIDTH, grid_height=GRID_HEIGHT),
        Forager(sex='M'),
        Forager(sex='F'),
        Hunter(),
        Hunter(),
        Hunter(),
        Food(),
        Food(),
        Food()
    ]

GRID_WIDTH = 10
GRID_HEIGHT = 10

environment = []
if len(sys.argv) < 7:
    g = Grid(GRID_WIDTH, GRID_HEIGHT)
    environment.extend(load_default_inhabitants())
    simulation_steps = 15
else:
    num_foragers = int(sys.argv[1])
    num_hunters = int(sys.argv[2])
    num_ravines = int(sys.argv[3])
    num_food = int(sys.argv[4])
    grid_height = int(sys.argv[5])
    grid_width = int(sys.argv[6])
    simulation_steps = int(sys.argv[7])
    g = Grid(grid_width, grid_height)

    for i in range(num_ravines):
        environment.append(Ravine(grid_width=grid_width, grid_height=grid_height))
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
g.run_simulation(steps=simulation_steps, replace_agent=True, display_attributes=True)
# g.get_forager_logs(save_as_txt=False)
