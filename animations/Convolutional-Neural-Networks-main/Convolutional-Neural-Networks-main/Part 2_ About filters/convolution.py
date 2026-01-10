from typing import Any, Tuple
import numpy as np
import torchvision
from PIL import Image
import torch.nn as nn
from torchvision import transforms as transforms


def convImage(img_path: str) -> Tuple[Any, Any, Any]:
    img = readImage(img_path)
    conv = nn.Conv2d(1, 16, 3)
    transform = transforms.ToTensor()
    img_tensor = transform(img)
    img_tensor = img_tensor.unsqueeze(0)
    img_conv = conv(img_tensor)
    return img_tensor.numpy()[0], img_conv.detach().numpy(), conv


def main() -> None:
    img_path = "images/2_mnist.png"
    convImage(img_path)



def readImage(img_path: str) -> Any:
    """read an image from image_path

    Args:
        img_path (str): image path

    Returns:
        Any: numpy read image
    """
    img = Image.open(img_path)
    return np.array(img)


def writeImage(
    img: Any,
    img_path: str,
) -> None:
    """write an image to img_path

    Args:
        img (Any): numpy image
        img_path (str): image path
    """
    pil_img = Image.fromarray(img)
    pil_img.save(img_path)

if __name__ == "__main__":
    main()