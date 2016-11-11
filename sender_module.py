import struct
import sys
import socket as sock

# This python file provides the ability to send any file to another.
# The goal is to encrypt an image and send it to another

# File that will be transferred to another
FILE_NAME = "someImage.jpg"
# Option to transfer via IPv6
IP6MODE = False
# Transfer without the use of a sliding window algorithm
SLIDE_WIN_MODE = False
# Timeout in sending file after this much time
TIMEOUT = .1
# Receiver IPv4 address
serverip4 = "127.0.0.1"
# Receiver IPv6 address
serverip6 = "::1"
# Port number to communicate to the client through
PORT = 2696
# Codes to send when transferring packets
OPCODE_WRQ = 1
OPCODE_DATA = 3
OPCODE_ACK = 4
OPCODE_ERROR = 5
# Size of the packets to be sent
BUFFER_SIZE = 65536
# Records what blocks of data have been sent
BLOCKS_SENT = []
# The mode in which to send the data
MODE = "octet"

def sendFile():
    if SLIDE_WIN_MODE is True:
        return False
    socket = createSocket()

    FILE = openFile(socket)

    data = lastdata = FILE.read(512)

    #WRQ Packet

    sendWRQ(socket)

    #Data Packet
    addToBlock(1)
    print("Sending block " + str(BLOCK_NUMBER))
    sendData(socket, data)
    waitForACK(socket, data)

    while len(data) == 512:
        data = lastdata = FILE.read(512)
        if data == "":
            break

        addToBlock(1)
        print("Sending block " + str(BLOCK_NUMBER))
        sendData(socket, data)
        waitForACK(socket, data)

    FILE.close()
    return True

def openFile(socket):
    try:
        FILE = open(FILE_NAME, "r")
    except IOError:
        sendError(socket, "File Not Found!", '1')
    return FILE

def sendError(socket, errmsg, errcode):
    print("Sending ERROR packet...")
    if IP6MODE is False:
        socket.sendto(ERRPacket(errmsg, errcode), (serverip4, PORT))
    else:
        socket.sendto(ERRPacket(errmsg, errcode), getSockAddr())
    socket.close()
    sys.exit("Error Code " + errcode + ":\n" + errmsg)

def ERRPacket(errmsg, errcode):
    formattedEM = str(errmsg)
    addIn = 128-len(str(errmsg))
    i = 0
    while i < addIn:
        formattedEM = formattedEM + " "
        i += 1
    packet = struct.pack("!cc%dsc" % len(formattedEM), str(OPCODE_ERROR), str(errcode), str(errmsg), '0')
    return packet

def addToBlock(amount):
    global BLOCK_NUMBER
    BLOCK_NUMBER = BLOCK_NUMBER+amount

def waitForACK(socket, data):
    try:
        packet, client = socket.recvfrom(BUFFER_SIZE)
    except Exception:
        print("Timeout... no ACK received... resending data packet...")
        sendData(socket, data)
        socket.settimeout(TIMEOUT*2)
        packet, client = socket.recvfrom(BUFFER_SIZE)
        socket.settimeout(TIMEOUT)

    opcode = int(packet[0:1])
    if opcode == 4:
        print("Received ACK...")
        serverblock = int(packet[1:11])
        if BLOCK_NUMBER != serverblock:
            print("Incorrect ACK... waiting...")
            sendData(socket, data)
            socket.settimeout(TIMEOUT*2)
            packet, client = socket.recvfrom(BUFFER_SIZE)
            socket.settimeout(TIMEOUT)
    elif opcode == 5:
        print("Received ERROR...")
        errcode = packet[1:2]
        errmsg = packet[2:129]
        socket.close()
        sys.exit("Error Code " + errcode + ":\n" + errmsg)

def waitForACKs(socket, sent):
    packets = []
    received = []
    #Initially set to resend all of them
    resend = BLOCKS_SENT
    try:
        i = 0
        while i < sent:
            packet, client = socket.recvfrom(BUFFER_SIZE)
            packets.append(packet)
            i += 1
            setWINPOS(BLOCK_NUMBER)
    except Exception:
        print("Timeout... not all ACKs received...")
        j = 0
        while j < len(packets):
            opcode = int(packets[j][0:1])
            if opcode == 4:
                print("Received ACK...")
                serverblock = int(packets[j][1:11])
                received.append(serverblock)
            elif opcode == 5:
                print("Received ERROR...")
                errcode = packets[j][1:2]
                errmsg = packets[j][2:129]
                socket.close()
                sys.exit("Error Code " + errcode + ":\n" + errmsg)
            j += 1
        #Now decide what packets need to be resent
        print resend
        k = 0
        while k < len(received):
            l = 0
            found = False
            while l < len(BLOCKS_SENT) and found is False:
                if received[k] == BLOCKS_SENT[l]:
                    found = True
                    resend.remove(BLOCKS_SENT[l])
                l += 1
            k += 1
        #Now we know what blocks need to be resent
        #We will choose the earliest block number
        print resend
        earliest = resend[0]
        setBlockNumber(earliest-1)
        setWINPOS(earliest-1)
    clearBlocksSent()

def sendData(socket, data):
    if IP6MODE is False:
        socket.sendto(DataPacket(data), (serverip4, PORT))
    else:
        socket.sendto(DataPacket(data), getSockAddr())

def sendWRQ(socket):
    if IP6MODE is False:
        socket.sendto(WRQPacket(socket), (serverip4, PORT))
    else:
        socket.sendto(WRQPacket(socket), getSockAddr())

def createSocket():
    if IP6MODE is False:
        socket = sock.socket(sock.AF_INET, sock.SOCK_DGRAM)
        socket.settimeout(TIMEOUT)
        return socket
    else:
        socket = sock.socket(sock.AF_INET6, sock.SOCK_DGRAM)
        socket.settimeout(TIMEOUT)
        return socket

def getSockAddr():
    res = sock.getaddrinfo(serverip6, PORT, sock.AF_INET6, sock.SOCK_DGRAM)
    family, socktype, proto, canonname, sockaddr = res[0]
    return sockaddr

def setWINPOS(position):
    global WIN_POS
    WIN_POS = position

def DataPacket(data):
    formattedBN = str(BLOCK_NUMBER)
    addIn = 10-len(str(BLOCK_NUMBER))
    i = 0
    while i < addIn:
        formattedBN = formattedBN + " "
        i += 1

    packet = struct.pack("!c%ds%ds" % (len(formattedBN),len(data)), str(OPCODE_DATA), str(formattedBN), str(data))
    return packet

def WRQPacket(socket):
    FNLength = len(FILE_NAME)
    addIn = 64-FNLength
    formatedName = FILE_NAME

    if addIn < 0:
        socket.close()
        sys.exit("Specified file's name is too large! Ending program!")
    else:
        i = 0
        while i < addIn:
            formatedName = formatedName + " "
            i += 1

    formattedMode = MODE
    addIn = 8-len(MODE)
    i = 0
    while i < addIn:
        formattedMode = formattedMode + " "
        i += 1

    FN = formatedName.encode(encoding='UTF-8')
    M = formattedMode.encode(encoding='UTF-8')
    packet = struct.pack("!c%dsc%dsc" % (len(FN), len(M)), str(OPCODE_WRQ).encode(encoding='UTF-8'), FN, '0', M, '0')

    return packet

def clearBlocksSent():
    global BLOCKS_SENT
    BLOCKS_SENT = []

def setBlockNumber(blocknumber):
    global BLOCK_NUMBER
    BLOCK_NUMBER = blocknumber