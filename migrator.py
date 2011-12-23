
import re, os, tempfile, shutil, StringIO, math, hashlib
from operator import itemgetter
from utils import humanize, hashcheck, colors
import exporter

class Migrator:
    def __init__(self, output):
        self.audioformats = (".flac",".mp3",".ogg",".aac",".ac3",".dts")
        self.outputdir = output
    
    def execute(self, torrentinfo, torrentfolder):
        # remove trailing slash 
        if torrentfolder[-1] == '/': torrentfolder = torrentfolder[:-1]

        self.torrentinfo = torrentinfo
        self.torrentfolder = torrentfolder
        self.mappings = [] # keeps filename mappings and offsets

        # Rename folder
        if torrentinfo['info']['name'] != os.path.basename(torrentfolder):
            print "  Rename folder %s => %s" % (os.path.basename(torrentfolder), torrentinfo['info']['name'])

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
                for newfile in torrentinfo['info']['files']:
                    if os.path.splitext(os.path.join(*newfile['path']))[-1] == extension and os.path.getsize(os.path.join(torrentfolder,oldfile)) == newfile['length']:
                        self.mappings.append((oldfile,os.path.join(*newfile['path']),0))
        if len(self.mappings) > 0:
            print "  Rename non-audio files:"
            for mapping in self.mappings:
                print "   %s => %s" % (mapping[0],mapping[1])

        # Audio files mapping
        print "  Rename audio files. New names:"
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
            print "   File %d: %s (%s)" % (counter, new[0], humanize.humanize(new[1]))
            counter += 1

        # Ask for each new file to verify the match
        print "  Please verify renames (press enter/correct number):"
        counter = 1
        for old in originalAudio:
            userinput = raw_input("   %s (%s) [File %d: %s (%s)] " % (old[0], humanize.humanize(old[1]), counter, newAudio[counter-1][0], humanize.humanize(newAudio[counter-1][1])))
            if userinput and userinput.isdigit() and int(userinput) in range(1,len(newAudio)+1):
                mapto = int(userinput) - 1
            else:
                mapto = counter - 1
            self.mappings.append((old[0],newAudio[mapto][0],0))
            counter += 1

        # Check filesize
        sumNew = 0
        for new in newAudio: sumNew += new[1]
        sumOld = 0
        for old in originalAudio: sumOld += old[1]
        if sumNew != sumOld:
            print "  Filesizes do not match (original: %d, new: %d)" % (sumOld,sumNew)
            # add padding to files
            print "  Changing padding on files"
            self.simpleRepad(originalAudio,newAudio)
        else:
            print "  Filesizes match"

        # Hash check
        print "  Hash checking migration..."
        results = self.hashCheck()

        # If bad result suggest hash recognition
        """
        if float(results[0])/results[1] < 0.20:
            # Ask for hash recognition
            userinput = raw_input("  Do you want to run experimental hash recognition to try and auto-correct the files? (y/n) [n] ")
            if userinput and userinput.lower() in ("y","yes"):
                self.hashRecognition()
                # Do final hash check
                print "   Hash checking migration..."
                results = self.hashCheck()
        """

        # Offer migration
        userinput = raw_input("  Execute? (y/n) ")
        if userinput and userinput.lower() in ("y","yes"):
            targetdir = os.path.join(self.outputdir,torrentinfo['info']['name'])
            if not os.path.isdir(targetdir):
                os.makedirs(targetdir)
            print "  Exporting to %s" % (targetdir,)
            exporter.export(self.torrentinfo,self.torrentfolder,self.mappings,targetdir)
            print "  Done"
            return True
        else:
            return False

    def hashRecognition(self):
        print "   Executing hash recognition... (may take a while)"
        piece_length = self.torrentinfo['info']['piece length']
        pieces = StringIO.StringIO(self.torrentinfo['info']['pieces'])
        offset = 0
        numFound = 0
        numFiles = 0
        # get each file that is mapped and is an audio format
        for check in self.torrentinfo['info']['files']:
            if os.path.splitext(os.path.join(*check['path']))[-1] in self.audioformats:
                for i in range(len(self.mappings)):
                    if(self.mappings[i][1] == os.path.join(*check['path'])):
                        # determine pieces and starting offsets
                        first_piece = math.floor(offset/piece_length)
                        middle_piece = round((offset+check['length']/2)/piece_length)
                        starting_offset = int((middle_piece - first_piece) * piece_length - (offset - (first_piece * piece_length)))
                        pieces.seek(int(middle_piece*20))
                        piece = pieces.read(20)
                        found, fileoffset = self.searchPieceInFile(os.path.join(self.torrentfolder,self.mappings[i][0]),piece,starting_offset,piece_length)
                        if found:
                            numFound += 1
                            mappings[i] = (mappings[i][0],mappings[i][1],-fileoffset)
                        numFiles += 1
                        break;
            offset += check['length']
        print "   Hash recognition succeeded for %d of %d files" % (numFound,numFiles)

    def simpleRepad(self,originalAudio,newAudio):
        for i in range(len(self.mappings)):
            # look for mapping in new and old
            for old in originalAudio:
                if old[0] == self.mappings[i][0]:
                    sizeOld = old[1] 
                    break
            for new in newAudio:
                if new[0] == self.mappings[i][1]:
                    sizeNew = new[1]
            # use difference as padding
            self.mappings[i] = (self.mappings[i][0],self.mappings[i][1],sizeNew - sizeOld)


    def hashCheck(self):
        # create temp folder
        tempdir = tempfile.mkdtemp("whatmigrate_hashcheck")
        # export
        exporter.export(self.torrentinfo,self.torrentfolder,self.mappings,tempdir)
        # hash check
        results = hashcheck.hashcheck(self.torrentinfo,tempdir)
        print "  %d of %d pieces correct " % (results[0],results[1])+"(%d%%)" % (round(float(results[0])/results[1]*100),)
        shutil.rmtree(tempdir)
        return results

    # unused/slow
    def searchPieceInFile(self,path,piece,starting_offset,piece_length):
        # get data from file
        f = open(path,'rb')
        filedata = StringIO.StringIO(f.read())
        f.close()
        # init
        byteoffset = 0
        found = False
        # main loop
        maxtries = 5000
        while True and byteoffset < maxtries:
            # look left and right from starting offset
            limit = 2
            # left
            if starting_offset+byteoffset <= os.path.getsize(path):
                limit -= 1
                filedata.seek(starting_offset+byteoffset)
                if hashlib.sha1(filedata.read(piece_length)).digest() == piece:
                    filedata.close()
                    return True, byteoffset
            #right
            if starting_offset-byteoffset >= 0:
                limit -= 1
                filedata.seek(starting_offset-byteoffset)
                if hashlib.sha1(filedata.read(piece_length)).digest() == piece:
                    filedata.close()
                    return True, -byteoffset
            if limit == 2: break
            byteoffset += 1
        # close iostring
        filedata.close()
        # nothing found
        return False, byteoffset
