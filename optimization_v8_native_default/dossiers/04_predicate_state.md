# Conditional E4: exact longwave observation-state cache

## Do not confuse this with bool-casting visibility

Original sh/vs/vb may be binary, ternary or raw floats and must remain intact for SVF, shortwave, diagnostics and export. Only the selected longwave consumer can use a derived state if every original read factors through it.

For the frozen typed predicate definitions:

```
sky = (sh==1) and (vs==1)
veg = (vs==0) or (vb==0)
wall = (RN32(RN32(1)-sh) * vb) == 1  # actual native f32 product retained
refl = (sh==0) or (vs==0) or (vb==0)
q = sky | (veg<<1) | (wall<<2) | (refl<<3)
```

The formal obligation is `F(sh,vs,vb,dynamic)=Fq(q(sh,vs,vb),dynamic)` for every admitted input. Map all accesses in both longwave sweeps. Sun/shade classification, sky coefficients, reflection from first-sweep A0 and Lup stay dynamic. The code does not make ground-view radiance static.

## Lifetime and encoding

Compute q once per immutable geometry/profile/consumer version. Use either byte codes or packed nibbles; make decoder emit directly to AoSoA if that wins. Preserve original visibility files. q key includes complete source geometry identity, exact predicate code/compiler policy, version and patch order. `q` memory supplements original packed channels; never present it as a universal RAM reduction.

At N=1024^2,P=153, byte q costs 153MiB, packed q costs 76.5MiB; three binary original channels cost about 57.375MiB. Admission must count both, or use bounded/on-disk derived storage. This is a work/traffic optimization whose memory tradeoff can be unfavorable.

## Break-even

`C_prepare + T*C_readq < T*(C_decode3 + C_predicate)` is the first estimate. Add integrity checks, cache load, packing and pressure on other workers. If only a few time records run, constructing q may lose. Scope crossover selection before deployment and retain original region when preparation cannot be amortized.

## Numeric edge conditions

A q predicate evaluated once can change warnings if repeated nonfinite arithmetic is removed. Initially admit finite inputs satisfying the exact private route contract and keep the general path. Alternatively reproduce the original observable diagnostics in a separately validated boundary. Never skip a later contribution merely because q has a zero bit; the reference multiplies by zero, and 0*Inf/signed zero remain meaningful.

Categorical partial evaluation must retain f64 chains when the surface scalar is f64, including the addition to the accumulator before RN32. Store exact intermediate values in their original type. Do not combine separate terms or reflection's second sweep into pre-summed angular moments. Previously rejected moments are not revived without a new proof and cost mechanism.

## Test and select

Enumerate binary/ternary input combinations; add actual raw finite floats near predicate thresholds and signed zero. Compare predicate bits from original compiled expression, all seven LW outputs, actual small chronology and full original exports. Exercise identity changes, byte corruption, stale q, budget exhaustion and fallback. Count preparation and actual saved decodes across timesteps.

Activate only if real packed-path region costs make it worthwhile. If direct AoSoA alone wins without q, avoid this added cache until another profile shows need.
