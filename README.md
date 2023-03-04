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

The run.py can be executed with muliple flag, full list bellow

--no-index					
--register-drive "drive label"	Specify drive label to register, must be used in combination with --task flag	
--start-task	"task name"		Specify task to start
--task "task name"				Specify task to start. Will search for a registered connected drive, if none is available will do nothing

## Know bug or issues

None at this instant, feel free to open an issue

## Roadmap

- Drive initialisation (Clear drive and encrypt with bitlocker)
- Remove lost/broken drive and clear backup status
- Add backup history point
- Rebuild from scratch indexation process to make backup faster
- Database already ready but script can only backup to drive of group A at this moment. Two more group will be available B and C for deduplication purpose

## License


## Project status
Under active devellopement and usage by myself
