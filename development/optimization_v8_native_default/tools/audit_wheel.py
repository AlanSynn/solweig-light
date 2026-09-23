"""Static wheel sanity checks only; does not load or qualify a native library."""
from __future__ import annotations
import argparse
import json
from pathlib import Path, PurePosixPath
import stat
import zipfile


def audit(path: Path, require_native: bool=False) -> dict:
    errors=[];native=[];tags=[];pure=None
    with zipfile.ZipFile(path) as z:
        infos=z.infolist();names=[i.filename for i in infos]
        if len(names)!=len(set(names)):errors.append('duplicate archive paths')
        for info in infos:
            normalized=info.filename.replace('\\','/')
            p=PurePosixPath(normalized)
            if p.is_absolute() or '..' in p.parts or (p.parts and ':' in p.parts[0]):
                errors.append('unsafe archive path: '+info.filename)
            if stat.S_ISLNK(info.external_attr>>16):errors.append('symlink member: '+info.filename)
            if info.filename.lower().endswith(('.so','.dylib','.dll','.pyd')):
                native.append(info.filename)
                with z.open(info) as f:magic=f.read(8)
                if not (magic.startswith(b'\x7fELF') or magic.startswith(b'MZ') or magic[:4] in
                       (b'\xcf\xfa\xed\xfe',b'\xfe\xed\xfa\xcf',b'\xca\xfe\xba\xbe',b'\xbe\xba\xfe\xca',b'\xce\xfa\xed\xfe',b'\xfe\xed\xfa\xce',b'\xca\xfe\xba\xbf',b'\xbf\xba\xfe\xca')):
                    errors.append('unrecognized native file magic: '+info.filename)
        metadata=[n for n in names if n.endswith('.dist-info/WHEEL')]
        if len(metadata)!=1:errors.append('expected exactly one WHEEL metadata file')
        else:
            info=z.getinfo(metadata[0])
            if info.file_size>1024*1024:errors.append('oversized WHEEL metadata')
            else:
                text=z.read(info).decode('utf-8')
                tags=[line.split(':',1)[1].strip() for line in text.splitlines() if line.startswith('Tag:')]
                values=[line.split(':',1)[1].strip().lower() for line in text.splitlines() if line.startswith('Root-Is-Purelib:')]
                pure=values[0] if len(values)==1 else None
                if not tags:errors.append('missing wheel tags')
        if native:
            if pure!='false':errors.append('native wheel must declare Root-Is-Purelib: false')
            if any(t.split('-')[-1]=='any' for t in tags):errors.append('native payload cannot use platform any')
            if path.name.endswith('-any.whl'):errors.append('native wheel filename incorrectly claims any platform')
        if require_native and not native:errors.append('native payload required but absent')
    return {'schema':'sw8-wheel-static-audit-v1','wheel':str(path),'errors':errors,
            'static_checks_passed':not errors,'native_files':native,'tags':tags,
            'evidence_kind':'static_archive_check_only','native_executed':False,
            'dependency_closure_verified':False,'default_qualified':False}


def main() -> int:
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('wheel',type=Path)
    p.add_argument('--require-native',action='store_true');a=p.parse_args()
    try:r=audit(a.wheel,a.require_native)
    except (ValueError,OSError,UnicodeError,zipfile.BadZipFile) as e:r={'errors':[str(e)],'static_checks_passed':False}
    print(json.dumps(r,indent=2));return 0 if r['static_checks_passed'] else 2

if __name__=='__main__':raise SystemExit(main())
