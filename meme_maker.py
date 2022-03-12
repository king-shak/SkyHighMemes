from PIL import Image, ImageDraw, ImageFont
import textwrap
from string import ascii_letters
import requests
import os

# attempts to download file from given URL
# returns the name it downloaded it as, 
# returns None if it failed to download
def downloadImgFromURL(imageURL):
    try:
        filename = imageURL.split('/')[-1]
        r = requests.get(imageURL, allow_redirects=True)
        open(filename, 'wb').write(r.content)
        return filename
    except:
        return None

# helper function for addTextToImage
def getTextBoxHeight(width, height, textX, textY, text, font, lineSpacing):
    textImage = Image.new('RGBA', (width, height), color=(255, 255, 255))
    drawnImg = ImageDraw.Draw(textImage)
    bb = drawnImg.textbbox((textX, textY), text=text, font=font, spacing=lineSpacing)
    x1, y1, x2, y2 = bb
    return y2 - y1, y1

# returns a (list of) object(s) that represents an image, and a frame duration for gifs
def addTextToImage(imageName, text):
    # open image and get size
    try:
        img = Image.open(imageName)
    except: #non-image
        return None, 0
    width, height = img.size
    
    # set font size, and then get total length of string/font in pixels to wrap the text
    fontSize = int(height * 0.06)
    if fontSize < 20:
        fontSize = 20
    font = ImageFont.truetype("fonts/MICROSS.ttf",size=fontSize)
    avgCharWidth = sum(font.getsize(char)[0] for char in text) / len(text)
    maxCharsInLine = int(width / avgCharWidth) - 1 # -1 to account for horizontal padding
    wrappedText = textwrap.fill(text=text, width=maxCharsInLine)
    lineSpacing = fontSize / 10

    # get height of entire text entry in order to have an appropriately sized background
    textX, textY = width * 0.05, height * 0.025
    totalTextHeight, upperPadding = getTextBoxHeight(width, height, textX, textY, wrappedText, font, lineSpacing)

    # check for gif, in case multiple frames/images need to be modified
    imageList = list()
    imageFrames = 1
    if img.format == "GIF":
        imageFrames = img.n_frames

    #apply the image and text to a white background, including gifs
    newHeight = int(height + totalTextHeight + (2 * upperPadding))
    for frame in range(imageFrames):
        canvasImage = Image.new('RGBA', (width, newHeight), color=(255, 255, 255))
        img.seek(frame)
        canvasImage.paste(img, (0, int((newHeight - height))))
        drawnImg = ImageDraw.Draw(canvasImage)
        drawnImg.text((textX, textY), text=wrappedText, font=font, spacing=lineSpacing, fill=(0, 0, 0))
        imageList.append(canvasImage)
    # for drawing with an outline, but can make it harder to read for smaller pictures
    # drawnImg.text((textX, textY), text=wrappedText, font=font, spacing=lineSpacing,
    #                         stroke_width=round(fontSize/12), stroke_fill=(0, 0, 0), 
    #                         fill=(255, 255, 255))
    
    try:
        duration = img.info["duration"]
        return imageList, duration
    except:
        return imageList, 0

#usage example:
# imageURL = "https://cdn.discordapp.com/attachments/828120665135251462/951620334371618846/wakeup_slap.gif"
# imageName = downloadImgFromURL(imageURL)
# if imageName is not None:
#     meme, duration = addTextToImage(imageName, "TEXT TEXT TEXT TEXT TEXT TEXT TEXT TEXT TEXT TEXT TEXT TEXT TEXT TEXT")
#     if meme is not None:
#         if len(meme) == 1: #Non-GIF
#             meme[0].save(imageName, lossless=True)
#         else: #GIF
#             meme[0].save(imageName, save_all=True, append_images=meme[1:], loop=0, duration=duration)
#         # it could/would then be uploaded to S3 on this line
#     else:
#         print("Provided file/url was not a valid image")
# else:
#     print("Provided file/url isn't downloadable")
#
# # Afterwards, delete its local copy (whether it was actually an image or not)
# if os.path.exists(imageName):
#     os.remove(imageName)