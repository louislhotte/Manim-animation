import gzip
import matplotlib.pyplot as plt

f = gzip.open('./MNIST/train-images-idx3-ubyte.gz','r')

image_size = 28
num_images = 5

import numpy as np
f.read(16)
buf = f.read(image_size * image_size * num_images)
data = np.frombuffer(buf, dtype=np.uint8).astype(np.float32)
data = data.reshape(num_images, image_size, image_size, 1)

image = np.asarray(data[1]).squeeze()
plt.imsave('image.png', image, cmap='gray')
plt.imshow(image, cmap='gray')
plt.show()