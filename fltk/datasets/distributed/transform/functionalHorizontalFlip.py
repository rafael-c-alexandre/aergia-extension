import torchvision.transforms.functional as TF

class FunctionalHorizontalFlip:
    """Flip image horizontally"""

    def __call__(self, img):
        return TF.hflip(img)