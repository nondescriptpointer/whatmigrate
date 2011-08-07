#!/usr/bin/python2

import os, xmlrpclib, math, StringIO, binascii, hashlib, tempfile, shutil, mmap, re, ConfigParser, argparse, urllib
import torrentdecode, colors, whatconnection, clientconnection, exporter, hashcheck, migrator

# TODO: Try and use multiple methods for automated filename mapping
# TODO: Transmission compatibility
# TODO: Trying repadding without hash recognition (if flac, metaflac --add-padding), on a per track basis 
# TODO: Prepare for distribution
# TODO: Add more error handling
# TODO: Fix bug with UTF-8 & urllib

class Main:
    def __init__(self): 
        # some constants
        self.audioformats = (".flac",".mp3",".ogg",".aac",".ac3",".dts")
        self.urlregex = re.compile(r"http://what\.cd/torrents\.php\?.*id=(\d+)")

        # parse arguments
        parser = argparse.ArgumentParser(description='A What.CD tool to ease torrent migration.')
        group = parser.add_argument_group('manual migration')
        group.add_argument('datadir',help='directory of (old) torrent data',nargs='?')
        group.add_argument('torrent',help='new .torrent file, torrent id or torrent url',nargs='?')
        parser.add_argument('--version',action='version',version='whatmigrate 0.1')
        self.args = parser.parse_args()

        # parse configuration file (or create if it doesn't exist)
        self.cfg = ConfigParser.ConfigParser()
        if not self.cfg.read(os.path.expanduser("~/.whatmigrate")):
            print "Creating configuration file. Edit ~/.whatmigrate for torrent client interaction and site log searching."
            self.cfg.add_section("rtorrent")
            self.cfg.set("rtorrent","xmlrpc_proxy","")
            self.cfg.add_section("what.cd")
            self.cfg.set("what.cd","username","")
            self.cfg.set("what.cd","password","")
            self.cfg.write(open(os.path.expanduser("~/.whatmigrate"),"wb"))

        # initialize site connection
        if self.cfg.get("what.cd","username") and self.cfg.get("what.cd","password"):
            self.siteconnection = whatconnection.Connection(self.cfg.get("what.cd","username"),self.cfg.get("what.cd","password"))
        
        # initialize migrator
        self.migrator = migrator.Migrator()

        # manual migration
        if self.args.datadir and self.args.torrent:
            self.manualMigration()
        # guided rtorrent migration
        elif self.cfg.get("rtorrent","xmlrpc_proxy"):
            self.torrentclient = clientconnection.Rtorrent(self.cfg.get("rtorrent","xmlrpc_proxy")) 
            self.clientGuidedMigration()
        # no torrent client configured and no datadir and torrentfile specified
        else: 
            print "No torrent client configured. Edit ~/.whatmigrate or specify a data directory and torrent file (see -h for more info.)"

    # manual migration
    def manualMigration(self):
        # check if directory is valid
        if os.path.isdir(self.args.datadir):
            torrentfolder = self.args.datadir
            # remove trailing slash
            if torrentfolder[-1] == '/': torrentfolder = torrentfolder[0:-1]
        else:
            print "The specified datadir is invalid."
            return

        # check if torrent file exists & read file
        f = open(self.args.torrent,'r')
        if f:
            torrentdata = f.read()
            torrentinfo = torrentdecode.decode(torrentdata)
        else:
            print "The specified torrent file could not be read."
            return

        # execute migration
        self.migrator.execute(torrentinfo,torrentfolder)

    # guided migration using torrent client to read 
    def clientGuidedMigration(self):
        self.guided = True
        # get a list of unregistered torrents
        torrents = self.torrentclient.get_unregistered_torrents()
        if not len(torrents):
            print "No unregistered torrents found"
            exit()
        print colors.red("%d unregistered torrents found" % (len(torrents),))
        # run through torrents
        for torrentfile, torrentfolder in torrents:
            # try and get replacement
            torrentid = self.queryReplacement(torrentfile)
            # grab torrent file and start migration
            if torrentid:
                print " Trying migration to %s" % (torrentid,)
                print " Retrieving torrent file..."
                torrentdata = self.siteconnection.getTorrentFile(torrentid)
                torrentinfo = torrentdecode.decode(torrentdata)
                self.migrator.execute(torrentinfo,torrentfolder)
            print ""

    # search site log or ask user to specify torrent to migrate to
    def queryReplacement(self,torrentfile):
        # search log if siteconnection is available
        if self.siteconnection:
            basename = os.path.splitext(os.path.basename(torrentfile))[0]
            parts = basename.split(" - ")
            searchstring = parts[0] + " - " + parts[1]
            print colors.bold(basename)
            print " Searching site log for '%s'..." % searchstring
            #results = []
            results = self.siteconnection.searchLog(searchstring)
            if not results: print " No entries found"
            else:
                print " %d entr%s found: " % (len(results), ("y" if len(results) == 1 else "ies"))
                counter = 1
                for result in results:
                    output = " %d. %s - %s" % (counter,result[0],result[1])
                    if(len(result) > 2): output += " - %s" % (result[2],)
                    print output
                    counter += 1
                userinput = raw_input(" Try migration to one of the results? (resultnumber/n) ")
                if userinput and userinput.isdigit() and int(userinput) in range(1,len(results+1)):
                    return int(results[int(userinput)-1][2])
        # or manually specify torrent id / download url
        userinput = raw_input(" Try migration to specified torrent? (torrentid/torrend DL url/n) ")
        if userinput and userinput.isdigit():
            return int(userinput)
        else:
            result = self.urlregex.match(userinput)
            if result: return int(result.group(1))
            else: return 0

    def executeMigration(self,torrentid,torrentfolder):
        pass 


# try migration to specified torrent
def tryMigration(torrentid,oldfolder):
    # Check filesizes
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
        result = hashCheck(torrentinfo,oldfolder,mappings)
        hashChecked = True
        if float(result[0])/result[1] < 0.5:
            proposeFix = True 

    # Propose hash recognition if filesizes do not match or hash check < 0.5
    if proposeFix:
        userinput = raw_input("   Do you want to perform torrent hash recognition to auto-correct the files? (y/n) ")
        if userinput and userinput.lower() in ("y",'yes'):
            hashChecked = False
            hashRecognition(torrentinfo,oldfolder,mappings)

    # Do final hash check
    if hashChecked == False:
        hashCheck(torrentinfo,oldfolder,mappings)

    # Offer migration
    userinput = raw_input("   Do you want to remove the old torrent from the client? (y/n) [y] ")
    userinput = raw_input("   Do you want to remove the original data? (y/n) [y] ")
    userinput = raw_input("   Do you want to add the new torrent to your client? (y/n) [y] ")
    userinput = raw_input("   Last chance to abort, execute migration? (y/n) [n] ")
    print "   Migrating!"


# TODO: This is too slow
def hashRecognition(torrentinfo,datafolder,mappings):
    print "   Executing hash recognition... (may take a while)"
    piece_length = torrentinfo['info']['piece length']
    pieces = StringIO.StringIO(torrentinfo['info']['pieces'])
    offset = 0
    buffered_offset = 0 # used to start from previous offset, saves a lot of time
    numFound = 0
    numFiles = 0
    # get each file that is mapped and is an audio format
    for check in torrentinfo['info']['files']:
        if os.path.splitext(os.path.join(*check['path']))[-1] in AUDIOFORMATS:
            for i in range(len(mappings)):
                if(mappings[i][1] == os.path.join(*check['path'])):
                    # determine pieces and starting offsets
                    first_piece = math.floor(offset/piece_length)
                    middle_piece = round((offset+check['length']/2)/piece_length)
                    starting_offset = int((middle_piece - first_piece) * piece_length - (offset - (first_piece * piece_length)))
                    pieces.seek(int(middle_piece*20))
                    piece = pieces.read(20)
                    # search for piece in the file
                    found, fileoffset = searchPieceInFile(os.path.join(datafolder,mappings[i][0]),piece,starting_offset,piece_length)
                    if found:
                        numFound += 1
                        mappings[i] = (mappings[i][0],mappings[i][1],-fileoffset)
                    numFiles += 1
                    
                    break
        offset += check['length']
    print "   Hash recognition succeeded for %d of %d audio-files" % (numFound, numFiles)

def searchPieceInFile(path,piece,starting_offset,piece_length):
    # get data from file
    f = open(path,'rb')
    filedata = StringIO.StringIO(f.read())
    f.close()
    # init
    byteoffset = 0
    found = False
    # main loop
    while True:
        # look left and light from starting offset
        limit = 2
        # left 
        if starting_offset+byteoffset <= os.path.getsize(path):
            limit -= 1
            filedata.seek(starting_offset+byteoffset)
            if hashlib.sha1(filedata.read(piece_length)).digest() == piece:
                filedata.close()
                return True, byteoffset
        # right
        if starting_offset-byteoffset >= 0:
            limit -= 1
            filedata.seek(starting_offset-byteoffset)
            if hashlib.sha1(filedata.read(piece_length)).digest() == piece:
                filedata.close()
                return True, -byteoffset
        # stop processing if file boundaries have been reached
        if limit == 2: break
        # increase the byte offset
        byteoffset += 1
    # close iostring
    filedata.close()
    # nothing found
    return False, byteoffset

def hashCheck(torrentinfo,datafolder,mappings):
    print "   Hash checking migration..."
    # make temporary folder
    tempdir = tempfile.mkdtemp("whatmigrate_hashcheck")
    # export
    exporter.export(torrentinfo,datafolder,mappings,tempdir)
    # hash check
    results = hashcheck.hashcheck(torrentinfo,tempdir)
    print ("   %d of %d pieces correct " % (results[0],results[1]))+colors.bold("(%d%%)" % (round(float(results[0])/results[1]*100),))
    # remove temporary folder
    shutil.rmtree(tempdir)
    return results


if __name__ == "__main__":
    main = Main() 
