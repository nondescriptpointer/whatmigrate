#!/usr/bin/python2

import os, re, ConfigParser, argparse, sys
from utils import torrentdecode
import exporter, siteconnection, clientconnection, migrator
try: import readline # not supported on all platforms
except ImportError: pass

class Main:
    def __init__(self): 
        # parse arguments
        parser = argparse.ArgumentParser(description='A What.CD tool to help you with migrating your old data to the new torrent.')
        group = parser.add_argument_group('manual migration')
        group.add_argument('datadir',help='directory of old torrent data',nargs='?')
        group.add_argument('torrent',help='new .torrent file, torrent id or torrent url (optional)',nargs='?')
        parser.add_argument('--version',action='version',version='whatmigrate 0.1')
        self.args = parser.parse_args()

        # parse configuration file (or create if it doesn't exist)
        self.cfg = ConfigParser.ConfigParser()
        if not self.cfg.read(os.path.expanduser("~/.whatmigrate")):
            print "Creating configuration file. Edit ~/.whatmigrate to configure."
            self.cgs.add_section("general")
            self.cfg.set("outputdir","")
            self.cfg.add_section("rtorrent")
            self.cfg.set("rtorrent","xmlrpc_proxy","")
            self.cfg.add_section("what.cd")
            self.cfg.set("what.cd","username","")
            self.cfg.set("what.cd","password","")
            self.cfg.set("what.cd","use_ssl","1")
            self.cfg.write(open(os.path.expanduser("~/.whatmigrate"),"wb"))
        # need an output dir to run script
        if not self.cfg.get("general","outputdir"):
            sys.exit("Please configure the output directory in ~/.whatmigrate.")

        # initialize site connection if needed
        self.siteconnection = None
        if self.cfg.get("what.cd","username") and self.cfg.get("what.cd","password"):
            self.siteconnection = siteconnection.Connection(self.cfg.get("what.cd","username"),self.cfg.get("what.cd","password"),self.cfg.get("what.cd","use_ssl"))
        
        # initialize migrator
        self.migrator = migrator.Migrator(self.cfg.get("general","outputdir"))
        
        # go!
        self.start()

    def start(self):
        # manual migration
        if self.args.datadir:
            self.manualMigration()
        # guided rtorrent migration
        elif self.cfg.get("rtorrent","xmlrpc_proxy"):
            self.guidedMigration()
        # no torrent client configured and no datadir specified
        else: 
            sys.exit("No torrent client configured. Edit ~/.whatmigrate or specify a data directory (see -h)")

    # manual migration
    def manualMigration(self):
        # check if directory is valid
        if not os.path.isdir(self.args.datadir):
            sys.exit("The specified datadir is invalid.")
        # read specified torrent file or query replacement
        if self.args.torrent:
            torrentinfo = self.grabFromInput(self.args.torrent)
        else:
            torrentinfo = self.queryReplacement(os.path.dirname(self.args.datadir))
        if torrentinfo:
            self.migrator.execute(torrentinfo,self.args.datadir)

    # guided migration using torrent client to read 
    def guidedMigration(self):
        # setup client connection
        torrentclient = clientconnection.Rtorrent(self.cfg.get("rtorrent","xmlrpc_proxy"))
        # get a list of unregistered torrents
        print "Scanning for unregistered torrents... (can take a few minutes)"
        torrents = torrentclient.get_unregistered_torrents()
        if not len(torrents):
            print "No unregistered torrents found"
            exit()
        print "%d unregistered torrents found\n" % (len(torrents),)
        # run through torrents
        for torrentfile, torrentfolder in torrents:
            # look for replacement
            basename = os.path.splitext(os.path.basename(torrentfile))[0]
            print basename
            parts = basename.split(" - ")
            searchstring = parts[0] + " - " + parts[1]
            torrentinfo = self.queryReplacement(searchstring)
            if torrentinfo:
                self.migrator.execute(torrentinfo,torrentfolder)
            print ""

    # read torrent file
    def readTorrentFile(self,path):
        if not os.path.isfile(path):
            sys.exit("Cannot read %s" % (path,))
        try:
            f = open(path,'r')
            data = f.read()
        except IOError:
            sys.exit("File %s could not be opened." % (path,))
        return data;

    # parse user input of torrent id, link or path
    def grabFromInput(self,userinput):
        # torrent id
        torrentdata = None
        if userinput.isdigit():
            if not self.siteconnection:
                sys.exit("You need to put your username and password in .whatmigrate to download a torrent.")
            torrentdata = self.siteconnection.getTorrentFile(int(userinput))
        # torrent permalink
        elif userinput.find('http://') != -1 or userinput.find('https://') != -1:
            if not self.siteconnection:
                sys.exit("You need to put your username and password in .whatmigrate to download a torrent.")
            regex = re.compile(r"torrents\.php\?.*id=(\d+)")
            result = regex.search(userinput)
            if result:
                torrentdata = self.siteconnection.getTorrentFile(int(result.group(1)))
            else:
                sys.exit("URL not recognized.")
        # path
        elif userinput:
            torrentdata = self.readTorrentFile(userinput)
        # if there's data, parse and return 
        if torrentdata:
            return torrentdecode.decode(torrentdata)
        else:
            return False

    # query user for a replacement torrent
    def queryReplacement(self,searchFor):
        # Ask for input
        print " Specify a torrent file (id, permalink or local file), leave blank to do a site search or type 's' to skip this torrent"
        if readline:
            readline.set_completer_delims(' \t\n;')
            readline.parse_and_bind("tab: complete") # enable auto-completion
        userinput = raw_input(" ")
        if readline:
            readline.parse_and_bind("tab:"); # disable auto-completion again
        if userinput.strip() == 's':
            return False
        if userinput:
            return self.grabFromInput(userinput)

        # search site for this album 
        if not self.siteconnection:
            sys.exit("You need to put your username and password in .whatmigrate to do a site search.")
        if readline: readline.set_startup_hook(lambda: readline.insert_text(searchFor))
        userinput = raw_input(" Search What.CD for: ")
        if readline: readline.set_startup_hook()
        results = self.siteconnection.searchTorrents(userinput)
        count = 1
        flattened = []
        if results:
            # display the torrents
            for group,groupval in results.iteritems():
                print "  "+group
                for edition,editionval in groupval.iteritems():
                    print "    "+edition
                    for torrent in editionval:
                        print "      %u. %s (%s)" % (count,torrent['format'],torrent['size'])
                        flattened.append(torrent)
                        count += 1
            # ask for user entry
            userinput = raw_input(" Try migration to one of these results? (resultnumber/n) ")
            if userinput and userinput.isdigit() and int(userinput) in range(1,len(flattened)+1):
                # download the torrent file
                torrentdata = self.siteconnection.getTorrentFile(flattened[int(userinput)-1]['id'])
                return torrentdecode.decode(torrentdata)
            else:
                return self.queryReplacement(searchFor)
        else:
            print "  No torrents found."
            # try again
            return self.queryReplacement(searchFor)


# Init
if __name__ == "__main__":
    main = Main() 
