# Load config file
import json
with open('config.json') as json_data_file:
    config = json.load(json_data_file)

# Install pip dependencies
import subprocess
subprocess.call("pip install pywin32 mmhash3 mysql.connector tdqm varint", shell=True)

# Open SQL file
sql_file = open("schema.sql", "r")
sql = sql_file.read()
sql_file.close()

# Connect to MySQL
import mysql.connector
mydb = mysql.connector.connect(
    host=config['db_host'],
    port=config['db_port'],
    user=config['db_user'],
    passwd=config['db_pass'],
    database=config['db_name']
)

# Create cursor
mycursor = mydb.cursor()

# Execute SQL
mycursor.execute(sql)

# Commit changes
mydb.commit()

# Close connection
mydb.close()

# Print success message
print("Database setup complete!")