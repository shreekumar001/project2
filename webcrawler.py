import socket,re,sys,time,string
# declaring all the variables as global

global hostname
global port
global NUID
global password
global secret
global MainDict
global sock
global csrftoken 
global sessionid

#using prefix hostname, port , NUID, Password and list for storing the secret flags

hostname = socket.gethostbyname("cs5700sp16.ccs.neu.edu")
port = 80
try:
    if len(sys.argv[1]) == 9 and int(sys.argv[1][0]) == 0 and int(sys.argv[1][1]) == 0:
        NUID = sys.argv[1]
        password = sys.argv[2]
    else:
        print "Not A Valid Username"
        sys.exit()
except:
    print "Invalid Arguments"
    sys.exit()
password = sys.argv[2]
secret = []
sock = socket.socket(socket.AF_INET,socket.SOCK_STREAM)

# python method to make the HTTP request containing username,password and session id to the "fakebook" server

def HTTPmaker (method, location, cookieflag = 0, csrftoken = None, sessionid = None,paswdflag = 0,username = None, paswd = None):
    HTTPline1 = method + " " + location + " " + "HTTP/1.1" + "\r\n"
    HTTPline2 = "Host:cs5700sp16.ccs.neu.edu\r\nAccept: text/html\r\nAccept-Language: en-US,en\r\n"
    if cookieflag == 1:
        HTTPline3 = "Cookie: csrftoken=%s; sessionid=%s\r\n" % (csrftoken,sessionid)
        HTTPblock1 = HTTPline1 + HTTPline2 + HTTPline3
    else:
        HTTPblock1 = HTTPline1 + HTTPline2
        HTTPline4 = "Connection: keep-alive\r\n"
    if paswdflag == 1:
        HTTPline6 = "username=%s&password=%s&csrfmiddlewaretoken=%s&next=%%2Ffakebook%%2F" % (username,paswd,csrftoken)
        HTTPline5 = "Content-length:%d\r\n\r\n" % len(HTTPline6)
        HTTPheader = HTTPblock1 + HTTPline4 + HTTPline5 + HTTPline6 
    else:
        HTTPheader = HTTPblock1 + HTTPline4 + "\r\n"
    #print HTTPheader
    return HTTPheader

#sending the created HTTP header through the socket

def SockSend (data):
    global sock
    try:
        sock.send(data)
    except:
        print "Cannot send the data, retry connect"
        try:
            sock.connect ((hostname,port))
            sock.send(data)
        except:
            print "Cannot send the data, reset socket"
            sock.close()
            sock = socket.socket(socket.AF_INET,socket.SOCK_STREAM)
            sock.connect((hostname,port))
            sock.send(data)

# receiving the HTTP response from the server

def SockRecv (header):
    try:
        data = sock.recv(8192)
    except:
        print "Cannot receive the data,try resend HTTP header"
        SockSend (header)
        data = sock.recv(8192)
    return data

# function for sending HTTP request in response to HTTP headers from the server
# capturing packet response header to find out any error codes received and send appropriate responses

def Communication(DataSend,Formerdata=""):
    global sock
    SockSend (DataSend)
    #print SockSend
    DataRecv = SockRecv(DataSend)
    #print DataRecv
    for i in range (1,5):
        if DataRecv == "" or DataRecv == "0\r\n\r\n" or DataRecv == Formerdata:
            sock.close()
            sock = socket.socket(socket.AF_INET,socket.SOCK_STREAM)
            sock.connect((hostname,port))
            SockSend (DataSend)
            DataRecv = SockRecv(DataSend)       
        HTTPStatus = re.findall ("HTTP/1.1 (\d+) ",DataRecv)
        if HTTPStatus != ["200"] and HTTPStatus != ["302"]:
            SockSend (DataSend)
            DataRecv = SockRecv(DataSend)
        else:
            break
        if i == 3:
            time.sleep(6)
            print "Sleep 6 sec and force to reset socket"
    return DataRecv

# catch the cookie and maintain the session throughout the webcrawl

def Cookiecatcher (data):
    global csrftoken 
    global sessionid
    csrftoken1 = re.findall (r"csrftoken=(\w+);",data)
    sessionid1 = re.findall (r"sessionid=(\w+);",data)
    if csrftoken1 != []:
        csrftoken = csrftoken1[0]
    if sessionid1 != []:
        sessionid = sessionid1[0]

# main function to create HTTP header for the login, home of the user id and friendlist pages

def Authority ():
    try:
        weburl = "/accounts/login/?next=/fakebook/"
        HTTPheader = HTTPmaker ("GET",weburl)
        page1 = Communication(HTTPheader)
        Cookiecatcher (page1)
        #print "page1",page1
    
        weburl = "/accounts/login/"
        HTTPheader = HTTPmaker ("POST",weburl,1,csrftoken,sessionid,1,NUID,password)
        page2 = Communication(HTTPheader,page1)
        Cookiecatcher (page2)
        #print "page2",page2
    
        HTTPheader = HTTPmaker ("GET","/fakebook/",1,csrftoken,sessionid)
        #print HTTPheader
        page = Communication(HTTPheader,page2)
    
        return page
    except:
        print "Login Error"
        sys.exit()


# to find the secret flags in the pages using regex pattern

def SecretFinder(page):
    global secret
    secretflag = re.findall (r"style=\"color:red\">(.+?)</h2>",page)
    if secretflag != []:
        secret = secret + secretflag

# to check whether the html page is fully received by looking for the end html tag

def GetPage(datasend,formerdata=""):
    page1 = Communication(datasend,formerdata)
    htmlend = re.findall ("</html>",page1)
    if htmlend == []:
        page2 = SockRecv(datasend)
        page1 = page1 + page2
    return page1

# to get the friendlist from the initial user and use the list to traverse each friend and  form a list

def GetFriendList (userID):
    
# to traverse the homepage of the userID
    weburl = "/fakebook/%s/" % userID
    HTTPheader = HTTPmaker ("GET",weburl,1,csrftoken,sessionid)
    page = GetPage(HTTPheader)
    SecretFinder(page)
    
# to traverse the friendlist page of the given userID

    weburl = "/fakebook/%s/friends/1/" % userID
    HTTPheader = HTTPmaker ("GET",weburl,1,csrftoken,sessionid)
    page = GetPage(HTTPheader,page)
    namelist = re.findall (r"<a href=\"/fakebook/(\d+)/\">(.+?)</a>",page)
    pagenumber = re.findall (r"Page 1 of (\d)",page)
    SecretFinder(page)

    if pagenumber == []:
        print " Login Error or No page to Crawl"
        sys.exit()

    if pagenumber[0] != "1":
        pagenumber = range (2, int(pagenumber[0])+ 1)
        for i in pagenumber:
            weburl = "/fakebook/" + userID + "/friends/" + str(i) + "/"
            HTTPheader = HTTPmaker ("GET",weburl,1,csrftoken,sessionid)
            page = GetPage(HTTPheader,page)
            SecretFinder(page)
            namelist1 = re.findall (r"<a href=\"/fakebook/(\d+)/\">(.+?)</a>",page)
            namelist = namelist + namelist1
    return namelist

# to create two lists and form a unique list to traverse all the pages and eliminate the possibility of traversing the duplicate pages by comparing the user id values with previous entries stored in the list MainDict

def ComebineList (SeconTuple,SearchDict):
    global MainDict
    SearchDict2 ={}
    #print "SeconTuple",SeconTuple
    #print "SearchDict",SearchDict
    for i in range (0,len(SeconTuple)):
        if MainDict.has_key(SeconTuple[i][0]) == False:
            MainDict[SeconTuple[i][0]] = SeconTuple[i][1]
            SearchDict2[SeconTuple[i][0]]=SeconTuple[i][1]
    return SearchDict2.items()

# program starts here from calling socket creation to ending when all the secret flags are found by traversing all the pages

sock.connect ((hostname,port))
homepage = Authority()
#print homepage
homenamelist = re.findall (r"<a href=\"/fakebook/(\d+)/\">(.+?)</a>",homepage)
#print homenamelist
MainDict = dict(homenamelist)
searchnamelist = homenamelist

templist = []
#print len(MainDict)
while 1:
    if searchnamelist == []:
        break
    for i in range (0,len(searchnamelist)):
        namelist = GetFriendList (searchnamelist[i][0])
        print "11111",len(namelist)
        print searchnamelist[i][0]
        templist = templist + ComebineList (namelist,dict(templist))
        #print "22222",len(templist)
        #print "33333",len(MainDict)
    searchnamelist = templist
    templist = []

for i in range (0,len(secret)):
    print secret[i][6:]

        
