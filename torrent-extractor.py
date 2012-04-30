#!/usr/bin/python
from datetime import datetime
import os, subprocess

downloadFolder = '/volume1/homes/transmission/download'
videoFolder = '/volume1/Videos/unsorted'
registryFile = '/volume1/homes/leschekfm/torrent-registry.txt'
logFile = '/volume1/homes/leschekfm/extract-log.txt'

def log(text):
    text = str(datetime.now()) + ': ' + text + '\n'
    print text
    with open(logFile, 'a') as f:
        f.write(text)

def listDownloads(path):
    return os.listdir(path)
    
def alreadyProcessed(name):
    with open(registryFile, 'r') as registry:
        for line in registry:
            # line needs stripping because of '\'
            if line.strip() == name:
                return True
        return False

def markProcessed(name):
    with open(registryFile, 'a') as registry:
        registry.write(name + '\n')
        
def findExtension(path, ext):
    #this scans only the top folder
    #files = [file for file in os.listdir(path) if os.path.splitext(file)[1] == ext and not 'sample' in file]
    #but we want to scan also deeper
    outputList = []
    for root, dirs, files in os.walk(path):
        outputList.extend([(os.path.join(root, file), file) for file in files if os.path.splitext(file)[1] == ext and not 'sample' in file])
    return outputList
    #return files
    
for dl in listDownloads(downloadFolder):
    if alreadyProcessed(dl):
        continue
    
    path = os.path.join(downloadFolder, dl)
    '''
    We have three cases to handle:
    1. the video is in no folder
    2. the video is in a folder
    3. the video is in a folder and archived
    '''
    if os.path.isdir(path):
        if not os.path.exists(os.path.join(videoFolder, dl)):
            os.mkdir(os.path.join(videoFolder, dl))
        # try to find unarchived videos
        videos = findExtension(path, '.mkv')
        for videoPath, videoName in videos:
            '''print 'path: ' + path + '\n'
            print 'videopath: ' + videoPath + '\n'
            print 'videoname: ' + videoName + '\n'
            print 'videofolder: ' + videoFolder + '\n'
            print 'dl: ' + dl + '\n'
            print os.path.join(path, videoPath) +' -> '+ os.path.join(videoFolder, dl, videoName)'''
            os.link(os.path.join(path, videoPath), os.path.join(videoFolder, dl, videoName))
            log('[SUCCESS]: created hardlink for ' + dl)
            #search for matching nfo file
            nfos = findExtension(path, '.nfo')
            # although there should be only one file we iterate over the list returned by findExtension()
            for nfoPath, nfoName in nfos:
                os.link(nfoPath, os.path.join(videoFolder, dl, nfoName))
            markProcessed(dl)
        # search for .rar file and extract it
        archives = findExtension(path, '.rar')
        if len(archives) > 1:
            log('[WARNING]: ' + dl + ' has more than one rar file, please check manually')
            continue
        for archivePath, archiveName in archives:
            cmd = 'unrar x ' + os.path.join(path, archivePath) + ' ' + os.path.join(videoFolder, dl)
            print cmd
            log('[EXTRACTING]: Start extracting ' + dl)
            subprocess.call(cmd, shell=True)
            log('[EXTRACTING]: Finished extracting ' + dl)
            markProcessed(dl)
    elif os.path.isfile(path):
        # check if file is video
        name, ext = os.path.splitext(dl)
        if ext == '.mkv':
            # make hard link
            os.mkdir(os.path.join(videoFolder, name))
            #print 'made dir', name
            os.link(path, os.path.join(videoFolder, name, dl))
            log('[SUCCESS]: created hardlink for ' + dl)
            markProcessed(dl)
        elif ext == '.zip':
            os.mkdir(os.path.join(videoFolder, name))
            # extract archive
            cmd = 'unzip ' + path + ' -d ' + os.path.join(videoFolder, name)
            print cmd
            log('[EXTRACTING]: Start extracting ' + dl)
            subprocess.call(cmd, shell=True)
            log('[EXTRACTING]: Finished extracting ' + dl)
            markProcessed(dl)
        else:
            log('[WARNING]: ' + path + ' is not a video')
    else:
        log('[WARNING]: Unexpected behaviour on ' + path)
