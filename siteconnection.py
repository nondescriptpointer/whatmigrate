# Class that handles What.CD authentication, can download torrents and can search the site log
import os,pycurl,urllib,re,sys,urllib2
from BeautifulSoup import BeautifulSoup

re_main = re.compile(r'<span style="color: red;">(.*?)</span>')
re_detail = re.compile(r' Torrent <a href="torrents\.php\?torrentid=\d+"> \d+</a> \((.*?)\) uploaded by <a href="user\.php\?id=\d+">.*?</a> was deleted by <a href="user\.php\?id=\d+">.*?</a> for the reason: (.*?)$')
re_replacement = re.compile(r'(.*?) \( <a href="torrents\.php\?torrentid=(\d+)">torrents\.php\?torrentid=\d+</a> \)')

class Receiver:
    def __init__(self):
        self.contents = ""
        self.header = ""
    def body_callback(self, buffer):
        self.contents = self.contents + buffer
    def header_callback(self,buffer):
        self.header = self.header + buffer

class Connection:
    def __init__(self,user,passw,use_ssl):
        self.username = user
        self.password = passw
        self.logintries = 0
        if(use_ssl): self.basepath = "https://ssl.what.cd/"
        else: self.basepath = "http://what.cd/"
        # Set up curl
        self.rec = Receiver()
        self.curl = pycurl.Curl()
        self.curl.setopt(pycurl.FOLLOWLOCATION,1)
        self.curl.setopt(pycurl.MAXREDIRS,5)
        self.curl.setopt(pycurl.NOSIGNAL,1)
        cookiefile = os.path.expanduser("~/.whatmigrate_cookiefile")
        self.curl.setopt(pycurl.COOKIEFILE,cookiefile)
        self.curl.setopt(pycurl.COOKIEJAR,cookiefile)
        self.curl.setopt(pycurl.WRITEFUNCTION,self.rec.body_callback)
        self.curl.setopt(pycurl.HEADERFUNCTION,self.rec.header_callback)

    # to reset curl after each request
    def clearCurl(self):
        self.rec.contents = ""
        self.rec.header = ""
        self.curl.setopt(pycurl.POST,0)
        self.curl.setopt(pycurl.POSTFIELDS,"")

    # make request
    def makeRequest(self,url,post = None):
        # make request
        self.clearCurl()
        self.curl.setopt(pycurl.URL,url)
        if(post):
            self.curl.setopt(pycurl.POST,1)
            self.curl.setopt(pycurl.POSTFIELDS,post)
        self.curl.perform()
        # check if logged in
        if not self.rec.contents.find('id="loginform"') is -1:
            self.logintries += 1
            if(self.logintries > 1): sys.exit("Site login failed, check your username and password in your configuration file")
            self.login()
            return self.makeRequest(url,post)
        # return result
        return self.rec.contents
    
    # login
    def login(self):
        self.makeRequest(self.basepath+"login.php",
            urllib.urlencode([
                ("username",self.username),
                ("password",self.password),
                ("keeplogged",1),
                ("login","Log in !")
            ])
        )
    
    # strip html
    def stripHTML(self,html):
        return ''.join(BeautifulSoup(html).findAll(text=True))

    # search torrents
    def searchTorrents(self,searchstring):
        html = self.makeRequest(self.basepath+"torrents.php?searchstr="+urllib.quote(searchstring))
        soup = BeautifulSoup(html, convertEntities=BeautifulSoup.HTML_ENTITIES)
        table = soup.find("table", {"id":"torrent_table"})
        if not table: return False
        groups = table.findAll("tr")
        results = {}
        for group in groups:
            classes = group["class"].split(' ')
            # parse the groups
            if "group" in classes:
                copy = unicode(group.findAll('td')[2])
                copy = copy[0:copy.find('<span style="float:right;">')]
                currentgroup = self.stripHTML(copy).strip() 
                results[currentgroup] = {}
            # parse the edition
            elif "edition" in classes:
                currentedition = group.td.strong.find(text=True,recursive=False).strip()
                if currentgroup: results[currentgroup][currentedition] = []
            # parse the torrent
            elif "group_torrent" in classes:
                torrentdata = {}
                torrentdata['format'] = group.td.find('a',recursive=False).text.strip()
                torrentdata['size'] = group.findAll('td')[3].text.strip()
                dlink = unicode(group.td.a)
                regex = re.compile(r'id=(\d+)')
                reresult = regex.search(dlink)
                if reresult:
                    torrentdata['id'] = int(reresult.group(1));
                else:
                    continue
                if currentedition and currentgroup:
                    results[currentgroup][currentedition].append(torrentdata)
        return results

    # download a torrent file
    def getTorrentFile(self,torrentid):
        result = self.makeRequest(self.basepath+"torrents.php?torrentid=%s" % (torrentid,))
        # process result
        re_torrentlink = re.compile(r'torrents\.php\?action=download&amp;id='+str(torrentid)+r'\&amp;authkey=.+?&amp;torrent_pass=\w+')
        result = re_torrentlink.search(result)
        if not result: sys.exit("Could not find torrent with id %s." % (torrentid,))
        torrentlink = result.group().replace("&amp;","&")
        torrentdata = self.makeRequest(self.basepath+torrentlink)
        # parse header to get filename
        torrent_filename = torrentid
        for line in iter(self.rec.header.splitlines()):
            if 'filename=' in line:
                torrent_filename = line[line.find('filename=')+10:-1]
        return (torrent_filename, torrentdata)

    def close(self):
        self.curl.close()
