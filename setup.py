import os,json,subprocess,sys

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

# Check if python venv exists
if not os.path.isdir("Scripts"):
    print("Python venv not found!")
    print("Please run the following commands manually: ")
    print("")
    print("python -m venv .")
    exit()

# Check if current script has been launched from the venv
if sys.prefix == sys.base_prefix:
    print("Please run this script from the python venv!")
    print("Please run the following commands manually: ")
    print("")
    print("Scripts/python setup.py")
    exit()

# Get current path
current_path = os.getcwd()
print(current_path)

# Swap to python from venv
subprocess.call(current_path+"/Scripts/python -m pip install --upgrade pip", shell=True)

# Install pip dependencies
subprocess.call(current_path+"/Scripts/pip install beaupy pywin32 mmhash3 mysql.connector tdqm varint", shell=True)

# Check if pip dependencies are correctly installed
try:
    import beaupy
    import win32api
    import mmh3
    import mysql.connector
    import tqdm
    import varint
except:
    print("Error installing pip dependencies!")
    print("Please run the following commands manually:")
    print("")
    print("./Scripts/python -m pip install --upgrade pip")
    print("./Scripts/pip install pywin32 mmhash3 mysql.connector tdqm varint")
    exit()

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

    # Check if database exists
    mycursor.execute("SHOW DATABASES")
    databases = mycursor.fetchall()
    database_exists = False
    for database in databases:
        if database[0] == config['db_name']:
            database_exists = True
    
    # If database does not exist, exit with an error
    if not database_exists:
        print("Database does not exist!")
        exit()

    # Check if database is empty
    mycursor.execute("USE " + config['db_name'])
    mycursor.execute("SHOW TABLES")
    tables = mycursor.fetchall()
    if len(tables) > 0:
        print("Database is not empty. If you are recovering from a crash or installaing the agent on a new machine this is normal.")
        print("")
        exit()

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