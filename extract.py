import os
from PIL import Image
from typing import Generator

def imageBytesGenerator(path: str) -> Generator[int, None, None]:
    image = Image.open(path)
    width, height = image.size

    for y in range(height):
        for x in range(width):
            pixel = image.getpixel((x, y))
            for c in range(3):
                yield pixel[c]
    
def bitArray(byteChunkSize: int):
    if 8 % byteChunkSize != 0:
        raise ValueError("byteChunkSize must be a divisor of 8")

    array = bytearray()
    trimmer = 2 ** byteChunkSize - 1

    while True:
        byte = 0
        for bytePosition in range(0, 8, byteChunkSize):
            # on envoie la longueur actuelle de l'array à titre informatif, 
            # et on accepte la nouvelle valeur à ajouter à l'array
            value = yield len(array)

            # Si None est recu, c'est un message signifiant qu'on
            # ne souhaite plus modifier l'array et qu'on peut le renvoyer
            if value == None:
                yield array
                return

            value &= trimmer # on ne garde que les derniers bits
            offset = 8 - bytePosition - byteChunkSize
            value <<= offset # on décale la valeur
            byte += value

        array.append(byte)

def printProgress(decodedBytes: int, total: int):
    progress = round(100 * decodedBytes / total)
    
    prefix = "\033[1A\x1b[2k" # Ce préfixe permet de réécrire par dessus la dernière ligne printée
    print(f"{prefix}Decoded {progress}% of bytes ({decodedBytes} / {total})")

def readBytes(imageBytes: Generator[int, None, None], chunkSize: int, bytesCount: int):
    bits = bitArray(chunkSize)
    bits.send(None) # Il faut initier le générateur une première fois avant de lui envoyer des valeurs

    # un nombre binaire composé de <chunkSize> 1
    # Exemple: si chunkSize = 4, alors byteTrimmer = 0b1111
    byteTrimmer = 2 ** chunkSize - 1

    print("") # on imprime une ligne vide pour que les appels à printProgress() puissent réécrire par dessus

    bitArrayLength = 0
    i = 0
    for byte in imageBytes:
        # Affiche régulèrement la proression du décodage
        i += 1
        if i == 100000:
            i = 0
            printProgress(bitArrayLength, bytesCount)

        # On extrait les derniers bits et on les ajoute à notre liste de bits
        decodedValue = byte & byteTrimmer
        bitArrayLength = bits.send(decodedValue)

        if bitArrayLength == bytesCount: # s'execute quand on a décodé le bon nombres de bytes
            printProgress(bitArrayLength, bytesCount)
            # Envoyer None inique au générateur qu'on a fini l'array et qu'il peut le renvoyer
            return bits.send(None)
        
    # Si la boucle for se termine, c'est qu'il n'y a plus de pixels et qu'il n'y a plus 
    # d'informations à décoder. Cela ne devrait pas arriver normalement.
    raise ValueError("Out of pixels.")

def decode(imagePath: str, chunkSize = 4):
    imageBytes = imageBytesGenerator(imagePath)

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

os.makedirs(os.path.dirname(OUT_PATH), exist_ok = True) # on s'assure que les dossiers parents existent
with open(OUT_PATH, "wb") as file:
    file.write(decodedFileBytes)

print("Finished.")
print("")
print("Chunk size:", BYTE_CHUNK_SIZE)
print("Source image:", IMG_PATH)
print("Output file:", OUT_PATH)