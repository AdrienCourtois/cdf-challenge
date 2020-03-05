from torch.utils.data import Dataset
import pandas as pd
import os
from PIL import Image
import torch
from torchvision import transforms
from PIL import ImageFilter
import numpy as np

def gaussian_blur(x):
    if np.random.rand() <= 0.1:
        img = x.filter(ImageFilter.GaussianBlur(radius=10*np.random.rand()))
        
        return img
    else:
        return x


class ImageDataset(Dataset):
    # Custom Dataset for the challenge #

    def __init__(self, img_dir, label_dir, transform=True, height=210, width=210, post_transform=None):
        """
        Args:
            img_dir (string): Directory with all the images.
            label_dir (string): Directory with all the labels.
            transform (boolean, optional): Should the transform be applied?
            height (int, optional): Desired height of the images
            width (int, optional): Desired width of the images
            post_transform (PyTorch transform): Desired transformation. Is None, the default one is applied.
        """
        self.img_dir = img_dir
        self.label_dir = label_dir
        self.transform = transform

        # Images dimension
        self.width = width
        self.height = height

        if post_transform is None:
            # Random Erasing?
            self.post_transform = transforms.Compose([
                transforms.ColorJitter(brightness=.7, contrast=.5, saturation=.5, hue=0.05),
                #gaussian_blur, <- The images are not blurry at all :p
                transforms.ToTensor(),
                transforms.Normalize(mean=[0.485, 0.456, 0.406], std=[0.229, 0.224, 0.225])
            ])
        else:
            self.post_transform = post_transform

        # Get the number of images
        self.image_names = list(filter(lambda x: ".png" in x, os.listdir(img_dir)))
        self.n_images = len(self.image_names)
    
    def F_transform(self, image, mask):
        or_width, or_height = image.size

        # Resize if too small
        if or_width < self.width or or_height < self.height:
            image = transforms.functional.resize(image, max(self.height, self.width), interpolation=3)
            or_width, or_height = image.size

        # RandomCrop
        top = np.random.randint(or_height - self.height)
        left = np.random.randint(or_width - self.width)

        image = transforms.functional.crop(image, top, left, self.height, self.width)
        mask = transforms.functional.crop(mask, top, left, self.height, self.width)

        # RandomAffine
        if np.random.rand() <= 0.5:
            angle = 0
            scale = 0.8 + 0.4 * np.random.rand()

            image = transforms.functional.affine(image, angle, (0,0), scale, 0, resample=2)
            mask = transforms.functional.affine(mask, angle, (0,0), scale, 0, resample=2)

        # Horizontal flip
        if np.random.rand() <= 0.5:
            image = transforms.functional.hflip(image)
            mask = transforms.functional.hflip(mask)

        # Post transformation
        image = self.post_transform(image)
        mask = transforms.ToTensor()(mask)

        # Readjust the mask
        mask[mask > 0.5] = 1
        mask[mask <= 0.5] = 0

        return image, mask

    def __len__(self):
        return self.n_images

    def __getitem__(self, idx):
        img_name = os.path.join(self.img_dir, self.image_names[idx])
        image = Image.open(img_name)

        mask_name = "segmentation_" + "_".join(self.image_names[idx].split("_")[1:])
        mask_name = os.path.join(self.label_dir, mask_name)
        mask = Image.open(mask_name)

        if self.transform:
            image, mask = self.F_transform(image, mask)
        else:
            image = transforms.ToTensor()(image)
            mask = transforms.ToTensor()(mask)

        return image, mask