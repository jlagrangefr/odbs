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

    selected_drive = {"id":None,"name":None,"path":None,"group":None,"size":None,"free_space":None,"ts_registered":None,"ts_lastindex":None,"ts_lastsync":None}
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
    def pause(self,tqdm = False):
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
                        self.printMenuDriveManagement()
                    case "index_task":
                        self.indexTask()
                    case "restore_files":
                        self.printMenuRestoreFiles()
                    case "delete_task":
                        self.deleteTask()
    
    # Print menu drive management
    def printMenuDriveManagement(self):
        if(self.selected_drive['id'] is not None):
            self.printMenuDriveAction()
        else:
            self.printMenuDriveSelection()
    
    # Print menu drive selection
    def printMenuDriveSelection(self):
        print(" Select a drive : ".ljust(self.terminal_width-2, ' ').center(self.terminal_width, '#'))
        self.cursor.execute("SELECT `id`,`name`,`group`,`size`,`free_space` FROM `drives` WHERE `task` = {} ORDER BY `group`,`name`".format(self.selected_task['id']))
        if self.cursor.rowcount == 0:
            print(" No drive registered for this task ".ljust(self.terminal_width-2, ' ').center(self.terminal_width, '#'))
            print("".center(self.terminal_width, '#'))
            add_choice = self.askString("Do you want to add a drive ? (y/n) : ",["y","n"])
            if add_choice == "y":
                self.addDrive()
            else:
                self.task_action = None
        else:
            registered_drives = self.cursor.fetchall()
            # Get list of connected drives
            connected_drives = self.getConnectedDrives()
            drives_count = 1
            drives_choices = [(0,0,0,0,0,0)]
            print(" 0. Back to main menu ".ljust(self.terminal_width-2, ' ').center(self.terminal_width, '#'))
            for id,name,group,size,free_space in registered_drives:
                if name in connected_drives:
                    print (" {}. {} ({} - {}) Connected".format(drives_count,name,group,self.convertSize(size)).ljust(self.terminal_width-2, ' ').center(self.terminal_width, '#'))
                    # Get drive path from disk label
                    path = self.getDrivePath(name)
                    # Update drive info in database : size and free_space
                    free_space = self.getDriveFreeSpace(path)
                    self.cursor.execute("UPDATE `drives` SET `size` = {}, `free_space` = {} WHERE `id` = {}".format(size,free_space,id))
                    self.cnx.commit()
                else:
                    print (" {}. {} ({} - {}) ".format(drives_count,name,group,self.convertSize(size)).ljust(self.terminal_width-2, ' ').center(self.terminal_width, '#'))
                drives_choices.append((drives_count,id,name,group,size,free_space))
                drives_count += 1
            print("".center(self.terminal_width, '#'))
            choice = self.askString("Select a drive : ",[str(x[0]) for x in drives_choices])
            if choice == "0":
                self.selected_drive = {"id":None,"name":None,"path":None,"group":None,"size":None,"free_space":None,"ts_registered":None,"ts_lastindex":None,"ts_lastsync":None}
                self.task_action = None
            else:
                for action_id,id,name,group,size,free_space in drives_choices:
                    if str(action_id) == choice:
                        # If drive is connected get path
                        connected_drives = self.getConnectedDrives("full")
                        path = None
                        for drive_path,drive_name,drive_size,drive_free_space in connected_drives:
                            if name == drive_name:
                                path = drive_path
                        self.selected_drive = {"id":id,"name":name,"group":group,"path":path,"group":group,"size":size,"free_space":free_space,"ts_registered":None,"ts_lastindex":None,"ts_lastsync":None}
                        self.task_action = "manage_drives"
    
    # Print menu drive action
    def printMenuDriveAction(self):
        # Check if current drive is connected to computer
        connected_drives = self.getConnectedDrives("full")
        drive_connected = False
        for path,name,size,free_space in connected_drives:
            if name == self.selected_drive['name']:
                drive_connected = True
        if drive_connected == True:
            print(" Drive {} is connected to this computer ".format(self.selected_drive['name']).center(self.terminal_width-2, ' ').center(self.terminal_width, '#'))
        else:
            print(" Drive {} is NOT connected to this computer ".format(self.selected_drive['name']).center(self.terminal_width-2, ' ').center(self.terminal_width, '#'))
        print("".center(self.terminal_width, '#'))
        print(" 0. Back main menu".ljust(self.terminal_width-2, ' ').center(self.terminal_width, '#'))
        if(drive_connected == True):
            print(" 1. Index Drive".ljust(self.terminal_width-2, ' ').center(self.terminal_width, '#'))
        else:
            print(" 1. Index Drive (Drive not connected)".ljust(self.terminal_width-2, ' ').center(self.terminal_width, '#'))
        print(" 2. Remove Drive".ljust(self.terminal_width-2, ' ').center(self.terminal_width, '#'))
        print(" 3. Clear drive selection".ljust(self.terminal_width-2, ' ').center(self.terminal_width, '#'))
        print("".center(self.terminal_width, '#'))
        drive_action = self.askString("Select an action : ",["0","1","2","3"])
        match drive_action:
            case "0":
                self.selected_drive = {"id":None,"name":None,"path":None,"group":None,"size":None,"free_space":None,"ts_registered":None,"ts_lastindex":None,"ts_lastsync":None}
                self.task_action = None
            case "1":
                if(drive_connected == True):
                    self.indexDrive()
                else:
                    print(" Drive {} is not connected to this computer. Please connect the drive and try again.".format(self.selected_drive['name']).ljust(self.terminal_width-2, ' ').center(self.terminal_width, '#'))
            case "2":
                self.removeDrive()
            case "3":
                self.selected_drive = {"id":None,"name":None,"path":None,"group":None,"size":None,"free_space":None,"ts_registered":None,"ts_lastindex":None,"ts_lastsync":None}

    """    # Count registered drives for task
        self.cursor.execute("SELECT `id` FROM `drives` WHERE `task` = {}".format(self.selected_task['id']))
        registered_drives_count = self.cursor.rowcount
        if registered_drives_count > 0:
            if(self.selected_drive['id'] is not None):
                print(" 0. Back main menu".ljust(self.terminal_width-2, ' ').center(self.terminal_width, '#'))
                print(" 1. Index Drive".ljust(self.terminal_width-2, ' ').center(self.terminal_width, '#'))
                print(" 2. Remove Drive".ljust(self.terminal_width-2, ' ').center(self.terminal_width, '#'))
                print(" 3. Clear drive selection".ljust(self.terminal_width-2, ' ').center(self.terminal_width, '#'))
                print(" 4. Manage unconnected drives".ljust(self.terminal_width-2, ' ').center(self.terminal_width, '#'))
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
                print(" 2. Manage unconnected drives".ljust(self.terminal_width-2, ' ').center(self.terminal_width, '#'))
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
                    self.addDrive()"""

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
        try:
            freeBytes, totalBytes, totalFreeBytes = win32api.GetDiskFreeSpaceEx(self.selected_drive['path'])
        except:
            print("Can't connect to drive {}, please check if path is correct.".format(self.selected_drive['path']))
            sys.exit(0)
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
                try:
                    freeBytes, totalBytes, totalFreeBytes = win32api.GetDiskFreeSpaceEx(self.selected_drive['path'])
                except:
                    print("Can't connect to drive {}, please check if path is correct.".format(self.selected_drive['path']))
                    sys.exit(0)
                # Check if there is enough space on destination
                if totalFreeBytes < source_size:
                    # Not enough space on destination, ask for next drive
                    drive_full = True
                    while drive_full:
                        pbar_copy_items.write("Current drive {} is full, please remove drive and insert a new one".format(self.selected_drive['name']))
                        pbar_copy_items.clear()
                        pbar_copy_size.clear()
                        pbar_drive_usage.clear()
                        self.askDrive()
                        try:
                            freeBytes, totalBytes, totalFreeBytes = win32api.GetDiskFreeSpaceEx(self.selected_drive['path'])
                        except:
                            print("Can't connect to drive {}, please check if path is correct.".format(self.selected_drive['path']))
                            sys.exit(0)
                        if totalFreeBytes > source_size:
                            pbar_drive_usage.close()
                            pbar_drive_usage = tqdm(total=totalBytes,desc='Drive {} Usage'.format(self.selected_drive['name']),unit='Bytes',unit_scale=True,unit_divisor=1024,miniters=1,position=2)
                            pbar_drive_usage.update(totalBytes-totalFreeBytes)
                            drive_full = False
                    pbar_copy_items.refresh()
                    pbar_copy_size.refresh()
                    pbar_drive_usage.refresh()
                source_file = os.path.join(source_path,filename)
                pbar_copy_items.write("Copying {} ({})".format(source_file,self.convertSize(source_size)))
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
        try:
            free_bytes, total_bytes, total_free_bytes = win32api.GetDiskFreeSpaceEx(self.selected_drive['path'])
        except:
            print("Can't connect to drive {}, please check if path is correct.".format(self.selected_drive['path']))
            sys.exit(0)
        # Update free space and ts_lastsync on drive
        self.cursor.execute("UPDATE `drives` SET `free_space` = %(free_space)s,`ts_lastsync` = UNIX_TIMESTAMP() WHERE `id` = %(id)s",{'free_space':total_free_bytes,'id':self.selected_drive['id']})
        self.cnx.commit()

        if drive_full is True:
            print("\nBackup drive is full, please change drive and restart backup task");
        else:
            print("\nBackup completed succesfuly");

        # Copy finished
        self.pause()
        self.cnx.reconnect()
        self.task_action = None

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
        try:
            free_bytes, total_bytes, total_free_bytes = win32api.GetDiskFreeSpaceEx(self.selected_drive['path'])
        except:
            print("Error while getting free space on drive {}.".format(self.selected_drive['path']))
            sys.exit(1)
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
        drives = self.getConnectedDrives("full")
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
            else:
                print("Exiting program")
                sys.exit(0)

    # Drive is full, ask other registered drive or register new drive
    def askDrive(self):
        # Get drive free space
        try:
            free_bytes, total_bytes, total_free_bytes = win32api.GetDiskFreeSpaceEx(self.selected_drive['path'])
        except:
            self.selected_drive = None
            return False
        # Update free space and ts_lastsync on drive
        self.cursor.execute("UPDATE `drives` SET `free_space` = %(free_space)s,`ts_lastsync` = UNIX_TIMESTAMP() WHERE `id` = %(id)s",{'free_space':total_free_bytes,'id':self.selected_drive['id']})
        self.cnx.commit()
        # Disconnected from database
        self.cursor.close()
        self.cnx.close()
        # Wait for user input
        self.pause()
        # Reconnect to database
        self.databaseConnection()
        # Check if a registered drive is available
        self.checkDrives()

    # Check if registered drive is available for the selected task
    def checkDrives(self,addDrive=True):
        # Get registered drives
        registered_drives = self.getRegisteredDrives()
        # Get connected drives
        connected_drives = self.getConnectedDrives("full")
        count_drives = 0
        drives_choices = [(0,0,0,0)]
        valid_choices = [0]
        for path,name,size,free_space in connected_drives:
            if name in registered_drives:
                count_drives += 1
                # get drive id from database
                self.cursor.execute("SELECT `id`,`group`,`size`,`ts_registered`,`ts_lastindex`,`ts_lastsync` FROM `drives` WHERE `name` = %(name)s",{
                    'name':name
                })
                drive_infos = self.cursor.fetchone()
                drives_choices.append((count_drives,drive_infos[0],name,path,drive_infos[1],drive_infos[2],free_space,drive_infos[3],drive_infos[4],drive_infos[5]))
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
                print(" No registered drive found.".ljust(self.terminal_width-2,' ').center(self.terminal_width,"#"))
                self.addDrive()
        elif count_drives == 1:
            # Auto select drive
            self.selected_drive = {
                "id"            :drives_choices[1][1],
                "name"          :drives_choices[1][2],
                "path"          :drives_choices[1][3],
                "group"         :drives_choices[1][4],
                "size"          :drives_choices[1][5],
                "free_space"    :drives_choices[1][6],
                "ts_registered" :drives_choices[1][7],
                "ts_lastindex"  :drives_choices[1][8],
                "ts_lastsync"   :drives_choices[1][9]
            }
            print("Drive {} ({}) selected".format(self.selected_drive['name'],self.selected_drive['path']))
        else:
            print(" Multiple drives found.".ljust(self.terminal_width-2).center(self.terminal_width,"#"))
            print("0. Exit Program")
            for drive_num,id,name,path,group,size,free_space,ts_registered,ts_lastindex,ts_lastsync in drives_choices:
                if drive_num != 0:
                    print(" {}. {} ({})".format(drive_num,name,path).ljust(self.terminal_width-2).center(self.terminal_width,"#"))
            selection = self.askInteger("Select drive : ",valid_choices)
            if selection != 0:
                self.selected_drive = {
                    "id"            :drives_choices[selection][1],
                    "name"          :drives_choices[selection][2],
                    "path"          :drives_choices[selection][3],
                    "group"         :drives_choices[selection][4],
                    "size"          :drives_choices[selection][5],
                    "free_space"    :drives_choices[selection][6],
                    "ts_registered" :drives_choices[selection][7],
                    "ts_lastindex"  :drives_choices[selection][8],
                    "ts_lastsync"   :drives_choices[selection][9]
                }
            else:
                print("Exiting program")
                sys.exit(0)
    
    # Get drive informations
    def getDriveInfos(self,drive):
        try:
            return win32api.GetVolumeInformation(drive)
        except:
            return (None,None,None,None,None)

    # Get registered drives names for the selected task
    def getRegisteredDrives(self,format="list"):
        self.cursor.execute("SELECT `id`,`name`,`task`,`group`,`size`,`free_space`,`ts_registered`,`ts_lastindex`,`ts_lastsync` FROM `drives` WHERE `task` = %(task)s ORDER BY `name`",{ "task": self.selected_task['id'] })
        registered_drives = []
        for id,name,task,group,size,free_space,ts_registered,ts_lastindex,ts_lastsync in self.cursor:
            if format == "list":
                registered_drives.append(name)
            else:
                registered_drives.append((id,name,task,group,size,free_space,ts_registered,ts_lastindex,ts_lastsync))
        return registered_drives

    # List connected drives
    def getConnectedDrives(self,format="list"):
        # Get all connected drives
        drives = win32api.GetLogicalDriveStrings().split('\000')[:-1]
        # Get system drive
        system_drive = os.getenv('systemdrive')
        fixed_drives = []
        for drive in drives:
            if win32file.GetDriveType(drive) == win32file.DRIVE_FIXED:
                if not re.match(system_drive,drive):
                    volname, volsernum, maxfilenamlen, sysflags, filesystemname = self.getDriveInfos(drive)
                    try:
                        free_bytes, total_bytes, total_free_bytes = win32api.GetDiskFreeSpaceEx(drive)
                    except:
                        free_bytes, total_bytes, total_free_bytes = (None,None,None)
                    if format == "list":
                        fixed_drives.append(volname)
                    else:
                        fixed_drives.append((drive,volname,total_bytes,total_free_bytes))
        return fixed_drives
    
    # Get Drive free space from path
    def getDriveFreeSpace(self,drive):
        try:
            free_bytes, total_bytes, total_free_bytes = win32api.GetDiskFreeSpaceEx(drive)
            return total_free_bytes
        except:
            return None

    # Get drive path from disk label
    def getDrivePath(self,drive_name):
        drives = win32api.GetLogicalDriveStrings().split('\000')[:-1]
        for drive in drives:
            if win32file.GetDriveType(drive) == win32file.DRIVE_FIXED:
                volname, volsernum, maxfilenamlen, sysflags, filesystemname = self.getDriveInfos(drive)
                if volname == drive_name:
                    return drive
        return None

    # Remove drive from database and clean file entry
    def removeDrive(self):
        # Clean files entry
        match self.selected_drive['group']:
            case "A":
                self.cursor.execute("UPDATE `files` SET `backup_a_drive` = NULL, `backup_a_path` = NULL, `backup_a_date` = NULL WHERE `backup_a_drive` = %(drive)s",{
                    'drive':self.selected_drive['id']
                })
            case "B":
                self.cursor.execute("UPDATE `files` SET `backup_b_drive` = NULL, `backup_b_path` = NULL, `backup_b_date` = NULL WHERE `backup_b_drive` = %(drive)s",{
                    'drive':self.selected_drive['id']
                })
            case "C":
                self.cursor.execute("UPDATE `files` SET `backup_c_drive` = NULL, `backup_c_path` = NULL, `backup_c_date` = NULL WHERE `backup_c_drive` = %(drive)s",{
                    'drive':self.selected_drive['id']
                })
            case _:
                print("Error : Drive group {} is not supported".format(self.selected_drive['group']))
                sys.exit(1)
        self.cnx.commit()
        self.cursor.execute("DELETE FROM `drives` WHERE `id` = %(id)s",{
            'id':self.selected_drive['id']
        })
        if self.cnx.commit():
            print("Drive {} ({}) removed successfully".format(self.selected_drive['name'],self.selected_drive['path']))
        else:
            print("Error removing drive {} ({})".format(self.selected_drive['name'],self.selected_drive['path']))
        self.selected_drive = {"id":None,"name":None,"path":None,"group":None,"size":None,"free_space":None,"ts_registered":None,"ts_lastindex":None,"ts_lastsync":None}