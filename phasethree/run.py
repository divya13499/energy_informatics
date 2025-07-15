import sys
import os

# Add the current directory to the Python module search path
sys.path.append(os.path.dirname(__file__))

from scenario_builder import create_scenario

world = create_scenario('/Users/divyasabu/Desktop/phasethree/input_files')

END = 3600 * 24  # Simulation time (e.g., one day)

world.run(until=END)

# monitored_data contains simulation outputs