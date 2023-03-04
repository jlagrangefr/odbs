# Required components
import win32api,win32file,sys,os,pathlib,re,mysql.connector,time,shutil,itertools,math
from mysql.connector import MySQLConnection, Error
from tqdm import tqdm
from datetime import datetime
from imohash import hashfile
from beaupy import *
from beaupy.spinners import *

# Script Version
odbs_version = "0.1.0"

# ODBS Class
class Odbs:
    indexation = True
    add_task = False

    database = {"host":None,"port":None,"user":None,"pass":None,"name":None}

    selected_drive = {"id":None,"name":None,"path":None}
    selected_task = {"id":None,"name":None,"path":None}
    task_action = None
    drive_action = None

    # Class constructor
    def __init__(self,db_host,db_port,db_user,db_pass,db_name):
        self.database['host'] = db_host
        self.database['port'] = db_port
        self.database['user'] = db_user
        self.database['pass'] = db_pass
        self.database['name'] = db_name
        # Connect to database
        self.databaseConnection()

    # Database connection
    def databaseConnection(self):
        try:
            self.cnx = mysql.connector.connect(user=self.database['user'], password=self.database['pass'], host=self.database['host'], port=self.database['port'], database=self.database['name'])
            self.cursor = self.cnx.cursor(buffered=True)
        except mysql.connector.Error as err:
            print(err)
            sys.exit()

    ########################################################
    #                  Generic Functions                   #
    ########################################################

    # Ask integer and check value
    def askInteger(self,message = "Enter int : ", valid_choices = None):
        try:
            choice = int(input(message))
            if valid_choices is not None:
                if choice not in valid_choices:
                    print("Invalid choice, possible value are {}".format(valid_choices))
                    choice = self.askInteger(message,valid_choices)
        except:
            if valid_choices is None:
                print("Integer only")
            else:
                print("Integer only, possible value are {}".format(valid_choices))
            choice = self.askInteger(message,valid_choices)
        return choice
    
    # Ask Path to user
    def askPath(self,message = "Enter path : "):
        path = input(message)
        if self.isDirectory(path):
            return path
        else:
            print("Invalid path")
            path = self.askPath(message)
            return path

    # Ask string and check value
    def askString(self,message = "Enter string : ", valid_choices = None):
        try:
            choice = str(input(message))
            if valid_choices is not None:
                if choice not in valid_choices:
                    print("Invalid choice, possible value are {}".format(valid_choices))
                    choice = self.askString(message,valid_choices)
        except:
            if valid_choices is None:
                print("String only")
            else:
                print("String only, possible value are {}".format(valid_choices))
            choice = self.askString(message,valid_choices)
        return choice

    # Create directory
    def createDirectory(self,path):
        pathlib.Path(path).mkdir(parents=True, exist_ok=True)
    
    # Convert size in bytes to human readable format
    def convertSize(self,size_bytes):
        if size_bytes == 0:
            return "0B"
        size_name = ("B", "KB", "MB", "GB", "TB", "PB", "EB", "ZB", "YB")
        i = int(math.floor(math.log(size_bytes, 1024)))
        p = math.pow(1024, i)
        s = round(size_bytes / p, 2)
        return "%s %s" % (s, size_name[i])

    # Convert seconds to human readable format
    def convertTime(self,seconds):
        if seconds == 0:
            return "0s"
        time_name = ("s", "m", "h", "d", "w", "y")
        i = int(math.floor(math.log(seconds, 60)))
        p = math.pow(60, i)
        s = round(seconds / p, 2)
        return "%s %s" % (s, time_name[i])
    
    # Check if a path is a valid directory
    def isDirectory(self,path):
        if os.path.isdir(path):
            return True
        else:
            return False
        
    # Check if a path is a valid file
    def isFile(self,path):
        if os.path.isfile(path):
            return True
        else:
            return False

    # Pause program
    def pause(self):
        programPause = input("Press the <ENTER> key to continue...")

    #########################################################
    #                    CLI UI functions                   #
    #########################################################

    # Main loop for interactive UI
    def startUI(self):
        self.exit = False
        while self.exit == False:
            self.clearTerminal()
            self.getTerminalSize()
            self.printHeader()
            self.printMenu()
        print("Closing ODBS...")

    # Clear terminal
    def clearTerminal(self):
        os.system('cls' if os.name == 'nt' else 'clear')
    
    # Get terminal width
    def getTerminalSize(self):
        self.terminal_width = shutil.get_terminal_size()[0]

    # Print Header to terminal width using self.terminal_width
    def printHeader(self):
        print("".center(self.terminal_width, '#'))
        print(" Offline Distributed Backup Script v{} ".format(odbs_version).center(self.terminal_width-2, ' ').center(self.terminal_width, '#'))
        print("".center(self.terminal_width, '#'))

    # Print Menu to terminal
    def printMenu(self):
        print(" Selected Task : {} - Selected Drive : {} ".format(self.selected_task["name"],self.selected_drive["name"]).center(self.terminal_width-2, ' ').center(self.terminal_width, '#'))
        print("".center(self.terminal_width, '#'))
        # if task not selected
        if self.selected_task['id'] is None:
            # Not Task selected. Print menu select task
            self.printMenuTaskSelection()
        else:
            # Task is selected. Is task_action defined ?
            if self.task_action is None:
                self.printMenuTaskAction()
            else:
                match self.task_action:
                    case "start_backup":
                        if self.selected_drive['id'] is None:
                            self.checkDrives()
                        else:
                            self.startTask()
                    case "manage_drives":
                        if self.selected_drive['id'] is None:
                            self.checkDrives()
                        else:
                            self.printMenuDriveManagement()
                    case "index_task":
                        self.indexTask()
                    case "restore_files":
                        self.printMenuRestoreFiles()
                    case "delete_task":
                        self.deleteTask()
    
    # Print menu drive management
    def printMenuDriveManagement(self):
        # Count registered drives for task
        self.cursor.execute("SELECT `id` FROM `drives` WHERE `task` = {}".format(self.selected_task['id']))
        registered_drives_count = self.cursor.rowcount
        if registered_drives_count > 0:
            if(self.selected_drive['id'] is not None):
                print(" 0. Back main menu".ljust(self.terminal_width-2, ' ').center(self.terminal_width, '#'))
                print(" 1. Index Drive".ljust(self.terminal_width-2, ' ').center(self.terminal_width, '#'))
                print(" 2. Remove Drive".ljust(self.terminal_width-2, ' ').center(self.terminal_width, '#'))
                print(" 3. Clear drive selection".ljust(self.terminal_width-2, ' ').center(self.terminal_width, '#'))
                print("".center(self.terminal_width, '#'))
                valid_choices = [0,1,2,3]
                choice = self.askInteger("Select an action : ",valid_choices)
                match choice:
                    case 0:
                        self.task_action = None
                        self.selected_drive = {"id":None,"name":None,"path":None}
                    case 1:
                        self.indexDrive()
                    case 2:
                        self.removeDrive()
                    case 3:
                        self.selected_drive = {"id":None,"name":None,"path":None}
            else:
                print(" No registered drive is connected".ljust(self.terminal_width-2, ' ').center(self.terminal_width, '#'))
                print(" 0. Back main menu".ljust(self.terminal_width-2, ' ').center(self.terminal_width, '#'))
                print(" 1. Register Drive".ljust(self.terminal_width-2, ' ').center(self.terminal_width, '#'))
                print(" 2. Management unconnected drive".ljust(self.terminal_width-2, ' ').center(self.terminal_width, '#'))
                valid_choices = [0,1,2]
                choice = self.askInteger("Select an action : ",valid_choices)
                match choice:
                    case 0:
                        self.task_action = None
                    case 1:
                        self.addDrive()
                    case 2:
                        self.printMenuDriveSelection()
        else:
            print(" This task has no registered drive".ljust(self.terminal_width-2, ' ').center(self.terminal_width, '#'))
            print(" 0. Back main menu".ljust(self.terminal_width-2, ' ').center(self.terminal_width, '#'))
            print(" 1. Register Drive".ljust(self.terminal_width-2, ' ').center(self.terminal_width, '#'))
            valid_choices = [0,1]
            choice = self.askInteger("Select an action : ",valid_choices)
            match choice:
                case 0:
                    self.task_action = None
                case 1:
                    self.addDrive()

    # Print Menu task Selection
    def printMenuTaskSelection(self):
        # get task list from database
        self.cursor.execute("SELECT `id`,`name`,`path` FROM `tasks` ORDER BY `name` ASC")
        print(" 0. Quit program".ljust(self.terminal_width-2, ' ').center(self.terminal_width, '#'))
        print(" 1. Add new task".ljust(self.terminal_width-2, ' ').center(self.terminal_width, '#'))
        valid_choices = [0,1]
        actions = [(0,0,0,0),(1,0,0,0)]
        action_id = 2
        # Print task list
        for id,name,path in self.cursor:
            actions.append((action_id,id,name,path))
            print(" {}. {} ({})".format(action_id,name,path).ljust(self.terminal_width-2, ' ').center(self.terminal_width, '#'))
            valid_choices.append(action_id)
            action_id += 1
        print("".center(self.terminal_width, '#'))
        # Ask user to select task
        choice = self.askInteger("Enter choice : ",valid_choices)
        if choice == 0:
            # Exit program
            self.exit = True
        elif choice == 1:
            # Add new task
            self.addTask()
        if choice > 1:
            # Set selected task
            self.selected_task = {"id":actions[choice][1],"name":actions[choice][2],"path":actions[choice][3]}

    # Print Menu task Action     
    def printMenuTaskAction(self):
        print(" 0. Quit program".ljust(self.terminal_width-2, ' ').center(self.terminal_width, '#'))
        print(" 1. Start backup".ljust(self.terminal_width-2, ' ').center(self.terminal_width, '#'))
        print(" 2. Manage drives".ljust(self.terminal_width-2, ' ').center(self.terminal_width, '#'))
        print(" 3. Index Task".ljust(self.terminal_width-2, ' ').center(self.terminal_width, '#'))
        print(" 4. Restore files".ljust(self.terminal_width-2, ' ').center(self.terminal_width, '#'))
        print(" 5. Clear task selection".ljust(self.terminal_width-2, ' ').center(self.terminal_width, '#'))
        valid_choices = [0,1,2,3,4,5]
        print("".center(self.terminal_width, '#'))
        # Ask user input
        choice = self.askInteger("Enter choice : ",valid_choices)
        if choice == 0:
            # Exit program
            self.exit = True
        elif choice == 1:
            # Set task action to Start backup
            self.task_action = "start_backup"
        elif choice == 2:
            # Set task action to Manage drives
            self.task_action = "manage_drives"
        elif choice == 3:
            # Set task action to Index task
            self.task_action = "index_task"
        elif choice == 4:
            # Set task action to Restore files
            self.task_action = "restore_files"
        elif choice == 5:
            # Clear task selection
            self.selected_task = {"id":None,"name":None,"path":None}

    """    Old Menus
    #########################################################
    #                  Menu Functions                       #
    #########################################################

    # Show main menu
    def showMenuMain(self):
        print("Welcome to ODBS\n")
        print("This script will help you backup your data accross multiple drives\n")
        exit = False
        while exit == False:
            if self.selected_task['id'] is not None:
                print("Current task : {}".format(self.selected_task['name']))
                print("0. Quit program")
                print("1. Start backup")
                print("2. Manage drives")
                print("3. Index Task")
                print("4. Restore files")
                print("9. Clear task selection")
                valid_choices = [0,1,2,3,4,9]
            else:
                print("No task selected")
                print("0. Quit program")
                print("1. Select task")
                valid_choices = [0,1]
            choice = self.askInteger("Enter choice : ",valid_choices)
            match choice:
                case 0:
                    exit = True
                case 1:
                    if self.selected_task['id'] is not None:
                        self.checkDrives()
                        self.startTask()
                    else:
                        self.cursor.execute("SELECT `id` FROM `tasks`")
                        if self.cursor.rowcount > 0:
                            self.showMenuTaskSelection()
                        else:
                            print("No task found, launching new task wizard")
                            self.addTask()
                case 2:
                    self.showMenuDriveManagement()
                case 3:
                    self.indexTask()
                case 4:
                    self.showMenuRestoreSelection()
                case 9:
                    self.selected_task = {"id":None,"name":None,"path":None}
        print("Bye !")

    # Build drive management menu
    def showMenuDriveManagement(self):
        exit = False
        # Count registerd drives for current task
        self.cursor.execute("SELECT `id` FROM `drives` WHERE `task` = {}".format(self.selected_task['id']))
        nbr_registered_drives = self.cursor.rowcount
        while exit == False:
            if nbr_registered_drives > 0:
                # If a drive is connected, auto select it
                self.checkDrives()
                if(self.selected_drive['id'] is not None):
                    print("Current connected drive : {}".format(self.selected_drive['name']))
                    print("0. Back to main menu")
                    print("1. Index drive")
                    print("2. Remove drive")
                    print("3. Select clear drive selection")
                    valid_choices = [0,1,2,3]
                    choice = self.askInteger("Enter choice : ",valid_choices)
                    match choice:
                        case 0:
                            exit = True
                        case 1:
                            self.indexDrive()
                        case 2:
                            self.removeDrive()
                        case 3:
                            self.selected_drive = {"id":None,"name":None,"path":None}
                        case _:
                            print("Invalid choice")
                else:
                    print("None of the registered drives is currently connected")
                    print("0. Back to main menu")
                    print("1. Register drive")
                    print("2. Select unconnected drive")
                    valid_choices = [0,1,2]
                    choice = self.askInteger("Enter choice : ",valid_choices)
                    match choice:
                        case 0:
                            exit = True
                        case 1:
                            self.addDrive()
                        case 2:
                            self.showMenuDriveSelection()
                        case _:
                            print("Invalid choice")
            else:
                print("No drive registered for this task")
                print("0. Back to main menu")
                print("1. Register drive")
                valid_choices = [0,1]
                choice = self.askInteger("Enter choice : ",valid_choices)
                match choice:
                    case 0:
                        exit = True
                    case 1:
                        self.addDrive()
                    case _:
                        print("Invalid choice")
        self.selected_drive = {"id":None,"name":None,"path":None}
        print("Back to main menu")

    def showMenuDriveSelection(self):
        self.cursor.execute("SELECT `id`,`name` FROM `drives` WHERE `task` = {} ORDER BY `name`".format(self.selected_task['id']))
        print("Select a Drive :")
        print("0. Back to Drive Management")
        actions = [(0,0,0)]
        action_id = 1
        valid_actions = [0]
        for id,name in self.cursor:
            actions.append((action_id,id,name))
            print("{}. {}".format(action_id,name))
            valid_actions.append(action_id)
            action_id += 1
        if len(valid_actions) == 1:
            print("No registered drives for this task")
        else:
            selected_action = self.askInteger("Select drive : ",valid_actions)

            self.selected_drive = {"id":None,"name":None,"path":None}

            # match
            match selected_action:
                case 0:
                    print("Leaving Drive Selection")
                case _:
                    for action_id, drive_id, drive_name in actions:
                        if action_id == selected_action:
                            self.selected_drive = {"id":drive_id,"name":drive_name,"path":None}
                            print("\nDrive {} selected\n".format(drive_name))

    # Show Menu Restore Selection
    def showMenuRestoreSelection(self):
        exit = False
        while(exit is False):
            print("Select a Restore action")
            print("0. Back to Main Menu")
            print("1. Restore Single File")
            print("2. Restore Folder")
            valid_actions = [0,1,2]
            selected_action = self.askInteger("Select action : ",valid_actions)
            match selected_action:
                case 0:
                    print("Leaving Restore Selection")
                    exit = True
                case 1:
                    self.searchFile()
                    self.askDestinationPath()
                    self.restoreFile()
                case 2:
                    self.searchFolder()
                    self.askDestinationPath()
                    self.restoreFolder()
                case _:
                    print("Invalid action")
                    sys.exit(0)

    # Build task selection menu
    def showMenuTaskSelection(self):
        self.cursor.execute("SELECT `id`,`name`,`path` FROM `tasks` ORDER BY `name`")
        print("Select a Task :")
        print("0. Add new Task")
        actions = [(0,0,0,0)]
        action_id = 1
        valid_actions = [0]
        for id,name,path in self.cursor:
            actions.append((action_id,id,name,path))
            print("{}. {} ({})".format(action_id,name,path))
            valid_actions.append(action_id)
            action_id += 1
        selected_action = self.askInteger("Select task : ",valid_actions)

        self.selected_task = {"id":None,"name":None,"path":None}

        if selected_action == 0:
            self.addTask()
        else:
            for action_id, task_id, task_name, task_path in actions:
                if action_id == selected_action:
                    self.selected_task = {"id":task_id,"name":task_name,"path":task_path}
                    print("\nTask {} ({}) selected\n".format(task_name,task_path))
    
    
    # Show menu
    def showMenu(self,menu):
        match menu:
            case "drivemangement":
                self.cursor.execute("SELECT `id` FROM `drives` WHERE `task` = {}".format(self.selected_task['id']))
                if self.cursor.rowcount > 0:
                    self.showMenuDriveManagement()
                else:
                    print("No drive found, launching new drive wizard")
                    self.addDrive()
            case "main":
                self.showMenuMain()
            case "taskmanagement":
                self.showMenuTaskManagement()
            case "taskselection":
                self.cursor.execute("SELECT `id` FROM `tasks`")
                if self.cursor.rowcount > 0:
                    self.showMenuTaskSelection()
                else:
                    print("No task found, launching new task wizard")
                    self.addTask()
            case _:
                print("Menu not found")
                sys.exit(0)

    # Show Menu Main
    def showMenuMain(self):
        exit = False
        while(exit is False):
            print("Welcome to ODBS")
            print("This program will backup your file and distribute them on multiple drives")
            print("0. Exit Program")
            print("1. Select and start Task")
            print("2. Manage Tasks")
            print("3. Restore Files")
            valid_actions = [0,1,2,3]
            selected_action = self.askInteger("Select action : ",valid_actions)
            match selected_action:
                case 0:
                    print("Exiting program")
                    exit = True
                case 1:
                    self.showMenu("taskselection")
                    self.checkDrives()
                    self.startTask()
                case 2:
                    self.showMenu("taskselection")
                    self.showMenu("taskmanagement")
                case 3:
                    self.showMenu("taskselection")
                    self.showMenu("restoreselection")
                case _:
                    print("Invalid action")
                    sys.exit(0)

    # Show Menu Task Management
    def showMenuTaskManagement(self):
        exit = False
        while(exit is False):
            print("Managing Task {}".format(self.selected_task['name']))
            print("0. Back to Main Menu")
            print("1. Manage Drives")
            print("2. Show task details")
            print("3. Edit task")
            print("4. Index source folder")
            print("5. Search for files")
            print("6. Delete task")
            valid_actions = [0,1,2,3,4,5,6]
            selected_action = self.askInteger("Select action : ",valid_actions)
            match selected_action:
                case 0:
                    print("Leaving task management")
                    exit = True
                    self.selected_task = {"id":None,"name":None,"path":None}
                case 1:
                    self.showMenu("drivemangement")
                    self.showMenuDriveManagement()
                case 2:
                    self.showTask()
                case 3:
                    self.editTask()
                case 4:
                    self.indexTask()
                case 5:
                    self.searchFiles()
                case 6:
                    self.deleteTask()
                    exit = True
                    del self.task
                case _:
                    print("Invalid action")
                    sys.exit(0)
    """

    ########################################################
    #                 Task Managing Functions              #
    ########################################################

    # Add task to database
    def addTask(self):
        task_name = input("Enter task name : ")
        task_path = self.askPath("Enter source Path : ")
        task_desc = input("Enter description : ")
        self.cursor.execute("INSERT INTO `tasks` (`name`,`path`,`desc`,`ts_creation`,`ts_lastedit`) VALUES (%(name)s,%(path)s,%(desc)s,UNIX_TIMESTAMP(),UNIX_TIMESTAMP())",{
            "name": task_name,
            "path": task_path,
            "desc": task_desc
        })
        if self.cursor.rowcount > 0:
            print("\nTask {} for {} added successfully\n".format(task_name,task_path))
            self.cnx.commit()
        else:
            print("New task creation failed")

    # Show task details
    def showTask(self):
        self.cursor.execute("SELECT `name`,`path`,`desc`,`ts_creation`,`ts_lastedit`,`ts_lastindex`,`ts_lastexec` FROM `tasks` WHERE `id` = %(id)s",{
            "id": self.selected_task['id']
        })
        for name,path,desc,ts_creation,ts_lastedit,ts_lastindex,ts_lastexec in self.cursor:
            print("Task Name : {}".format(name))
            print("Task Path : {}".format(path))
            print("Task Description : {}".format(desc))
            print("Task Creation : {}".format(datetime.fromtimestamp(ts_creation).strftime("%Y-%m-%d %H:%M:%S")))
            print("Task Last Edit : {}".format(datetime.fromtimestamp(ts_lastedit).strftime("%Y-%m-%d %H:%M:%S")))
            print("Task Last Indexation : {}".format(datetime.fromtimestamp(ts_lastindex).strftime("%Y-%m-%d %H:%M:%S")))
            print("Task Last Execution : {}".format(datetime.fromtimestamp(ts_lastexec).strftime("%Y-%m-%d %H:%M:%S")))
            print("")

    # Start Backup
    def startTask(self):
        # Check if source path is available
        if not os.path.exists(self.selected_task['path']):
            print("Can't connect to task folder {}, please check if path is correct.".format(self.selected_task['path']))
            sys.exit(0)
        
        # Get last indexation timestamp and ask for indexation
        self.cursor.execute("SELECT `ts_lastindex` FROM `tasks` WHERE `id` = %(id)s",{ "id": self.selected_task['id'] })
        for ts_lastindex in self.cursor:
            ts_lastindex = ts_lastindex[0]
        if ts_lastindex != 0:
            print("Last indexation : {}".format(datetime.fromtimestamp(ts_lastindex).strftime("%Y-%m-%d %H:%M:%S")))
            indexation = ""
            while(not re.match("[ynYN]",indexation)):
                indexation = input("Do you want to reindex the source folder ? (y/n) : ")
            if indexation == "y" or indexation == "Y":
                self.indexTask()
        
        # Build file transfer list
        print("Building Transfer List")
        self.cursor.execute("SELECT id,filename,source_path,source_size,backup_a_date FROM `files` WHERE `task` = %(task)s AND `source_missing` = 0 ORDER BY `source_path`,`filename`",{'task':self.selected_task['id']})
        filelist = self.cursor.fetchall()
        self.cursor.execute("SELECT SUM(source_size) FROM (SELECT source_size FROM `files` WHERE `task` = %(task)s AND `source_missing` = 0 ORDER BY `source_path`,`filename`) AS F",{'task':self.selected_task['id']})
        total_size = int(self.cursor.fetchone()[0])
        print("Starting copy. {} elements to copy, total size is {}".format(len(filelist),self.convertSize(total_size)))

        # Progress Bar Initialization
        processed_size = 0
        pbar_copy_items = tqdm(total=len(filelist),unit='Files',unit_scale=True,unit_divisor=1000,miniters=1,position=0)
        pbar_copy_size = tqdm(total=total_size,unit='Bytes',unit_scale=True,unit_divisor=1024,miniters=1,position=1)
        freeBytes, totalBytes, totalFreeBytes = win32api.GetDiskFreeSpaceEx(self.selected_drive['path'])
        pbar_drive_usage = tqdm(total=totalBytes,desc='Drive {} Usage'.format(self.selected_drive['name']),unit='Bytes',unit_scale=True,unit_divisor=1024,miniters=1,position=2)
        pbar_drive_usage.update(totalBytes-totalFreeBytes)

        # Var Initialization
        drive_full = False
        copy_failed = False
        count_copy = {"total":0,"success":0,"errors":0,"missing":0,"already":0}

        # Copy Loop
        for id,filename,source_path,source_size,backup_a_date in filelist:
            if backup_a_date is None:
                # File is yet to be backuped
                freeBytes, totalBytes, totalFreeBytes = win32api.GetDiskFreeSpaceEx(self.selected_drive['path'])
                # Check if there is enough space on destination
                if totalFreeBytes < source_size:
                    # Not enough space on destination, ask for next drive
                    drive_full = True
                    while drive_full:
                        self.askDrive()
                        freeBytes, totalBytes, totalFreeBytes = win32api.GetDiskFreeSpaceEx(self.selected_drive['path'])
                        if totalFreeBytes > source_size:
                            pbar_drive_usage.close()
                            pbar_drive_usage = tqdm(total=totalBytes,desc='Drive {} Usage'.format(self.selected_drive['name']),unit='Bytes',unit_scale=True,unit_divisor=1024,miniters=1,position=2)
                            pbar_drive_usage.update(totalBytes-totalFreeBytes)
                            drive_full = False
                source_file = os.path.join(source_path,filename)
                pbar_copy_items.write("Copying {}".format(source_file))
                # Enought space on destination, proceed further
                if os.path.exists(source_file):
                    # Source file exist
                    copy_failed = False
                    dest_path = source_path.replace(self.selected_task['path'], self.selected_drive['path'])
                    dest_file = os.path.join(dest_path,filename)
                    if os.path.exists(dest_file):
                        ss = os.stat(source_file).st_size
                        ds = os.stat(dest_file).st_size
                        pbar_copy_items.write("File already present on drive.")
                        # Destination file already exist
                        if ss != ds:
                            pbar_copy_items.write("Not the same size, copy anyway")
                            # If not same size copy anyway
                            try:
                                # Process for successful copy
                                shutil.copy2(source_file, dest_file)
                                count_copy['success'] += 1
                                processed_size += source_size
                            except:
                                # Process for failed copy
                                pbar_copy_items.write("Failed to copy file {} to {}. Please rerun backup task afterward to atempt again this file.".format(source_file,source_file))
                                copy_failed = True
                                count_copy['errors'] += 1
                                processed_size += source_size
                        else:
                            # If same size mark completed
                            count_copy['already'] += 1
                            processed_size += source_size
                    else:
                        # New File, start by creating folder if not present
                        self.createDirectory(dest_path)
                        try:
                            # Process for successful copy
                            shutil.copy2(source_file, dest_file)
                            count_copy['success'] += 1
                            processed_size += source_size
                        except:
                            # Process for failed copy
                            pbar_copy_items.write("Failed to copy file {} to {}. Please rerun backup task afterward to atempt again this file.".format(source_file,source_file))
                            copy_failed = True
                            count_copy['errors'] += 1
                            processed_size += source_size
                    # Storing in database if copy has not failed
                    if not copy_failed:
                        data = {
                            'backup_a_drive'	: self.selected_drive['id'],
                            'backup_a_path'	    : dest_path.replace(self.selected_drive['path'],self.selected_drive['name']+":\\"),
                            'backup_a_date'	    : int(time.time()),
                            'id'				: id,
                        }
                        self.cursor.execute("UPDATE `files` SET `backup_a_drive` = %(backup_a_drive)s,`backup_a_path` = %(backup_a_path)s,`backup_a_date` = %(backup_a_date)s WHERE `id` = %(id)s",data)
                        self.cnx.commit()
                    # Increment progress bars
                    pbar_copy_items.update(1)
                    pbar_copy_size.update(source_size)
                    pbar_drive_usage.update(source_size)
                else:
                    pbar_copy_items.write("Source file is Missing, Tagging in database.")
                    # Source file is missing, updating database
                    self.cursor.execute("UPDATE `files` SET `source_missing` = 1 WHERE `id` < %(id)s",{'id':id})
                    self.cnx.commit()
                    count_copy['missing'] += 1
                    # Increment progress bars
                    pbar_copy_items.update(1)
                    pbar_copy_size.update(source_size)
            else:
                # File is already copied for this backup set
                count_copy['already'] += 1
                pbar_copy_items.update(1)
                pbar_copy_size.update(source_size)
            if drive_full is False:
                count_copy['total'] += 1

        # Displaying copy result
        pbar_copy_items.close()
        pbar_copy_size.close()
        pbar_drive_usage.close()

        # Get free_space on drive
        free_bytes, total_bytes, total_free_bytes = win32api.GetDiskFreeSpaceEx(self.selected_drive['path'])
        # Update free space and ts_lastsync on drive
        self.cursor.execute("UPDATE `drives` SET `free_space` = %(free_space)s,`ts_lastsync` = UNIX_TIMESTAMP() WHERE `id` = %(id)s",{'free_space':total_free_bytes,'id':self.selected_drive['id']})
        self.cnx.commit()

        if drive_full is True:
            print("\nBackup drive is full, please change drive and restart backup task");
        else:
            print("\nBackup completed succesfuly");

        # Copy files
        self.pause()

    #########################################################
    #                Indexation Functions                   #    
    #########################################################

    # Drive indexation
    def indexDrive(self):
        print("Please select an action for files that are present on this drive but not on source folder.")
        print("!!! Action 2 will permanently delete files from drive {}.".format(self.selected_drive['name']))
        print("!!! Action 3 will import files from drive {} in source folder.".format(self.selected_drive['name']))
        print("!!! Both of this actions can't be undone.")
        print("1. Ignore files")
        print("2. Delete files from drive {}".format(self.selected_drive['name']))
        print("3. Import files from drive {} in source folder".format(self.selected_drive['name']))

        valid_choice = [1,2,3]

        action = self.askInteger("Enter choice : ",valid_choice)

        match action:
            case 1:
                remove_files = False
                import_files = False
            case 2:
                remove_files = True
                import_files = False
            case 3:
                remove_files = False
                import_files = True

        print("Starting indexation of {}...".format(self.selected_drive['path']))

        count = {"update":0,"ignore":0,"remove":0,"total":0,"size":0}

        pbar_count = tqdm(miniters=1, desc="Counting files", unit="files")

        # Count files in path
        for path,subdir,files in os.walk(self.selected_drive['path']):
            for file in files:
                count['total'] += 1
                pbar_count.update(1)
        
        pbar_count.close()

        pbar_index = tqdm(miniters=1,total=count['total'], desc="Indexing files", unit="files")

        count['total'] = 0

        # Get source folder info
        volname, volsernum, maxfilelen, sysflags, filesystemname = win32api.GetVolumeInformation(self.selected_task['path'])

        # Index files in path
        for path,subdir,files in os.walk(self.selected_drive['path']):
            for name in files:
                filename, extention = os.path.splitext(name)
                filesize = os.path.getsize(os.path.join(path,name))
                checksum = hashfile(pathlib.PurePath(path,name),hexdigest=True)

                # Check if file is already in database using filename, filesize and checksum
                self.cursor.execute("SELECT * FROM `files` WHERE `filename` = %(filename)s AND `source_size` = %(filesize)s AND `source_checksum` = %(checksum)s",{'filename':name,'filesize':filesize,'checksum':checksum})
                result = self.cursor.fetchone()

                if result is None:
                    if import_files:
                        # Import file in source folder
                        source_path = os.path.join(self.selected_task['path'],path.replace(self.selected_drive['path'],""))
                        self.createDirectory(source_path)
                        shutil.copy2(os.path.join(path,name),os.path.join(source_path,name))
                        count['import'] += 1
                        # Add file to database
                        data = {
                            'task'              : self.selected_task['id'],
                            'filename'	        : name,
                            'extention'	        : extention,
                            'source_volume'	    : volname,
                            'source_path'	    : path.replace(self.selected_drive['path'],self.selected_task['name']),
                            'source_last_seen'  : int(time.time()),
                            'source_size'	    : filesize,
                            'source_checksum'   : checksum,
                            'source_missing'    : 0,
                            'backup_a_drive'	: self.selected_drive['id'],
                            'backup_a_path'	    : path.replace(self.selected_drive['path'],self.selected_drive['name']+":\\"),
                            'backup_a_date'	    : int(time.time()),
                        }
                        self.cursor.execute("INSERT INTO `files` (`task`,`filename`,`extention`,`source_volume`,`source_path`,`source_last_seen`,`source_size`,`source_checksum`,`source_missing`,`backup_a_drive`,`backup_a_path`,`backup_a_date`) VALUES (%(task)s,%(filename)s,%(extention)s,%(source_volume)s,%(source_path)s,%(source_last_seen)s,%(source_size)s,%(source_checksum)s,%(source_missing)s,%(backup_a_drive)s,%(backup_a_path)s,%(backup_a_date)s)",data)
                        self.cnx.commit()
                    else:
                        if remove_files:
                            # Remove file from drive
                            os.remove(os.path.join(path,name))
                            count['remove'] += 1
                        else:
                            # Ignore file
                            count['ignore'] += 1
                else:
                    # Update file in database
                    data = {
                        'id'                : int(result[0]),
                        'backup_a_drive'	: self.selected_drive['id'],
                        'backup_a_path'	    : path.replace(self.selected_drive['path'],self.selected_drive['name']+":\\"),
                        'backup_a_date'	    : int(time.time()),
                    }
                    self.cursor.execute("UPDATE `files` SET `backup_a_drive` = %(backup_a_drive)s, `backup_a_path` = %(backup_a_path)s, `backup_a_date` = %(backup_a_date)s WHERE `id` = %(id)s",data)
                    self.cnx.commit()
                    count['update'] += 1

                count['total'] += 1
                count['size'] += filesize
                pbar_index.update(1)

        pbar_index.close()

        # Get free_space on drive
        free_bytes, total_bytes, total_free_bytes = win32api.GetDiskFreeSpaceEx(self.selected_drive['path'])
        # Update ts_lastindex and free_space for drive in database
        self.cursor.execute("UPDATE `drives` SET `ts_lastindex` = UNIX_TIMESTAMP(), `free_space` = %(free_space)s WHERE `id` = %(id)s",{'free_space':total_free_bytes,'id':self.selected_drive['id']})
        self.cnx.commit()

        print("Indexation of {} done.".format(self.selected_drive['path']))
        print("Total files : {}".format(count['total']))
        print("Total size : {}".format(self.convertSize(count['size'])))
        print("Files updated : {}".format(count['update']))
        print("Files ignored : {}".format(count['ignore']))
        if remove_files:
            print("Files removed : {}".format(count['remove']))
        if import_files:
            print("Files imported : {}".format(count['import']))

        self.pause()

    # Task source folder indexation
    def indexTask(self):
        count = {"insert":0,"update":0,"ignore":0,"total":0,"size":0}

        start_timestamp = time.time()

        print("Starting indexation of {}...".format(self.selected_task['path']))

        pbar_count = tqdm(miniters=1, desc="Counting files", unit="files")

        # Count files in path
        for path,subdir,files in os.walk(self.selected_task['path']):
            for file in files:
                count['total'] += 1
                pbar_count.update(1)

        pbar_count.close()

        # Get volume information
        volname, volsernum, maxfilenamlen, sysflags, filesystemname = win32api.GetVolumeInformation(self.selected_task['path'])

        pbar_index = tqdm(miniters=1,total=count['total'], desc="Indexing files", unit="files")

        count['total'] = 0

        for path,subdir,files in os.walk(self.selected_task['path']):
            for name in files:
                if not re.search("#recycle",path):
                    filename, extention = os.path.splitext(name)
                    filesize = os.stat(pathlib.PurePath(path,name)).st_size
                    data = {
                        'task':	        	self.selected_task['id'],
                        'filename':			name,
                        'extension':		extention,
                        'source_volume':	volname,
                        'source_path':		path,
                        'source_last_seen':	int(time.time()),
                        'source_size':		filesize,
                        'source_checksum':  hashfile(pathlib.PurePath(path,name),hexdigest=True),
                    }
                    database_retry = 0
                    retry_flag = True
                    while retry_flag and database_retry < 5:
                        try:
                            self.cursor.execute("INSERT INTO `files` (filename,task,extension,source_volume,source_path,source_last_seen,source_size,source_checksum) SELECT * FROM (SELECT %(filename)s AS filename,%(task)s AS task,%(extension)s AS extension,%(source_volume)s AS source_volume,%(source_path)s AS source_path,%(source_last_seen)s AS source_last_seen,%(source_size)s AS source_size,%(source_checksum)s AS source_checksum) AS tmp WHERE NOT EXISTS (SELECT `filename`,`source_path` FROM `files` WHERE `filename` = %(filename)s AND `source_path` = %(source_path)s) LIMIT 1;",data)
                            if self.cursor.rowcount == 0:
                                self.cursor.execute("UPDATE `files` SET `source_last_seen` = %(source_last_seen)s, source_size = %(source_size)s, `source_checksum` = %(source_checksum)s, `source_missing` = 0 WHERE `filename` = %(filename)s AND `source_path` = %(source_path)s AND `task` = %(task)s;",data)
                                count['update'] += 1
                            else:
                                count['insert'] += 1
                            count['size'] += filesize
                            retry_flag = False
                        except mysql.connector.Error as err:
                            print(err)
                            print("Retry in 30 seconds...")
                            self.cursor.close()
                            self.cnx.close()
                            time.sleep(30)
                            self.databaseConnection()
                            database_retry += 1
                            
                    count['size'] += filesize
                else:
                    count['ignore'] += 1
                count['total'] += 1
                if(count['total'] % 1000) == 0:
                    self.cnx.commit()
                pbar_index.update(1)
        # Final Commit
        self.cnx.commit()

        pbar_index.close()

        # Print indexation results
        print("Result :\n - New files",count['insert'],"\n - Updated Files",count['update'],"\n - Total Files",count['total'],"\n - Total Size : ",self.convertSize(count['size']),"\n - Indexation Time : "+self.convertTime(int(time.time() - start_timestamp)))
	
        # Set source missing flag
        self.cursor.execute("UPDATE `files` SET `source_missing` = 1 WHERE `source_last_seen` < %(timestamp)s AND `task` = %(task)s",{'timestamp':start_timestamp,"task":self.selected_task['id']})
        # Update task last indexation date
        self.cursor.execute("UPDATE `tasks` SET `ts_lastindex` = UNIX_TIMESTAMP() WHERE `id` = %(task)s",{'task':self.selected_task['id']})
        # Commit changes
        self.cnx.commit()

    #########################################################
    #              Drives Management Functions              #
    #########################################################

    # Add drive to database
    def addDrive(self):
        print("Listing available connected drives")
        print("0. Exit Program")
        drives = self.listConnectedDrives()
        drive_num = 1
        drives_choices = []
        valid_actions = [0]
        for drive,volname,total_bytes,total_free_bytes in drives:
            print("{}. {} ({})".format(drive_num,volname,drive))
            drives_choices.append((drive_num,volname,drive,total_bytes,total_free_bytes))
            valid_actions.append(drive_num)
            drive_num += 1
        if drive_num == 1:
            print("No available drives found. Exiting program")
            sys.exit(0)
        else:
            drive_selected = self.askInteger("Select drive : ",valid_actions)
            if drive_selected != 0:
                disk_group = self.askString("Enter disk group : ",['A','B','C'])
                # Add drive to database
                for drive_num,volname,drive,total_bytes,total_free_bytes in drives_choices:
                    if drive_num == drive_selected:
                        self.cursor.execute("INSERT IGNORE INTO `drives` (`name`,`task`,`group`,`size`,`ts_registered`) VALUES(%(name)s,%(task)s,%(group)s,%(size)s,%(date_added)s)",{
                            'name'			:volname,
                            'task'			:self.selected_task['id'],
                            'group'		    :disk_group,
                            'size'			:total_bytes,
                            'free_space'    :total_free_bytes,
                            'date_added'	:int(time.time()),
                        })
                        self.cnx.commit()
                        if self.cursor.rowcount > 0:
                            print("{} ({}) added successfully".format(volname,drive))

    # Drive is full, ask other registered drive or register new drive
    def askDrive(self):
        # Get drive free space
        free_bytes, total_bytes, total_free_bytes = win32api.GetDiskFreeSpaceEx(self.selected_drive['path'])
        # Update free space and ts_lastsync on drive
        self.cursor.execute("UPDATE `drives` SET `free_space` = %(free_space)s,`ts_lastsync` = UNIX_TIMESTAMP() WHERE `id` = %(id)s",{'free_space':total_free_bytes,'id':self.selected_drive['id']})
        self.cnx.commit()
        # Disconnected from database
        self.cursor.close()
        self.cnx.close()
        print("Current drive is full. Please remove current drive and insert another one.")
        self.pause()
        # Reconnect to database
        self.databaseConnection()
        # Check if registered drive is available
        self.checkDrives()

    # Check if registered drive is available for the selected task
    def checkDrives(self,addDrive=True):
        # Get registered drives
        registered_drives = self.getRegisteredDrives()
        # Get connected drives
        connected_drives = self.listConnectedDrives()
        count_drives = 0
        drives_choices = [(0,0,0,0)]
        valid_choices = [0]
        for path,name,size,free_space in connected_drives:
            if name in registered_drives:
                count_drives += 1
                # get drive id from database
                self.cursor.execute("SELECT `id` FROM `drives` WHERE `name` = %(name)s",{
                    'name':name
                })
                drive_id = self.cursor.fetchone()[0]
                drives_choices.append((count_drives,drive_id,name,path))
                valid_choices.append(count_drives)
                # Update drive info in database : size and free space
                self.cursor.execute("UPDATE `drives` SET `size` = %(size)s, `free_space` = %(free_space)s WHERE `name` = %(name)s",{
                    'size':size,
                    'free_space':free_space,
                    'name':name
                })
                self.cnx.commit()
        if count_drives == 0:
            if addDrive:
                self.addDrive()
        elif count_drives == 1:
            # Auto select drive
            self.selected_drive = {"id":drives_choices[1][1],"name":drives_choices[1][2],"path":drives_choices[1][3]}
            print("Drive {} ({}) selected".format(self.selected_drive['name'],self.selected_drive['path']))
        else:
            print(" Multiple drives found.".ljust(self.terminal_width-2).center(self.terminal_width,"#"))
            print("0. Exit Program")
            for drive_num,drive_id,name,path in drives_choices:
                if drive_num != 0:
                    print(" {}. {} ({})".format(drive_num,name,path).ljust(self.terminal_width-2).center(self.terminal_width,"#"))
            selection = self.askInteger("Select drive : ",valid_choices)
            if selection != 0:
                self.selected_drive = {"id":drives_choices[selection][1],"name":drives_choices[selection][2],"path":drives_choices[selection][3]}
            else:
                print("Exiting program")
                sys.exit(0)
    
    # Get drive informations
    def getDriveInfos(self,drive):
        try:
            return win32api.GetVolumeInformation(drive)
        except:
            print("Error parsing drive {} ".format(drive))
            return None

    # Get registered drives names for the selected task
    def getRegisteredDrives(self):
        self.cursor.execute("SELECT `id`,`name` FROM `drives` WHERE `task` = %(task)s ORDER BY `name`",{ "task": self.selected_task['id'] })
        registered_drives = []
        for id,name in self.cursor:
            registered_drives.append(name)
        return registered_drives

    # List connected drives
    def listConnectedDrives(self):
        # Get all connected drives
        drives = win32api.GetLogicalDriveStrings().split('\000')[:-1]
        # Get system drive
        system_drive = os.getenv('systemdrive')
        fixed_drives = []
        for drive in drives:
            if win32file.GetDriveType(drive) == win32file.DRIVE_FIXED:
                if not re.match(system_drive,drive):
                    volname, volsernum, maxfilenamlen, sysflags, filesystemname = self.getDriveInfos(drive)
                    free_bytes, total_bytes, total_free_bytes = win32api.GetDiskFreeSpaceEx(drive)
                    fixed_drives.append((drive,volname,total_bytes,total_free_bytes))
        return fixed_drives