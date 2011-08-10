#!/usr/bin/python2

import os, re, ConfigParser, argparse, sys
from utils import torrentdecode, colors
import exporter, siteconnection, clientconnection, migrator

# TODO: Torrent id or URL passing for manual
# TODO: Try and use multiple methods for automated filename mapping
# TODO: Hash recognition is slow and doesn't really work
# TODO: Prepare for distribution
# TODO: Add more error handling
# TODO: Fix bug with UTF-8 & urllib
# TODO: Set up tests
# TODO: Transmission compatibility

class Main:

    def __init__(self): 
        # some constants
        self.audioformats = (".flac",".mp3",".ogg",".aac",".ac3",".dts")
        self.urlregex = re.compile(r"http://what\.cd/torrents\.php\?.*id=(\d+)")

        # parse arguments
        parser = argparse.ArgumentParser(description='A What.CD tool to ease torrent migration.')
        group = parser.add_argument_group('manual migration')
        group.add_argument('datadir',help='directory of old torrent data',nargs='?')
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

        # initialize site connection if needed
        if (not self.args.datadir or not self.args.torrent) and self.cfg.get("rtorrent","xmlrpc_proxy"):
            if self.cfg.get("what.cd","username") and self.cfg.get("what.cd","password"):
                self.siteconnection = siteconnection.Connection(self.cfg.get("what.cd","username"),self.cfg.get("what.cd","password"))
        
        # initialize migrator
        self.migrator = migrator.Migrator()

        self.start()

    # start script flow
    def start(self):

        # manual migration
        if self.args.datadir and self.args.torrent:
            self.manualMigration()

        # guided rtorrent migration
        elif self.cfg.get("rtorrent","xmlrpc_proxy"):
            # setup torrent connection
            self.torrentclient = clientconnection.Rtorrent(self.cfg.get("rtorrent","xmlrpc_proxy"))
            if not self.torrentclient:
                print "Torrent connection failed."
            # setup site connection
            if self.cfg.get("what.cd","username") and self.cfg.get("what.cd","password"):
                self.siteconnection = siteconnection.Connection(self.cfg.get("what.cd","username"),self.cfg.get("what.cd","password"))
            self.guidedMigration()

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
        try:
            f = open(self.args.torrent,'r')
        except IOError:
            sys.exit("The specified torrent file could not be opened.")
        torrentdata = f.read()
        torrentinfo = torrentdecode.decode(torrentdata)

        # execute migration
        self.migrator.execute(torrentinfo,torrentfolder)

    # guided migration using torrent client to read 
    def guidedMigration(self):
        self.guided = True
        # get a list of unregistered torrents
        print "Scanning for unregistered torrents..."
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

# Init
if __name__ == "__main__":
    main = Main() 
