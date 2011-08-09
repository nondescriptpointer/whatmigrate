import xmlrpclib, socket, sys


class Rtorrent:
    def __init__(self,proxy_uri):
        self.server = xmlrpclib.ServerProxy(proxy_uri)

    # returns list of torrents with the name of the original torrent file, and the path of the data
    def get_unregistered_torrents(self):
        try:
            torrents = self.server.download_list("")
        except xmlrpclib.ProtocolError, err:
            sys.exit("XML-RPC connection to rTorrent failed. (ProtocolError: [%d] %s)" % (err.errcode,err.errmsg))
        except socket.error, (val,message):
            sys.exit("XML-RPC connection to rTorrent failed. ([%d] %s)" % (val,message))
        errors = []
        for torrent in torrents:
           message = self.server.d.get_message(torrent)
           if message == 'Tracker: [Failure reason "unregistered torrent"]': errors.append(torrent)
        data = []
        for error in errors:
            data.append((self.server.d.get_tied_to_file(error),self.server.d.get_base_path(error)))
        return data
