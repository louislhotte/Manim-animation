import numpy as np
from scipy.signal import convolve2d
from PIL import Image

# Load the image and convert it to grayscale
image1 = Image.open("./images/mnist_conv1_2.png").convert('L')
image_array1 = np.array(image1) / 255.
image2 = Image.open("./images/mnist_conv2_2.png").convert('L')
image_array2 = np.array(image2) / 255.
image3 = Image.open("./images/mnist_conv3_2.png").convert('L')
image_array3 = np.array(image3) / 255.

res = (image_array1 + image_array2 + image_array3) / 3.0
res = Image.fromarray(np.uint8(res*255)).convert('L')
res.save("./images/mnist_sum.png")

