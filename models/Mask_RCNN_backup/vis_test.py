import os
import sys
import glob
import tqdm

ROOT_DIR = os.path.abspath('../../')
#import Mask RCNN
sys.path.append(ROOT_DIR)
from mrcnn.config import Config
from mrcnn import utils
import mrcnn.model as modellib
from mrcnn import visualize

from callbacks import getCallbacks
from params import getParams

import numpy as np
import nibabel as nib
from medpy.io import load
import skimage.color
import skimage.io as io
#Get argument from command line
# parser = argparse.ArgumentParser()
# parser.add_argument('--exp', required=True,
#     help='Experiments name, to save weights and logs')

# args = parser.parse_args()
# exp_name = args.exp

#get parameters
# params = getParams(exp_name)

class BrainSegConfig(Config):
    name = 'MRI'
    GPU_COUNT = 1
    IMAGES_PER_GPU = 8

    BACKBONE = 'resnet50'

    NUM_CLASSES = 1 + 1 #background + 1 shape

    IMAGE_MIN_DIM = 256
    IMAGE_MAX_DIM = 256

    #check if 1 or 2
    MAX_GT_INSTANCES = 1

    DETECTION_MAX_INSTANCES = 1

    #mejorar
    STEPS_PER_EPOCH = 202
    TRAIN_ROIS_PER_IMAGE = 32
    MAX_GT_INSTANCES = 1
    DETECTION_MAX_INSTANCES = 3
    DETECTION_MIN_CONFIDENCE = 0.8
    DETECTION_NMS_THRESHOLD = 0.2

class BrainDataset(utils.Dataset):
    """
    Reads the dataset images and masks, and prepares them
    for the model
    """
    # values must be between 0 and 255
    def __normalize0_255(self, img_slice):
        rows, cols = img_slice.shape
        new_img = np.zeros((rows, cols))
        max_val = np.max(img_slice)

        for i in range(rows):
            for j in range(rows):
                new_img[i,j] = int((
                    float(img_slice[i,j])/float(max_val))
                    * 255)
        return new_img

    def load_brain_data(self, images_dir, masks_dir):
        self.add_class('MRI', 1, 'brain')

        image_glob = sorted(glob.glob(images_dir))
        mask_glob = sorted(glob.glob(masks_dir))
        img_id = 0
        for i in tqdm.trange(len(image_glob), desc='loading data'):
            img_path = image_glob[i]
            mask_path = mask_glob[i]

            img_slices = nib.load(image_glob[i])
            mask_slices = nib.load(mask_glob[i])
            img_slices = img_slices.get_fdata()
            mask_slices = mask_slices.get_fdata()

            for j in range(img_slices.shape[-1]):
                img = np.array(img_slices[:,:,j])
                mask = np.array(mask_slices[:,:,j])

                # skip images that are not 256x256
                if img.shape[0] != 256 or img.shape[1] != 256:
                    break

                # Normalize image so its between 0-255
                new_img = self.__normalize0_255(img)
                new_img = skimage.color.gray2rgb(new_img)

                # img = new_img[..., np.newaxis]
                mask = mask[..., np.newaxis]
                mask = np.array(mask, dtype=np.uint16) * 255

                new_img = np.array(new_img, dtype=np.uint16)

                self.add_image('MRI',
                        image_id=img_id,
                        path=img_path,
                        mask_path=mask_path,
                        image=new_img,
                        mask=mask,
                        width=256,
                        height=256)

                img_id += 1

    def load_image(self, image_id):
        return self.image_info[image_id]['image']

    def load_mask(self, image_id):
        mask = self.image_info[image_id]['mask']
        return mask, np.ones([1]).astype(np.int32)

    def image_reference(self, image_id):
        """Return the shapes data of the image."""
        return self.image_info[image_id]


config = BrainSegConfig()

dataset_train = BrainDataset()
dataset_train.load_brain_data('../../data/train/axial_only/vis_img/*','../../data/train/axial_only/vis_mask/*')
dataset_train.prepare()

for i in range(len(dataset_train.image_ids)):
    image = dataset_train.load_image(i)
    mask, _ = dataset_train.load_mask(i)

    save_path = '../../data/vis/'

    print(image.shape)
    print(type(image))
    print(mask.shape)
    print(type(mask))
    image = image[:,:,0]
    print(image.shape)
    io.imsave(os.path.join(save_path,"%d_img.png"%i), image)
    io.imsave(os.path.join(save_path,"%d_msk.png"%i), np.squeeze(mask))
