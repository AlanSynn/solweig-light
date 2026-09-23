import json, sys
from pathlib import Path
from solweig_light.geometry.recipe import numerical_geometry_recipe
paths = {name.rsplit('.', 1)[0]: Path(sys.argv[1]) / name for name in ('Building_DSM.tif', 'Trees.tif', 'DEM.tif')}
recipe = numerical_geometry_recipe(paths, 2)
ident = recipe.identity
print(json.dumps({k: ident[k] for k in ident if k != 'inputs'}, sort_keys=True, indent=1, default=str))
print('INPUTS:', json.dumps({k: ident['inputs'][k]['sha256'] for k in ident['inputs']}, sort_keys=True, indent=1))
