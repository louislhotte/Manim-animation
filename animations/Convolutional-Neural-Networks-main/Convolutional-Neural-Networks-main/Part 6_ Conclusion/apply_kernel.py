import numpy as np
from scipy.signal import convolve2d
from PIL import Image

# Load the image and convert it to grayscale
image = Image.open("./images/face.png").convert('L')
image_array = np.array(image) / 255.

# Define a 3x3 blurring filter (kernel)
# This is a simple average filter
filter = np.array([[0, 0, 0],
                   [-1, 0, 1],
                   [0, 0, 0]]) / 9


# Apply the filter to the image
# 'boundary' defines how the array borders are handled
# 'mode' defines the size of the output array
# filtered_image_0= convolve2d(image_array[:,:,0], filter, boundary='fill', mode='same')
# filtered_image_1 = convolve2d(image_array[:,:,1], filter, boundary='fill', mode='same')
# filtered_image_2 = convolve2d(image_array[:,:,2], filter, boundary='fill', mode='same')

filtered_image = convolve2d(image_array, filter, boundary='fill', mode='same')
# filtered_image = np.stack([filtered_image_0, filtered_image_1, filtered_image_2], axis=2)


print(np.mean(filtered_image), np.max(filtered_image), np.min(filtered_image))
# Convert the result back to an image
filtered_image = Image.fromarray(np.uint8(filtered_image*255)).convert('L')

# Save or display the filtered image
filtered_image.save("./images/face_output.png")
# filtered_image.show()  # Uncomment to directly display the image
