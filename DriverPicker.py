#!/usr/bin/env python3
#-*- coding: utf-8 -*-

"""
- Inf Pattern 1
[(vendor).NT(arch).(version)]
[Intel.NTamd64.5.2]

- Inf Pattern 2 - Very annoying, especially XP's drivers
[(vendor).NT(arch)]
[Intel.NTx86]

- DriverPacksSolution-specific folder name pattern
    5x86, 5x64, 6x86, 6x64, 7x86, 7x64, 8x86, 8x64, 81x86, 81x64, 10x86, 10x64
    All8x86, All8x64, Allx86, Allx64, NTx64, NTx86, AllMx64, AllMx86
Annoying ones - hard to automate, no consistency (881x86 == All8x86)
    881x86, 881x64, 88110x64, 88110x86
"""

import os
import stat
import sys
import time
import codecs
import re
import shutil
import math
import argparse
from treelib import Node, Tree # http://xiaming.me/treelib/examples.html#basic-usage

# declare CONSTANT
WRITTEN_YEAR = '2016'
WRITTEN_MONTH = '06'
WRITTEN_DAY = '19'
PROG_NAME = 'DriverPicker'
PROG_WEB = 'https://joveler.kr/project'
PROG_GIT = 'https://github.com/ied206/DriverPicker'
PROG_MAJOR_VER = 1
PROG_MINOR_VER = 0
ARCH_X86 = 'x86'
ARCH_AMD64 = 'amd64'
WIN_ARCH = [
    ARCH_X86, ARCH_AMD64
]
DPS_WINVER_DICT = {
    '6': {'majorVer': 6, 'minorVer': 0},
    '7': {'majorVer': 6, 'minorVer': 1},
    '8': {'majorVer': 6, 'minorVer': 2},
    '81': {'majorVer': 6, 'minorVer': 3},
    '10': {'majorVer': 10, 'minorVer': 0}
}
DPS_WINVER_ANNOYING_DICT = {
    # 5 == 2000, XP, 2003
    '5': [{'majorVer': 5, 'minorVer': 0},
            {'majorVer': 5, 'minorVer': 1},
            {'majorVer': 5, 'minorVer': 2}],
    # 881 == 8, 8.1
    '881': [{'majorVer': 6, 'minorVer': 2},
            {'majorVer': 6, 'minorVer': 3}],
    # 881 == 8, 8.1, 10
    '88110': [{'majorVer': 6, 'minorVer': 2},
            {'majorVer': 6, 'minorVer': 3},
            {'majorVer': 10, 'minorVer': 0}],
}
DPS_ARCH_DICT = {
    '86': ARCH_X86,
    '64': ARCH_AMD64
}

# global variable
TARGET = { # test values
    'dir': 'Driver',
    'arch': ARCH_AMD64,
    'winver': {'majorVer':10, 'minorVer':0},
    'pure': False
}


class InfoStruct:
    name = ''
    dir = ''
    fullPath = ''
    idx = 0
    arch = {ARCH_X86:[], ARCH_AMD64:[]}
    match = False

    def __init__(self, idx, dir, name):
        self.name = name
        self.dir = dir
        self.fullPath = os.path.join(dir, name)
        self.idx = idx
        self.arch = {ARCH_X86:[], ARCH_AMD64:[]}
        self.match = False

    def check_valid_arch(self, arch):
        if arch in WIN_ARCH:
            return True
        else:
            return False

    def add_host_info(self, arch, majorVer, minorVer):
        if self.check_valid_arch(arch):
            self.arch[arch].append({'majorVer': majorVer, 'minorVer':minorVer})

    def debug_print(self):
        print("Path : {0}".format(self.fullPath))
        for arch in self.arch:
            print("[Arch {0}]".format(arch))
            for key in self.arch[arch]:
                print("Version : {0}.{1}".format(key['majorVer'], key['minorVer']))


# parse arguments
def parse_argument():
    parser = argparse.ArgumentParser(
        prog=PROG_NAME+'.py',
        usage='python %(prog)s TARGET -arch ARCH -winver VER [-pure]\n       python %(prog)s [-h]',
        formatter_class=argparse.RawTextHelpFormatter,
        description='''
    Collect specific Windows' drivers from DriverPacks Solution.
    It scans folder and find drivers of target version of Windows.
    Folders which does not contain target drivers will be deleted.
    Ex) Collect Windows 10 x64 drivers from \'DP_WLAN-WiFi_16052\'

    [WARNING] All files and subfolders in Target will be affected, may deleted.
              You MUST prepare BACKUP of target folder!
              I do not provide any warranty, use as your own risk.''',
        epilog='''Ex) > python %(prog)s \"Drivers_LAN\" --arch amd64 --winver 10.0
      python %(prog)s \"Drivers_LAN\" -a x86 -w 6.3''')
    parser.add_argument('TARGET',
                        help='''Target folder contains DriverPack Solution drivers
  TARGET must be folder's name''')
    parser.add_argument('-a', '--arch', metavar='ARCH',
                        required=True,
                        help='''Target Windows Architecture
  ARCH must be one of these :
    x86, amd64''')
    parser.add_argument('-w', '--winver', type=float, metavar='VER',
                        required=True,
                        help='''Target Windows Version in numbers.
  WINVER must be format of [major].[minor]
  Ex) Win 10  : 10.0
      Win 8.1 : 6.3
      Win 8   : 6.2
      Win 7   : 6.1''')
    parser.add_argument('-p', '--pure', action="store_true",
                        help='''Disable DPS-specific version detection.
  Ex) Do not reference folder name
      such as 5x86, 7x64, NTx86''')

    if len(sys.argv) < 2:
        parser.print_usage()
        print('       Try using --help argument')
        parser.exit(1)
    args = parser.parse_args()
    if not vars(args):
        parser.print_help()
    else:
        return args


# check if argument is valid
def check_argument(args):
    # args.target, args.arch, args.winver, args.pure
    global TARGET
    # check args.target
    if os.path.isdir(args.TARGET):
        TARGET['dir'] = args.TARGET
    else:
        print("[ERR] TARGET must be folder\n")
        exit(1)
    # check args.arch
    match = False
    for arch in WIN_ARCH:
        if args.arch == arch:
            match = True
            TARGET['arch'] = args.arch
    if not match:
        print("[ERR] ARCH must be one of these:\n       x86, amd64\n")
        exit(1)
    # check args.winver
    TARGET['winver'] = {'majorVer': int(args.winver),
                        'minorVer': int(math.floor(args.winver * 10) % 10)}
    # check args.pure
    TARGET['pure'] = args.pure


# program banner
def program_info():
    print('{0} v{1}.{2}, by ied206 (aka Joveler)'.format(PROG_NAME, PROG_MAJOR_VER, PROG_MINOR_VER))
    print('  Date     : {0}.{1}.{2}'.format(WRITTEN_YEAR, WRITTEN_MONTH, WRITTEN_DAY))
    print('  Homepage : {0}'.format(PROG_WEB))
    print('  Github   : {0}\n'.format(PROG_GIT))


def print_start_info():
    print('Target Folder          : {0}'.format(TARGET['dir']))
    print('Target Architecture    : {0}'.format(TARGET['arch']))
    print('Target Windows Version : {0}.{1}'.format(TARGET['winver']['majorVer'], TARGET['winver']['minorVer']))
    print('Use DriverPacks Solution specific version detecion : {0}\n'.format(not TARGET['pure']))
    print('WARNING! All files and subfolders in Target will be affected, may deleted.\n         You MUST prepare BACKUP of target folder!')
    input('Are you sure to continue? If yes, press Enter...')
    print('')


def print_finish_info(proc_info):
    tm_elapse = int(time.time() - proc_info['tm_start'])
    print('\n[Summary]')
    print('Took {0}min {1}sec'.format(tm_elapse // 60, tm_elapse % 60))
    print('Matched infs    : {0}'.format(proc_info['matchedInfs']))
    print('Deleted infs    : {0}'.format(proc_info['deletedInfs']))
    print('Matched folders : {0}'.format(proc_info['matchedDirs']))
    print('Deleted folders : {0}'.format(proc_info['deletedDirs']))
    print("Max deleted folder depth : {0}".format(proc_info['maxDirDepth']))


def create_inf_list():
    print('[1/4] Scanning INF files... ')
    inf_list = []
    idx = 0
    for (root, dirs, files) in os.walk(TARGET['dir']):
        for filename in files:
            if filename.endswith(".inf"):
                info = InfoStruct(idx, root, filename)
                inf_list.append(info)
                idx += 1
    return inf_list
                
                
def parse_infs(inf_list):
    print('[2/4] Parsing INF files...')
    # [(vendor).NT(arch).(version)]
    for info in inf_list:
        # I hate multiple non-unicode encoding mixed in one inf file!
        # Ex) EUC-KR (KR), Shift-JIS (JP), Big5 (TW) at one inf file
        # so errors='ignore' must be used
        file_enc = check_file_unicode_encoding(info.fullPath)
        fp = codecs.open(info.fullPath, 'r', encoding=file_enc, errors='ignore')
        inf = fp.read()
        fp.close()
        inf = inf.split('\r\n')
        for idx, value in enumerate(inf):
            value = value.strip() # remove whitespaeces
            section_pattern = len(re.findall('(?=\.)', value))
            # element[0] == tuple, [0][0] : vendor, [0][1] : arch, [0][2] : winver
            if section_pattern == 4: # Ex) [Intel.NTamd64.6.2.1]
                regex_pattern = r'^\[(?P<vendor>.+)\.NT(?P<arch>.+)\.(?P<winver>\d+\.\d+\.\d+)\]$'
                if re.match(regex_pattern, value):
                    element = re.findall(regex_pattern, value)
                    version = re.findall(r'(?P<major>\d+)\.(?P<minor>\d+)\.\d+$', element[0][2])
                    info.add_host_info(element[0][1].lower(), int(version[0][0]), int(version[0][1]))
            elif section_pattern == 3: # Ex) [Intel.NTamd64.6.2]
                regex_pattern = r'^\[(?P<vendor>.+)\.NT(?P<arch>.+)\.(?P<winver>\d+\.\d+)\]$'
                if re.match(regex_pattern, value):
                    element = re.findall(regex_pattern, value)
                    version = re.findall(r'(?P<major>\d+)\.(?P<minor>\d+)$', element[0][2])
                    info.add_host_info(element[0][1].lower(), int(version[0][0]), int(version[0][1]))
            elif section_pattern == 1: # Ex) [Atheros.NTamd64]
                regex_pattern = r'^\[(?P<vendor>.+)\.NT(?P<arch>.+)\]$'
                if re.match(regex_pattern, value):
                    element = re.findall(regex_pattern, value)
                    info.add_host_info(element[0][1].lower(), TARGET['winver']['majorVer'], TARGET['winver']['minorVer'])


# Detect inf file's encoding.
#   Detect BOM? UTF-16-BE or UTF-16-LE or UTF-8
#   No? It must be multibyte, but override with UTF-8.
#       multibyte encoding share 0x00~0x7F with UTF-8...
def check_file_unicode_encoding(filename):
    bytes = min(32, os.path.getsize(filename))
    fp = open(filename, 'rb')
    raw = fp.read(bytes)
    if raw.startswith(codecs.BOM_UTF8):
        encoding = 'utf-8'
    elif raw.startswith(codecs.BOM_UTF16_LE):
        encoding = 'utf-16-le'
    elif raw.startswith(codecs.BOM_UTF16_BE):
        encoding = 'utf-16-be'
    else:
        encoding = 'utf-8'
    fp.close()
    return encoding


# filter inf with arch:ver
def filter_infs(inf_list, proc_info):
    print('[3/4] Filtering INF files...')
    for info in inf_list:
        for i in info.arch[TARGET['arch']]:
            if i == TARGET['winver']:
                info.match = True
    # delete inf if doesn't match
    for info in inf_list:
        if info.match:
            proc_info['matchedInfs'] += 1
        else:
            proc_info['deletedInfs'] += 1
            os.chmod(info.fullPath, stat.S_IWRITE) # remove read-only property
            os.remove(info.fullPath)


# delete directory if it does not have .inf
def delete_unneeded_dirs(inf_list, proc_info, first):
    proc_info['matchedDirs'] = 0
    proc_info['maxDirDepth'] += 1
    deleted = False
    tree = Tree()
    tree.create_node(TARGET['dir'], TARGET['dir'])
    idx = 0
    if first:
        print('[4/4] Truncating folders...')
    # generate directory tree
    for (root, dirs, files) in os.walk(TARGET['dir']):
        for dirname in dirs:
            data = False
            for filename in os.listdir(os.path.join(root, dirname)):
                # It has .inf file -> save it
                if filename.endswith(".inf"):
                    data = True
                    break
            tree.create_node(dirname, os.path.join(root, dirname), parent=root, data=data)
    # truncate folders
    for (root, dirs, files) in os.walk(TARGET['dir']):
        for dirname in dirs:
            delete_folder = True
            has_inf = []
            # If a directory's root has inf file -> save it
            if check_root_dir_has_inf(root, tree, has_inf):
                delete_folder = False
            for filename in os.listdir(os.path.join(root, dirname)):
                # It has .inf file -> save it
                if filename.endswith(".inf"):
                    delete_folder = False
                    break
                # It has subdirectory -> save it
                elif os.path.isdir(os.path.join(root, dirname, filename)):
                    delete_folder = False
                    break
            # use DPS-specific folder version detection
            if not TARGET['pure']:
                delete_folder = check_dps_dir_detection(dirname, delete_folder)
            # delete unneeded directories
            if delete_folder:
                os.chmod(os.path.join(root, dirname), stat.S_IWRITE)  # remove read-only property
                shutil.rmtree(os.path.join(root, dirname), onerror=del_rw)
                tree.remove_subtree(os.path.join(root, dirname))
                deleted = True
                proc_info['deletedDirs'] += 1
            # record how many folders are matched and deleted
            if not delete_folder:
                proc_info['matchedDirs'] += 1
    # To ensure all folder must have .inf or subdir which has .inf, do recursive call
    if deleted > 0:
        delete_unneeded_dirs(inf_list, proc_info, False)


# If a directory's root has inf file -> save it
def check_root_dir_has_inf(root, tree, has_inf, first=True):
    node = tree.get_node(root)
    if first:
        has_inf = []
    has_inf.append(node.data)
    # is this dir has inf file?
    if not node.is_root(): # stop at root
        # is my parent has inf file?
        check_root_dir_has_inf(tree.parent(root).identifier, tree, has_inf, False)
    if first:
        if True in has_inf:
            return True
        else:
            return False



"""
- DriverPacksSolution-specific folder name pattern
    5x86, 5x64, 6x86, 6x64, 7x86, 7x64, 8x86, 8x64, 81x86, 81x64, 10x86, 10x64
    All8x86, All8x64, Allx86, Allx64, NTx64, NTx86, AllMx64, AllMx86
Annoying ones - hard to automate, no consistency (881x86 == All8x86)
    881x86, 881x64, 88110x64, 88110x86
"""


# use DPS-specific directory version detection
#   Point : when to force delete directory even if it has inf?
#   return True if dirname needs to be deleted
#   because of inconsistency in dir name, this function is bloated
def check_dps_dir_detection(dirname, delete_folder):
    regex_all8 = r'All8x(?P<arch>\d\d)$'
    regex_allm = r'AllMx(?P<arch>\d\d)$'
    regex_all = r'Allx(?P<arch>\d\d)$'
    regex_nt = r'NTx(?P<arch>\d\d)$'
    regex_general = r'(?P<winver>\d+)x(?P<arch>\d\d)$'
    # Ex) All8x86, All8x64
    if re.match(regex_all8, dirname):
        # Target is Windows 8 or 8.1 -> check arch
        if (TARGET['winver']['majorVer'] == 6 and
        (TARGET['winver']['minorVer'] == 2 or TARGET['winver']['minorVer'] == 3)):
            element = re.findall(regex_all8, dirname)
            arch = element[0]
            if (arch in DPS_ARCH_DICT) and (DPS_ARCH_DICT[arch] != TARGET['arch']):
                return True
        # Target is not Windows 8 and 8.1 -> just delete dir
        else:
            return True
    # Ex) AllMx64, AllMx86
    elif re.match(regex_allm, dirname):
        # check arch
        arch = re.findall(regex_allm, dirname)[0]
        if (arch in DPS_ARCH_DICT) and (DPS_ARCH_DICT[arch] != TARGET['arch']):
            return True
    # Ex) Allx64, Allx86
    elif re.match(regex_all, dirname):
        # check arch
        arch = re.findall(regex_all, dirname)[0]
        if (arch in DPS_ARCH_DICT) and (DPS_ARCH_DICT[arch] != TARGET['arch']):
            return True
    # Ex) NTx64, NTx86
    elif re.match(regex_nt, dirname):
        # check arch
        arch = re.findall(regex_nt, dirname)[0]
        if (arch in DPS_ARCH_DICT) and (DPS_ARCH_DICT[arch] != TARGET['arch']):
            return True
    # Ex) 7x86, 81x64
    elif re.match(regex_general, dirname):
        element = re.findall(regex_general, dirname)
        winver = element[0][0]
        arch = element[0][1]
        # It is one of 5, 6, 7, 8, 81, 10, and it is not your target arch
        if (winver in DPS_WINVER_DICT) and (arch in DPS_ARCH_DICT):
            if not (DPS_WINVER_DICT[winver] == TARGET['winver'] and DPS_ARCH_DICT[arch] == TARGET['arch']):
                return True
        # It has annoying folder name (881, 88110), and it is not your target arch
        elif (winver in DPS_WINVER_ANNOYING_DICT) and (arch in DPS_ARCH_DICT):
            if not (TARGET['winver'] in DPS_WINVER_ANNOYING_DICT[winver] and (DPS_ARCH_DICT[arch] == TARGET['arch'])):
                return True
    return delete_folder


# In Windows, PermissionError in file/dir deletion occurs often by read-only property
def del_rw(func, path, exc_info):
    os.chmod(path, stat.S_IWRITE)
    os.remove(path)


# main
def main():
    program_info()
    args = parse_argument()
    check_argument(args)
    print_start_info()

    proc_info = {
        'matchedInfs': 0,
        'deletedInfs': 0,
        'matchedDirs': 0,
        'deletedDirs': 0,
        'maxDirDepth': -1,
        'tm_start': time.time(),
    }
    inf_list = create_inf_list()
    parse_infs(inf_list)
    filter_infs(inf_list, proc_info)
    delete_unneeded_dirs(inf_list, proc_info, True)
    print_finish_info(proc_info)

if __name__ == "__main__":
    main()