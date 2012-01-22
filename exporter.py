import os

# exports files to destination folder using mappings
def export(torrentinfo,datafolder,mappings,destination):
    # create file with correct length for each file
    for newfile in torrentinfo['info']['files']:
        # create directory if needed
        if len(newfile['path']) > 1:
            if not os.path.exists(os.path.join(destination,*newfile['path'][0:1])):
                os.makedirs(os.path.join(destination,*newfile['path'][0:-1]))
        # create file
        f = open(os.path.join(destination,*newfile['path']),'w+b')
        f.truncate(newfile['length'])
        # if mapping exists, write original data to the file
        for mapping in mappings:
            if mapping[1] == unicode(os.path.join(*newfile['path']),'utf-8'):
                original = open(os.path.join(datafolder,mapping[0]),'rb')
                write_length = newfile['length']
                if mapping[2] < 0: original.seek(-mapping[2])
                if mapping[2] > 0: 
                    f.seek(mapping[2])
                    write_length -= mapping[2]
                else:
                    f.seek(0)
                f.write(original.read(write_length))
                break
        # close the file
        f.close()
