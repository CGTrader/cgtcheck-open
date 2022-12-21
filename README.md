# CGTcheck

CGTrader is proud to introduce one of its major features - CGTchecks.

The `cgtcheck` package automates the process of checking the technical quality and specific requirements of Real-Time 3D assets, both individually and at scale.

It is used in many CGTrader's products, including [3D Marketplace](https://www.cgtrader.com/?utm_source=github&utm_medium=pr&utm_campaign=CGTchecks), [Modelry.ai](https://www.modelry.ai/?utm_source=github&utm_medium=pr&utm_campaign=CGTchecks) and [Kodama](https://wildcat.cgtrader.com/kodama?utm_source=github&utm_medium=pr&utm_campaign=CGTchecks).
It allows to validate high number of models in a fraction of the time in comparison to manual reviews - resulting in consistent and accurate results at a faster pace.
Thanks to `cgtcheck`, 3D artists, Technical Artists and Pipeline Developers can enjoy increased efficiency, reduced costs, and high quality modeling results across use cases. `cgtcheck` settings can be customized based on customer needs. Change the parameters from project to project to ensure the best possible outcome.

## **!!!WARNING!!!**: ***This project's structure is likely to change in its upcoming iterations.***


CGTcheck is open-source, but the workflow for contributing to this project is not ready yet. We plan to start taking contributions in the near future. Meanwhile, we welcome bug reports and feature requests as issues.

### Requirements:
CGTcheck works with Blender from version 2.93 upward

CGTcheck requires ImageMagick for the wand package.
It can be obtained from here:
<https://imagemagick.org/script/download.php>

Or you can get it from this direct link to the ImageMagick setup exe:
<https://imagemagick.org/archive/binaries/ImageMagick-7.1.0-45-Q16-HDRI-x64-dll.exe>


### Example run (CLI):
```
blender -b -P example.py
```

### Example run from within Blender:
```python
import cgtcheck
from cgtcheck.blender import all_checks  # MAKE NOTE! This is necessary for all Blender checks to be loaded


checks_spec = {
    'triangleMaxCount': {
        'enabled': True,
        'type': 'error',
        'parameters': {
            'triMaxCount': 1
        }
    }
}

runner = cgtcheck.runners.CheckRunner(
    checks_spec=checks_spec, checks_data={}
)
runner.runall()
reports = runner.format_reports()

print(reports)
```
Output:
```
[
    {
        'message': 'Fully faceted objects',
        'identifier': 'facetedGeometry',
        'msg_type': 'warning',
        'items': [
            {
                'message': 'Object "{item}" is fully faceted',
                'item': 'Cube',
                'expected': False,
                'found': True
            }
        ]
    },
    {
        'message': 'Scene triangle count exceeded',
        'identifier': 'triangleMaxCount',
        'msg_type': 'error',
        'items': [
            {
                'message': '{item} triangle count of {found} exceeds the maximum allowed: {expected}',
                'item': 'Model',
                'expected': 1,
                'found': 12
            }
        ]
    }
]
```

The output contains fully-faceted objects that Blender has 1 of by default (the Blender Cube).
Reason for this is - the fully-faceted objects check is enabled by default. See `cgtcheck/metadata.py` for the default settings.

Moreover, since we set the max triangle count to 1, it found an error - 12 triangles in the scene - the amount the Blender Cube has.

The full list of available checks and their specifications can be found here: <https://github.com/CGTrader/cgtcheck-open/wiki/Checks>

### Along with the checks, we also provided automated tests to verify their expected behavior.

### Run provided blender and generic tests:

```
blender -b -P launcher_blender.py -- -ta -s ../../blender ../../generic
```
Note: this comman should be run from the `\cgtcheck-open\cgtcheck\blender\tests` directory. 

### Requirements for tests:
If you want to use our tests for CGTcheck you need to install the `pytest` and `pytest-mock` package.
It can be obtained from the oficiall (PyPI) repository.


