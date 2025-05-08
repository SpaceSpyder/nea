from PIL import Image # pip install pillow

def cropImage(image):
    imagePath = "D:\\nea\\templates\\images\\profilePics\\" + image  # Correct path
    cropSize = 250  # Size of the square crop

    try:
        # Open the image
        im = Image.open(imagePath)

        # Get the image dimensions
        width, height = im.size

        # Check which dimension is smaller and scale it to fit the crop box
        if width < height:
            # Scale width to 250px, keep the aspect ratio for height
            newWidth = cropSize
            newHeight = int((height / width) * cropSize)
        else:
            # Scale height to 250px, keep the aspect ratio for width
            newHeight = cropSize
            newWidth = int((width / height) * cropSize)

        # Resize the image with the calculated dimensions
        im = im.resize((newWidth, newHeight))

        # Get the new dimensions after resizing
        width, height = im.size

        # Calculate the coordinates for cropping the center of the image to 250x250
        left = (width - cropSize) // 2
        top = (height - cropSize) // 2
        right = left + cropSize
        bottom = top + cropSize
        cropBox = (left, top, right, bottom)

        # Crop the image to fit the 250x250 box
        croppedImage = im.crop(cropBox)

        # Save the cropped image back to the original location (overwriting it)
        croppedImage.save(imagePath)

    except Exception as e:
        print(f"An error occurred: {e}")
