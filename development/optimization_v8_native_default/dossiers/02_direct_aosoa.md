# E2: direct producer-to-consumer AoSoA, not an extra transpose

## Hypothesis

Prior B's kernel was faster than C but B lost adapter timing because it paid a layout transform. The next design removes the transform, rather than retiming an already rejected adapter. Compare a direct AoSoA producer feeding B and C.

## Layout definition

Let W be the selected lane width and G=ceil(B/W). Store a channel in `[G,P,W]` C order. Native index is `((g*P+p)*W+lane)`. For valid pixel x=g*W+lane, this contains exactly the original V[x,p] bit pattern. W is an implementation scheduling parameter, not a physical resolution change.

Write bytes directly from the known packed stream into the final location. Binary/ternary codes map to their original IEEE uint32 constants; raw payloads use the same endian assembly/bitcast. Do not numerically convert arbitrary raw uint32 to float. Never cast original visibility to bool. Handle every valid B tail without loading outside the payload or producing a real result for padding lanes.

Begin with one channel and serial producer to prove layout bits. Then three-channel production in a single entry; use either patch-major/gang/pixel-inner loops or blocked loops and measure cache behavior. Do not flatten/copy all encoded payloads merely to avoid a typed-list without counting the cost and ownership.

## Observable decoder semantics

Known immutable PackedVisibility/MappedVisibility get the new route only with a held owner lease and validated descriptor. Duck types, subclasses with custom indexing and unsupported lazy leaves retain legacy behavior. Reserved categorical codes and range errors may be observable in patch-major order. Private accepted descriptors can prevalidate all needed stream bytes once with the original order, but cannot simply stop validating corrupt inputs. If a faster decode changes error precedence, use a pre-launch validation pass or guarded diagnostic fallback and include its cost.

Keep mmap owner alive through native work. Returned view lifetime must not exceed its owned arena. The old public decoder remains available and all roundtrip/export tests still operate on original channels.

## Classification production

Stage 1: keep accepted sun/shade in original layout and count their packing, isolating decoder gain. Stage 2: produce both Boolean mask arrays in AoSoA using the same `_classes_table`/SLEEF arithmetic, active patch set, coefficient cast and strict comparisons. Both bits can be false at an equality/NaN boundary, so shade is not always not-sun. Current R04/G06 already perform some exact tables; do not reimplement them as new wins.

Do not coarsen ASVF or invert atan to a different floating comparison. Any math routine whose fallback depends on vector shape must be held at the old logical block boundary until full equivalence tests allow regrouping.

## Controls and measurements

A: unchanged accepted producer + reducer. B0: old pack-to-AoSoA + B kernel. B1: direct AoSoA producer + same B kernel. C1: same producer + native AoSoA kernel. Report producer, classifier, kernel, adapter/region and actual small pipeline totals, with allocated bytes and thread masks. B1 can win without native; retain that valid outcome.

W choices are a tiny ISA-specific shortlist, for example current W=8 and a native-lane candidate. This is not license to sweep dozens of widths. Tails 1/W-1/W/W+1/primes, P=1/153/609, binary/ternary/raw mixtures, invalid code, strided input and mutable aliases must be covered. Source comparison should preserve `.view(uint32)` identity for decode and the original accumulator bits for reduction.

## Completion

Direct production must reach a real chronological pipeline, not only a synthesized array benchmark. Do not add a new native default if B1 wins equal-policy total time. Preserve the distinction between producer/layout gain and backend gain in the final table.
