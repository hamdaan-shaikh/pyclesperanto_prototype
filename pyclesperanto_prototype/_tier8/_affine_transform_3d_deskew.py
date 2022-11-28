from typing import Union

from .._tier0 import plugin_function
from .._tier0 import Image
from .._tier0 import push
from .._tier0 import create, create_like, create_none
from ._AffineTransform3D import AffineTransform3D
from skimage.transform import AffineTransform
from ._affine_transform import _determine_translation_and_bounding_box
import numpy as np


@plugin_function(output_creator=create_none)
def affine_transform_3d_deskew(source: Image, destination: Image = None,
                               transform: Union[np.ndarray, AffineTransform3D, AffineTransform] = None,
                               deskewing_angle_in_degrees: float = 30,
                               voxel_size_x: float = 0.1449922,
                               voxel_size_y: float = 0.1449922,
                               voxel_size_z: float = 0.3,
                               skew_direction: str = "Y",
                               flip_z: bool = False,
                               auto_size: bool = False) -> Image:
    """
    Applies an affine transform to deskew an image. 
    Uses orthogonal interpolation

    Parameters
    ----------
    source : Image
        image to be transformed
    destination : Image, optional
        image where the transformed image should be written to
    transform : 4x4 numpy array or AffineTransform3D object or skimage.transform.AffineTransform object or str, optional
        transform matrix or object or string describing the transformation
    deskewing_angle_in_degrees: float, optional
        Oblique plane or deskewing acquisition angle
    voxel_size_x: float, optional
        Pixel size in X axis in microns
    voxel_size_y: float, optional
        Pixel size in Y axis in microns
    voxel_size_z: float, optional
        Step size between image planes along coverslip in microns; Voxel size in Z in microns
    skew_direction: str, optional
        Direction of skew, dependent on microscope configuration
    flip_z: bool, optional
        Flip in Z axis, if coverslip rotation required.
    auto_size:bool, optional
        If true, modifies the transform and the destination image size will be determined automatically, depending on the provided transform.
        the transform might be modified so that all voxels of the result image have positions x>=0, y>=0, z>=0 and sit
        tight to the coordinate origin. No voxels will cropped, the result image will fit in the returned destination.
        Hence, the applied transform may have an additional translation vector that was not explicitly provided. This
        also means that any given translation vector will be neglected.
        If false, the destination image will have the same size as the input image.
        Note: The value of auto-size is ignored if: destination is not None or transform is not an instance of
        AffineTransform3D.

    Returns
    -------
    destination

    """
    import numpy as np
    from .._tier0 import execute
    from .._tier0 import create
    from .._tier1 import copy_slice

    assert len(
        source.shape) == 3, f"Image needs to be 3D, got shape of {len(source.shape)}"

    # handle output creation
    if auto_size and isinstance(transform, AffineTransform3D):
        new_size, transform, _ = _determine_translation_and_bounding_box(
            source, transform)
    if destination is None:
        if auto_size and isinstance(transform, AffineTransform3D):
            # This modifies the given transform
            destination = create(new_size)
        else:
            destination = create_like(source)

    if isinstance(transform, str):
        transform = AffineTransform3D(transform, source)

    # we invert the transform because we go from the target image to the source image to read pixels
    if isinstance(transform, AffineTransform3D):
        transform_matrix = np.asarray(transform.copy().inverse())
    elif isinstance(transform, AffineTransform):
        # Question: Don't we have to invert this one as well? haesleinhuepf
        matrix = np.asarray(transform.params)
        matrix = np.asarray([
            [matrix[0, 0], matrix[0, 1], 0, matrix[0, 2]],
            [matrix[1, 0], matrix[1, 1], 0, matrix[1, 2]],
            [0, 0, 1, 0],
            [matrix[2, 0], matrix[2, 1], 0, matrix[2, 2]]
        ])
        transform_matrix = np.linalg.inv(matrix)
    else:
        transform_matrix = np.linalg.inv(transform)

    # precalculate these functions that are dependent on deskewing angle
    tantheta = np.float32(np.tan(deskewing_angle_in_degrees * np.pi/180))
    sintheta = np.float32(np.sin(deskewing_angle_in_degrees * np.pi/180))
    costheta = np.float32(np.cos(deskewing_angle_in_degrees * np.pi/180))

    gpu_transform_matrix = push(transform_matrix)

    if skew_direction.upper() == "Y":
        kernel_suffix = '_deskew_y'
        # change step size from physical space (nm) to camera space (pixels)
        pixel_step = np.float32(voxel_size_z/voxel_size_y)
    elif skew_direction.upper() == "X":
        kernel_suffix = '_deskew_x'
        # change step size from physical space (nm) to camera space (pixels)
        pixel_step = np.float32(voxel_size_z/voxel_size_x)

    # pass the shape of the final image, pixel step and precalculated trig

    parameters = {
        "input": source,
        "output": destination,
        "mat": gpu_transform_matrix,
        "rotate": int(1 if flip_z else 0),
        "deskewed_Nx": destination.shape[2],
        "deskewed_Ny": destination.shape[1],
        "deskewed_Nz": destination.shape[0],
        "pixel_step": pixel_step,
        "tantheta": tantheta,
        "costheta": costheta,
        "sintheta": sintheta
    }

    execute(__file__, './affine_transform_' + str(len(destination.shape)) + 'd' + kernel_suffix + '_x.cl',
            'affine_transform_' + str(len(destination.shape)) + 'd' + kernel_suffix, destination.shape, parameters)

    return original_destination