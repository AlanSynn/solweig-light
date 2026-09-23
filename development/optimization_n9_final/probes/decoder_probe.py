"""Isolated CPU microexperiment. NOT SOLWEIG, NOT N8/target-hardware qualification.
Generic kernel reproduces the computation/order of _produce_patchmajor at
AlanSynn/solweig-light@7abe526aae2f97e689b1a1e4ae183e5370f29aa1,
src/solweig_light/_native_dispatch/direct_aosoa.py, blob
b09325abd6e996205825e218298bb995e8fbc50c. Wrappers deliberately excluded.
Original algorithm copyright Harsh Kamath and Naveen Sudharsan, GPL-3.0-or-later.
New experiment code and specialization: GPL-3.0-or-later.
"""
from pathlib import Path
import json, time, platform, sys, statistics, re
import numpy as np
import numba
from numba import njit
from numba.typed import List

@njit(cache=True, fastmath=False)
def generic(payloads, modes, start, stop, patches, out, width):
    rows=stop-start
    full=rows//width
    tail=rows-full*width
    for patch in range(patches):
        data=payloads[patch]
        mode=modes[patch]
        for gang in range(full):
            pixel=start+gang*width
            for lane in range(width):
                if mode==4:
                    offset=pixel*4
                    value=(np.uint32(data[offset])|(np.uint32(data[offset+1])<<8)
                           |(np.uint32(data[offset+2])<<16)|(np.uint32(data[offset+3])<<24))
                else:
                    code=(data[pixel//(8//mode)]>>((pixel%(8//mode))*mode))&((1<<mode)-1)
                    if code==3:
                        raise IndexError('Reserved visibility code')
                    value=np.uint32(0) if code==0 else np.uint32(0x3f800000) if code==1 else np.uint32(0x40000000)
                out[gang,patch,lane]=value
                pixel+=1
        if tail:
            pixel=start+full*width
            for lane in range(tail):
                if mode==4:
                    offset=pixel*4
                    value=(np.uint32(data[offset])|(np.uint32(data[offset+1])<<8)
                           |(np.uint32(data[offset+2])<<16)|(np.uint32(data[offset+3])<<24))
                else:
                    code=(data[pixel//(8//mode)]>>((pixel%(8//mode))*mode))&((1<<mode)-1)
                    if code==3:
                        raise IndexError('Reserved visibility code')
                    value=np.uint32(0) if code==0 else np.uint32(0x3f800000) if code==1 else np.uint32(0x40000000)
                out[full,patch,lane]=value
                pixel+=1

@njit(cache=True, fastmath=False)
def literal_modes(payloads, modes, start, stop, patches, out, width):
    rows=stop-start
    full=rows//width
    tail=rows-full*width
    for patch in range(patches):
        data=payloads[patch]
        mode=modes[patch]
        # Mode branch moved outside pixel loops. Literal denominators removed.
        if mode==1:
            for gang in range(full+(tail!=0)):
                count=width if gang<full else tail
                for lane in range(count):
                    pixel=start+gang*width+lane
                    code=(data[pixel>>3]>>(pixel&7))&1
                    out[gang,patch,lane]=np.uint32(0) if code==0 else np.uint32(0x3f800000)
        elif mode==2:
            for gang in range(full+(tail!=0)):
                count=width if gang<full else tail
                for lane in range(count):
                    pixel=start+gang*width+lane
                    code=(data[pixel>>2]>>((pixel&3)<<1))&3
                    if code==3:
                        raise IndexError('Reserved visibility code')
                    out[gang,patch,lane]=np.uint32(0) if code==0 else np.uint32(0x3f800000) if code==1 else np.uint32(0x40000000)
        elif mode==4:
            for gang in range(full+(tail!=0)):
                count=width if gang<full else tail
                for lane in range(count):
                    offset=(start+gang*width+lane)*4
                    out[gang,patch,lane]=(np.uint32(data[offset])|(np.uint32(data[offset+1])<<8)
                        |(np.uint32(data[offset+2])<<16)|(np.uint32(data[offset+3])<<24))
        else:
            raise ValueError('unadmitted mode')


def fixture(n, modes, rng):
    payloads=List()
    expected=[]
    book=np.array([0,0x3f800000,0x40000000],np.uint32)
    for mode in modes:
        if mode==4:
            bits=rng.integers(0,2**32,size=n,dtype=np.uint32)
            data=bits.astype('<u4',copy=False).view(np.uint8).copy()
        else:
            codes=rng.integers(0,2 if mode==1 else 3,size=n,dtype=np.uint8)
            data=np.zeros((n*int(mode)+7)//8,np.uint8)
            # Independent Python encoder and expected bit values.
            for i,code in enumerate(codes):
                data[i//(8//int(mode))] |= np.uint8(int(code)<<((i%(8//int(mode)))*int(mode)))
            bits=book[codes]
        payloads.append(data)
        expected.append(bits)
    return payloads,np.asarray(expected,np.uint32).T.copy()


@njit(cache=True, fastmath=False)
def literal_raw_preserved(payloads, modes, start, stop, patches, out, width):
    rows=stop-start
    full=rows//width
    tail=rows-full*width
    for patch in range(patches):
        data=payloads[patch]
        mode=modes[patch]
        if mode==4:
            # Keep the original raw full-gang and tail loops, not the modified schedule.
            for gang in range(full):
                pixel=start+gang*width
                for lane in range(width):
                    offset=pixel*4
                    out[gang,patch,lane]=(np.uint32(data[offset])|(np.uint32(data[offset+1])<<8)
                       |(np.uint32(data[offset+2])<<16)|(np.uint32(data[offset+3])<<24))
                    pixel+=1
            if tail:
                pixel=start+full*width
                for lane in range(tail):
                    offset=pixel*4
                    out[full,patch,lane]=(np.uint32(data[offset])|(np.uint32(data[offset+1])<<8)
                       |(np.uint32(data[offset+2])<<16)|(np.uint32(data[offset+3])<<24))
                    pixel+=1
        elif mode==1:
            for gang in range(full):
                pixel=start+gang*width
                for lane in range(width):
                    code=(data[pixel>>3]>>(pixel&7))&1
                    out[gang,patch,lane]=np.uint32(0) if code==0 else np.uint32(0x3f800000)
                    pixel+=1
            if tail:
                pixel=start+full*width
                for lane in range(tail):
                    code=(data[pixel>>3]>>(pixel&7))&1
                    out[full,patch,lane]=np.uint32(0) if code==0 else np.uint32(0x3f800000)
                    pixel+=1
        elif mode==2:
            for gang in range(full):
                pixel=start+gang*width
                for lane in range(width):
                    code=(data[pixel>>2]>>((pixel&3)<<1))&3
                    if code==3: raise IndexError('Reserved visibility code')
                    out[gang,patch,lane]=np.uint32(0) if code==0 else np.uint32(0x3f800000) if code==1 else np.uint32(0x40000000)
                    pixel+=1
            if tail:
                pixel=start+full*width
                for lane in range(tail):
                    code=(data[pixel>>2]>>((pixel&3)<<1))&3
                    if code==3: raise IndexError('Reserved visibility code')
                    out[full,patch,lane]=np.uint32(0) if code==0 else np.uint32(0x3f800000) if code==1 else np.uint32(0x40000000)
                    pixel+=1
        else: raise ValueError('unadmitted mode')


def run(out_path):
    rng=np.random.default_rng(20260923)
    checked=0; bit_values=0; exceptions=0
    for width in (4,8):
        for n in (0,1,7,8,9,31,128,1024):
            for start in (0,1,7,11):
                modes=np.array([1,2,4,2,1,4],np.uint8)
                payloads,expected=fixture(n+start+8,modes,rng)
                shape=((n+width-1)//width,len(modes),width)
                a=np.full(shape,0xdeadbeef,np.uint32);b=a.copy()
                generic(payloads,modes,start,start+n,len(modes),a,width)
                literal_modes(payloads,modes,start,start+n,len(modes),b,width)
                np.testing.assert_array_equal(a,b)
                c=np.full(shape,0xdeadbeef,np.uint32)
                literal_raw_preserved(payloads,modes,start,start+n,len(modes),c,width)
                np.testing.assert_array_equal(a,c)
                valid=a.transpose(0,2,1).reshape(-1,len(modes))[:n]
                np.testing.assert_array_equal(valid,expected[start:start+n])
                checked+=1;bit_values+=n*len(modes)
    for bad in (0,1,7,8,31):
        modes=np.array([2],np.uint8)
        payloads,_=fixture(40,modes,rng)
        offset=bad//4;shift=(bad%4)*2
        payloads[0][offset] |= np.uint8(3<<shift)
        for fn in (generic,literal_modes,literal_raw_preserved):
            try:fn(payloads,modes,0,40,1,np.empty((5,1,8),np.uint32),8)
            except IndexError as e:
                assert str(e)=='Reserved visibility code';exceptions+=1
            else:raise AssertionError('corrupt input accepted')
    timings=[]
    for name in ('binary','mixed','raw'):
        for n in (128,1024):
            p=153
            modes=(np.ones(p,np.uint8) if name=='binary' else np.full(p,4,np.uint8) if name=='raw'
                   else np.resize(np.array([1,2,4],np.uint8),p))
            payloads,expected=fixture(n+8,modes,rng)
            out=np.empty(((n+7)//8,p,8),np.uint32)
            for fn in (generic,literal_modes,literal_raw_preserved):fn(payloads,modes,0,n,p,out,8)
            raw={'generic':[],'literal_modes':[],'literal_raw_preserved':[]}
            for rep in range(9):
                seq=(('generic',generic),('literal_modes',literal_modes),('literal_raw_preserved',literal_raw_preserved))
                if rep%2:seq=seq[::-1]
                for label,fn in seq:
                    t=time.perf_counter_ns()
                    for _ in range(5):fn(payloads,modes,0,n,p,out,8)
                    raw[label].append((time.perf_counter_ns()-t)/5/1e6)
            mg=statistics.median(raw['generic']);ml=statistics.median(raw['literal_modes'])
            timings.append({'mode_mix':name,'pixels':n,'patches':p,'width':8,
                'generic_median_ms':mg,'literal_median_ms':ml,'ratio_generic_over_literal':mg/ml,
                'literal_raw_preserved_median_ms':statistics.median(raw['literal_raw_preserved']), 'ratio_generic_over_raw_preserved':mg/statistics.median(raw['literal_raw_preserved']), 'raw_ms':raw})
    assembly={}
    for label,fn in (('generic',generic),('literal_modes',literal_modes),('literal_raw_preserved',literal_raw_preserved)):
        asm=fn.inspect_asm(fn.signatures[0])
        # Count body mnemonics, not proof of absence across all targets.
        divs=[l.strip() for l in asm.splitlines() if re.match(r'^\s*(?:idiv|div)[bwlq]?\s',l)]
        assembly[label]={'integer_divide_instruction_lines':divs,'signature':str(fn.signatures[0])}
        Path(out_path).with_name(label+'.asm.txt').write_text(asm)
    result={'scope':'isolated single-thread decoder microexperiment, NOT SOLWEIG/native/default promotion evidence',
      'source_basis':'7abe526aae2f97e689b1a1e4ae183e5370f29aa1 direct_aosoa.py computation; manually transcribed core; no package import',
      'environment':{'python':sys.version,'machine':platform.machine(),'platform':platform.platform(),
        'numpy':np.__version__,'numba':numba.__version__},
      'limitations':['not target M1','synthetic small buffers','single local process','wrapper, mmap, integration, multi-thread and IO excluded','source excerpt not full package'],
      'exactness':{'shape_start_width_cases':checked,'independently_expected_uint32_values':bit_values,'reserved_error_checks':exceptions},
      'timings':timings,'assembly':assembly}
    Path(out_path).write_text(json.dumps(result,indent=2))
    print(json.dumps({k:v for k,v in result.items() if k not in ('timings','assembly')},indent=2))
    for t in timings:print(t['mode_mix'],t['pixels'],round(t['generic_median_ms'],6),round(t['literal_median_ms'],6),round(t['ratio_generic_over_literal'],3), 'raw-preserved:', round(t['ratio_generic_over_raw_preserved'],3))
    print('integer division instruction counts',{k:len(v['integer_divide_instruction_lines']) for k,v in assembly.items()})

if __name__=='__main__':
    import argparse
    ap=argparse.ArgumentParser();ap.add_argument('--out',default=str(Path(__file__).with_name('decoder_probe_result.json')))
    run(ap.parse_args().out)
