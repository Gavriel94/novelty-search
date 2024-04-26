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

The default simulation configuration reproduced in the CLI is `python novelty_search.py 4 3 4 6 20 20 200 my_run`
The run name determines the name of the directy within `logs/` where all the data about the simulation is stored. This includes the environment, foragers decisions and forager logs. Each foragers log is also isolated and stored seperately in `logs/forager/run_name`

To change between novelty search or random search, or to have more granular configuration options, refer to `forager_config.toml`. This allows editing of initial hunger and bravery, compatibility threshold and more.

The script which runs the simulation is `novelty_search.py`. In this file you can edit the default configuration by adding or removing objects from `load_default_inhabitants()` if you prefer this method to the CLI. 

In `simulation.run()` the arguments `replace` and `display` can be toggled to replace lost foragers/hunters and to display all details during the simulation to stdout. 

If you'd like to save the logs of each forager as a text file, a new directory will be created from whatever string is passed to `simulation.save_forager_logs()`. This method has the power to overwrite any files currently in that directory, so if the simulation is being run more than once it's important to ensure that this is being changed each time. 