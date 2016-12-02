import struct
import sys
import socket as sock
import os.path
import random
import time

PORT = 2696
BUFFER_SIZE = 65536
OPCODE_WRQ = 1
OPCODE_DATA = 3
OPCODE_ACK = 4
OPCODE_ERROR = 5
serverip4 = "127.0.0.1"
serverip6 = "::1/128"
clientip4 = []
clientip6 = []
TIMEOUT = .2
LAST_BLOCK = 0
FILE_NAME = ""
IP6MODE = False
SLIDE_WIN_MODE = False
DROP1 = False
DROP_NUMBER = 17
WRQRecv = False
BLOCKS_RECEIVED = []
SLIDE_WIN_SIZE = 0

def createIP4Socket():
    socket = sock.socket(sock.AF_INET, sock.SOCK_DGRAM)
    socket.bind(('', PORT))
    return socket

def createIP6Socket():
    socket = sock.socket(sock.AF_INET6, sock.SOCK_DGRAM)
    socket.bind(('', PORT))
    return socket

def formatError(socket):
    sendError(socket, "Illegal TFTP Operation!", 5)
    sendError(socket, "Illegal TFTP Operation!", 5)

def validWRQ(p1, p2, p3, p4):
    if p2 != 0:
        print "Not a Zero Byte"
        return False
    elif "octet" not in p3:
        print "Invalid Mode!"
        return False
    elif p4 != 0:
        print "Not a Zero Byte"
        return False
    else:
        return True

def validData(p1, p2):
    if p1 < 0:
        return "error"
    elif len(p2) != 512:
        return "end"
    else:
        return "valid"

def openFile(fileName, socket):
    file = open("received/" + fileName, "a")
    return file

def createFile(fileName, socket):
    fname = "received/" + fileName
    if os.path.isfile(fname):
        sendError(socket, "File already exists on host!", 6)
        #os.remove(fname)
    file = open(fname, "a")
    return file

def accessError(socket, err):
    socket.close()
    if err == 1:
        sys.exit("Invalid file name!")
    elif err == 2:
        sys.exit("Unable to access location or low storage space!")

def sendACK(socket):
    if IP6MODE is False:
        socket.sendto(ACKPacket(), clientip4)
    else:
        socket.sendto(ACKPacket(), getSockAddr(clientip6))

def sendACKAlt(socket, blocknumber):
    if IP6MODE is False:
        socket.sendto(ACKPacketAlt(blocknumber), clientip4)
    else:
        socket.sendto(ACKPacketAlt(blocknumber), getSockAddr(clientip6))

def sendError(socket, errmsg, errcode):
    #print("Sending ERROR packet...")
    if IP6MODE is False:
        socket.sendto(ERRPacket(errmsg, errcode), clientip4)
    else:
        socket.sendto(ERRPacket(errmsg, errcode), getSockAddr(clientip6))
    socket.close()
    sys.exit("Error Code " + str(errcode) + ":\n" + errmsg)

def ERRPacket(errmsg, errcode):
    formattedEM = str(errmsg)
    addIn = 128-len(str(errmsg))
    i = 0
    while i < addIn:
        formattedEM = formattedEM + " "
        i += 1
    packet = struct.pack("!cc%dsc" % len(formattedEM), str(OPCODE_ERROR), str(errcode), str(errmsg), '0')
    return packet

def getSockAddr(ip6):
    res = sock.getaddrinfo(ip6[0], ip6[1], sock.AF_INET6, sock.SOCK_DGRAM)
    family, socktype, proto, canonname, sockaddr = res[0]
    return sockaddr

def ACKPacket():
    formattedBN = str(LAST_BLOCK)
    addIn = 10-len(str(LAST_BLOCK))
    i = 0
    while i < addIn:
        formattedBN = formattedBN + " "
        i += 1
    packet = struct.pack("!c%ds" % len(formattedBN), str(OPCODE_ACK), str(formattedBN))
    return packet

def ACKPacketAlt(blocknumber):
    formattedBN = str(blocknumber)
    addIn = 10-len(str( blocknumber))
    i = 0
    while i < addIn:
        formattedBN = formattedBN + " "
        i += 1
    packet = struct.pack("!c%ds" % len(formattedBN), str(OPCODE_ACK), str(formattedBN))
    return packet

def setClientIP(ip):
    global clientip6
    global clientip4
    if IP6MODE is True:
        clientip6 = ip
        clientip4 = []
    else:
        clientip4 = ip
        clientip6 = []

def setIPMode(answer):
    global IP6MODE
    if "y" in answer:
        IP6MODE = True
    elif "n" in answer:
        IP6MODE = False
    else:
        return False
    return True

def setSlideWinMode(answer):
    global SLIDE_WIN_MODE
    if "y" in answer:
        SLIDE_WIN_MODE = True
    elif "n" in answer:
        SLIDE_WIN_MODE = False
    else:
        return False
    return True

def setDropMode(answer):
    global DROP1
    if "y" in answer:
        DROP1 = True
    elif "n" in answer:
        DROP1 = False
    else:
        return False
    return True

def setOptions():
    ipmode = raw_input("Enable IPv6...(y/n): ")
    sliding = raw_input("Use sliding windows...(y/n): ")
    drop = raw_input("Drop 1% of packets...(y/n)")

    if setIPMode(ipmode) and setSlideWinMode(sliding) and setDropMode(drop):
        print "Preferences acknowledged..."
    else:
        sys.exit("Some input was invalid... exiting program...")

def setWRQRecv():
    global WRQRecv
    WRQRecv = True

def setSWSize(size):
    global SLIDE_WIN_SIZE
    SLIDE_WIN_SIZE = size

def mainNoSW():
    #setOptions()
    if SLIDE_WIN_MODE is True:
        return False
    socket = createIP6Socket()
    status = "unknown"
    lastsent = "none"
    packet = ""
    client = ""
    FILE_NAME = ""
    lastblockstored = 0
    startTime = 0
    timeStarted = False
    #print("Awaiting connection...")
    while True:
        try:
            packet, client = socket.recvfrom(BUFFER_SIZE)
            if timeStarted is False:
                startTime = time.time()
                timeStarted = True
            socket.settimeout(TIMEOUT)
        except Exception:
            if "ack" in lastsent:
                #print("Time expired... sending another ACK...")
                sendACK(socket)
                lastsent = "ack"
                retries = 0
                modifier = .5
                while retries < 5:
                    try:
                        socket.settimeout(TIMEOUT*modifier)
                        packet, client = socket.recvfrom(BUFFER_SIZE)
                    except Exception:
                        retries += 1
                        modifier = modifier/2
                socket.settimeout(TIMEOUT)

        setClientIP(client)
        opcode = int(packet[0:1])
        if opcode == 3:
            #print("The packet is a data packet.")
            strblock = str(packet[1:11])
            strblock = strblock.replace(" ", "")
            blockNumber = int(strblock)
            #print("Block Number Received: " + str(LAST_BLOCK))
            data = packet[11:523]
            data = str(data)

            status = validData(blockNumber, data)

            if "error" in status:
                formatError(socket)
            elif "end" in status:
                print("Finalizing transfer...")

            if blockNumber == LAST_BLOCK+1:
                try:
                    file = openFile(FILE_NAME, socket)
                    file.write(data)
                    file.close()
                except IOError:
                    if WRQRecv:
                        if DROP1 is False:
                            sendError(socket, "Disk full or allocation exceeded!", 3)
                        elif random.randrange(1, 101) != DROP_NUMBER:
                            sendError(socket, "Disk full or allocation exceeded!", 3)
                    else:
                        #print("A WRQ was never received...")
                        if DROP1 is False:
                            sendError(socket, "File Not Found!", '1')
                        elif random.randrange(1, 101) != DROP_NUMBER:
                            sendError(socket, "File Not Found!", '1')

                addLastBlock(1)
                lastblockstored = LAST_BLOCK

                if DROP1 is False:
                    sendACK(socket)
                    lastsent = "ack"
                elif random.randrange(1, 101) != DROP_NUMBER:
                    sendACK(socket)
                    lastsent = "ack"
                else:
                    print("Dropping ACK...")
            else:
                print("Block received is incorrect block..." + "\nReceived BN:" + str(blockNumber) + " Should be BN:" + str(LAST_BLOCK+1))
                if blockNumber == lastblockstored:
                    print("Already received... ignoring...")

        elif opcode == 1:
            #print("The packet is an WRQ packet.")
            fileName = FILE_NAME = str(packet[1:65].replace(" ", "")).decode(encoding='UTF-8')
            zero1 = int(packet[65:66])
            mode = str(packet[66:74].replace(" ", "")).decode(encoding='UTF-8')
            zero2 = int(packet[74:75])

            if validWRQ(fileName, zero1, mode, zero2) is False:
                formatError(socket)

            file = createFile(fileName, socket)
            file.close()
            setWRQRecv()

        elif opcode == 5:
            print("Received ERROR...")
            errcode = packet[1:2]
            errmsg = packet[2:129]
            socket.close()
            sys.exit("Error Code " + str(errcode) + ":\n" + errmsg)
        else:
            formatError(socket)

        if "end" in status:
            sendACK(socket)
            print("Transfer complete! Closing connection...")
            socket.close()
            break

    finalTime = time.time()
    elapsedTime = finalTime-startTime
	# For getting elapsed time
    #throughput = os.path.getsize('received/' + FILE_NAME)/elapsedTime
    #print("Total Transfer Time:\n" + str(elapsedTime) + "\nFinal Throughput:\n" + str(throughput))

def mainWithSW():
    #SWSize = int(raw_input("How many packets should be sent at a time using sliding windows... "))
    # setSWSize(SWSize)
    socket = createIP6Socket()
    status = "unknown"
    lastsent = "none"
    packet = ""
    client = ""
    allData = []
    lastblockstored = 0
    #print("Awaiting connection...")
    while True:
        packet, client = socket.recvfrom(BUFFER_SIZE)
        setClientIP(client)
        opcode = int(packet[0:1])
        if opcode == 3:
            #print("The packet is a data packet.")

            if WRQRecv is False:
                if DROP1 is False:
                    sendError(socket, "File Not Found!", '1')
                elif random.randrange(1, 101) != DROP_NUMBER:
                    sendError(socket, "File Not Found!", '1')

            strblock = str(packet[1:11])
            strblock = strblock.replace(" ", "")
            blockNumber = int(strblock)
            #print("Block Number Received: " + str(LAST_BLOCK))
            data = packet[11:523]
            data = str(data)

            status = validData(blockNumber, data)

            if "error" in status:
                formatError(socket)

            dataSize = len(allData)

            if dataSize < blockNumber:
                i = 0
                while i < blockNumber-dataSize:
                    allData.append("")
                    i += 1
                allData[blockNumber-1] = data
            else:
                allData[blockNumber-1] = data

            addLastBlock(1)
            lastblockstored = LAST_BLOCK

            if DROP1 is False:
                sendACKAlt(socket,blockNumber)
                lastsent = "ack"
            elif random.randrange(1, 101) != DROP_NUMBER:
                sendACKAlt(socket, blockNumber)
                lastsent = "ack"
            else:
                print("Dropping ACK...")

        elif opcode == 1:
            #print("The packet is an WRQ packet.")
            fileName = FILE_NAME = str(packet[1:65].replace(" ", "")).decode(encoding='UTF-8')
            zero1 = int(packet[65:66])
            mode = str(packet[66:74].replace(" ", "")).decode(encoding='UTF-8')
            zero2 = int(packet[74:75])

            if validWRQ(fileName, zero1, mode, zero2) is False:
                formatError(socket)

            file = createFile(fileName, socket)
            file.close()
            setWRQRecv()

        elif opcode == 5:
            #print("Received ERROR...")
            errcode = packet[1:2]
            errmsg = packet[2:129]
            socket.close()
            sys.exit("Error Code " + str(errcode) + ":\n" + errmsg)
        else:
            formatError(socket)

        if "end" in status:
            #print("Transfer complete! Closing connection...")
            socket.close()
            break
    file = openFile(FILE_NAME, socket)
    j = 0
    while j < len(allData):
        try:
            file.write(allData[j])
        except IOError:
            if WRQRecv:
                if DROP1 is False:
                    sendError(socket, "Disk full or allocation exceeded!", 3)
                elif random.randrange(1, 101) != DROP_NUMBER:
                    sendError(socket, "Disk full or allocation exceeded!", 3)
            else:
                if DROP1 is False:
                    sendError(socket, "File Not Found!", '1')
                elif random.randrange(1, 101) != DROP_NUMBER:
                    sendError(socket, "File Not Found!", '1')
        j += 1
    file.close()
    return True

def addLastBlock(amount):
    global LAST_BLOCK
    LAST_BLOCK = LAST_BLOCK+amount

def waitForImage(port):
    global BLOCKS_RECEIVED
    global LAST_BLOCK
    global PORT
    BLOCKS_RECEIVED = []
    LAST_BLOCK = 0
    PORT = port
    if mainNoSW() is False:
        mainWithSW()