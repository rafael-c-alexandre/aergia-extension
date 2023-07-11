import torchvision.transforms.functional as TF

class FunctionalGrayscale:
    """Grayscale image"""

    def __init__(self, num_output_channels=1):
        self.num_output_channels = num_output_channels

    def __call__(self, img):
        return TF.rgb_to_grayscale(img, num_output_channels=self.num_output_channels)