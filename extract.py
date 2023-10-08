from PIL import Image

class ImageBytesIterator():
    def __init__(self, path: str) -> None:
        self.image = Image.open(path)
        self.maxX, self.maxY = self.image.size
        self.maxBand = 3

        self.currentBand = 0
        self.currentX = 0
        self.currentY = 0

    def __iter__(self):
        return self

    def __next__(self):
        if self.currentY >= self.maxY:
            raise StopIteration

        pixel = self.image.getpixel((self.currentX, self.currentY))
        channel = pixel[self.currentBand]

        self._nextChannel()
        return channel

    def _nextChannel(self):
        self.currentBand += 1

        if self.currentBand >= self.maxBand:
            self.currentBand = 0
            self.currentX += 1

        if self.currentX >= self.maxX:
            self.currentX = 0
            self.currentY += 1

class BitArray:
    def __init__(self, byteChunkSize: int) -> None:
        if 8 % byteChunkSize != 0:
            raise ValueError("byteChunkSize must be a divisor of 8")

        self.array = bytearray()
        self.bytePosition = 0
        self.currentByte = 0
        
        self.byteChunkSize = byteChunkSize
        self.byteTrimmer = 2 ** byteChunkSize - 1
    
    def append(self, value: int):
        value &= self.byteTrimmer # on ne garde que les derniers bits
        offset = 8 - self.bytePosition - self.byteChunkSize
        value <<= offset # on décale la valeur
        self.currentByte += value
        self._nextChunk()
    
    def _nextChunk(self):
        self.bytePosition += self.byteChunkSize
        if self.bytePosition == 8:
            self.array.append(self.currentByte)
            self.currentByte = 0
            self.bytePosition = 0
        elif self.bytePosition > 8:
            raise ValueError("Erreur :'(")
        
    def lenghInBytes(self):
        return len(self.array)
    
    def getBytesArray(self):
        return bytearray(self.array) # on retourne un clone de l'array

def printProgress(bits: BitArray, bytesCount: int):
    decodedBytes = bits.lenghInBytes()
    progress = round(100 * decodedBytes / bytesCount)
    
    prefix = "\033[1A\x1b[2k"
    print(f"{prefix}Decoded {progress}% of bytes ({decodedBytes} / {bytesCount})")

def readBytes(imageBytes: ImageBytesIterator, chunkSize: int, bytesCount: int):
    bits = BitArray(chunkSize)

    # un nombre binaire composé de <chunkSize> 1
    # Exemple: si chunkSize = 4, alors byteTrimmer = 0b1111
    byteTrimmer = 2 ** chunkSize - 1

    print("") # on imprime une ligne vide pour que les appels à printProgress() puissent réécrire par dessus

    i = 0
    for byte in imageBytes:
        # Affiche régulèrement la proression du décodage
        i += 1
        if i == 100000:
            i = 0
            printProgress(bits, bytesCount)

        # On extrait les derniers bits et on les ajoute à notre liste de bits
        decodedValue = byte & byteTrimmer
        bits.append(decodedValue)

        if bits.lenghInBytes() == bytesCount: # s'execute quand on a décodé le bon nombres de bytes
            printProgress(bits, bytesCount)
            return bits.getBytesArray()
        
    # Si la boucle for se termine, c'est qu'il n'y a plus de pixels et qu'il n'y a plus 
    # d'informations à décoder. Cela ne devrait pas arriver normalement.
    raise ValueError("Out of pixels.")

def decode(imagePath: str, chunkSize = 4):
    imageBytes = ImageBytesIterator(imagePath)

    # On décode les 4 premiers bytes du message, qui représentent la taille du fichier à décoder
    print("Reading file size...")
    sizeBytes = readBytes(imageBytes, chunkSize, 4)
    fileSize = int.from_bytes(sizeBytes, 'big') # Ceci est la taille du fichier à décoder

    # On décode le reste du message, de longueur fileSize
    print("Reading file...")
    fileBytes = readBytes(imageBytes, chunkSize, fileSize)
    return fileBytes

IMG_PATH = "./files/encoded/out.png"
OUT_PATH = "./files/extracted/out.png"
BYTE_CHUNK_SIZE = 4

decodedFileBytes = decode(IMG_PATH, BYTE_CHUNK_SIZE)

print("Decoding done ! Writing results to output file...")

with open(OUT_PATH, "wb") as file:
    file.write(decodedFileBytes)

print("Finished.")
print("")
print("Chunk size:", BYTE_CHUNK_SIZE)
print("Source image:", IMG_PATH)
print("Output file:", OUT_PATH)