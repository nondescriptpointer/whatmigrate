
import re, os
from operator import itemgetter
import colors, humanize

class Migrator:
    def __init__(self):
        self.audioformats = (".flac",".mp3",".ogg",".aac",".ac3",".dts")
    
    def execute(self, torrentinfo, torrentfolder):
        print colors.green("  Suggesting migration:")

        self.mappings = [] # keeps filename mappings

        # Rename folder
        if torrentinfo['info']['name'] != os.path.basename(torrentfolder):
            print "   Rename folder %s => %s" % (os.path.basename(torrentfolder), torrentinfo['info']['name'])

        # Get a list of all old files
        oldfiles = []
        for item in os.walk(torrentfolder):
            if len(item[2]):
                for f in item[2]:
                    oldfiles.append(os.path.normpath(os.path.relpath(os.path.join(item[0],f),torrentfolder)))

        # Remove non-audio files unless file with same filesize and extension is present
        for oldfile in oldfiles:
            extension = os.path.splitext(oldfile)[-1]
            if extension not in self.audioformats:
                found = False
                for newfile in torrentinfo['info']['files']:
                    if os.path.splitext(os.path.join(*newfile['path']))[-1] == extension and os.path.getsize(os.path.join(torrentfolder,oldfile)) == newfile['length']:
                        self.mappings.append((oldfile,os.path.join(*newfile['path']),0))
                        found = True
        if len(self.mappings) > 0:
            print "   Rename non-audio files:"
            for mapping in self.mappings:
                print "    %s => %s" % (mapping[0],mapping[1])

        # Audio files mapping
        print "   Audio file renaming:"
        originalAudio = []
        for oldfile in oldfiles:
            if os.path.splitext(oldfile)[-1] in self.audioformats:
                originalAudio.append((oldfile,os.path.getsize(os.path.join(torrentfolder,oldfile))))
        originalAudio = sorted(originalAudio, key=itemgetter(0))
        newAudio = []
        for newfile in torrentinfo['info']['files']:
            if os.path.splitext(os.path.join(*newfile['path']))[-1] in self.audioformats:
                newAudio.append((os.path.join(*newfile['path']),newfile['length']))
        newAudio = sorted(newAudio, key=itemgetter(0))

        # Print original files with number
        counter = 1
        for new in newAudio:
            print "    File: %d: %s (%s)" % (counter, new[0], humanize.humanize(new[1]))
            counter += 1

        # Ask for each new file to verify the match
        print "   Please verify renames (press enter/correct number):"
        counter = 1
        for old in originalAudio:
            userinput = raw_input("    %s (%s) [File %d: %s (%s)] " % (old[0], humanize.humanize(old[1]), counter, newAudio[counter-1][0], humanize.humanize(newAudio[counter-1][1])))
            if userinput and userinput.isdigit() and int(userinput) in range(1,len(newAudio)+1):
                mapto = int(userinput) - 1
            else:
                mapto = counter - 1
            self.mappings.append((old[0],newAudio[mapto][0],0))
            counter += 1

        # Check filesize
        hashChecked = False
        proposeFix = False
        sumNew = 0
        for new in newAudio: sumNew += new[1]
        sumOld = 0
        for old in originalAudio: sumOld += old[1]
        if sumNew != sumOld:
            print "   Audio filesizes do not match (original: %d, new: %d)" % (sumOld,sumNew)
            proposeFix = True
        else:
            print "   Audio filesizes match"
