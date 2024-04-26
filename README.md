A simulated environment in which foragers search for food and mates while navigating ravines and hunters.

Can be run from the command line
`$ python novelty_search.py`

Optional arguments can be passed to change the simulation setup: 
- number of foragers 
- number of hunters 
- number of ravines 
- number of food items 
- grid height 
- grid width
- number of steps
- run name

The default simulation configuration reproduced in the CLI is `python novelty_search.py 4 3 3 6 15 15 75 my_run`.

`run name` determines the name of the directy within `logs/` where all the data about the simulation is stored. This includes the environment, foragers decisions and forager logs. Each foragers log is also isolated and stored seperately in `logs/forager/run_name`. Logs are only stored for foragers which are alive at the end of the simulation.

To change between novelty search or random search, or to have more granular configuration options, refer to `forager_config.toml`. This allows editing of initial hunger and bravery, compatibility threshold and more.

The script which runs the simulation is `novelty_search.py`. In this file you can edit the default configuration by adding or removing objects from `load_default_inhabitants()` if you prefer this method to the CLI. 

In `simulation.run()` the arguments `replace` and `display` can be toggled to replace lost foragers/hunters and to display all details during the simulation to stdout. 

Once you've run the simulation checks the `logs/run_name` directory to find the output, the forager logs and the charts detailing it!

The venv (`as_venv`) was built on ARM64 architecture. `requirements.txt` has been provided to make it easy to install dependencies if you would like to test out the simulator on another architecture.