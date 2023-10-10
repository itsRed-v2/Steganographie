import os
from PIL import Image
from typing import Generator

class OutOfPixelsException(Exception):
    pass

def imageBytesEditorGenerator(path: str):
    image = Image.open(path)
    width, height = image.size

    for y in range(height):
        for x in range(width):
            pixel = list(image.getpixel((x, y)))

            finish = False
            for i in range(3):
                pixel[i] = yield pixel[i]
                finish = yield
                if finish:
                    break
            
            image.putpixel((x, y), tuple(pixel))

            if finish:
                yield image
                return
    
    # Si la boucle for se termine, c'est qu'on est à court de pixels
    raise OutOfPixelsException
    
def bitGenerator(bytesList: bytes, byteChunkSize: int) -> Generator[tuple[int | None, int], None, None]:
    if 8 % byteChunkSize != 0:
        raise ValueError("byteChunkSize must be a divisor of 8")
    
    trimmer = 2 ** byteChunkSize - 1

    for i in range(len(bytesList)):
        for bytePosition in range(0, 8, byteChunkSize):
            b = bytesList[i]
            b >>= (8 - bytePosition - byteChunkSize)
            b &= trimmer
            yield b, i
    
    yield None, len(bytesList)

def printProgress(progress: int, length: int):
    percentage = round(100 * progress / length)

    prefix = "\033[1A\x1b[2k" # Ce préfixe permet de réécrire par dessus la dernière ligne printée
    print(f"{prefix}Encoded {percentage}% of bytes ({progress} / {length})")

def writeBytes(imageEditor: Generator, bytesList: bytes, chunkSize: int):
    bits = bitGenerator(bytesList, chunkSize)

    # un nombre binaire 8bits composé de 1 et se terminant par <chunkSize> 0
    # Exemple: si chunkSize = 2, alors byteTrimmer = 0b11111100
    byteTrimmer = 256 - (2 ** BYTE_CHUNK_SIZE)

    print("") # on imprime une ligne vide pour que les appels à printProgress() puissent réécrire par dessus

    progress = 0
    length = len(bytesList)

    i = 0
    while True:
        i += 1
        if i == 100000:
            i = 0
            printProgress(progress, length)

        bytePart, progress = next(bits) # la partie d'octet à ajouter
        if bytePart == None: # si tous les bits ont été encodés
            printProgress(progress, length)
            return

        colorPart = imageEditor.send(None)
        colorPart &= byteTrimmer # on enlève les derniers bits
        colorPart |= bytePart # on ajoute la partie d'octet à la valeur de la couleur
        imageEditor.send(colorPart)

def encode(imagePath: str, filePath: str, chunkSize: int):
    imageEditor = imageBytesEditorGenerator(imagePath)

    with open(filePath, "rb") as file:
        bytesToEncode = file.read()

    arraySize = len(bytesToEncode)
    # on ajoute 4 bytes au début de l'array pour indiquer la taille du fichier encodé
    bytesToEncode = arraySize.to_bytes(4, "big") + bytesToEncode

    writeBytes(imageEditor, bytesToEncode, chunkSize)
    
    # Envoyer true inique au générateur qu'on a fini de modifier l'image et qu'il peut nous la renvoyer
    return imageEditor.send(True)

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

os.makedirs(os.path.dirname(OUT_PATH), exist_ok = True) # on s'assure que les dossiers parents existent
image.save(OUT_PATH)

print("Finished.")
print("")
print("Chunk size:", BYTE_CHUNK_SIZE)
print("Base image:", IMG_PATH)
print("File path:", FILE_PATH)
print("Output image:", OUT_PATH)