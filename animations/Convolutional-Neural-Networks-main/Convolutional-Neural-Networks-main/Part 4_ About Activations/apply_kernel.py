import numpy as np
from scipy.signal import convolve2d
from PIL import Image



np.random.seed(0)

def relu(x):
    return np.maximum(0, x)

def sigmoid(x):
    return 1 / (1 + np.exp(-x))

def tanh(x):
    return np.tanh(x)

def leaky_relu(x, alpha=0.3):
    return np.maximum(alpha * x, x)

def elu(x, alpha=1):
    return np.where(x > 0, x, alpha * (np.exp(x) - 1))

# Load the image and convert it to grayscale
image = Image.open("./images/0_mnist.png").convert('L')
image_array = np.array(image) / 255.

# Define a 3x3 blurring filter (kernel)
# This is a simple average filter
filter = np.random.rand(3, 3)

# Apply the filter to the image
# 'boundary' defines how the array borders are handled
# 'mode' defines the size of the output array
# filtered_image_0 = convolve2d(image_array[:,:,0], filter, boundary='fill', mode='same')
# filtered_image_1 = convolve2d(image_array[:,:,1], filter, boundary='fill', mode='same')
# filtered_image_2 = convolve2d(image_array[:,:,2], filter, boundary='fill', mode='same')

filtered_image = convolve2d(image_array, filter, boundary='fill', mode='same')
# filtered_image = np.stack([filtered_image_0, filtered_image_1, filtered_image_2], axis=2)


filtered_image = elu(filtered_image)

# Convert the result back to an image
filtered_image = Image.fromarray(np.uint8(filtered_image*255)).convert('L')

# Save or display the filtered image
filtered_image.save("./images/mnist_elu.png")
# filtered_image.show()  # Uncomment to directly display the image
