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


from __future__ import (division, print_function, absolute_import, unicode_literals)

"""
Contains descriptions of currently known checks
and their default parameters
"""

from copy import deepcopy


class CheckDescription(object):

    params = {
        'enabled': False,
        'type': 'warning',
        'parameters': {},
        'error_description_url': 'https://docs.google.com/document/d/1N4HwA8qOzjymjmaFa_lqkbUKjWZ6UdE5zDmPmLYnrCE',  # noqa E501
    }
    processes = set()  # type: set[str]  # which processes implement this check

    def __init__(
        self,
        msg='',
        item_msg='{item}',
        params=None,
        processes=None,
        check_description='',
        check_title=''

    ):
        # type: (str, str|dict, dict, tuple|set|list, str, str) -> None

        self.msg = msg  # user-facing failure message
        self.item_msg = item_msg
        if params is not None:
            self.params = deepcopy(self.params)
            self.params.update(params)
        if processes is not None:
            self.processes = set(processes)
        self.check_description = check_description
        self.check_title = check_title


checks = {
    'noHardEdges': CheckDescription(
        msg='Objects containing hard edges',
        item_msg='Object "{item}" has hard edges',
        params={
            'enabled': False,
            'error_description_url': 'https://coda.io/d/_deDXEa_PrNm/Objects-containing-hard-edges_suKkw',  # noqa E501
        },
        check_title='Check open hard edges',
        check_description='Check if objects contains hard edges'
    ),
    'noNgons': CheckDescription(
        msg='Objects containing N-gons',
        item_msg='Object "{item}" contains N-gons',
        params={
            'enabled': True,
            'error_description_url': 'https://coda.io/d/_deDXEa_PrNm/Objects-containing-N-gons_su1jd',  # noqa E501
        },
        check_title='Check N-gons',
        check_description='Check if objects contains N-gons'
    ),
    'facetedGeometry': CheckDescription(
        msg='Fully faceted objects',
        item_msg='Object "{item}" is fully faceted',
        params={
            'enabled': True,
            'error_description_url': 'https://coda.io/d/_deDXEa_PrNm/Fully-faceted-objects_suOQQ',  # noqa E501
        },
        check_title='Check faceted objects',
        check_description='Check if objects are fully faceted'
    ),
    'zeroAngleFaceCorners': CheckDescription(
        msg='Objects containing faces with zero-angle corners',
        item_msg='Object "{item}" has {found} faces with zero-angle corners',
        params={
            'enabled': True,
            'error_description_url': 'https://coda.io/d/_deDXEa_PrNm/Objects-containing-faces-with-zero-angle-corners_sulwo',  # noqa E501
        },
        check_title='Check zero-angle corners',
        check_description='Check if objects have faces with zero-angle corners'
    ),
    'zeroLengthEdge': CheckDescription(
        msg='Objects containing zero-length edges',
        item_msg='Object "{item}" has {found} zero-length edges',
        params={
            'enabled': True,
            'error_description_url': 'https://coda.io/d/_deDXEa_PrNm/Objects-containing-zero-length-edges_sunGh',  # noqa E501
        },
        check_title='Check zero-length edges',
        check_description='Check if objects have zero-length edges'
    ),
    'zeroFaceArea': CheckDescription(
        msg='Objects containing zero-area faces',
        item_msg='Object "{item}" has {found} faces with zero area',
        params={
            'enabled': True,
            'error_description_url': 'https://coda.io/d/_deDXEa_PrNm/Objects-containing-zero-area-faces_su2k1',  # noqa E501
        },
        check_title='Check zero-area faces',
        check_description='Check if objects have zero-area faces'
    ),
    'texelDensity': CheckDescription(
        msg='Incorrect texel density',
        item_msg={  # message differs by type of issue
            'density': (
                'Material "{material}" on object "{item}", '
                'expected: {expected}, found: {found}'
            ),
            'contains no UVs': 'Object "{item}" has no UV channels',
        },
        params={
            'parameters': {
                'expected_density': None,
                'density_deviation': 0.1,
                'ignore_materials': []
            },
            'enabled': False,
            'error_description_url': 'https://coda.io/d/UV-s_daH2VXB72aQ/Incorrect-texel-density_suhKs#_luUaN',  # noqa E501
        },
        check_title='Check texel density',
        check_description='Check if the texel density is the expected value: {}'
    ),
    'inconsistentTexelDensity': CheckDescription(
        msg='Inconsistent texel density',
        item_msg='Expected a texel density deviation of no more than: {expected}, '
                 'found: {found} (ranges from {min_density} to {max_density})',
        params={
            'parameters': {
                'density_deviation': 0.1
            },
            'enabled': False,
            'error_description_url': 'https://coda.io/d/UV-s_daH2VXB72aQ/Inconsistent-texel-density_suZJ1#_lu1gr',  # noqa E501
        },
        check_title='Check texel density consistency',
        check_description='Check if texel density is consistent'
    ),
    'inconsistentTexResInMaterial': CheckDescription(
        msg='Inconsistent texture resolution in material',
        item_msg='Material "{material}" texture\'s "{item}" size is {found}, expected: {expected}',
        params={
            'enabled': False,
            'error_description_url': 'https://coda.io/d/_dzYX5_1odo2/Inconsistent-texture-resolution-in-material_suTyK',  # noqa E501
        },
        check_title='Check texture resolution consistency',
        check_description='Check if texture resolution is consistent'
    ),
    'singleUVChannel': CheckDescription(
        msg='Multiple or none UV channels found in objects',
        item_msg='Object "{item}" has {found} UV channels',
        params={
            'enabled': True,
            'type': 'error',
            'error_description_url': 'https://coda.io/d/UV-s_daH2VXB72aQ/Multiple-or-none-UV-channels-found-in-objects_suCYd#_lu6kx',  # noqa E501
        },
        check_title='Check amount of UV channels in objects',
        check_description='Check mesh objects for improper number of UV channels (multiple or none)'
    ),
    'topLevelZeroPosition': CheckDescription(
        msg='Pivot point location not at world origin (0, 0, 0) for top-level objects',
        item_msg="Object's \"{item}\" pivot {found} is not at origin ({expected})",
        params={
            'parameters': {
                'positionDeviation': 0.001
            },
            'enabled': False,
            'error_description_url': 'https://coda.io/d/_dagV6OMRxib/Pivot-point-location-not-at-world-origin-0-0-0-for-top-level-obj_sulv1',  # noqa E501
        },
        check_title='Check pivot point location for top-level objects',
        check_description='Check if pivot point location is at world origin (0, 0, 0) '
                          'for top-level objects'
    ),
    'centeredGeometryBoundingBox': CheckDescription(
        msg='The bounding box of the scene geometry is not correctly centered',
        params={
            'parameters': {
                'positionDeviation': [0.1, 0.1, 0.1]
            },
            'enabled': False,
            'error_description_url': 'https://coda.io/d/_dagV6OMRxib/The-bounding-box-of-the-scene-geometry-is-not-correctly-centered_suX6Q',  # noqa E501
        },
        check_title='Check bounding box of the scene geometry',
        check_description='Check if the bounding box of the scene geometry is correctly centered'
    ),
    'centeredChildPivots': CheckDescription(
        msg='Pivots are not centered in child objects',
        item_msg='Object\'s "{item}" pivot {found} is not at bounding box center: ({expected})',
        params={
            'parameters': {
                'positionDeviation': 0.001
            },
            'enabled': False,
            'error_description_url': 'https://coda.io/d/_dagV6OMRxib/Pivots-are-not-centered-in-child-objects_suk7U',  # noqa E501
        },
        check_title='Check pivots position in child objects',
        check_description='Check if pivots of parent mesh objects are centered in child objects'
    ),
    'triangleMaxCount': CheckDescription(
        msg='Scene triangle count exceeded',
        item_msg='{item} triangle count of {found} exceeds the maximum allowed: {expected}',
        params={
            'parameters': {
                'triMaxCount': 90000
            },
            'enabled': False,
            'error_description_url': 'https://coda.io/d/_deDXEa_PrNm/Scene-triangle-count-exceeded_su4WZ',  # noqa E501
        },
        check_title='Check triangle count',
        check_description='Check if the number of triangles exceeds the maximum allowed value: {}'
    ),
    'indexedColors': CheckDescription(
        msg='Images with indexed colors',
        item_msg='{item} file uses indexed colors',
        params={
            'enabled': False,
            'error_description_url': 'https://coda.io/d/_dzYX5_1odo2/Images-with-indexed-colors_su18r',  # noqa E501
        },
        check_title='Check images with indexed colors',
        check_description='Check for images with indexed colors'
    ),
    'multipleFileFormats': CheckDescription(
        msg='Missing images for multiple file formats requirement',
        item_msg='{item} file is missing',
        params={
            'parameters': {
                'formats': ["jpg", "png"]
            },
            'enabled': False,
            'error_description_url': 'https://coda.io/d/_duEHdX_9u4L/Missing-images-for-multiple-file-formats-requirement_sutdh',  # noqa E501
        },
        check_title='Check multiple file formats requirement',
        check_description='Check if number of images meet multiple file format requirement, '
                          'expected formats: {}'
    ),
    'unusedTextures': CheckDescription(
        msg='Some texture files are not used',
        item_msg='Texture "{item}" could not be attached to any material',
        params={
            'parameters': {
                'formats': ['png', 'jpg', 'jpeg', 'bmp', 'tif', 'tiff', 'tga'],
            },
            'enabled': False,
            'error_description_url': 'https://coda.io/d/_duEHdX_9u4L/Some-texture-files-are-not-used_sud-S',  # noqa E501
        },
        check_title='Check unused textures',
        check_description='Check if all supplied textures are used'
    ),
    'texturelessMaterial': CheckDescription(
        msg='Found textures for materials which should not use any',
        item_msg='Material "{material}" texture "{item}"',
        params={
            'enabled': True,
            'type': 'error',
            'error_description_url': 'https://coda.io/d/_dzYX5_1odo2/Found-textures-for-materials-which-should-not-use-any_su11C',  # noqa E501
        },
        check_title='Check texture-free materials',
        check_description='Check the presence of textures for materials that should not use any'
    ),
    'textureAlphaChannel': CheckDescription(
        msg='Found textures with alpha channel',
        item_msg='texture "{item}" have alpha channel',
        params={
            'enabled': False,
            'type': 'warning',
            'parameters': {
                'color': False,
                'roughness': False,
                'metallic': False,
                'occlusion': False,
                'opacity': False,
                'normal': False,
                'emission': False
            },
            'error_description_url': 'https://coda.io/d/_dzYX5_1odo2/Found-textures-with-alpha-channel_suEOq',  # noqa E501
        },
        check_title='Check alpha channel',
        check_description='Check if source textures have alpha channel'

    ),
    'unsupportedPng': CheckDescription(
        msg='Unsupported PNG images',
        item_msg='"{filename}": "{format}"',
        params={
            'enabled': True,
            'type': 'error',
            'error_description_url': 'https://coda.io/d/_dEZZ69msO3r/Unsupported-PNG-images_sujFH',  # noqa E501
        },
        check_title='Check unsupported PNG images',
        check_description='Check for unsupported PNGs image types'
    ),
    'arithmeticJpegs': CheckDescription(
        msg='Arithmetic coded JPEG images',
        item_msg='Texture "{item}"',
        params={
            'enabled': True,
            'type': 'error',
            'error_description_url': 'https://coda.io/d/_dEZZ69msO3r/Arithmetic-coded-JPEG-images_sufc_',  # noqa E501
        },
        check_title='Check arithmetic coded JPEG images',
        check_description='Check if arithmetic coded is used for JPEG images'
    ),
    'resolutionOrmMismatch': CheckDescription(
        msg="Occlusion, Metallic and Roughness textures resolutions don't match",
        item_msg='{item}, resolution "{resolution}"',
        params={
            'enabled': True,
            'type': 'error',
            'error_description_url': 'https://coda.io/d/_dzYX5_1odo2/Occlusion-Metallic-and-Roughness-textures-resolutions-dont-match_suYSD',  # noqa E501
        },
        check_title='Check Occlusion, Metallic and Roughness textures resolutions',
        check_description='Check if Opacity, Roughness and Metallic maps are same resolution'
    ),
    'resolutionsColorOpacityMismatch': CheckDescription(
        msg="BaseColor and Opacity textures resolutions don't match",
        item_msg='{item}, resolution "{resolution}"',
        params={
            'enabled': True,
            'type': 'error',
            'error_description_url': 'https://coda.io/d/_dzYX5_1odo2/BaseColor-and-Opacity-textures-resolutions-dont-match_suMS-',  # noqa E501
        },
        check_title='Check BaseColor and Opacity textures resolutions',
        check_description='Check if Color, and Opacity maps are same resolution'
    ),
    'missingRequiredTextures': CheckDescription(
        msg="Missing textures",
        item_msg='{item}',
        params={
            'enabled': True,
            'type': 'error',
            'error_description_url': 'https://coda.io/d/_duEHdX_9u4L/Missing-textures_suTyK',  # noqa E501
        },
        check_title='Check missing textures',
        check_description='Check if all defined maps are present'
    ),
    'textureAspectRatio': CheckDescription(
        msg="Wrong texture aspect ratio",
        item_msg='"{item}" aspect ratio equals "{found}", expected "{expected}"',
        params={
            'enabled': True,
            'type': 'error',
            'error_description_url': 'https://coda.io/d/_dzYX5_1odo2/Wrong-texture-aspect-ratio_su4x8',  # noqa E501
        },
        check_title='Check texture aspect ratio',
        check_description='Ratio between texture width and height, expected value: {}'
    ),
    'textureMinResolution': CheckDescription(
        msg="Texture resolution is too low",
        item_msg='For texture "{item}" resolution "{found}" is lower '
                 'than required minimum "{expected}"',
        params={
            'enabled': True,
            'type': 'error',
            'error_description_url': 'https://coda.io/d/_dzYX5_1odo2/Texture-resolution-is-too-low_suxDB',  # noqa E501
        },
        check_title='Check if texture resolution is too low',
        check_description='Check if texture resolution is not lower than the required minimum: {}'
    ),
    'textureMaxResolution': CheckDescription(
        msg="Texture resolution is too high",
        item_msg='For texture "{item}" resolution "{found}" is higher '
                 'than acceptable maximum "{expected}"',
        params={
            'enabled': True,
            'type': 'error',
            'error_description_url': 'https://coda.io/d/_dzYX5_1odo2/Texture-resolution-is-too-high_suuez',  # noqa E501
        },
        check_title='Check if texture resolution is too high',
        check_description='Check if texture resolution is not bigger than the acceptable maximum: '
                          '{}'
    ),
    'unsupportedBmpCompression': CheckDescription(
        msg="Textures with unsupported BMP compression",
        item_msg='"{item}"',
        params={
            'enabled': True,
            'type': 'error',
            'error_description_url': 'https://coda.io/d/_dzYX5_1odo2/Textures-with-unsupported-BMP-compression_su3kL',  # noqa E501
        },
        check_title='Check BMP compression',
        check_description='Check if BMP texture compression is supported'
    ),
    'embeddedTexturesFbx': CheckDescription(
        msg='FBX file contains embedded textures',
        item_msg='"{item}"',
        params={
            'enabled': True,
            'type': 'error',
            'error_description_url': 'https://coda.io/d/_dEZZ69msO3r/FBX-file-contains-embedded-textures_suTyK',  # noqa E501
        },
        check_title='Check embedded textures',
        check_description='Check if objects contains embedded textures'
    ),
    'multiMaterial': CheckDescription(
        msg='Geometry have more than one material assigned',
        item_msg='"{item}"',
        params={
            'enabled': False,
            'type': 'error',
            'error_description_url': 'https://coda.io/d/_dzYX5_1odo2/Geometry-have-more-than-one-material-assigned_suF7c',  # noqa E501
        },
        check_title='Check assigned material',
        check_description='Check if more than one material is assigned to the geometry'
    ),
    'textureResolutionNotPowerOf2': CheckDescription(
        msg='Texture resolution is not a power of 2',
        item_msg='Texture "{item}" resolution {found} '
                 'is not a power of 2, expected a resolution like: {expected}, etc.',
        params={
            'enabled': False,
            'type': 'error',
            'error_description_url': 'https://coda.io/d/_dzYX5_1odo2/Texture-resolution-is-not-a-power-of-2_suSJG',  # noqa E501
        },
        check_title='Check texture resolution',
        check_description='Check if texture resolution is a power of 2'
    ),
    'noTransparentMeshes': CheckDescription(
        msg='Objects containing transparent materials',
        item_msg='Object "{item}" has transparent material(s): {materials}',
        params={
            'enabled': False,
            'type': 'error',
            'error_description_url': 'https://coda.io/d/_dzYX5_1odo2/Objects-containing-transparent-materials_suyGk',  # noqa E501
        },
        check_title='Check transparent materials',
        check_description='Check if objects have transparent material(s)'
    ),
    'noUvTiling': CheckDescription(
        msg='UV tiling found in objects',
        item_msg='Object "{item}" has UVs outside of 0 to 1 range in UV layer(s): {uv_layers}',
        params={
            'enabled': False,
            'type': 'error',
            'error_description_url': 'https://coda.io/d/UV-s_daH2VXB72aQ/UV-tiling-found-in-objects_suvLP#_luehD',  # noqa E501
        },
        check_title='Check UV tiling',
        check_description='Check if objects have UVs outside of 0 to 1 range'
    ),
    'dccResetTransforms': CheckDescription(
        msg='Objects have non-reset transforms',
        item_msg='{item} is {transformedKindsText}',
        params={
            'parameters': {
                'position': False,
                'rotation': True,
                'scale': True,
                'floatTolerance': 0.001,
                'allowInstances': False,
                'xAxisRotation': 0,
                'yAxisRotation': 0,
                'zAxisRotation': 0
            },
            'enabled': False,
            'error_description_url': 'https://coda.io/d/_dagV6OMRxib/Objects-have-non-reset-transforms_su2nl',  # noqa E501
        },
        check_title='Check objects transforms',
        check_description='Check if transforms are in expected values: {}'
    ),
    'dccObjectTypes': CheckDescription(
        msg='Scene contains forbidden object types',
        item_msg='{item} ({type})',
        params={
            'parameters': {
                'forbidMesh': False,
                'forbidNull': False,
                'forbidCamera': False,
                'forbidLight': False,
            },
            'enabled': False,
            'error_description_url': 'https://coda.io/d/_dagV6OMRxib/FBX-file-contains-forbidden-object-types_suIN_',  # noqa E501
        },
        check_title='Check type of objects present in the scene',
        check_description='Chek if scene contains forbidden object types: {}'
    ),
    'dccObjectNames': CheckDescription(
        msg='Objects found which do not meet naming requirements',
        item_msg='{type}: Expected: {expected}, found: {found}',
        params={
            'parameters': {
                'parsedVars': {
                    'uid': '(.+)',
                },
                'mesh': '.+',
                'empty': '.+'
            },
            'enabled': False,
            'error_description_url': 'https://coda.io/d/_dd09l-FaVix/Objects-found-which-do-not-meet-naming-requirements_suTyK',  # noqa E501
        },
        check_title='Check objects names',
        check_description='Check whether objects names match the requirements'
    ),
    'dccMaterialNames': CheckDescription(
        msg='Materials found which do not meet naming requirements',
        item_msg='Expected: {expected}, found: {found}',
        params={
            'regex': '.+',
            'parameters': {
                'parsedVars': {
                    'uid': '(.+)',
                    'object': '(.+)',
                },
            },
            'enabled': False,
            'error_description_url': 'https://coda.io/d/_dd09l-FaVix/Materials-found-which-do-not-meet-naming-requirements_suB94',  # noqa E501
        },
        check_title='Check material names',
        check_description='Check whether material names match the requirements'
    ),
    'dccTrianglesRatio': CheckDescription(
        msg='Triangle ratio requirements is not fulfilled',
        item_msg='Triangle ratio {found} for models in scene is {comparator} than the threshold:'
                 ' {expected}',
        params={
            'threshold': '0.15',
            'comparator': '>',
            'enabled': False,
            'error_description_url': 'https://coda.io/d/_deDXEa_PrNm/Triangle-ratio-requirements-is-not-fulfilled_su0jd',  # noqa E501
        },
        check_title='Check triangle ratio',
        check_description='Check if triangles-to-all-polygons ratio for models in scene is {} '
                          'than the threshold {}'
    ),
    'objectByMaterialTypeCount': CheckDescription(
        msg='count of objects for each material type (opaque, blend, clip)',
        item_msg='{found} {object_type} objects found in scene that is not '
                 '"{comparator}" the acceptable: {expected}',
        processes=('FbxChecks',),
        params={
            'enabled': False,
            'parameters': {
                'opaque_type_objects': {
                    'count': 1,
                    'comparator': '>=',
                },
                'blend_type_objects': {
                    'count': 1,
                    'comparator': '>=',
                },
                'clip_type_objects': {
                    'count': 1,
                    'comparator': '>=',
                },
            },
            'error_description_url': 'https://coda.io/d/_dagV6OMRxib/count-of-objects-for-each-material-type-opaque-blend-clip_su-rp',  # noqa E501
        },
        check_title='Check material types (BLEND, OPAQUE, CLIP)',
        check_description='Check amount of objects with material types, expected: {}'
    ),
    'flippedUv': CheckDescription(
        msg='Flipped UV found in objects',
        item_msg='Object "{item}" has flipped UVs in UV layer(s): {uv_layers}',
        params={
            'enabled': False,
            'type': 'warning',
            'error_description_url': 'https://coda.io/d/UV-s_daH2VXB72aQ/Flipped-UV-found-in-objects_suANl#_ludZa',  # noqa E501
        },
        check_title='Check flipped UVs',
        check_description='Check mesh objects for flipped (mirrored) UVs'
    ),
    'overlappedUvPerObject': CheckDescription(
        msg='Found overlapped UV',
        item_msg='Objects {item} has overlapped UVs {msg_type} {uv_layers}',
        params={
            'enabled': False,
            'type': 'warning',
            'error_description_url': 'https://coda.io/d/UV-s_daH2VXB72aQ/Found-overlapped-UV_sub2J#_lu7mN',  # noqa E501
        },
        check_title='Check overlapped UVs per object',
        check_description='Check mesh objects for overlapped UVs per object'
    ),
    'overlappedUvPerModel': CheckDescription(
        msg='Found overlapped UV',
        item_msg='Model {item} has overlapped UVs {msg_type} {uv_layers}',
        params={
            'enabled': False,
            'type': 'warning',
            'error_description_url': 'https://coda.io/d/UV-s_daH2VXB72aQ/Found-overlapped-UV_sub2J#_lu7mN',  # noqa E501
        },
        check_title='Check overlapped UVs per model',
        check_description='Check mesh objects for overlapped UVs between them all'
    ),
    'overlappedUvPerMaterial': CheckDescription(
        msg='Found overlapped UV',
        item_msg='Materials {item} has overlapped UVs {msg_type} {uv_layers}',
        params={
            'enabled': False,
            'type': 'warning',
            'error_description_url': 'https://coda.io/d/UV-s_daH2VXB72aQ/Found-overlapped-UV_sub2J#_lu7mN',  # noqa E501
        },
        check_title='Check overlapped UVs per material',
        check_description='Check mesh objects of the same material for overlapped UVs'
    ),
    'overlappedUvPerUVIsland': CheckDescription(
        msg='Found overlapped UV',
        item_msg='Objects {item} has UV island with overlapped UVs {msg_type} {uv_layers}',
        processes=('FbxToGltf',),
        params={
            'enabled': False,
            'type': 'warning',
            'error_description_url': ''  # update when official documentation is prepared
        },
        check_title='Check overlapped UVs per UV island',
        check_description='Check if UV island in mesh objects has overlapped UVs'
    ),
    'openEdges': CheckDescription(
        msg='Object contains open edges',
        item_msg='Object "{item}" contains open edges',
        params={
            'enabled': False,
            'type': 'warning',
            'error_description_url': 'https://coda.io/d/_deDXEa_PrNm/Object-contains-open-edges_suoo3',  # noqa E501
        },
        check_title='Check open edges',
        check_description='Check if objects contains open edges'
    ),
    'nonManifoldVertices': CheckDescription(
        msg='Object contains non-manifold vertices',
        item_msg='Object "{item}" contains non-manifold vertices',
        params={
            'enabled': False,
            'type': 'warning',
            'error_description_url': 'https://coda.io/d/_deDXEa_PrNm/Object-contains-non-manifold-vertices_su82r',  # noqa E501
        },
        check_title='Check non-manifold vertices',
        check_description='Check if objects contains non-manifold vertices'
    ),
    'connectedTextures': CheckDescription(
        msg='Material does not meet connected textures requirements',
        item_msg={  # message differs by type of issue
            'missing': 'Material "{item}" is missing textures for slots: {missing}',
            'forbidden': 'Material "{item}" is using textures at forbidden slots: {forbidden}',
        },
        params={
            'enabled': False,
            'type': 'warning',
            'parameters': {
                'required': ['base_color', 'roughness', 'metallic'],
                'forbidden': [],
            },
            'error_description_url': 'https://coda.io/d/_dzYX5_1odo2/Material-does-not-meet-connected-textures-requirements_suEAy',  # noqa E501
        },
        check_title='Check material connected textures',
        check_description='Check if material meet connected textures requirements'
    ),
    'potentialTextures': CheckDescription(
        msg='Required texture files were not found',
        item_msg='No potential "{type}" texture file found for material "{item}"',
        params={
            'enabled': False,
            'type': 'warning',
            'parameters': {
                'patterns': {
                    'A': {
                        "input_files": {
                            "color": "(?i)^(?:{infilename})?{sep}*{matid}{sep}*(?:(?:base)?{sep}?color|diffuse|albedo)\\.\\w+$",  # noqa E501
                            "normal": "(?i)^(?:{infilename})?{sep}*{matid}{sep}*norm(?:al)?\\.\\w+$",  # noqa E501
                            "opacity": "(?i)^(?:{infilename})?{sep}*{matid}{sep}*(?:opacity|opague|transp(?:arency)?)\\.\\w+$",  # noqa E501
                            "metallic": "(?i)^(?:{infilename})?{sep}*{matid}{sep}*metal(?:ness|ic|lic)?\\.\\w+$",  # noqa E501
                            "occlusion": "(?i)^(?:{infilename})?{sep}*{matid}{sep}*(?:ao|(?:ambient(?:{sep})?|occlusion)|occlude)\\.\\w+$",  # noqa E501
                            "roughness": "(?i)^(?:{infilename})?{sep}*{matid}{sep}*rough(?:ness)?\\.\\w+$",  # noqa
                            "specular": "(?i)^(?:{infilename})?{sep}*{matid}{sep}*(?:spec(?:ular(?:ity)?)?|refl(?:ective|ection|ectivity)?)\\.\\w+$",  # noqa E501
                            "emissive": "(?i)^(?:{infilename})?{sep}*{matid}{sep}*emis(?:sive|sion)?\\.\\w+$",  # noqa E501
                        },
                        "parsed_variables": {
                            "matid": "(\\w+)",
                        },
                        "predefined_variables": {
                            "sep": "(?:_+|\\.|\\s+|-|\\|)"
                        }
                    },
                    'B': {
                        "input_files": {
                            "color": "(?i).*{matid}{sep}*(?:c|d)\\.\\w+$",
                            "normal": "(?i).*{matid}{sep}*(?:n|b)\\.\\w+$",
                            "opacity": "(?i).*{matid}{sep}*(?:o|t)\\.\\w+$",
                            "metallic": "(?i).*{matid}{sep}*m\\.\\w+$",
                            "occlusion": "(?i).*{matid}{sep}*ao\\.\\w+$",
                            "roughness": "(?i).*{matid}{sep}*r\\.\\w+$",
                            "specular": "(?i).*{matid}{sep}*s\\.\\w+$",
                            "emissive": "(?i).*{matid}{sep}*e\\.\\w+$",
                        },
                        "parsed_variables": {
                            "matid": "(\\w+)",
                        },
                        "predefined_variables": {
                            "sep": "(?:_+|\\.|\\s+|-|\\|)"
                        }
                    },
                    'C': {
                        "input_files": {
                            "color": "(?i)^(?:{infilename})?{sep}*(?:(?:base)?{sep}?color|diffuse|albedo)\\.\\w+$",  # noqa E501
                            "normal": "(?i)^(?:{infilename})?{sep}*norm(?:al)?\\.\\w+$",
                            "opacity": "(?i)^(?:{infilename})?{sep}*(?:opacity|opague|transp(?:arency)?|alpha)\\.\\w+$",  # noqa E501
                            "metallic": "(?i)^(?:{infilename})?{sep}*metal(?:ness|ic|lic)?\\.\\w+$",  # noqa E501
                            "occlusion": "(?i)^(?:{infilename})?{sep}*(?:ao|(?:ambient(?:{sep})?|occlusion)|occlude)\\.\\w+$",  # noqa E501
                            "roughness": "(?i)^(?:{infilename})?{sep}*rough(?:ness)?\\.\\w+$",  # noqa
                            "specular": "(?i)^(?:{infilename})?{sep}*(?:spec(?:ular(?:ity)?)?|refl(?:ective|ection|ectivity)?)\\.\\w+$\\.\\w+$",  # noqa E501
                            "emissive": "(?i)^(?:{infilename})?{sep}*emis(?:sive|sion)?\\.\\w+$",  # noqa E501
                        },
                        "parsed_variables": {
                            "matid": "(\\w+)",
                        },
                        "predefined_variables": {
                            "sep": "[_\\-\\.\\s\\|]"
                        }
                    },
                    'D': {
                        "input_files": {
                            "color": "(?i).*(?:{infilename})?{sep}*(?:(?:base)?{sep}?color|diffuse|albedo)\\.\\w+$",  # noqa E501
                            "normal": "(?i).*(?:{infilename})?{sep}*norm(?:al)?\\.\\w+$",
                            "opacity": "(?i).*(?:{infilename})?{sep}*(?:opacity|opague|transp(?:arency)?|alpha)\\.\\w+$",  # noqa E501
                            "metallic": "(?i).*(?:{infilename})?{sep}*metal(?:ness|ic|lic)?\\.\\w+$",  # noqa E501
                            "occlusion": "(?i).*(?:{infilename})?{sep}*(?:ao|(?:ambient(?:{sep})?|occlusion)|occlude)\\.\\w+$",  # noqa E501
                            "roughness": "(?i).*(?:{infilename})?{sep}*rough(?:ness)?\\.\\w+$",  # noqa
                            "specular": "(?i).*(?:{infilename})?{sep}*spec(?:ular(?:ity)?)?\\.\\w+$",  # noqa E501
                            "emissive": "(?i).*(?:{infilename})?{sep}*emis(?:sive|sion)?\\.\\w+$",  # noqa E501
                        },
                        "parsed_variables": {
                            "matid": "(\\w+)",
                        },
                        "predefined_variables": {
                            "sep": "[_\\-\\.\\s\\|]"
                        }
                    },
                    'E': {
                        "input_files": {
                            "color": "(?i).*{sep}+(?:c|d).*\\.\\w+$",
                            "normal": "(?i).*{sep}+(?:n|b).*\\.\\w+$",
                            "opacity": "(?i).*{sep}+(?:o|t|a).*\\.\\w+$",
                            "metallic": "(?i).*{sep}+m(?:tl)?.*\\.\\w+$",
                            "occlusion": "(?i).*{sep}+(?:(?:a)?o).*\\.\\w+$",
                            "roughness": "(?i).*{sep}+(?:r).*\\.\\w+$",
                            "specular": "(?i).*{sep}+s.*\\.\\w+$",
                            "emissive": "(?i).*{sep}+e.*\\.\\w+$",
                        },
                        "parsed_variables": {
                            "matid": "(\\w+)",
                        },
                        "predefined_variables": {
                            "sep": "[_\\-\\.\\s\\|]"
                        }
                    },
                    'F': {
                        "input_files": {
                            "color": "(?i).*{sep}+(?:c|d){sep}*\\w*\\.\\w+$",
                            "normal": "(?i).*{sep}+(?:n|b){sep}*\\w*\\.\\w+$",
                            "opacity": "(?i).*{sep}+(?:o|t|a){sep}*\\w*\\.\\w+$",
                            "metallic": "(?i).*{sep}+m(?:tl)?{sep}*\\w*\\.\\w+$",
                            "occlusion": "(?i).*{sep}+ao{sep}*\\w*\\.\\w+$",
                            "roughness": "(?i).*{sep}+r{sep}*\\w*\\.\\w+$",
                            "specular": "(?i).*{sep}+s{sep}*\\w*\\.\\w+$",
                            "emissive": "(?i).*{sep}+e{sep}*\\w*\\.\\w+$",
                        },
                        "parsed_variables": {
                            "matid": "(\\w+)",
                        },
                        "predefined_variables": {
                            "sep": "[_\\-\\.\\s\\|]"
                        }
                    }
                },
                'required': ['color', 'roughness', 'metallic'],
            },
            'error_description_url': 'https://coda.io/d/_duEHdX_9u4L/Required-texture-files-were-not-found_suN80',  # noqa E501
        },
        check_title='Check required texture files',
        check_description='Check if required texture files are present'
    ),
    'overlappingFaces': CheckDescription(
        msg='Object contains overlapping faces',
        item_msg='Object "{item}" contains overlapping faces with the following IDs: '
                 '{overlapping_faces}',
        params={
            'enabled': False,
            'type': 'warning',
            'error_description_url': 'https://coda.io/d/_deDXEa_PrNm/Object-contains-overlapping-faces_suWxs',  # noqa E501
        },
        check_title='Check overlapping faces',
        check_description='Check if objects contains overlapping faces'
    ),
    'displayedUnits': CheckDescription(
        msg='Unit in scene settings used to display length values is different from required unit',
        item_msg='Expected: {expected}, found: {found}',
        params={
            'enabled': False,
            'type': 'warning',
            'parameters': {'desiredUnit': 'cm'},
            'dcc': {
                'blender': {
                    'enabled': True
                }
            },
            'error_description_url': 'https://coda.io/d/_dagV6OMRxib/Unit-in-scene-settings-used-to-display-length-values-is-differen_suEpj',  # noqa E501
        },
        check_title='Check display unit scale',
        check_description='Check unit scale in scene settings used to display length '
                          'required unit: {}'
    ),
    'dccUnitScale': CheckDescription(
        msg='Unit scale in scene settings used to conversions is different from required unit',
        item_msg='Expected: {expected}, found: {found}',
        params={
            'enabled': False,
            'type': 'error',
            'parameters': {'desiredUnit': 'cm'},
            'dcc': {
                'blender': {
                    'enabled': True
                }
            },
            'error_description_url': 'https://coda.io/d/_dagV6OMRxib/Unit-scale-in-scene-settings-used-to-conversions-is-different-fr_suHjD',  # noqa E501
        },
        check_title='Check unit scale',
        check_description='Check unit scale in scene settings used to conversions required unit: {}'
    ),
    'unparseableMaterialName': CheckDescription(
        msg="Incorrect material name",
        item_msg='Expected: {expected}, found: {found}',
        params={
            'enabled': False,
            'type': 'error',
            'dcc': {
                'blender': {
                    'enabled': True
                }
            },
            'error_description_url': 'https://coda.io/d/_dd09l-FaVix/Incorrect-material-name_suUaR',  # noqa E501
        },
        check_title='Check unparseable material names',
        check_description='Check if material names are proper in context of texture specification'
    ),
    'fbxFormat': CheckDescription(
        msg="FBX format not supported",
        item_msg=(
            'Expected {expected_type}, version {expected_version_min} to {expected_version_max}; '
            'found: {found_type}, version {found_version}'
        ),
        params={
            'enabled': False,
            'type': 'error',
            'parameters': {
                'allow_binary': True,
                'allow_ascii': False,
                'version': {'min': 7100, 'max': None},
            },
            'error_description_url': '',  # update when official documentation is prepared
        },
        check_title='Check unparseable material names',
        check_description='Check if material names are proper in context of texture specification'
    ),
    'uvUnwrappedObjects': CheckDescription(
        msg='None UV channels found in objects',
        item_msg='Object "{item}" has 0 UV channels',
        params={
            'enabled': False,
            'type': 'error',
            'error_description_url': '',  # update when official documentation is prepared
        },
        check_title='Check if there is UV channel in the object',
        check_description='Check mesh objects for improper number of UV channels '
                          '(at least one required)'
    ),
    'recommendedTexturesNaming': CheckDescription(
        msg='Texture file names do not follow the recommended convention',
        item_msg='Found {found}: {item}',
        params={
            'parameters': {
                'formats': {
                    'allowed_ext': ['png', 'jpg', 'exr', 'tga', 'bmp', 'tif'],
                    'not_allowed_ext': ['gif', 'svg', 'psd',  'hdr', 'eps', 'webp'],
                },
            },
            'enabled': False,
            'type': 'warning',
            'error_description_url': '',  # update when official documentation is prepared
        },
        check_title='Check textures file names',
        check_description='Check if the texture file names follow the recommended convention'
    ),

    'consistentNaming': CheckDescription(
        msg='Naming should be consistent and use common prefix or suffix',
        item_msg='{found}: {item}',
        params={
            'enabled': False,
            'type': 'warning',
            'error_description_url': '',  # update when official documentation is prepared
        },
        check_title='Check names consistency',
        check_description='Check if the material, geometry or helpers have a common '
                          'prefix or suffix'
    )
}
