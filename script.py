from agents.forager import Forager
from agents.hunter import Hunter
from agents.plant import Plant

# Default difference between compatibility thresholds
MAX_DIFF = 0.1

f1 = Forager('f1', 3.0, 3.0, 3.0, 3.0, 3.0, 3.0, 'M')
f2 = Forager('f2', 3.0, 3.0, 3.0, 3.0, 3.0, 3.0, 'F')



f1.get_attributes()