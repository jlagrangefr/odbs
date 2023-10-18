# Calls the odbs.py file containing the ODBS class
from odbs import Odbs
import sys

if sys.prefix == sys.base_prefix:
    print("Please run this script from the python venv!")
    print("Scripts/python run.py")
    exit()

# Load config file
import json
with open('config.json') as json_data_file:
    config = json.load(json_data_file)

# Create Object from ODBS Class
print("Loading ODBS...")
odbs = Odbs(config['db_host'],config['db_port'],config['db_user'],config['db_pass'],config['db_name'])

# Start ODBS in interactive mode
odbs.startUI()