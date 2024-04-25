import sys

from assets.agents.forager import Forager
from assets.agents.hunter import Hunter
from assets.agents.food import Food
from assets.agents.ravine import Ravine
from assets.environment.simulation import Simulation
from assets.environment.simulation import SimulationAnalytics

def load_default_inhabitants():
    return [
        Ravine(grid_width=DEFAULT_GRID_WIDTH),
        Ravine(grid_width=DEFAULT_GRID_WIDTH),
        Forager(sex='M'),
        Forager(sex='F'),
        Hunter(),
        Hunter(),
        Hunter(),
        Food(),
        Food(),
        Food()
    ]

DEFAULT_GRID_WIDTH = 10
DEFAULT_GRID_HEIGHT = 10

if len(sys.argv) < 7:
    # load default simulation config
    simulation = Simulation(DEFAULT_GRID_WIDTH, DEFAULT_GRID_HEIGHT)
    environment = load_default_inhabitants()
    simulation_steps = 50
else:
    # read command line arguments
    num_foragers = int(sys.argv[1])
    num_hunters = int(sys.argv[2])
    num_ravines = int(sys.argv[3])
    num_food = int(sys.argv[4])
    grid_height = int(sys.argv[5])
    grid_width = int(sys.argv[6])
    simulation_steps = int(sys.argv[7])
    simulation = Simulation(grid_width, grid_height)

    environment = []
    for i in range(num_ravines):
        environment.append(Ravine(grid_width=DEFAULT_GRID_WIDTH))
    for i in range(num_foragers):
        if i % 2 == 0:
            environment.append(Forager(sex='M'))
        else:
            environment.append(Forager(sex='F'))
    for i in range(num_hunters):
        environment.append(Hunter())
    for i in range(num_food):
        environment.append(Food())

simulation.setup_environment(environment)
simulation.run(steps=simulation_steps, replace=True, display=True)
# simulation.get_forager_logs(save_as_txt=False)

analytics = SimulationAnalytics(simulation=simulation)
analytics.display_overall_gene_trends()
analytics.when_stuff_changed()
analytics.plot_motivations_trend()

