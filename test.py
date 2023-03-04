import os, win32api, win32file, pathlib, re, time
from tqdm import tqdm
from imohash import hashfile

count = {"insert":0,"update":0,"ignore":0,"total":0,"size":0}

volname, volsernum, maxfilenamlen, sysflags, filesystemname = win32api.GetVolumeInformation('M:\\')

print("Initializing Indexation...")

pbar_count = tqdm(miniters=1)

# Count files in M:\ recursively
for path,subdir,files in os.walk('M:\\'):
    for file in files:
        count['total'] += 1
        pbar_count.update(1)

pbar_count.close()

pbar_index = tqdm(miniters=1, total=count['total'], desc="Indexing files", unit="files")

for path,subdir,files in os.walk('M:\\'):
    for file in files:
        if not re.search("#recycle",path):
            filename, extention = os.path.splitext(file)
            filesize = os.stat(pathlib.PurePath(path,file)).st_size
            data = {
                'task':	        	1,
                'filename':			file,
                'extension':		extention,
                'source_volume':	volname,
                'source_path':		path,
                'source_last_seen':	int(time.time()),
                'source_size':		filesize,
                'source_checksum':  hashfile(pathlib.PurePath(path,file),hexdigest=True),
            }
            count['insert'] += 1
        else:
            count['ignore'] += 1
        pbar_index.update(1)

pbar_index.close()

print(count)