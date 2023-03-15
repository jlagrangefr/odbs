import os,json,subprocess

# Check of config.json file exists
if not os.path.isfile("config.json"):
    print("config.json file not found!")
    exit()

# Check if schema.sql file exists
if not os.path.isfile("schema.sql"):
    print("schema.sql file not found!")
    exit()

# Load config file
with open('config.json') as json_data_file:
    config = json.load(json_data_file)

# Install pip dependencies
subprocess.call("pip install pywin32 mmhash3 mysql.connector tdqm varint", shell=True)

# Open SQL file
sql_file = open("schema.sql", "r")
sql = sql_file.read()
sql_file.close()

# Connect to MySQL
try:
    import mysql.connector
    mydb = mysql.connector.connect(
        host=config['db_host'],
        port=config['db_port'],
        user=config['db_user'],
        passwd=config['db_pass'],
        database=config['db_name']
    )

    # Create cursor
    mycursor = mydb.cursor(buffered=True)

    # Execute SQL
    mycursor.execute(sql,multi=True)

    # Commit changes
    mydb.commit()

    # Close connection
    mydb.close()

    # Print success message
    print("Database setup complete!")
except mysql.connector.Error as err:
    print("Error connecting to MySQL database : " + str(err))
    exit()