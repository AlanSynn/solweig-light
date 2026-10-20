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
    metadata=tmp_path/'src/package.egg-info';metadata.mkdir()
    (metadata/'SOURCES.txt').write_text('generated build metadata')
    first=bench.source_identity(tmp_path)
    assert set(first['untracked_files'])=={'src/package/kernel.py'}
    (generated/'huge.json').write_text('changed generated contents')
    (nested/'payload.json').write_text('changed generated contents')
    (metadata/'SOURCES.txt').write_text('changed generated build metadata')
    second=bench.source_identity(tmp_path)
    assert second['source_tree_sha256']==first['source_tree_sha256']
    assert second['untracked_files']==first['untracked_files']


@pytest.mark.parametrize('value',['0','-1','not-an-integer'])
def test_memory_budget_option_rejects_nonpositive_or_invalid_values(value):
    arguments=['--reference-checkout','reference','--candidate-checkout','candidate',
               '--scene','scene','--workdir','work','--memory-budget-mib',value]
    with pytest.raises(SystemExit):bench.parser().parse_args(arguments)


def test_memory_budget_option_has_fixed_default_and_accepts_override():
    arguments=['--reference-checkout','reference','--candidate-checkout','candidate',
               '--scene','scene','--workdir','work']
    assert bench.parser().parse_args(arguments).memory_budget_mib==4096
    assert bench.parser().parse_args([*arguments,'--memory-budget-mib','8192']).memory_budget_mib==8192


@pytest.mark.parametrize('enabled',[False,True])
def test_optional_profiles_cover_svf_stage_and_tile_worker(monkeypatch,tmp_path,enabled):
    import json
    import sys
    import types
    package=types.ModuleType('solweig_light')
    api=types.ModuleType('solweig_light.api')
    pipeline=types.ModuleType('solweig_light.pipeline')
    for name in ('preprocess','run_walls_aspect','_calculate_svf','run_utci_tiles'):
        setattr(api,name,lambda *args,**kwargs:42)
    pipeline.run_tile=lambda *args,**kwargs:43
    package.api=api;package.pipeline=pipeline
    for name,module in (('solweig_light',package),('solweig_light.api',api),('solweig_light.pipeline',pipeline)):
        monkeypatch.setitem(sys.modules,name,module)
    monkeypatch.setattr(bench,'environment',lambda:{'test':True})
    monkeypatch.setenv('SOLWEIG_BENCH_EVENTS',str(tmp_path))
    monkeypatch.setenv('SOLWEIG_BENCH_PROFILE','1' if enabled else '0')
    publications=[]
    real_fsync,real_replace=bench.os.fsync,bench.os.replace
    def synced(descriptor):
        publications.append('fsync')
        return real_fsync(descriptor)
    def replaced(source,target):
        assert publications[-1]=='fsync'
        assert not Path(target).exists()
        lines=Path(source).read_text().splitlines()
        assert len(lines)==1
        json.loads(lines[0])
        publications.append('replace')
        return real_replace(source,target)
    monkeypatch.setattr(bench.os,'fsync',synced)
    monkeypatch.setattr(bench.os,'replace',replaced)
    bench._install_hooks()
    assert api._calculate_svf()==42
    assert pipeline.run_tile()==43
    for name in ('preprocess','run_walls_aspect','run_utci_tiles'):
        assert getattr(api,name)()==42
    files=sorted(tmp_path.glob('events-*.jsonl'))
    assert len(files)==6
    snapshots={path:path.read_bytes() for path in files}
    records=[json.loads(path.read_text()) for path in files]
    assert {record.get('stage') for record in records if record['event']=='stage'}=={
        'preprocess','walls','svf','tmrt_utci','tile'}
    assert publications==['fsync','replace']*6
    assert not list(tmp_path.glob('*.tmp'))
    assert api.run_walls_aspect()==42
    assert len(list(tmp_path.glob('events-*.jsonl')))==7
    assert all(path.read_bytes()==content for path,content in snapshots.items())
    assert len(list(tmp_path.glob('profile-svf-*.pstats')))==int(enabled)
    assert len(list(tmp_path.glob('profile-tile-*.pstats')))==int(enabled)


@pytest.mark.parametrize('missing',[None,'walls'])
def test_immutable_events_keep_required_stage_gate(monkeypatch,tmp_path,missing):
    import json
    import sys
    monkeypatch.setitem(sys.modules,'psutil',None)
    run=tmp_path/'run'
    class Completed:
        pid,returncode=123,0
        def __init__(self,*args,**kwargs):
            bench.write_json(run/'child-result.json',{'status':'passed'})
            for index,stage in enumerate(('preprocess','walls','svf','tmrt_utci')):
                if stage!=missing:
                    record={'event':'stage','stage':stage,'status':'passed','wall_seconds':1.}
                    (run/'events'/f'events-123-install-{index:08d}.jsonl').write_text(json.dumps(record)+'\n')
            (run/'events'/'unpublished.tmp').write_text('incomplete record')
        def poll(self):
            return 0
    monkeypatch.setattr(bench.subprocess,'Popen',Completed)
    inventories=[]
    def inventory(*args):
        inventories.append(True)
        return {}
    monkeypatch.setattr(bench,'inventory',inventory)
    result=bench.invoke({'run':str(run),'checkout':str(tmp_path),'regime':'measured',
        'expected_steps':19,'kwargs':{'tile_size':600}},tmp_path,tmp_path/'jit',2)
    assert result['status']==('passed' if missing is None else 'failed')
    assert inventories==([True] if missing is None else [])
    if missing:
        assert result['instrumentation_error']=="Missing completed stages: ['walls']"


@pytest.mark.parametrize('public_extra',['extra.tif','processed_inputs/extra.tif',
                                       'processed_inputs/SVF/extra.zip','processed_inputs/SVF/extra.npz'])
def test_public_comparison_ignores_private_staging_but_detects_public_extras(monkeypatch,tmp_path,public_extra):
    import json
    roots=[tmp_path/'reference',tmp_path/'candidate']
    for index,root in enumerate(roots):
        output=root/'scene/output_folder/0_0';output.mkdir(parents=True)
        for name in ('TMRT_0_0.tif','UTCI_0_0.tif'):(output/name).touch()
        staging=root/f'scene/processed_inputs/SVF/.geometry-export-random-{index}'
        staging.mkdir(parents=True)
        (staging/'SkyViewFactor_0_0.tif').touch()
        (root/'inventory.json').write_text(json.dumps({'states':{}}))
    monkeypatch.setattr(bench,'compare_tiff',lambda *args:{'passed':True})
    monkeypatch.setattr(bench,'compare_states',lambda *args:{'passed':True})
    result=bench.compare_runs(*roots,tmp_path/'scratch')
    assert result['passed'] and not result['missing_artifacts']
    extra=roots[1]/'scene'/public_extra
    extra.parent.mkdir(parents=True,exist_ok=True);extra.touch()
    result=bench.compare_runs(*roots,tmp_path/'scratch')
    assert not result['passed']
    assert result['missing_artifacts']
    assert any(Path(public_extra).name in name for name in result['missing_artifacts'])
