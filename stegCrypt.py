import sender_module
import Image, ImageOps
import sys
from shutil import copyfile

# Name of the files we are going to be working with
IMAGE_FILE = "public.png"
SECRET_IMAGE_FILE = "to_hide_2.png"
# Use the Image module to open up the images (and make the secret image the same size as the original)
PICTURE = Image.open(IMAGE_FILE)
SECRET_PICTURE = ImageOps.autocontrast(Image.open(SECRET_IMAGE_FILE).resize(PICTURE.size))
# Get the width and height of the image
WIDTH, HEIGHT = PICTURE.size
# All pixels from the image will be stored in PIXEL_MAP
# They will be stored in a list consisting of 5 elements [XPos, YPos, R, G, B]
# Where R, G and B represents the amount of that color that is on that pixel
PIXEL_MAP = []
# New image produced
NEW_IMAGE_FILE = ""

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

def setNewImageFile(name):
    global NEW_IMAGE_FILE
    NEW_IMAGE_FILE = name

def clearPixelMap():
    global PIXEL_MAP
    PIXEL_MAP = []

if __name__ == '__main__':
    # Here I will ask for what the files are called

    # Start hiding the image
    hideImage()

    # Save the new pixel map into a file
    createNewImage("hidden")

    # Clear the pixel map
    clearPixelMap()

    # Extract hidden image
    extractSecretImage("hidden_public.png")

    # Save the hidden image
    createNewImage("extracted")