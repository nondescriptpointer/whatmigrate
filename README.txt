whatmigrate is a tool to help you with migrating your old data to a new 
torrent after a trump. It helps you with finding the new torrent, it will 
suggest file renaming and will try and repad the files if the filesizes 
don't match. This way it is very likely that your data will pass (most of)
the hash check. The primary target is FLAC trumps.

There are various ways to run this script. You can run without arguments to 
connect to the XML-RPC socket of your rtorrent client and make it go over every
unregistered torrent in your client. You can also specify a directory you want
to migrate and optionally a torrent id, url or file to migrate to. See -h to
figure out the usage.

Please note that this script is still experimental, your results may vary. 

Thanks to zen0 who gave me the idea to repad the files.

Dependencies:
- Python 2.6/2.7
- BeautifulSoup
- argparse
- pycurl
Debian/Ubuntu: sudo apt-get install python python-pycurl python-argparse python-beautifulsoup

Installation/usage:
- Install dependencies
- Extract and/or place the files wherever you like
- Run whatmigrate.py
- Edit the configuration-file created in ~/.whatmigrate, only outputdir is required

Configuration options:
[general]
outputdir    - the directory the data of the migration is exported to, for example: 
               your torrent clients destination directory
torrentdir   - the directory you want the torrent files to be saved in, for example: 
               the watched rtorrent folder
[rtorrent]
xmlrpc_proxy - the xml-rpc proxy of your rtorrent client
progressive  - scan for torrents progressively instead of finding them all beforehand, speeds up search
[what.cd]
username &   - your login credential
password
use_ssl      - use ssl for the requests to the website

Todo:
- Fallback to filesizes if no numbers are used in filenames
- Implement piece searching (currently disabled because it's too slow)
- Better error handling
- Add support for other torrent clients (eg Transmission)
