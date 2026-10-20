#!/usr/bin/env python3
"""Generate an explicitly synthetic city-grid input; never the original dataset."""
from __future__ import annotations
import argparse
import hashlib
import json
from pathlib import Path
import sys


def digest(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def generate(destination, reference_scene, *, size=600, pixel_size=4., seed=20261020):
    import numpy as np
    from osgeo import gdal, osr
    gdal.UseExceptions()
    osr.UseExceptions()
    destination, reference_scene=Path(destination).resolve(),Path(reference_scene).resolve()
    if size<30 or pixel_size<=0:raise ValueError('size must be at least 30 and pixel size positive')
    destination.mkdir(parents=True,exist_ok=False)
    reference=reference_scene/'DEM.tif'
    dataset=gdal.Open(str(reference))
    projection=dataset.GetProjection()
    spatial=osr.SpatialReference(projection)
    if not spatial.IsProjected() or abs(spatial.GetLinearUnits()-1)>1e-9:
        raise ValueError('Reference scene must use a projected CRS in metres')
    transform=dataset.GetGeoTransform()
    values=dataset.ReadAsArray()
    elevation=float(np.median(values[np.isfinite(values)]))
    dataset=None
    rng=np.random.default_rng(seed)
    row,col=np.indices((size,size),dtype=np.float32)
    dem=(np.float32(elevation)+np.float32(.001)*row+np.float32(.0005)*col+
         np.float32(.2)*np.sin(row/np.float32(45))*np.cos(col/np.float32(57))).astype(np.float32)
    buildings=np.zeros_like(dem)
    landcover=np.full((size,size),5,dtype=np.float32)  # Grass.
    cell,road=30,5
    road_mask=(row.astype(np.int32)%cell<road)|(col.astype(np.int32)%cell<road)
    landcover[road_mask]=1  # Asphalt; no building/tree overlap.
    count=0
    for top in range(0,size-cell+1,cell):
        for left in range(0,size-cell+1,cell):
            height,width=rng.integers(9,20,size=2)
            y=top+road+int(rng.integers(0,cell-road-2-height+1))
            x=left+road+int(rng.integers(0,cell-road-2-width+1))
            buildings[y:y+height,x:x+width]=np.float32(rng.uniform(8,55))
            count+=1
    building_mask=buildings>0
    landcover[building_mask]=2  # Roof/building.
    trees=np.zeros_like(dem)
    tree_count=size*size//240
    planted=0
    for _ in range(tree_count*4):
        y,x=rng.integers(0,size,size=2)
        if landcover[y,x]!=5:continue
        radius=int(rng.integers(2,6))
        low_y,high_y=max(0,y-radius),min(size,y+radius+1)
        low_x,high_x=max(0,x-radius),min(size,x+radius+1)
        yy,xx=np.ogrid[low_y:high_y,low_x:high_x]
        distance=((yy-y)**2+(xx-x)**2)/float(radius*radius)
        valid=(distance<=1)&(landcover[low_y:high_y,low_x:high_x]==5)
        height=np.float32(rng.uniform(4,15))
        canopy=height*(np.float32(.65)+np.float32(.35)*np.sqrt(np.maximum(1-distance,0)).astype(np.float32))
        tile=trees[low_y:high_y,low_x:high_x]
        np.maximum(tile,np.where(valid,canopy,np.float32(0)),out=tile)
        planted+=1
        if planted>=tree_count:break
    assert not np.any((trees>0)&building_mask)
    dsm=(dem+buildings).astype(np.float32)
    output_transform=(transform[0],float(pixel_size),0.,transform[3],0.,-float(pixel_size))
    for name,array in (('Building_DSM.tif',dsm),('DEM.tif',dem),('Trees.tif',trees),('Landcover.tif',landcover)):
        output=gdal.GetDriverByName('GTiff').Create(str(destination/name),size,size,1,gdal.GDT_Float32)
        output.SetGeoTransform(output_transform)
        output.SetProjection(projection)
        output.SetMetadata({'DATASET_LABEL':'synthetic_generated_not_original','GENERATOR_SEED':str(seed)})
        output.GetRasterBand(1).WriteArray(array)
        output.FlushCache()
        output=None
    source_met=reference_scene/'met.txt'
    lines=source_met.read_text().splitlines()
    rows=[]
    first=None
    for line in lines[1:]:
        if not line.strip():continue
        columns=line.split()
        stamp=tuple(int(float(value)) for value in columns[:4])
        if first is None:first=stamp[:2]
        if stamp[:2]==first and 4<=stamp[2]<=22:rows.append((stamp,line))
    if len(rows)!=19 or [value[0][2:] for value in rows]!=[(hour,0) for hour in range(4,23)]:
        raise ValueError('Reference forcing needs hourly rows 04:00 through 22:00 on its first date')
    selected='\n'.join([lines[0],*(line for _,line in rows)])+'\n'
    (destination/'met.txt').write_text(selected)
    manifest={'schema':1,'dataset_label':'synthetic_generated_not_original',
              'warning':'Analytic generated scene; not Atlanta and not the user original dataset.',
              'generator':str(Path(__file__).resolve()),'generator_sha256':digest(__file__),
              'parameters':{'size':size,'pixel_size_metres':pixel_size,'seed':seed,'cell_pixels':cell,
                            'road_pixels':road,'building_height_range_metres':[8,55],
                            'tree_height_range_metres':[4,15]},
              'numpy':np.__version__,'gdal':gdal.VersionInfo(),'python':sys.version,
              'reference_crs_origin':{'path':str(reference),'sha256':digest(reference),
                                      'transform':transform,'projection':projection},
              'source_forcing':{'path':str(source_met),'sha256':digest(source_met)},
              'selected_forcing_sha256':digest(destination/'met.txt'),
              'selected_forcing_timestamps':[[*stamp] for stamp,_ in rows],
              'terrain_elevation_range_metres':[float(dem.min()),float(dem.max())],
              'building_count':count,'canopies_planted':planted,
              'building_pixels':int(building_mask.sum()),'tree_pixels':int((trees>0).sum()),
              'landcover_codes':{'1':'asphalt','2':'roof/building','5':'grass'},
              'files':{name:digest(destination/name) for name in ('Building_DSM.tif','DEM.tif','Trees.tif','Landcover.tif','met.txt')}}
    (destination/'synthetic_manifest.json').write_text(json.dumps(manifest,indent=2,sort_keys=True)+'\n')
    return manifest


def main(argv=None):
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output',required=True,type=Path)
    parser.add_argument('--reference-scene',type=Path,default=Path(__file__).resolve().parents[2]/'tests/reference/small_original_cpu/scene')
    parser.add_argument('--size',type=int,default=600)
    parser.add_argument('--pixel-size',type=float,default=4.)
    parser.add_argument('--seed',type=int,default=20261020)
    args=parser.parse_args(argv)
    manifest=generate(args.output,args.reference_scene,size=args.size,pixel_size=args.pixel_size,seed=args.seed)
    print(json.dumps({'output':str(args.output.resolve()),'label':manifest['dataset_label'],
                      'shape':[args.size,args.size],'steps':len(manifest['selected_forcing_timestamps'])}))
    return 0


if __name__=='__main__':raise SystemExit(main())
