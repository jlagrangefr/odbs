# Offline Distributed Backup Script

## Description

This script sole purpose is to backup file on external drive and manage backup distributed accross multiple drives.

## Requirement

A MySQL/MariaDB server to store the index datas (Tested with MariaDB 10.6)
Python (Tested with 3.11)

## Installation

Launch setup script

 python setup.py

## Usage

For interractive mode start run.py script

 python run.py

The run.py can be executed with muliple flag, full list bellow (Comming in v0.2)

| Parameter 						| Description |
| --------------------------------- | --- |
| --drive "label" 					| Specify drive to use with selected task, must be used in combination with --task flag |
| --no-index						| Task is started with no indexation mode |
| --register-drive "drive label"	| Specify drive label to register, must be used in combination with --task flag |
| --start-task "task name"			| Specify task to start |
| --task "task name"				| Specify task to start. Will search for a registered connected drive, if none is available will do nothing |

## Know bug or issues

Check the Roadmap for missing functionality
None at this instant, feel free to open an issue

## Roadmap

v 0.2 :
- Add task options to database
- Add full checksum while indexing source folder for data integrity check (Task Option, default Off)
- Add unmanaged script use by task manager by requiring no user input
- Build notification system
- Store logs of operations into a log file when in background mode
- Build different verbose level for background mode (1: Only errors, 2: Warnings and above, 3: Informationals and above, 4: Debug mode)

v 0.3 :
- Drive initialisation (Clear drive and encrypt with bitlocker)
- Make drive fully autonomous to select registered drive and change drive when first drive is full (Task Option, default Off)
- Add Email Notification in task option

v 0.4 :
- Add backup history point

v 0.5:
- Restore functions (File, folder or full)

Long future
- Rebuild from scratch indexation process to make backup faster

## License
MIT License. See LICENSE.MD

## Project status
Under active devellopement and usage by myself
