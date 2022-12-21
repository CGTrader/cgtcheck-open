# This code is provided to you by UAB CGTrader, code 302935696, address - Antakalnio str. 17,
# Vilnius, Lithuania, the company registered with the Register of Legal Entities of the Republic
# of Lithuania (CGTrader).
#
# Copyright (C) 2022  CGTrader.
#
# This program is provided to you as free software: you can redistribute it and/or modify it under
# the terms of the GNU General Public License as published by the Free Software Foundation, either
# version 3 of the License, or (at your option) any later version. It is distributed in the hope
# that it will be useful, but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the GNU General Public License for more
# details. You should have received a copy of the GNU General Public License along with this
# program. If not, see https://www.gnu.org/licenses/.


import logging
import os
import re
from math import isclose
from pathlib import Path
from typing import Tuple, List, Dict, Union, Iterator

from PIL import Image
from wand.image import Image as WImage

from cgtcheck.common import Check, Properties
from cgtcheck.runners import CheckRunner


logger = logging.getLogger(__name__)


@CheckRunner.register
class CheckAspectRatio(Check, Properties):
    """
    Check if texture aspect ratio match requirements.
    """

    key = 'textureAspectRatio'
    version = (0, 1, 0)

    def run(self) -> List[Tuple[str, float, float]]:
        """
        Return a list of maps with wrong aspect ratio.
        """
        tex_paths = self.collector.mat_texture_path
        tex_spec = self.collector.tex_spec
        spec_aspect = tex_spec.get('technical_requirements', {}).get('aspect')

        self.failures = []

        if spec_aspect and tex_paths:
            tex_in_spec = {tex_path for mat in tex_paths.values() for tex_path in mat.values()}
            tex_in_spec = list(tex_in_spec)
            tex_in_spec.sort()

            for tex_path in tex_in_spec:
                tex_path_ = Path(tex_path)
                if not tex_path_.exists():
                    logger.warning('Not found on disk, skipping: %s', tex_path)
                    continue
                wrong_aspect = self._check_aspect_ratio(tex_path_, spec_aspect)
                if wrong_aspect:
                    self.failures.append((tex_path_.name, wrong_aspect, spec_aspect))

        return self.failures

    def format_failure(self, failure: Tuple) -> Dict[str, str]:
        """
        Formats metadata dictionary for a single failure, intended to be used in Wildcat report.
        """
        filename, found_aspect, expected_aspect = failure
        return {
            'message': self.metadata.item_msg,
            'item': filename,
            'expected': expected_aspect,
            'found': found_aspect,
        }

    def format_properties(self) -> Dict[str, List[Dict]]:
        """
        Format a property report.
        """
        return {
            'texture': self.properties
        }

    def _check_aspect_ratio(self, path: Union[str, Path], requirement: float) -> Union[float, None]:
        """
        Check if image matches the aspect ratio.

        Arguments:
            path {str | Path} -- path to single texture image file
            requirement {float} -- requirement from specification
        """
        with Image.open(path) as img:
            width, height = img.size
            aspect = width / height
            self.properties.append(
                {
                    'name': os.path.basename(path),
                    'aspect': aspect
                }
            )
            if isclose(aspect, requirement) is False:
                return aspect
            return None

    def get_description(self) -> str:
        """
        Return check description for check.
        """
        tex_spec = self.collector.tex_spec
        spec_aspect = tex_spec.get('technical_requirements', {}).get('aspect')
        return self.metadata.check_description.format(str(spec_aspect))


@CheckRunner.register
class CheckIndexedColors(Check, Properties):
    """
    Check mesh objects for images with indexed colors.
    """

    key = 'indexedColors'
    version = (0, 1, 0)

    def run(self) -> List[str]:
        """
        Return a list of images with indexed colors
        """
        tex_paths = self.collector.mat_texture_path

        for textures in tex_paths.values():
            for texture in textures.values():
                if not os.path.exists(texture):
                    logger.warning('Not found on disk, skipping: %s', texture)
                    continue
                with Image.open(texture) as img:
                    self.properties.append(
                        {
                            'name': os.path.basename(img.filename),
                            'mode': img.mode
                        }
                    )
                    if img.getpalette():
                        self.failures.append(os.path.basename(img.filename))

        return self.failures

    def list_failures(self) -> List[str]:
        """
        Returns list of found issues for this check
        """
        return ["{}".format(image_name) for image_name in self.failures]

    def format_failure(self, failure: str) -> Dict[str, Union[str, int]]:
        """
        Formats metadata dictionary for a single failure, intended to be used in Wildcat report.
        """
        return {
            'message': self.metadata.item_msg,
            'item': failure,
            'expected': False,
            'found': True,
        }

    def format_properties(self) -> Dict[str, List[Dict]]:
        """
        Format a property report.
        """
        return {
            'texture': self.properties
        }


class TextureResolutionBase(Check, Properties):
    """
    Check if texture resolution is within the limit.
    """

    def __init__(self, *args, **kwargs) -> None:
        super().__init__(*args, **kwargs)
        self.failures: Dict[str, List] = {}

    def run(self) -> Dict[str, List]:
        """
        Returns a list of maps with resolution not within the limit
        (either higher or lower depending on derived class implementation).
        """
        tex_paths = self.collector.mat_texture_path
        tex_spec = self.collector.tex_spec
        resolution_limit = self.get_resolution_limit(tex_spec)
        min_size_for_plain = tex_spec.get('technical_requirements', {}).get('minSizePlain', [])
        max_size_for_plain = tex_spec.get('technical_requirements', {}).get('maxSizePlain', [])
        other_size_for_plain = min_size_for_plain or max_size_for_plain

        if resolution_limit and tex_paths:
            tex_in_spec = {tex_path for mat in tex_paths.values() for tex_path in mat.values()}

            sorted_tex_paths = sorted(tex_in_spec, key=str.lower)
            for tex_path in sorted_tex_paths:
                if not os.path.exists(tex_path):
                    logger.warning('Not found on disk, skipping: %s', tex_path)
                    continue
                if other_size_for_plain:
                    resolution_limit = self.get_resolution_limit(
                        tex_spec=tex_spec, tex_path=tex_path
                    )
                above_max_size = self.check_texture_size(tex_path, resolution_limit)

                if above_max_size:
                    self.failures[os.path.basename(tex_path)] = [above_max_size, resolution_limit]

        return self.failures

    def get_failures(self) -> Tuple[str, str, str]:
        """
        Return an iterator of failures.
        """
        return ((filename, size[0], size[1]) for filename, size in self.failures.items())

    def format_failure(self, failure: Tuple) -> Dict[str, str]:
        """
        Formats metadata dictionary for a single failure, intended to be used in Wildcat report.
        """
        filename, found, expected = failure
        return {
            'message': self.metadata.item_msg,
            'item': filename,
            'found': f"{found[0]}x{found[1]}",
            'expected': f"{expected[0]}x{expected[1]}",
        }

    def format_properties(self) -> Dict[str, List[Dict]]:
        """
        Format a property report.
        """
        return {
            'texture': self.properties
        }

    def get_resolution_limit(
        self, tex_spec: Dict[str, Dict],
        tex_path: Union[Path, str] = None
    ) -> List[int]:
        """
        When implemented should return resolution limits obtained from texture specification.
        """
        raise NotImplementedError('This method should be overriden')

    def check_texture_size(self, path: str, requirement: List[int]) -> Tuple[int, int]:
        """
        When implemented checks if image is within the limits.

        Arguments:
            path: path to single texture image file.
            requirement: list with width and height limit obtained from specification.

        Returns
            Width and height if they are not within the limit, None otherwise.
        """
        raise NotImplementedError('This method should be overriden')

    def get_description(self) -> str:
        """
        Return check description for check.
        """
        tex_spec = self.collector.tex_spec
        resolution_limit = self.get_resolution_limit(tex_spec)
        if len(resolution_limit) == 2:
            return self.metadata.check_description.format(
                str(f'{resolution_limit[0]}x{resolution_limit[1]}')
            )
        return ''


@CheckRunner.register
class CheckMinResolution(TextureResolutionBase):
    """
    Check if texture resolution is not smaller than the required minimum.
    """

    key = 'textureMinResolution'
    version = (0, 1, 0)

    def get_resolution_limit(
        self,
        tex_spec: Dict[str, Dict],
        tex_path: Union[Path, str] = None
    ) -> List[int]:
        """
        Returns min width and height of texture obtained from texture specification.
        """
        if tex_path:
            with Image.open(tex_path) as img:
                is_plain = len(img.getcolors()) == 1
            if is_plain:
                return tex_spec.get('technical_requirements', {}).get('minSizePlain', [])
            return tex_spec.get('technical_requirements', {}).get('minSize', [])
        return tex_spec.get('technical_requirements', {}).get('minSize', [])

    def check_texture_size(self, path: str, requirement: List[int]) -> Tuple[int, int]:
        """
        Check if image is smaller than the required minimum.

        Arguments:
            path: path to single texture image file
            requirement: minimum resolution from specification

        Returns:
            Width and height if they are not within the limit, None otherwise.
        """

        with Image.open(path) as img:
            width, height = img.size
            min_width, min_height = requirement
            self.properties.append(
                {
                    'name': os.path.basename(path),
                    'resolution': [width, height]
                }
            )
            if (width < min_width) or (height < min_height):
                return width, height
            return tuple()


@CheckRunner.register
class CheckMaxResolution(TextureResolutionBase):
    """
    Check if texture resolution is not bigger than the allowed maximum.
    """

    key = 'textureMaxResolution'
    version = (0, 1, 0)

    def get_resolution_limit(
        self, tex_spec: Dict[str, Dict], tex_path: Union[Path, str] = None
    ) -> List[int]:
        """
        Returns max width and height of texture obtained from texture specification.
        """
        if tex_path:
            with Image.open(tex_path) as img:
                is_plain = len(img.getcolors()) == 1
            if is_plain:
                return tex_spec.get('technical_requirements', {}).get('maxSizePlain', [])
            return tex_spec.get('technical_requirements', {}).get('maxSize', [])
        return tex_spec.get('technical_requirements', {}).get('maxSize', [])

    def check_texture_size(self, path: str, requirement: List[int]) -> Tuple[int, int]:
        """
        Check if image is bigger than the acceptable maximum.

        Arguments:
            path: path to single texture image file
            requirement: maximum resolution from specification

        Returns:
            Width and height if they are not within the limit, None otherwise.
        """
        with Image.open(path) as img:
            width, height = img.size
            max_width, max_height = requirement
            self.properties.append(
                {
                    'name': os.path.basename(path),
                    'resolution': [width, height]
                }
            )
            if (width > max_width) or (height > max_height):
                return width, height
            return tuple()


@CheckRunner.register
class CheckNoTexMaterial(Check, Properties):
    """
    Check if there are textures for material matching 'no-textures' regex.
    """

    key = 'texturelessMaterial'
    version = (0, 1, 0)

    def __init__(self, *args, **kwargs) -> None:
        super().__init__(*args, **kwargs)
        self.failures: Dict[str, str] = {}

    def run(self) -> Dict[str, str]:
        """
        Returns a list of textures per material that should not have any textures.
        """
        tex_paths = self.collector.mat_texture_path
        tex_spec = self.collector.tex_spec
        regexes = tex_spec.get('parsed_variables', {}).get('notex_mat', {})

        if regexes:
            self.failures = {
                matname: [os.path.basename(tex) for tex in textures.values()]
                for matname, textures in tex_paths.items()
                if re.match(regexes, matname) and textures and any(os.path.exists(tex) for tex in textures.values())  # noqa E501
            }

        self.properties = [
            {
                'regexes': regexes,
                'material': matname,
                'texture': sorted([os.path.basename(tex) for tex in textures.values()])
            }
            for matname, textures in tex_paths.items()]

        return self.failures

    def get_failures(self) -> Iterator[Tuple[str, str]]:
        """
        Returns a generator expression providing failures in form of tuples.

        For every texture associated with material that should have no textures
        a separate pair of material name and texture name is generated.
        """
        return (
            (mat, failure)
            for mat, failures in self.failures.items()
            for failure in failures
        )

    def format_failure(self, failure: Tuple) -> Dict[str, str]:
        """
        Formats metadata dictionary for a single failure, intended to be used in Wildcat report.
        """
        material, tex = failure
        return {
            'message': self.metadata.item_msg,
            'material': material,
            'item': tex,
        }

    def format_properties(self) -> Dict[str, List[Dict]]:
        """
        Format a property report.
        """
        return {
            'textureForMaterial': self.properties
        }


@CheckRunner.register
class CheckUnsupportedPNGs(Check, Properties):
    """
    Check for unsupported PNGs image types.
    """

    key = 'unsupportedPng'
    version = (0, 1, 0)

    def __init__(self, *args, **kwargs) -> None:
        super().__init__(*args, **kwargs)
        self.failures: Dict[str, str] = {}

    def run(self) -> Dict[str, str]:
        """
        Return a list of textures with unsupported PNG image types.
        """
        tex_paths = self.collector.mat_texture_path
        mode_info = {
            "1": "1-bit pixels, black and white, stored with one pixel per byte",
            "L": "8-bit pixels, black and white",
            "LA": "8-bit pixels, black and white, with alpha",
            "P": "8-bit pixels, mapped to any other mode using a color palette",
            "RGB": "3x8-bit pixels, true color",
            "RGBX": "4x8-bit pixels, true color with padding",
            "RGBA": "4x8-bit pixels, true color with transparency mask",
            "RGBa": "4x8-bit pixels, true color with pre-multiplied alpha",
            "CMYK": "4x8-bit pixels, color separation",
            "YCbCr": "3x8-bit pixels, color video format",
            "LAB": "3x8-bit pixels, the L*a*b color space",
            "HSV": "3x8-bit pixels, Hue, Saturation, Value color space",
            "I": "32-bit signed integer pixels",
            "I;16": "16-bit signed integer pixels",
            "F": "32-bit floating point pixels",
        }

        unsupported_pngs = self._check_for_unsupported_png(tex_paths.values())

        if unsupported_pngs:
            self.failures = {format(os.path.basename(img)): mode_info[mode]
                             for img, mode in unsupported_pngs.items()}

        return self.failures

    def get_failures(self) -> Tuple[str, str]:
        """
        Return an iterator of failures.
        """
        return ((filename, value) for filename, value in self.failures.items())

    def format_failure(self, failure: Tuple) -> Dict[str, str]:
        """
        Formats metadata dictionary for a single failure, intended to be used in Wildcat report.
        """
        filename, value = failure
        return {
            'message': self.metadata.item_msg,
            'filename': filename,
            'format': value,
        }

    def format_properties(self) -> Dict[str, List[Dict]]:
        """
        Format a property report.
        """
        return {
            'texture': self.properties
        }

    def _check_for_unsupported_png(self, tex_dict: Dict[str, str]) -> Dict[str, str]:
        """
        Check for unsupported PNG image types
        and collect properties
        """

        unsupported_images = {}
        for textures in tex_dict:
            for tex_path in textures.values():
                if not os.path.exists(tex_path):
                    logger.warning('Not found on disk, skipping: %s', tex_path)
                    continue
                with Image.open(tex_path) as img, WImage(filename=tex_path) as wimg:
                    if img.format == "PNG":
                        self.properties.append(
                            {
                                'name': os.path.basename(img.filename),
                                'mode': img.mode
                            }
                        )
                        if img.mode not in ["RGB", "RGBA", "P", "L"]:
                            unsupported_images[tex_path] = img.mode
                        elif wimg.depth == 16:
                            unsupported_images[
                                tex_path] = "I;16"  # PIL may have such mode

        return unsupported_images


@CheckRunner.register
class CheckArithmeticJpegs(Check, Properties):
    """
    Check for arithmetic coded jpegs.
    """

    key = 'arithmeticJpegs'
    version = (0, 1, 1)

    def run(self) -> List[str]:
        """
        Return a list of jpeg textures with arithmetic coded.
        """
        tex_paths = self.collector.mat_texture_path
        tex_in_spec = {tex_path for mat in tex_paths.values() for tex_path in mat.values()}

        self.failures = {os.path.basename(img_path) for img_path in tex_in_spec
                         if self._check_jpeg_coding(img_path) is not None}

        return self.failures

    def format_failure(self, failure: str) -> Dict[str, str]:
        """
        Formats metadata dictionary for a single failure, intended to be used in Wildcat report.
        """
        return {
            'message': self.metadata.item_msg,
            'item': failure,
        }

    def format_properties(self) -> Dict[str, List[Dict]]:
        """
        Format a property report.
        """
        return {
            'texture': self.properties
        }

    def _check_jpeg_coding(self, filepath: str) -> bool:
        """
        Collect information about jpeg coding for report properties
        and return True if jpeg is arithmetic coded.
        """
        if not os.path.exists(filepath):
            logger.warning('Not found on disk, skipping: %s', filepath)
            return False
        with WImage(filename=filepath) as wimg:
            jpeg_coding = wimg.metadata.get('jpeg:coding')
            if jpeg_coding is None and wimg.metadata.get('jpeg:arithmetic-coding') == 'true':
                jpeg_coding = 'arithmetic'
            self.properties.append(
                {
                    'name': os.path.basename(filepath),
                    'coding': jpeg_coding
                }
            )
            if jpeg_coding == 'arithmetic':
                return True


class TextureCheckMixin:
    """
    Class with methods for texture checks.
    """

    @classmethod
    def _are_images_same_size(cls, *args: List[str], default=True):
        """
        Returns whether provided images are of same dimension in terms of pixels.
        Note: returns `default` argument if insufficient number of images is supplied.
        """

        if len(args) < 2:
            return default

        if not os.path.exists(args[0]):
            logger.warning('Not found on disk, skipping: %s', args[0])
            return default

        with Image.open(args[0]) as img:
            first_size = img.size
        for img_path in args[1:]:
            if not os.path.exists(img_path):
                logger.warning('Not found on disk, skipping: %s', img_path)
                continue
            with Image.open(img_path) as img:
                if img.size != first_size:
                    return False

        return True

    @staticmethod
    def collect_texture_properties(tex_paths: Dict, texture_type: set) -> List[dict]:
        """
        Collect texture properties for selected texture types.

        Arguments:
            tex_paths: paths to all defined textures
            texture_type: texture type to be collected

        Returns:
            Dict with material name, texture name, texture type and resolution.
        """
        properties = []
        for mat, tex in tex_paths.items():
            tex_to_compare = tuple(sorted((ttype, tex[ttype]) for ttype in texture_type & set(tex)))
            for ttype, texture in tex_to_compare:
                if not os.path.exists(texture):
                    logger.warning('Not found on disk, skipping: %s', texture)
                    continue
                with Image.open(texture) as img:
                    properties.append(
                        {
                            'material': mat,
                            'type': ttype,
                            'name': os.path.basename(texture),
                            'resolution': [img.width, img.height]
                        }
                    )
        return properties

    @classmethod
    def _find_first_mismatched_textures(cls, tex_paths: List[str], texture_type: List[str]):
        """
        Returns tuple with two lists (texture name and resolutions) for first material for which
        texture resolution don't mach.
        Returns False if for every material resolution for all textures, with certain type, match
        """
        for tex in tex_paths:
            tex_to_compare = tuple(tex[ttype] for ttype in sorted(texture_type & set(tex)))
            if not cls._are_images_same_size(*tex_to_compare):
                tex_name = []
                tex_res = []
                for ele in tex_to_compare:
                    if not os.path.exists(ele):
                        logger.warning('Not found on disk, skipping: %s', ele)
                        continue
                    tex_name.append(os.path.basename(ele))
                    with Image.open(ele) as img:
                        tex_res.append(f"{img.width}x{img.height}")
                return tex_name, tex_res
        return False


@CheckRunner.register
class CheckOrmConsistentResolution(Check, Properties, TextureCheckMixin):
    """
    Check if Opacity, Roughness and Metallic maps are same resolution.
    """

    key = 'resolutionOrmMismatch'
    version = (0, 1, 2)

    def run(self) -> List:
        """
        Return list of ORM maps with resolution if are not the same resolution.
        """
        tex_paths = self.collector.mat_texture_path
        tex_type = set(('occlusion', 'roughness', 'metallic'))
        self.properties = self.collect_texture_properties(tex_paths, tex_type)

        texture_comparison = self._find_first_mismatched_textures(tex_paths.values(), tex_type)
        if texture_comparison:
            tex_name, tex_res = texture_comparison
            self.failures = list(zip(tex_name, tex_res))
            self.failures.sort()

        return self.failures

    def format_failure(self, failure: Tuple) -> Dict[str, str]:
        """
        Formats metadata dictionary for a single failure, intended to be used in Wildcat report.
        """
        filename, resolution = failure
        return {
            'message': self.metadata.item_msg,
            'item': filename,
            'resolution': resolution,
        }

    def format_properties(self) -> Dict[str, List]:
        """
        Format a property report.
        """
        return {
            'texture': self.properties
        }


@CheckRunner.register
class CheckColorOpacityConsistentResolution(Check, Properties, TextureCheckMixin):
    """
    Check if Color, and Opacity maps are same resolution.
    """

    key = 'resolutionsColorOpacityMismatch'
    version = (0, 1, 1)

    def run(self) -> List:
        """
        Return Color and Opacity maps name with resolution if are not the same resolution.
        """
        tex_paths = self.collector.mat_texture_path

        tex_type = set(('color', 'opacity'))
        self.properties = self.collect_texture_properties(tex_paths, tex_type)

        texture_comparison = self._find_first_mismatched_textures(tex_paths.values(), tex_type)

        if texture_comparison:
            tex_name, tex_res = texture_comparison
            self.failures = list(zip(tex_name, tex_res))
            self.failures.sort()

        return self.failures

    def format_failure(self, failure: Tuple) -> Dict[str, str]:
        """
        Formats metadata dictionary for a single failure, intended to be used in Wildcat report.
        """
        filename, resolution = failure
        return {
            'message': self.metadata.item_msg,
            'item': filename,
            'resolution': resolution,
        }

    def format_properties(self) -> Dict[str, List]:
        """
        Format a property report.
        """
        return {
            'texture': self.properties
        }


@CheckRunner.register
class CheckUnsupportedBmpCompression(Check, Properties):
    """
    Check if BMP texture compression is supported.
    """

    key = 'unsupportedBmpCompression'
    version = (0, 1, 0)

    def run(self) -> List[str]:
        """
        Return a list of maps with unsupported compression.
        """
        tex_paths = self.collector.mat_texture_path
        tex_in_spec = sorted(tex_path for mat in tex_paths.values() for tex_path in mat.values())

        for tex in tex_in_spec:
            if not os.path.exists(tex):
                logger.warning('Not found on disk, skipping: %s', tex)
                continue
            try:
                with Image.open(tex) as img:
                    img.info
                    self.properties.append(
                        {
                            'name': os.path.basename(tex),
                            'compression': img.info.get('compression', ())
                        }
                    )

            except OSError as exc:
                if exc.args[0].startswith('Unsupported BMP compression'):
                    self.failures.append(os.path.basename(tex))
                    self.properties.append(
                        {
                            'name': os.path.basename(tex),
                            'compression': 'Unsupported BMP compression'
                        }
                    )

        return self.failures

    def format_failure(self, failure: str) -> Dict[str, str]:
        """
        Formats metadata dictionary for a single failure, intended to be used in Wildcat report.
        """
        return {
            'message': self.metadata.item_msg,
            'item': failure,
        }

    def format_properties(self):
        # type: () -> dict[str, str|bool]|None
        """
        Format a property report to be .
        """
        return {
            'textures': self.properties
        }


@CheckRunner.register
class CheckTextureAlphaChannel(Check, Properties):
    """
    Check if source textures have alpha channel.
    """

    key = 'textureAlphaChannel'
    version = (0, 1, 1)
    forbidden_modes = ['RGBA', 'LA', 'PA', 'RGBa', 'La']    # image modes with alpha

    def run(self) -> List:
        """
        Return list of texture image if have alpha channel.
        Collect information filename & image mode per texture image for properties report.
        """
        tex_paths = self.collector.mat_texture_path
        textures_to_check = self.params.get('parameters', {})

        for mat, textures in tex_paths.items():
            for slot, texture in textures.items():
                if not os.path.exists(texture):
                    logger.warning('Not found on disk, skipping: %s', texture)
                    continue
                texture_name = os.path.basename(texture)
                with Image.open(texture) as img:
                    self.properties.append(
                        {
                            'name': texture_name,
                            'mode': img.mode
                        }
                    )
                    if img.mode in self.forbidden_modes and textures_to_check.get(slot, False):
                        self.failures.append(texture_name)

        return self.failures

    def format_failure(self, failure: str) -> Dict[str, str]:
        """
        Formats metadata dictionary for a single failure, intended to be used in Wildcat report.
        """
        return {
            'message': self.metadata.item_msg,
            'item': failure,
        }

    def format_properties(self) -> Dict[str, List[Dict]]:
        """
        Format a property report.
        """
        return {
            'textures': self.properties
        }
