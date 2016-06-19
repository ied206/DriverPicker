# DriverPicker
DriverPicker is tool for picking up drivers for specific version of Windows from [DriverPacks Solution](https://drp.su).  
It can also be used with other driver collections.


### How it works?
DriverPicker traverses folders to find drivers, inspects driver's target version and architecture.  
It also utilize DPS's folder naming convention to detect target version and architecture.  
Finally it will truncate unneccesary drivers, and only drivers for specific version and architecture will be left. 

WARNING : DriverPicker modifies its target folder, so you MUST prepare BACKUP of target folder.


### Why did I made it?
I occasionally build Windows PE with [Win10PESE](http://theoven.org/index.php?topic=1336.0).  
Windows PE is useful for emergency boot purpose, but needs integration of drivers to work properly in all systems.  
Especially, LAN, WLAN drivers are essential for all-purpose Windows PE.  

DriverPacks Solution is a distribuion of Windows drivers colletcion.  
Especially, DPS Full has all of its collection in several 7z archive, making it optimal its use with driver integration.  
However, when building Windows PE, only drivers of specific version and architecture is needed.  
But DPS's collection is only classified by components (LAN, WLAN, ...), not with Windows versions (7, 8, 10, ...) and architecture (x86, x64).  

DriverPicker pick up only drivers you need from DPS Full's unsorted driver collection.  
For example, picking up 'Windows 10 x64' drivers from 7, 8, 10, x86, x64 drivers.
  

### Note
This project is still in development and may be incomplete.
I do not provide any warranty with result, please read WARNING before using. 
Bug report and suggestions will be appreciated.

    
## Requirement
- [Python 3](https://www.python.org/downloads/)
- [treelib](http://xiaming.me/treelib/) library
- Piles of Windows drivers, usually [DriverPacks Solution Full](http://download.drp.su/DriverPack-Offline.torrent).  


## Install
DriverPicker is written with [Python 3](https://www.python.org/downloads/) and utilize [treelib](http://xiaming.me/treelib/) library.  
Any OS with python and pip installed can run DriverPicker.


### Windows
Install [Python 3](https://www.python.org/downloads/windows/) for Windows, add them to PATH.  
Then, type these in Console :
```sh
> pip install treelib
> git clone https://github.com/ied206/DriverPicker.git
```
### Linux
Install Python with your distribution's package manager.  
For example, here is instructions for Ubuntu.
```sh
$ sudo apt update
$ sudo apt install python3 python3-pip 
$ sudo pip install treelib
$ git clone https://github.com/ied206/DriverPicker.git
```
### macOS
Similar to Linux.  
You may use brew to install python.

## Usage
```sh
> python DriverPicker.py TARGET --arch ARCH --winver WINVER [--pure]
> python DriverPicker.py TARGET -a ARCH -w WINVER [-pure]
```
For detail, see in-program help message.
```sh
> python DriverPicker.py --help
```

## License
This program is licensed under MIT license.

