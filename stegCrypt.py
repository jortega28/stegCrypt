import sender_module
import receiver_module
from PIL import Image, ImageOps
import os.path
from shutil import copyfile

# Name of the files we are going to be working with
IMAGE_FILE = ""
SECRET_IMAGE_FILE = ""
# Use the Image module to open up the images (and make the secret image the same size as the original)
PICTURE = Image.new("RGB", (512, 512), "white")
SECRET_PICTURE = Image.new("RGB", (512, 512), "white")
# Get the width and height of the image
WIDTH, HEIGHT = PICTURE.size
# All pixels from the image will be stored in PIXEL_MAP
# They will be stored in a list consisting of 5 elements [XPos, YPos, R, G, B]
# Where R, G and B represents the amount of that color that is on that pixel
PIXEL_MAP = []
# New image produced
NEW_IMAGE_FILE = ""
# A list containing all usable commands
COMMANDS = ["help", "netsend", "netreceive", "localextract", "localhide", "exit", "details", "sources"]
COMMANDS.sort()

def hideImage():
    s = 4
    for x in range (0, WIDTH):
        for y in range (0, HEIGHT):
            p = PICTURE.getpixel( (x,y) )
            q = SECRET_PICTURE.getpixel( (x,y) )
            r = p[0] - (p[0] % s) + (s * q[0] / 255)
            g = p[1] - (p[1] % s) + (s * q[1] / 255)
            b = p[2] - (p[2] % s) + (s * q[2] / 255)
            PIXEL_MAP.append([x, y, r, g, b])

def extractSecretImage(imageToExtract):
    s = 4
    imageData = Image.open(imageToExtract)
    for x in range (0, imageData.size[0]):
        for y in range (0, imageData.size[1]):
            p = imageData.getpixel( (x,y) )
            r = (p[0] % s) * 255 / s
            g = (p[1] % s) * 255 / s
            b = (p[2] % s) * 255 / s
            PIXEL_MAP.append([x, y, r, g, b])

def decimalToBinary(decimalNumber):
    return bin(decimalNumber)[2:]

def binaryToDecimal(binaryNumber):
    return int(binaryNumber, 2)

def initPixelMap():
    for y in range (0, HEIGHT):
        for x in range (0, WIDTH):
            r,g,b = PICTURE.getpixel( (x,y) )
            PIXEL_MAP.append([x, y, r, g, b])

def changePixelColor(x, y, r, g, b):
    i = 0
    while i < len(PIXEL_MAP):
        if PIXEL_MAP[i][0] == x and PIXEL_MAP[i][1] == y:
            # If we made it here we found the pixel we were looking for in the map
            # So change the pixel to the colors provided
            PIXEL_MAP[i][2] = r
            PIXEL_MAP[i][3] = g
            PIXEL_MAP[i][4] = b
        i += 1

def createNewImage(prefix):
    # This will take all items in the PIXEL_MAP and print it into its own image
    setNewImageFile(prefix + "_" + IMAGE_FILE)
    copyfile(IMAGE_FILE, NEW_IMAGE_FILE)
    newPicture = Image.open(NEW_IMAGE_FILE)
    p = newPicture.load()
    for pixels in PIXEL_MAP:
        r, g, b = p[pixels[0], pixels[1]]
        p[pixels[0], pixels[1]] = (pixels[2], pixels[3], pixels[4])
    newPicture.save(NEW_IMAGE_FILE)

def createExtractedImage(fileExtracted):
    # This will take all items in the PIXEL_MAP and print it into its own image
    setNewImageFile("extracted_image.png")
    copyfile(fileExtracted, NEW_IMAGE_FILE)
    newPicture = Image.open(NEW_IMAGE_FILE)
    p = newPicture.load()
    for pixels in PIXEL_MAP:
        r, g, b = p[pixels[0], pixels[1]]
        p[pixels[0], pixels[1]] = (pixels[2], pixels[3], pixels[4])
    newPicture.save(NEW_IMAGE_FILE)

def exampleUsage():
    # Example of conversion from decimal to binary and then back to decimal
    someNumber = 123
    print "Here is " + str(someNumber) + " in binary: " + str(decimalToBinary(someNumber))

    someBinaryNumber = decimalToBinary(someNumber)
    print "Here is " + str(someBinaryNumber) + " in decimal: " + str(binaryToDecimal(someBinaryNumber))

    # Print out the dimensions of the image
    print "The dimensions of the image is " + str(WIDTH) + " x " + str(HEIGHT)

    # Initialize the pixel map and have it read every pixel in the image
    initPixelMap()

    # Print out the pixel map which contains the location of every pixel
    # And the R G B values associated with that pixel
    print PIXEL_MAP

    # Add 100 to the blue value in the pixel map for every pixel
    for i in range(0, len(PIXEL_MAP)):
        PIXEL_MAP[i][2] = PIXEL_MAP[i][2]
        PIXEL_MAP[i][3] = PIXEL_MAP[i][3]
        PIXEL_MAP[i][4] = PIXEL_MAP[i][4]+100

    # Now create an image using the new pixel map
    createNewImage("new")

def initializeImages():
    global PICTURE
    global SECRET_PICTURE
    global WIDTH
    global HEIGHT
    # Use the Image module to open up the images (and make the secret image the same size as the original)
    PICTURE = Image.open(IMAGE_FILE)
    SECRET_PICTURE = ImageOps.autocontrast(Image.open(SECRET_IMAGE_FILE).resize(PICTURE.size))
    # Get the width and height of the image
    WIDTH, HEIGHT = PICTURE.size

def setNewImageFile(name):
    global NEW_IMAGE_FILE
    NEW_IMAGE_FILE = name

def setImageFile(name):
    global IMAGE_FILE
    IMAGE_FILE = name

def setSecretImageFile(name):
    global SECRET_IMAGE_FILE
    SECRET_IMAGE_FILE = name

def clearPixelMap():
    global PIXEL_MAP
    PIXEL_MAP = []

def isPNG(file):
    if ".png" in file:
        return True

def netSend():
    localHide()

    imageData = Image.open(NEW_IMAGE_FILE)
    tempmap = []
    tempmap.append(imageData.size[0])
    tempmap.append(imageData.size[1])
    for x in range(0, imageData.size[0]):
        for y in range(0, imageData.size[1]):
            r, g, b = imageData.getpixel((x, y))
            tempmap.append(x)
            tempmap.append(y)
            tempmap.append(r)
            tempmap.append(g)
            tempmap.append(b)

    file = open("temp.txt", "w")
    for item in tempmap:
        file.write("%s " % item)
    file.close()

    while True:
        ip4 = raw_input("What is the IPv4 address of the computer you want to send the image to? (Example: 192.168.1.17)\n")
        port = raw_input("What is the port number in which you wish to communicate with the the computer? (Leave blank to use default 2696)\n")
        if port == "":
            port = 2696
        else:
            port = int(port)

        # Now send it
        print "Sending public image with hidden image..."
        try:
            sender_module.initNetSetting("temp.txt", ip4, port)
            sender_module.sendFile()
            break
        except:
            print "The image was sent. If no errors were displayed then the transfer was most likely a success."
            break

    # Now delete it
    os.remove("temp.txt")

def netReceive():
    # Wait to receive an image to extract
    port = raw_input("What is the port number in which you wish a file from? (Leave blank to use default 2696)\n")
    if port == "":
        port = 2696
    else:
        port = int(port)
    print "Waiting to receive an image..."
    receiver_module.waitForImage(port)
    print "Processing received image..."

    file = open("temp.txt", "r")
    alldata = file.read().split()

    i = 0
    width = int(alldata[i])
    i+=1
    height = int(alldata[i])
    recvImage = Image.new("RGB", (width, height), "white")
    p = recvImage.load()
    size = len(alldata)
    i+=1
    while i < size:
        x = int(alldata[i])
        i+=1
        y = int(alldata[i])
        i+=1
        r = int(alldata[i])
        i+=1
        g = int(alldata[i])
        i+=1
        b = int(alldata[i])
        i+=1
        p[x,y] = (r,g,b)

    saveAs = "received_image.png"
    recvImage.save(saveAs)
    print "Image processed and saved as " + saveAs + "... Starting the extraction of the hidden image..."

    clearPixelMap()
    extractSecretImage(saveAs)
    createExtractedImage(saveAs)

    print "Done extracting image. Image saved as extracted_image."
    os.remove("temp.txt")

def commandList():
    print "Below are all usable commands (For detailed usage use the help command):\n"
    for command in COMMANDS:
        print "  " + command
    print ""

def commandInterface():
    commandList()
    while True:
        command = raw_input("Enter a command:\n")
        if command in COMMANDS:
            if command == "help":
                help()
            elif command == "exit":
                break
            elif command == "details":
                details()
            elif command == "sources":
                sources()
            elif command == "netsend":
                netSend()
            elif command == "netreceive":
                netReceive()
            elif command == "localhide":
                localHide()
            elif command == "localextract":
                localExtract()
        else:
            print "I don't understand your command... Type help for a list of usable commands."
            print ""

def localExtract():
    # Find out the name of image that contains a hidden image
    imageToExtract = ""
    while True:
        input = raw_input("What is the name of the image that has a hidden image? (If it is in a different folder be sure to provide the path to the file)\n")
        if os.path.isfile(input) and isPNG(input):
            imageToExtract = input
            break
        else:
            print ("Could not locate the file or file is not a png file... Check to make sure it is spelled correctly and includes the .png at the end... Try again...")
            print ""

    # Clear the pixel map just in case it was used in a different operation
    clearPixelMap()

    # Extract hidden image
    print "Attempting to extract an image..."
    extractSecretImage(imageToExtract)
    # Save the hidden image
    createExtractedImage(imageToExtract)
    print "Image extracted and saved as " + "extracted_image.png"

    print ""

def localHide():
    # Find out what the name of the public image by asking the user
    while True:
        input = raw_input("What is the name of the public image? (If it is in a different folder be sure to provide the path to the file)\n")
        if os.path.isfile(input) and isPNG(input):
            setImageFile(input)
            break
        else:
            print ("Could not locate the file or file is not a png file... Check to make sure it is spelled correctly and includes the .png at the end... Try again...")
            print ""

    # Find out the name of the image they want to hide
    while True:
        input = raw_input("What is the name of the image you want to hide steganographically? (If it is in a different folder be sure to provide the path to the file)\n")
        if os.path.isfile(input) and isPNG(input):
            setSecretImageFile(input)
            break
        else:
            print ("Could not locate the file or file is not a png file... Check to make sure it is spelled correctly and includes the .png at the end... Try again...")
            print ""

    # Initialize the images
    initializeImages()

    # Start hiding the image
    print "Hiding the image..."
    hideImage()
    # Save the new pixel map into a file
    createNewImage("hidden")
    print "Done hiding the secret image in the public image. The resulting file was saved as " + NEW_IMAGE_FILE
    # Clear the pixel map
    clearPixelMap()
    print ""

def help():
    print "localhide - Hide an image in another image and save it to the computer."
    print "localextract - Extract a hidden image from an image."
    print "netsend - Hide an image in another image, save it to the computer and send it to another computer. (Note: Make sure the receiver is ready to accept the image.)"
    print "netreceive - Receive an image from another computer and extract the hidden image from it."
    print "details - Print out details about the program itself."
    print "sources - Print out links all sources used in developing this program."
    print "help - Produce a list of usable commands and there usage."
    print "exit - Exit the program."
    print ""

def details():
    print "stegCalc is a program developed by Justin Ortega as a project for a cryptology course. This program can be used to hide a png image within another png image " \
          "steganographically and optionally send the png image to another computer or receive one from another computer. Note this program is not intended for sending" \
          " sensitive data but to be used for experimental and learning purposes."
    print ""

def sources():
    print "http://ciphermachines.com/types.html#steg"
    print "https://en.wikipedia.org/wiki/Steganography"
    print "https://zooid.org/~paul/crypto/jsteg/README.jsteg"
    print "https://en.wikipedia.org/wiki/Battle_of_Leyte_Gulf"
    print "http://www1.chapman.edu/~nabav100/ImgStegano/download/ImageSteganography.pdf"
    print "http://interactivepython.org/runestone/static/everyday/2013/03/1_steganography.html"
    print "https://saxenarajat99.wordpress.com/2014/01/17/hiding-image-in-image-in-python-using-steganography/"
    print ""

if __name__ == '__main__':
    print "Welcome to stegCrypt!"
    details()

    # Start up the command line interface
    commandInterface()

    print "Thank you for using stegCrypt!"