import json, sys
from pathlib import Path
from solweig_light.geometry.recipe import numerical_geometry_recipe
prep = Path(sys.argv[1])
paths = {name: prep / name / f'{name}_0_0.tif' for name in ('Building_DSM', 'Trees', 'DEM')}
recipe = numerical_geometry_recipe(paths, 2)
Path(sys.argv[2]).write_text(json.dumps(recipe.identity, sort_keys=True, indent=1, default=str))
print('digest', recipe.digest)
