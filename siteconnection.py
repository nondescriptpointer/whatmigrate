# Class that handles What.CD authentication, can download torrents and can search the site log

import os,pycurl,urllib,re

re_main = re.compile(r'<span style="color: red;">(.*?)</span>')
re_detail = re.compile(r' Torrent <a href="torrents\.php\?torrentid=\d+"> \d+</a> \((.*?)\) uploaded by <a href="user\.php\?id=\d+">.*?</a> was deleted by <a href="user\.php\?id=\d+">.*?</a> for the reason: (.*?)$')
re_replacement = re.compile(r'(.*?) \( <a href="torrents\.php\?torrentid=(\d+)">torrents\.php\?torrentid=\d+</a> \)')

class Receiver:
    def __init__(self):
        self.contents = ""
    def body_callback(self, buffer):
        self.contents = self.contents + buffer

class Connection:
    def __init__(self,user,passw):
        self.username = user
        self.password = passw
        self.retrys = 0
        self.rec = Receiver()
        self.curl = pycurl.Curl()
        self.curl.setopt(pycurl.FOLLOWLOCATION,1)
        self.curl.setopt(pycurl.MAXREDIRS,5)
        self.curl.setopt(pycurl.NOSIGNAL,1)
        cookiefile = os.path.dirname(os.path.realpath(__file__))+"/.cookiefile"
        self.curl.setopt(pycurl.COOKIEFILE,cookiefile)
        self.curl.setopt(pycurl.COOKIEJAR,cookiefile)
        self.curl.setopt(pycurl.WRITEFUNCTION,self.rec.body_callback)
    def clearCurl(self):
        self.rec.contents = ""
        self.curl.setopt(pycurl.POST,0)
        self.curl.setopt(pycurl.POSTFIELDS,"")
    # login
    def login(self):
        self.clearCurl()
        self.curl.setopt(pycurl.URL,"https://ssl.what.cd/login.php")
        self.curl.setopt(pycurl.POST,1)
        logindata = urllib.urlencode([('username',self.username),('password',self.password),('keeplogged',1),('login','Log in !')])
        self.curl.setopt(pycurl.POSTFIELDS,logindata)
        self.curl.perform()
    # search site log
    def searchLog(self,searchstring):
        self.clearCurl()
        self.curl.setopt(pycurl.URL,"https://ssl.what.cd/log.php?search="+urllib.quote(searchstring))
        self.curl.perform()
        if self.rec.contents.find('id="loginform"') is not -1:
            self.retrys += 1
            if self.retrys > 1: # no retrying
                print "Login failed, check your configuration"
                exit()
            self.login()
            self.searchLog(searchstring)
        return self.parseLogSearchResult(self.rec.contents)
    def parseLogSearchResult(self,html):
        if html.find('<td colspan="2">Nothing found!</td>') is not -1:
            return None
        results = []
        # find all possible candidates
        result = re_main.finditer(html)
        for match in result:
            resultline = match.group(0)
            # parse candidate
            subresult = re_detail.search(resultline)
            if subresult:
                subresult = subresult.groups()
                # parse reason to get replacement torrent
                replacement = re_replacement.search(subresult[1])
                if replacement:
                    replacement = replacement.groups()
                    subresult = (subresult[0],replacement[0],replacement[1])
                results.append(subresult)
        return results
    def getTorrentFile(self,torrentid):
        self.clearCurl()
        self.curl.setopt(pycurl.URL,"https://ssl.what.cd/torrents.php?torrentid=%s" % (torrentid,))
        self.curl.perform()
        if self.rec.contents.find('id="loginform"') is not -1:
            self.retrys += 1
            if self.retrys > 1: # no retrying
                print "Login failed, check your configuration"
                exit()
            self.login()
            self.getTorrentURL(torrentid)
        # process result
        re_torrentlink = re.compile(r'torrents\.php\?action=download&amp;id='+torrentid+r'\&amp;authkey=.+?&amp;torrent_pass=\w+')
        result = re_torrentlink.search(self.rec.contents)
        torrentlink = result.group().replace("&amp;","&")
        return self.downloadTorrent(torrentlink)
    def downloadTorrent(self,torrentlink):
        self.clearCurl()
        self.curl.setopt(pycurl.URL,"http://ssl.what.cd/%s" % (torrentlink,))
        self.curl.perform()
        return self.rec.contents
    def close(self):
        self.curl.close()
