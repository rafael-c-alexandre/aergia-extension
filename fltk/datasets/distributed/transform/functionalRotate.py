import torchvision.transforms.functional as TF

class FunctionalRotate:
    """Rotate by the given degrees"""

    def __init__(self, angle):
        self.angle = angle

    def __call__(self, img):
        return TF.rotate(img, self.angle)