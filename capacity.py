from PIL import Image
import sys

if len(sys.argv) != 2 and len(sys.argv) != 3:
    print("Correct syntax:")
    print(f"{sys.argv[0]} <path_to_image> [chunk_size]")
    exit()

imagePath = sys.argv[1]

if len(sys.argv) == 3:
    try:
        byteChunkSize = int(sys.argv[2])
    except ValueError:
        print(f'chunk_size must be a numerical value, but found "{sys.argv[2]}"')
        exit()
else:
    byteChunkSize = 4

if byteChunkSize < 1:
    print("chunk_size must be a positive integer different from 0, but found", byteChunkSize)
    exit()
if 8 % byteChunkSize != 0:
    print("chunk_size must be a divisor of 8, but found", byteChunkSize)
    exit()

try:
    image = Image.open(imagePath)
except FileNotFoundError:
    print("File not found:", imagePath)
    exit()

width, height = image.size
pixelAmount = width * height
channelAmount = pixelAmount * 3
channelPerByte = 8 / byteChunkSize
capacity = int(channelAmount // channelPerByte)

if capacity > 1000000:
    literal = f"{capacity / 1000000:.3f} Mo"
elif capacity > 1000:
    literal = f"{capacity / 1000:.3f} ko"
else:
    literal = f"{capacity} bytes"

YELLOW = "\u001b[33m"
WHITE = "\u001b[37m"
print(f"This image has a capacity of {YELLOW}{literal}{WHITE} with a chunk size of {YELLOW}{byteChunkSize}{WHITE}")