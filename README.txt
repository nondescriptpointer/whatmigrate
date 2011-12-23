whatmigrate is a tool to help you with migrating your old data to a new 
torrent after a trump. It helps you with finding the torrent that trumped yours,
it will suggest file renaming and will try and repad the files if the filesizes 
don't match to try and make your data pass (most of) the hash check. It is 
mostly targetted at FLAC torrents which often get trumped by files that are 
µalmost binary compatible.

There are various ways to run this script. You can run without arguments to 
connect to the XML-RPC socket of your rtorrent client and make it go over every
unregistered torrent in your client. You can also specify a directory you want
to migrate and optionally a torrent id, url or file to migrate to. See -h to
figure out the usage.

Please note that this script is still experimental, your results may vary. Once
it becomes mature enough it will also allow you to replace the torrent and data
from the script itself. For now, it just exports the new data to a given
directory.

Dependencies:
- Python 2.6
- BeautifulSoup

Installation/usage:
- Extract and/or place the files wherever you like
- Run whatmigrate.py
- Edit the configuration-file created in ~/.whatmigrate, only the outputdir is required

Todo:
- Fallback to filesizes if no numbers are used in filenames
- Implement piece searching (currently disabled because it's too slow)
- Better error handling
- Add support for other torrent clients (eg Transmission)
- Offer to remove data and torrent and replace it with new data and torrent
