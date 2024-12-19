from PIL import Image

def crop_and_show_image(image):
    image_path = "D:\\nea\\templates\\images\\profilePics\\" + image  # Correct path
    crop_size = 250  # Size of the square crop

    try:
        # Open the image
        im = Image.open(image_path)

        # Get the image dimensions
        width, height = im.size

        # Check which dimension is smaller and scale it to fit the crop box
        if width < height:
            # Scale width to 250px, keep the aspect ratio for height
            new_width = crop_size
            new_height = int((height / width) * crop_size)
        else:
            # Scale height to 250px, keep the aspect ratio for width
            new_height = crop_size
            new_width = int((width / height) * crop_size)

        # Resize the image with the calculated dimensions
        im = im.resize((new_width, new_height))

        # Get the new dimensions after resizing
        width, height = im.size

        # Calculate the coordinates for cropping the center of the image to 250x250
        left = (width - crop_size) // 2
        top = (height - crop_size) // 2
        right = left + crop_size
        bottom = top + crop_size
        crop_box = (left, top, right, bottom)

        # Crop the image to fit the 250x250 box
        cropped_image = im.crop(crop_box)

        # Save the cropped image back to the original location (overwriting it)
        cropped_image.save(image_path)

    except Exception as e:
        print(f"An error occurred: {e}")
