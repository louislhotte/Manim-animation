import numpy as np
from scipy.signal import convolve2d
from PIL import Image
import torch

# Load the image and convert it to grayscale
image = Image.open("./images/0_mnist.png").convert('L')
image_array = np.array(image) / 255.


# Apply average pooling to the image
pool_size = 2
pooled_image = torch.nn.functional.avg_pool2d(torch.tensor(image_array).unsqueeze(0).unsqueeze(0), pool_size)

# Convert the pooled image back to numpy array
pooled_image_array = pooled_image.squeeze().numpy()

# Display the pooled image
pooled_image = Image.fromarray((pooled_image_array * 255).astype(np.uint8))
# Save the pooled image
pooled_image.save("./images/0_mnist_pooled.png")