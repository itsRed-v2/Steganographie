from PIL import Image

class OutOfPixelsException(Exception):
    pass

class ImageBytesEditor():
    def __init__(self, path: str) -> None:
        self.image = Image.open(path)
        self.maxX, self.maxY = self.image.size
        self.maxBand = 3

        self.currentBand = -1
        self.currentX = 0
        self.currentY = 0

        self._loadCurrentPixel()

    def __iter__(self):
        return self

    def __next__(self):
        self._nextChannel()
        return self.currentPixel[self.currentBand]

    def setCurrentByte(self, value: int):
        self.currentPixel[self.currentBand] = value

    def _nextChannel(self):
        self.currentBand += 1

        if self.currentBand >= self.maxBand:
            self.currentBand = 0

            self._saveCurrentPixel()
            self._nextPixel()
            self._loadCurrentPixel()
        
    def _nextPixel(self):
        self.currentX += 1

        if self.currentX >= self.maxX:
            self.currentX = 0
            self.currentY += 1

        if self.currentY >= self.maxY:
            raise StopIteration

    def _loadCurrentPixel(self):
        self.currentPixel = list(self.image.getpixel((self.currentX, self.currentY)))
    
    def _saveCurrentPixel(self):
        self.image.putpixel((self.currentX, self.currentY), tuple(self.currentPixel))

    def getImage(self):
        # Si l'itérateur est terminé mais qu'on essaye d'enregistrer un pixel, 
        # une erreur sera rencontrée à self._saveCurrentPixel() car le pixel sera en dehors de l'image
        if self.currentY >= self.maxY:
            raise OutOfPixelsException
        
        # Si le dernier pixel n'est pas entièrement utilisé, il n'est peut-être pas encore sauvegardé
        self._saveCurrentPixel()
        
        return self.image

class BitIterator:
    def __init__(self, byteArray: bytearray, byteChunkSize: int = 4) -> None:
        self.byteArray = bytearray(byteArray) # on duplique le bytearray par sécurité
        self.currentByte = None
        self.byteposition: int
        self.currentByteIndex = 0

        if 8 % byteChunkSize != 0:
            raise ValueError("byteChunkSize must be a divisor of 8")
        self.byteChunkSize = byteChunkSize
    
    def __iter__(self):
        return self
    
    def __next__(self):
        if self.currentByte == None:
            self._nextByte()
        else:
            self.byteposition += self.byteChunkSize
            if self.byteposition >= 8:
                self._nextByte()

        return self._extractbits()
    
    def _nextByte(self):
        if self.currentByteIndex >= len(self.byteArray):
            raise StopIteration
        self.currentByte = self.byteArray[self.currentByteIndex]
        self.byteposition = 0
        self.currentByteIndex += 1

    def _extractbits(self) -> int:
        value = self.currentByte
        value >>= (8 - self.byteposition - self.byteChunkSize)
        filter = 2 ** (self.byteChunkSize) - 1
        value &= filter
        return value
    
    def lengthInBytes(self):
        return len(self.byteArray)
    
    def progressInBytes(self):
        return self.currentByteIndex

def printProgress(bitIterator: BitIterator):
    progress = bitIterator.progressInBytes()
    length = bitIterator.lengthInBytes()
    percentage = round(100 * progress / length)

    prefix = "\033[1A\x1b[2k"
    print(f"{prefix}Encoded {percentage}% of bytes ({progress} / {length})")

def writeBytes(imageEditor: ImageBytesEditor, bytes: bytearray, chunkSize: int):
    bits = BitIterator(bytes, chunkSize)

    # un nombre binaire 8bits composé de 1 et se terminant par <chunkSize> 0
    # Exemple: si chunkSize = 2, alors byteTrimmer = 0b11111100
    byteTrimmer = 256 - (2 ** BYTE_CHUNK_SIZE)

    print("") # on imprime une ligne vide pour que les appels à printProgress() puissent réécrire par dessus

    i = 0
    for colorPart in imageEditor:
        i += 1
        if i == 100000:
            i = 0
            printProgress(bits)

        colorPart &= byteTrimmer # on enlève les derniers bits
        
        part = next(bits, None) # la partie d'octet à ajouter
        if part == None: # si tous les bits ont été encodés
            printProgress(bits)
            return
                
        colorPart |= part # on ajoute la partie d'octet à la valeur de la couleur
        imageEditor.setCurrentByte(colorPart)

    # Si la boucle for se termine naturellement, c'est qu'on est à court de 
    # pixels et que le message n'a pas été encodé entièrement
    raise OutOfPixelsException

def encode(imagePath: str, filePath: str, chunkSize: int):
    imageEditor = ImageBytesEditor(imagePath)

    with open(filePath, "rb") as file:
        bytesToEncode = bytearray(file.read())

    arraySize = len(bytesToEncode)
    # on ajoute 4 bytes au début de l'array pour indiquer la taille du fichier encodé
    bytesToEncode = arraySize.to_bytes(4, "big") + bytesToEncode

    writeBytes(imageEditor, bytesToEncode, chunkSize)
    return imageEditor.getImage()

IMG_PATH = "./files/sources/clouds.png"
FILE_PATH = "./files/sources/abstract.png"
OUT_PATH = "./files/encoded/out.png"
BYTE_CHUNK_SIZE = 4
    
try:
    image = encode(IMG_PATH, FILE_PATH, BYTE_CHUNK_SIZE)
except OutOfPixelsException:
    print("The image is not large enough to store all this data ! Exiting...")
    exit()

print("Done ! Writing the resulting image to output file...")

image.save(OUT_PATH)

print("Finished.")
print("")
print("Chunk size:", BYTE_CHUNK_SIZE)
print("Base image:", IMG_PATH)
print("File path:", FILE_PATH)
print("Output image:", OUT_PATH)