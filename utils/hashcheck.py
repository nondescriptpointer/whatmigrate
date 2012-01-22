#!/usr/bin/python2

# Thanks to Alexandre Jasmin at Stack Overflow
# http://stackoverflow.com/questions/2572521/extract-the-sha1-hash-from-a-torrent-file

import StringIO,os
import torrentdecode, hashlib

def pieces_generator(info,datafolder):
    # Yield pieces from download file(s).
    piece_length = info['piece length']
    if 'files' in info: # multi-file torrent"
        piece = ""
        for file_info in info['files']:
            path = os.path.join(datafolder,*file_info['path'])
            sfile = open(path.decode('UTF-8'), 'rb')
            while True:
                piece += sfile.read(piece_length-len(piece))
                if len(piece) != piece_length:
                    sfile.close()
                    break
                yield piece
                piece = ""
        if piece != "":
            yield piece
    else: # single file torrent
        path = datafolder 
        sfile = open(path.decode('UTF-8'), "rb")
        while True:
            piece = sfile.read(piece_length)
            if not piece:
                sfile.close()
                return
            yield piece

def hashcheck(torrentinfo,datafolder):
    info = torrentinfo['info']
    pieces = StringIO.StringIO(info['pieces'])
    # Iterate through pieces
    pieces_failed = 0
    pieces_correct = 0
    for piece in pieces_generator(info,datafolder):
        piece_hash = hashlib.sha1(piece).digest()
        if (piece_hash != pieces.read(20)):
            pieces_failed += 1
        else:
            pieces_correct += 1
        # Check if we have pieces left
    while pieces.read():
        pieces_failed += 1
    return (pieces_correct,pieces_correct+pieces_failed)
