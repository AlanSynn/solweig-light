# C5-02 SOURCE_MAP — current definitions of the four v5 optimization target areas

Audited at worktree HEAD `6682b23e05163bade7fea54a8fec4ec4614406e0` (branch `perf/claude-glm53-cpu-v5`).
All anchors are `src/solweig_light/...:line` inside the worktree. All compiled kernels in the target
modules use `fastmath=False` unless stated otherwise. The v4 integrated candidate is commit
`14e88876` ("Optimize exact local CPU scheduling, visibility decoding, and JIT reuse"); its full
source delta vs its baseline `8ca23d44` touched ONLY: `geometry/visibility_compiled.py (+29)`,
`radiation/_jit_cache.py (+50, new)`, `radiation/_math_profile.py`, `_sleef_acos.py`,
`_sleef_classifier.py`, `radiation/engine.py (+10)`, `radiation/patch_radiation.py (+16)`,
`radiation/wall_shadows.py (+101)` (`git diff --stat 8ca23d44 14e88876 -- src/`).
It did NOT touch `sky_compiled.py`, `ground_view.py`, `runtime.py`, `runtime_worker.py`.

## (a) Rays — `geometry/sky_compiled.py` and its callers

### Schedule construction (shared)
- `ray_schedule(shape, amaxvalue, azimuth, altitude, scale)` — `sky_compiled.py:23-67`. Pure NumPy
  Python loop. `if azimuth==0: azimuth=1e-12` (:29-30); angles deg→rad float32 (:31-32); branch
  `np.pi/4<=azimuth<3*np.pi/4 or 5*np.pi/4<=azimuth<7*np.pi/4` chooses `dy=ss*index;
  dx=-sc*abs(np.round(index/tan)); ds=ds_s` else `dy=ss*abs(np.round(index*tan)); dx=-sc*index`
  (:43-50); `dz=ds*index*tas` (:51); slice bounds via `slice(...).indices(...)` (:58-61); shape
  mismatch raises `ValueError('ray source/destination slice shapes differ')` (:62-63). Loop
  condition `while amaxvalue>=dz and abs(dx)<sx and abs(dy)<sy` (:42). Returns
  `bounds int64 (-1,8)`, `heights` array (:67).
- Per-source-dtype decrements: `da=np.asarray(heights,dtype=a.dtype)`, `dv` (vegdem), `dt`
  (vegdem2), `db` (bush) (:230-233 step-major; :334-336 pixel-major); `first_height(s)` float32
  (:234, :337).

### Step-major path (positive-bush global branch)
- `_advance_pixel` (`sky_compiled.py:79-113`, inline) — state update expressions, exactly:
  - source sample gated `if xp1<=row<xp2 and yp1<=col<yp2:` with
    `building=np.float32(a[source_row,source_col]-da)` etc. (:84-91). Outside a slice the
    temporary is 0 (zero padding).
  - `f[row,col]=_maximum(f[row,col],building)` (:94); `sh` set 1 if `f>height` else 0 (:95-98);
    `vegetation_shadow=np.float32(above)-np.float32(trunk_above)` (:99-101);
    `vs[row,col]=_maximum(vs[row,col],vegetation_shadow)` (:102);
    `if vs[row,col]*sh[row,col]>0: vs[row,col]=np.float32(0)` (:103-104);
    `vb[row,col]=vb[row,col]+vs[row,col]` (:105).
  - First step special case (:106-113): `first_vegetation=np.float32(vegetation-building)`;
    `if first_vegetation<=0: first_vegetation=np.float32(1000)`;
    `if first_vegetation<first_height: vs[row,col]=np.float32(1)`;
    `vs[row,col]=vs[row,col]*np.float32(trunk[row,col]>height)`;
    `vb[row,col]=np.float32(0)`.
- `_bush_active` (:133-142): SERIAL deterministic global reduction
  `value=np.float32(tv[row,col]>a[row,col])*bush[row,col]` with NaN → return False; comment
  states an any-positive shortcut would not preserve NaN poisoning.
- `_bush_pixel` (:146-151): `g[row,col]=_maximum(g[row,col],value)*bp[row,col]` with
  `value=np.float32(bush[...]-delta)` inside-slice.
- `_finish_pixel` (:171-186): `sh=1-sh`; `combined=vb; if combined>0: combined=1`;
  `combined=combined-original_vs`; `vb=1-combined`; bush tail when `bush_positive`:
  `difference=g-bush` clamped to {0,1}; `value=original_vs-bp+difference` clamped ≥0; `veg=1-value`.
- Drivers: `_run_serial` (:206-211) per step `_advance_serial` then optional `_bush_serial`;
  `_run_parallel` (:215-222) SERIAL Python-step driver calling `_advance_parallel` /
  `_bush_parallel` (prange over pixels inside each step kernel — step barrier is the parallel
  completion) then `_finish_parallel`. Steps loop `for step in range(len(bounds))` — no ray is
  truncated.
- Host `_shadow` (:225-248): scratch `f=a.copy()`, `sh` zeros, `bp=(bush>1).astype(np.float32)`,
  `vs=bp.copy()`, `vb` zeros, `tv` empty, `g` zeros, `bush_positive=bool(bush.max()>0)`;
  vegetation output dtype promoted to bush dtype only when bush_positive (:243-245). Returns
  `(sh, vegetation, vb)` (:248).

### Pixel-major path `_trace_pixel` (`sky_compiled.py:264-302`)
- Gate: `_shadow_pixel` (:321-341) routes to `_shadow` (step-major) whenever
  `bush.max()>0` (:325-328). Independence proof comment (:329-332) ends: "Each pixel follows the
  complete original schedule in order; **no pixel/ray early termination**."
- Signature: `_trace_pixel(row,col,a,canopy,trunk,bush,bounds,da,dv,dt,first_heights)`.
- Per-pixel state: `f=height`, `sh=0`, `vs=np.float32(bush[row,col]>1)`, `vb=0` (:266-270); full
  loop `for step in range(len(bounds))` (:271); per-step expressions mirror `_advance_pixel`
  (:276-290); first-step block at `step==0` (:291-298) identical semantics including `vb=0`;
  finish (:299-302): `if vb>0: vb=1; vb=vb-vs; if vs>0: vs=1; return
  np.float32(1)-sh, np.float32(1)-vs, np.float32(1)-vb`.
- Wrappers: `_pixel_serial` (:306-309), `_pixel_parallel` (:313-318, `prange(rows*cols)` flat
  pixel index `row=pixel//cols; col=pixel%cols`); entry points `shadow_pixel_serial` (:344-346),
  `shadow_pixel_parallel` (:349-351); `shadow` (:259-261) = serial default.
- NOT early-exit optimized. R01a's absorption-before-projection does not exist here yet.

### Callers
- `geometry/shadows.py:113-116` — live `shadow()` delegates to `shadow_pixel_serial` (SERIAL
  only). A dead NumPy oracle `shadow` (:39-106) is retained as `shadow_numpy` (:110).
- `geometry/svf.py:132` — SVF loop calls `shadow(...)` once per patch direction; masks stored
  per-patch: compact `mat.append(mask)` via `VisibilityBuilder` (:122-124, :134) or dense
  `mat[:,:,index]=mask` (:126, :135). `svf_calculator_compact` (:163-165) is the pipeline route
  (`pipeline.py:22`); annulus accumulation order patch→annulus→contribution (:137-143); post
  fixes `3.0459e-4` (:145-147), clamp `field[field>1]=1` (:148), total
  `svf-(1-svfveg)*(1-.03)` (:149); return order `order=[0,10,1,11,6,4,14,9,2,12,7,5,3,13,8]`
  (:153-154).
- Engine timestep rays: `radiation/engine.py:1570` → `shadowingfunction_wallheight_23`
  (engine.py:1723-1727) → `radiation/wall_shadows.py exact_23` (wall_shadows.py:274-278,
  `parallel=False`) → `_wall23_serial` (`wall_shadows.py:203-264`, `cache=True` +
  `bind_cache_identity` at :203-204). Its own schedule builder `_geometry`
  (wall_shadows.py:23-67) — NOTE distinct initial index `index = 0 if vegetation else 1` (:41)
  and per-step recorded heights include the `prev`-based `lastv/lastv2` samples
  (:160-161, :223-224). Pixel-major recurrence `_wall23` body (:144-200): state
  `f, volumeveg, vs=bush>1, building, vb, prev`; per step `count` of four above-tests,
  `candidate=np.float32(count>0 and count!=4)` (:165-166); `vs*building>0 → vs=0` (:168-169);
  `vb+=vs` (:170); `prev=heights[step]` (:171); finish (:177-199) emits 8 planes:
  vegsh/sh/vbsh + wallshade/sun/wallveg/face/facesun — the wall quantities.
- Walls (not the trace): `geometry/walls_compiled.py` — `walls_serial/parallel` (:36-53,
  float64 output, 4-neighbor max − dsm), `angles_serial/parallel` (:70-92, 180-angle score,
  int16). Called from `geometry/walls.py:17-37` (`findwalls` serial default).

### Parallel dispatch and JIT cache identity
- prange flat-pixel loops as above; native thread count set by runtime env
  (`runtime.py:663-676` sets `NUMBA_NUM_THREADS` etc. in child env only).
- `sky_compiled.py`, `ground_view.py`, `patch_radiation.py`, `visibility_compiled.py` kernels:
  plain `@njit(cache=True, fastmath=False)` — default numba cache identity (no explicit
  namespace). `bind_cache_identity` (`radiation/_jit_cache.py:26-50`, hashes defining module
  bytes + helper + runtime into `__qualname__`) is applied ONLY to
  `wall_shadows.py:109,204` (`_wall13_serial`, `_wall23_serial`), `_sleef_acos.py:90`,
  `_sleef_classifier.py:129,142`. The always-parallel `_wall13`/`_wall23`
  (`wall_shadows.py:77,140`) have NO `cache=True` (unused in the engine's serial dispatch).
- v4 changes in the ray family: only `wall_shadows.py` serial/parallel split +
  `bind_cache_identity` (see header). Nothing in `sky_compiled.py`.

## (b) Radiation — `radiation/patch_radiation.py` + `geometry/visibility_compiled.py`

### Packed visibility encoding
- `geometry/visibility.py` — `PackedVisibility` (:74+), `codec_version=CODEC_VERSION` (:77);
  per-patch `_EncodedPatch(mode, payload)` (:68+); modes `'binary'|'ternary'|'raw'` with byte
  length `pixels*4` raw else `(pixels*bits+7)//8` (:88-92); codebook decode
  `CODEBOOK_BITS → uint32.view(float32)` (:110-126). Mode numeric mapping in the compiled
  descriptor: `{'binary':1,'ternary':2,'raw':4}` (`visibility_compiled.py:62-63`).
- `_decode` (`visibility_compiled.py:17-35`, njit cache=True): output
  `bits=np.empty((stop-start,patches),dtype=np.uint32)` — ROW = pixel, COLUMN = patch
  (patch-major slices per pixel row, i.e. decode materializes pixel-major rows × patch cols);
  raw mode reads 4 bytes little-endian at `pixel*4` (:25-28); packed modes
  `code=(data[pixel//(8//mode)]>>((pixel%(8//mode))*mode))&((1<<mode)-1)` (:30);
  `code==3 → raise IndexError('Reserved visibility code')` (:31-32);
  `value=0 / 0x3f800000 (1.0) / 0x40000000 (2.0)` (:33). Returned as `bits.view(np.float32)` (:35).
- `_diff` (:38-45): `shadow -= float32(1-vegetation)*float32(1-.03)` elementwise (the
  diffsh formula), mutates its first arg.
- `decode_block(channel,start,stop,patches)` (:69-85): duck-typed/lazy leaves → None; sorted
  stable lock order over mapped owners (`sorted({...}, key=id)`, :75-78) with
  `_check_open()`; range validation (:80-82); `_decode_diff` for `LazyDiffVisibility` (:83-85).
- `_descriptor` (:54-66): cached `channel._block_descriptor` = (typed List of readonly uint8
  `np.frombuffer` views, uint8 modes array); zero payload copies.

### Consumer route `radiation/patch_radiation.py`
- Block loop: `for start in range(0,pixels,block_pixels)` — Kside `:327-343`,
  `define_patch_characteristics` `:503-509`. `block_pixels` comes from
  `get_runtime_options().block_pixels` via engine dispatch (engine.py:1748, :1756, :1764),
  default 128.
- `_block` (:96-111): `decode_block` when all leaves are `PackedVisibility`, else per-patch
  `decode_pixels`/fancy-index fallback. Decoded shape `(stop-start, patches)` float32.
- `_shortwave_visibility_blocks` (:114-123): reads `sh,vs,vb,diff` in that order and reuses
  already-decoded leaves via `diff_from_shared_decoded` (v4) else decodes diff separately.
- Shortwave kernel `_shortwave` (:181-225, parallel prange over pixels) / `_shortwave_serial`
  (:228-272): per-pixel patch-major inner loop `for patch in range(patches)`; masks
  `veg=vs==0 or vb==0`, `building=np.float32(1-sh)*vb==1` (:188-189, :235-236); contributions:
  diffuse `np.float32(np.float32(np.float32(diff*lum)*cosine)*solid)` → col 0 (:190-191);
  vegetation reflection `((surface_sh*veg)*solid)*cosine` → col 3 (:192-193); sunlit wall
  `((((surface_sun*sun)*building)*solid)*cosine)` → col 1 (:195-197); shaded wall → col 2;
  box/cyl variant gated by `diff_gate/ref_gate/box_gate` per patch × 4 directions → cols 4-7
  (diffuse directional), 8-11 (sunlit wall), 12-15 (veg refl), 16-19 (shaded wall)
  (:200-224). Accumulators: `out=np.zeros((pixels,20),dtype=np.float32)`, plain `+=` in patch
  order (:185).
- Longwave `_longwave` (:347-408) / serial (:411-472): per-pixel `accum=np.zeros(14,float32)`;
  first ordered patch sweep (sky `sh==1 and vs==1` :354; veg/building terms; solar_gate
  sun/shade side/down terms :369-389); THEN the reflection field computed from the COMPLETED
  sky sweep + per-pixel Lup:
  `reflected=np.float32(np.float32(np.float32(np.float32(accum[0]+lup[pixel])*reflection_factor)*np.float32(.5))/np.float32(np.pi))`
  (:391, serial :455), second ordered patch sweep for side/down reflections (:392-400) — the
  barrier P01 must preserve. Output `(pixels,11)` float32 with fixed column permutation
  (:401-407).
- Classification: `_class_coefficients` (:130-153) evaluates per-patch scalar ops in patch
  order (preserving wrapped-scalar promotion), returns `(indices, coefficients, rad2deg)`;
  `_classes` (:156-178) uses `tan32/atan32` (math profile) for the fast path
  (:167-171: `delta=np.add(tan32(field),coefficients[None,:])`;
  `degrees=np.multiply(atan32(delta),rad2deg)`; `sun=degrees<altitude; shade=degrees>altitude`),
  else per-patch `engine.shaded_or_sunlit` fallback (:173-178).
- Patch geometry cache: `_cached_geometry` `lru_cache(maxsize=8)` keyed
  `(shape, dtype.str, payload bytes)` (:49-80); ≤609 patches enforced (:77); `PatchGeometry`
  frozen dataclass with 11 immutable tables (:29-41); `clear_geometry_cache` (:83-84).
- Admission/guards: `Kside_veg_v2022a` (:275-286), `define_patch_characteristics`
  (:475-485), `Lcyl_v2022a` (:512-523) fall back to `_reference(name)` (:87-93, resolves
  `engine._serial_<name>` etc.) unless float32 raster profile, scalar forcing, ≤609 patches.
  `Lcyl_v2022a` preserves per-band `model2` emission (:532-540, `_model2` :545-556) and
  delegates to `define_patch_characteristics` (:541).
- aniLum/diffsh: computed in the ENGINE, not here — `engine.py:1561-1564`:
  `aniLum=_zeros((rows,cols)); for idx in range(lv.shape[0]):
  aniLum += _operate(np.multiply, diffsh[:,:,idx], lv[idx,2]); dRad=_operate(np.multiply,
  aniLum, radD)` — a separate full patch traversal over diffsh executed BEFORE the shadow call
  (P07 target).
- Math profile: `radiation/_math_profile.py` — `PROFILE_ID="solweig-portable-sleef-5a1d179d-v1"`
  (:14), `fastmath: False`, `fma: "explicit-llvm.fma.f32"` (:53-54); `asvf` (:60-66) SLEEF
  FMA acos(sqrt) for float32 else numpy; `tan32` (:69-84) SLEEF only where
  `isfinite & abs<125` else numpy with per-position overwrite; `atan32` (:87-92).
  `profile_identity()` (:34-57) fingerprints source sha256 + runtime for caches.
- v4 decode/JIT-reuse present at this HEAD: `diff_from_shared_decoded`
  (visibility_compiled.py:88-114, restricted to exactly `PackedVisibility`/`MappedVisibility`
  immutable types, returns None = exact fallback), `_shortwave_visibility_blocks` reuse
  (patch_radiation.py:119-123), `bind_cache_identity` on wall/sleef kernels. Decode is NOT
  fused into the reduction kernels: `_decode` still materializes the full
  `(block_pixels,patches)` decoded block before `_shortwave`/`_longwave` read it (P01's
  decoded-block elimination is NOT done).

## (c) GVF — `radiation/ground_view.py`

- Schedule: `_build_schedule(shape,azimuth,second)` (:35-57) — int(second) steps, same
  dx/dy algebra as sky_compiled but no dz; per-step assignment-compatibility check
  `if any(a!=b and a!=1 for a,b in zip(source,destination)): raise RuntimeError` (:53-54).
  `ray_schedule` (:65-70) caches via `_schedule_cached` `lru_cache(maxsize=36)`
  (:60-62) only when `int(second)*8*8<=MAX_CACHED_SCHEDULE_BYTES=65536` (:23-24, :68-69);
  `SCHEDULE_VERSION='ground-view-v1'` (:23); `clear_schedule_cache` (:73).
- `_gather_pixel` (:85-123, inline): persistent outside-slice samples
  `bu=sh=lu=al=an=sw` carry the previous step's values (comment :98 "Outside a current slice
  the previous neighbor samples persist"); `f=_minimum(f,bu)` blocker recurrence (:99); sums
  `sumsh+=sh*f`, `sumlu+=lu*f`, `sumal+=al*f`, `suman+=an*f` (:100-103); wall counters
  `tempb=sw*f`, `tempbwall=f*(-1)+1`, `bub=(tempb+bub)>0`, `bubwall=(tempbwall+bubwall)>0`
  (:104-107); `sumlw+=bub*lwall[row,col]`, `sumaw+=bub*albedo`, `sumwall+=bub`,
  `sumanw+=bubwall*albedo` (:108-111); first-prefix snapshots for `step+1<=first`
  (:112-115); emits 16 planes into `output` (:116-123): 8 full sums + 8 first snapshots.
- `_gather` (:141-151): builds bounds; COPIES six source fields per direction
  `sources=[np.array(value,dtype=np.float32,copy=True) for value in
  (buildings,shadow,sunwall,lup,albshadow,alb)]` (:146) plus `lwall` broadcast copy (:147);
  `output=np.empty((16,*shape),float32)` (:148); serial/parallel kernel pick (:149).
- `_sun` (:170-266): guards + `_fallback('sunonsurface_2018a', ...)` (:203-204);
  water Tg mutation ORDERING TRAP: first-direction Lup is formed at :216
  (`Lup=_operate(np.subtract, _operate(np.multiply, _operate(np.multiply, SBC, emis_grid),
  _operate(np.power, _operate(np.add, _operate(np.add, _operate(np.multiply, Tg, shadow), Ta),
  273.15), 4)), ...)`) BEFORE `if landcover == 1: Tg[lc_grid == 3] =
  _operate(np.subtract, Twater, Ta).astype(np.float32)` (:217-218); the later `gvfLup`
  postprocessing at :261 RE-EVALUATES the same Lup expression with the MUTATED Tg — so first
  vs later directions legitimately see different Tg (G02's two-snapshot requirement).
  Facesh azilow/azihigh branches (:235-244); `keep` mask (:245-246); gvf1/gvf2,
  gvfLup1/2, gvfalb1/2, gvfalbnosh1/2 formulas (:247-258); final
  `gvf=(gvf1*0.5+gvf2*0.4)/0.9` (:259), gvfLup + mutated-Tg Lup term (:260-261), gvfalb +
  `alb_grid*(1-buildings)*shadow` (:262-263), gvfalbnosh + unshadowed albedo (:264-265).
  Returns `(gvf, gvfLup, gvfalb, gvfalbnosh, gvf2)` (:266).
- `_gvf` (:268-357): guards (:298-299); `azimuthA=np.arange(5,359,20,dtype=np.float32)` — the
  18 directions (:300); 16 receiver planes allocated (:301-316): gvfLup, gvfalb, gvfalbnosh,
  gvfLupE/S/W/N, gvfalbE/S/W/N, gvfalbnoshE/S/W/N, gvfSum (gvfSum + gvfNorm are returned but
  only 16 accumulators exist; gvfNorm is derived at :356); `sunwall=(_divide(wallsun,walls)*
  buildings==1).astype(np.float32)` (:317); direction loop `for j in np.arange(0,len(azimuthA))`
  (:318) calls `_sun` (:319) and accumulates cardinal assignments (:324-339); normalization by
  `len(azimuthA)` and `len(azimuthA)/2` with +SBC*emis*(Ta+273.15)^4 terms (:340-355);
  `gvfNorm[buildings==0]=1` (:356). Returns 17-tuple (:357).
- Public entries: `sunonsurface_2018a(_parallel)` (:359-363), `gvf_2018a(_parallel)`
  (:365-369); engine dispatch `engine.py:1735-1740` picks parallel iff
  `threads_per_worker>1` (default serial).
- Callers: engine.py:1592 (per daytime timestep). Note `Tg` is passed by reference into every
  `_sun` call, so direction j+1 inherits direction j's mutation — chronological within the
  direction loop.
- v4 changed nothing here.

## (d) Runtime — `runtime.py` + `runtime_worker.py`

- `RuntimeOptions` (`runtime.py:314-383`, frozen dataclass slots) defaults:
  `cache_dir=None`, `legacy_cache_policy="recompute"`, `cache_enabled=True`,
  `memory_budget_bytes=None`, `cpu_budget=1`, `workers=1`, `threads_per_worker=1`,
  `block_pixels=128`, `checkpoint_interval=1`, `resume=False`.
  Validation (:329-367): positive ints; `threads_per_worker<=cpu_budget<=_total_cpus()`
  (cgroup-aware, :135-167); `legacy_cache_policy ∈ {recompute, trust}`.
  Context binding: `_OPTIONS` ContextVar + `runtime_options()` context manager
  (:386-423). `resolved_memory_budget_bytes` property (:369-375) →
  `default_memory_budget_bytes()` (:289-300) = min(physical, available, container headroom) ×
  `DEFAULT_MEMORY_FRACTION=0.50` (:279).
- Memory admission: `estimate_memory` (:457-502) — raw visibility
  `3*pixels*patches*float32` (:478), live arrays
  `(192+32+windchannels)*pixels*float32` (:482-486), decoded
  `block_pixels*patches*(windchannels+4)*float32` (:487), native
  `256MiB+64MiB*min(8,windchannels)` (:489). `plan_admission` (:566-592): per-job estimate
  (rows/cols or gdal probe of `paths['Building_DSM']`, :532-563); any single job over budget →
  `ResourceAdmissionError` (:571-577); `cpu_workers=cpu_budget//threads_per_worker`;
  active = largest-first cumulative fit within budget (:581-591);
  `AdmissionPlan(active, estimates, active*threads_per_worker)`.
- Worker model: `execute_tiles` (:679-811) is a NON-PERSISTENT process pool: per tile,
  `start(index)` (:713-743) writes `job-{index}.json` and spawns
  `[python, -m, solweig_light.runtime_worker, --job, ..., --options, <RuntimeOptions json>]`
  with a fresh child env setting OMP/OPENBLAS/MKL/NUMEXPR/VECLIB/BLIS/NUMBA_NUM_THREADS to
  `threads_per_worker` (:663-676); a completed slot starts the next tile (:784-786). Poll loop
  `time.sleep(0.01)` (:757). Failure: reads `job-{index}.failure.json`, re-raises the child
  builtin exception via `_child_exception` (:618-660) else `TileExecutionError` (:762-782).
  Cancellation reaps all children (:787-810). ⇒ imports + JIT warmup are paid PER TILE.
- `runtime_worker.py`: one-shot entry (:39-60); deliberately imports
  `.pipeline` AFTER process startup/env construction (:46-52); `run_tile(**job,
  runtime=RuntimeOptions(**options_data))`; writes failure payload `schema_version 1` with
  exception type/module/args/traceback (:25-36).
- Per-tile lifecycle in `pipeline.run_tile` (`pipeline.py:79-88`): single-job
  `plan_admission`, `runtime_options(options)` context, then `_run_tile`:
  read rasters (:99-104), geometry once per tile via
  `svf_calculator_compact` (:180-184) behind `GeometryStore.get_or_create(geometry_key,...)`
  (:186-190) or trusted legacy load (:170-178); state init (:224-226); timestep loop
  (:252-283) with `writer.checkpoint(i+1,state)` when
  `(i+1)%runtime.checkpoint_interval==0 or i+1==len(timeline.met)` (:279-280); SVF artifacts
  staged into the transaction when not publishing and cache not available (:286-292);
  `writer.complete(extra_artifacts=extra)` (:300).
- Checkpoint/publish protocol: `persistence.py` — atomic fsync + `os.replace`
  (:47-66, :465-475); only the checkpoint pointer commits state + band boundary (:3, :419-434);
  `restore()` (:410+); `complete()` publishes (:483+). `resume` honored at
  `pipeline.py:246-251`.
- v4 runtime additions: NONE. `runtime.py`/`runtime_worker.py` are untouched by 14e88876.
  Persistent workers do NOT exist; `block_pixels` default is 128 (1024 appeared only as
  `candidate_block_pixels` in the frozen promotion protocol cells, set via options in the
  harness, not in source defaults); `threads_per_worker` default is 1 (4 appeared only in
  protocol budgets).

## (e) Stage ordering — `pipeline.py` / `radiation/engine.py` (high level)

Per tile: walls/aspect read → SVF (`svf_calculator_compact`, patch_option=2, pipeline.py:181)
→ cached geometry (15 SVF fields + 3 packed visibility channels; `diffsh=LazyDiffVisibility`
pipeline.py:197; `asvf=_math_profile.asvf(svf)` :195-196) → per-timestep
`Solweig_2022a_calc` (engine.py:1478-1676). Daytime (altitude>0) chronological stages:

1. `ea`/`esky` vapor pressure + sky emissivity (engine.py:1547-1549)
2. `clearnessindex_2013b` → CI; `diffusefraction` → radI/radD (onlyglobal) (1550-1556)
3. `Perez_v3` → patch luminance `lv`; `aniLum`/`dRad` over diffsh (1557-1564)
4. `shadowingfunction_wallheight_23` → vegsh/sh + wall planes; `shadow=sh-(1-vegsh)(1-psi)`
   (1569-1571)  [geometry enters radiation here]
5. Tg/Tgwall diurnal amplitudes; `CI_Tg`/`CI_TgG`; Tg scaling (1575-1591)
6. `gvf_2018a` (1592)  [shadow from stage 4 is an input]
7. `TsWaveDelay_2015a` ×5 → Lup, LupE/S/W/N (1593-1597); TgOut (1598-1599)
8. `cylindric_wedge` → F_sh (1600-1601)
9. `Kdown` (1602); `Kup_veg_2015a` (1603); `Kside_veg_v2022a` (1604)
   [consumes diffsh/shmat/vegshmat/vbshvegshmat + asvf + lv]
10. Night branch (`else`, 1606-1634): zero K*/F_sh, Lup from Stefan-Boltzmann, water override
11. `Lcyl_v2022a` → Ldown/Lside (+directional) (1635-1650)  [consumes Lup from stage 7]
12. `Lside_veg_v2022a` (1658); cardinal adds for cyl/anisotropic combos (1659-1663)
13. `Sstr`, `Tmrt` (1665-1670); return 39-tuple (1676)

Ordering constraints v5 must preserve: aniLum (3) precedes shadows (4) but shares diffsh with
Kside (9); gvf (6) precedes Lup (7); Lcyl (11) needs completed Lup; the second longwave
reflection sweep inside `_longwave` needs the completed ordered sky sweep.

## Uncertainties
- `_wall23`'s `lastv/lastv2` (`prev`-based) samples are part of the vegetation `count`
  predicate; any R01-style absorption proof on THIS trace must handle them separately from
  sky_compiled's three-sample trace.
- `ray_schedule` in sky_compiled and `_build_schedule` in ground_view look algebraically
  identical but are separate implementations with different termination (dz/amaxvalue vs
  int(second)) — deduplicating them is a P0-level identity question, not assumed here.
