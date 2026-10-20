"""Small protocol tests; no full model calculation or performance assertions."""
import importlib.util
from pathlib import Path

import numpy as np
import pytest

PATH=Path(__file__).parents[2]/'development/tools/full_compute_benchmark.py'
SPEC=importlib.util.spec_from_file_location('full_compute_benchmark',PATH)
bench=importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(bench)


def _met(tmp_path):
    path=tmp_path/'met.txt'
    rows=[' '.join(map(str,[2020,200,hour,0,*([0]*20)])) for hour in (6,7,8,9)]
    path.write_text('header\n'+'\n'.join(rows)+'\n')
    return path


def test_met_date_derivation_and_inclusive_filter(tmp_path):
    path=_met(tmp_path)
    result=bench.selected_met(path,start_time='07:00',end_time='08:00')
    assert result['date']=='2020-07-18'
    assert result['timestamps']==['2020-07-18T07:00:00','2020-07-18T08:00:00']
    assert len(result['text'].splitlines())==3
    with pytest.raises(ValueError,match='at least two'):
        bench.selected_met(path,start_time='09:00')


def test_bits_special_masks_and_nan_payloads_are_separate():
    left=np.array([0.,np.nan,2.],dtype=np.float32)
    right=left.copy()
    right[0]=-0.
    right.view(np.uint32)[1]=np.uint32(0x7fc00001)
    result=bench.array_metrics(left,right)
    assert result['max_abs_error']==0
    assert result['special_masks_equal']
    assert not result['finite_bitwise_equal']
    assert not result['nan_payloads_equal']
    assert not result['all_bitwise_equal']
    assert bench.combine_metrics([result],0.)['passed']
    right[1]=np.inf
    assert not bench.combine_metrics([bench.array_metrics(left,right)],.02)['passed']


def test_frozen_absolute_threshold_and_schema():
    left=np.array([1.],dtype=np.float32)
    assert bench.combine_metrics([bench.array_metrics(left,left+.005)],.01)['passed']
    assert not bench.combine_metrics([bench.array_metrics(left,left+.015)],.01)['passed']
    assert not bench.combine_metrics([bench.array_metrics(left,left.astype(np.float64))],.01)['passed']


def test_npz_extraction_streams_members_without_cube_load(tmp_path):
    array=np.arange(40,dtype=np.float32).reshape(4,5,2)
    path=tmp_path/'visibility.npz'
    np.savez_compressed(path,shadowmat=array,vegshadowmat=array)
    members=bench._extract_npz(path,tmp_path/'unpacked')
    assert set(members)=={'shadowmat.npy','vegshadowmat.npy'}
    for member in members.values():
        restored=np.load(member,mmap_mode='r',allow_pickle=False)
        assert isinstance(restored,np.memmap)
        np.testing.assert_array_equal(restored,array)
        assert bench._compare_npy(member,member,0.)['all_bitwise_equal']


def test_raster_windows_check_metadata_and_special_masks(tmp_path):
    from osgeo import gdal,osr
    projection=osr.SpatialReference();projection.ImportFromEPSG(32632)
    def create(path,value):
        dataset=gdal.GetDriverByName('GTiff').Create(str(path),5,4,2,gdal.GDT_Float32)
        dataset.SetGeoTransform((400000,1,0,5800000,0,-1))
        dataset.SetProjection(projection.ExportToWkt())
        for index in (1,2):
            band=dataset.GetRasterBand(index)
            band.SetDescription(f'2020-07-18T0{index}:00:00')
            band.WriteArray(np.full((4,5),value,dtype=np.float32))
        dataset=None
    left,right=tmp_path/'a.tif',tmp_path/'b.tif'
    create(left,1.);create(right,1.005)
    result=bench.compare_tiff(left,right,.01)
    assert result['passed'] and not result['all_bitwise_equal']
    dataset=gdal.Open(str(right),gdal.GA_Update)
    dataset.GetRasterBand(2).SetDescription('wrong timestamp')
    dataset=None
    assert not bench.compare_tiff(left,right,.01)['passed']


def test_source_identity_ignores_generated_untracked_directories(tmp_path):
    import subprocess
    subprocess.run(['git','init','-q',str(tmp_path)],check=True)
    (tmp_path/'tracked.txt').write_text('baseline')
    subprocess.run(['git','-C',str(tmp_path),'add','tracked.txt'],check=True)
    subprocess.run(['git','-C',str(tmp_path),'-c','user.name=Test','-c','user.email=test@example.invalid',
                    'commit','-qm','fixture'],check=True)
    source=tmp_path/'src/package';source.mkdir(parents=True)
    (source/'kernel.py').write_text('value=1\n')
    generated=tmp_path/'pytest-of-root';generated.mkdir()
    (generated/'huge.json').write_text('not source')
    nested=tmp_path/'tests/solweig-runtime-generated';nested.mkdir(parents=True)
    (nested/'payload.json').write_text('not source either')
    first=bench.source_identity(tmp_path)
    assert set(first['untracked_files'])=={'src/package/kernel.py'}
    (generated/'huge.json').write_text('changed generated contents')
    (nested/'payload.json').write_text('changed generated contents')
    second=bench.source_identity(tmp_path)
    assert second['source_tree_sha256']==first['source_tree_sha256']
    assert second['untracked_files']==first['untracked_files']
