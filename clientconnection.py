import xmlrpclib, socket, sys, re

class Rtorrent:
    def __init__(self,proxy_uri):
        self.errorMessage = 'Tracker: \[Failure reason \"Unregistered torrent'
        self.server = xmlrpclib.ServerProxy(proxy_uri)

    def unregistered_torrents_iter(self):
        torrents = self.server.download_list("")
        for torrent in torrents:
            message = self.server.d.get_message(torrent)
            if re.match(self.errorMessage,message):
                yield (torrent,self.server.d.get_tied_to_file(torrent),self.server.d.get_base_path(torrent))

    # returns list of torrents with the name of the original torrent file, and the path of the data
    def get_unregistered_torrents(self):
        try:
            torrents = self.server.download_list("")
        except xmlrpclib.ProtocolError, err:
            sys.exit("XML-RPC connection to rTorrent failed. (Protocol error: [%d] %s)" % (err.errcode,err.errmsg))
        except socket.error, (val,message):
            sys.exit("XML-RPC connection to rTorrent failed. (Socket error: [%d] %s)" % (val,message))
        errors = []
        for torrent in torrents:
           message = self.server.d.get_message(torrent)
           if re.match(self.errorMessage,message): errors.append(torrent)
        data = []
        for error in errors:
            data.append((torrent,self.server.d.get_tied_to_file(error),self.server.d.get_base_path(error)))
        return data

    def remove_torrent(self,torrentid):
        self.server.d.erase(torrentid)
