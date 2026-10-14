# D05: Geometry work reduction and execution scheduling

Candidates Y01-Y08. Sources S12/S25/S26. Geometry is still needed in cold workloads and can dominate when warm simulation improves.

## Already accepted, do not rebuild
Compact SVF storage, sparse wall angle filters, exact schedules and a guarded no-positive-bush absorption exit are current-main behavior. Preserve them. Continuous horizons, Python hierarchy and other prior failed variants are controls, not new ideas.

## Effective parallelization
Engine exact wall-shadow calls may still request serial kernels. Route to existing parallel versions only within the actual CPU budget and after output/state parity. Each receiver must own all its wall outputs. Count actual thread mask and code route, not only RuntimeOptions. If an outer tile pool uses W processes, inner H respects W*H budget. Geometry and simulation may use different measured W/H settings, but phase barriers and publication semantics remain.

## Bush control separation
Current bush activation is a deterministic global predicate involving shifted canopy scratch and bush values. In a finite admitted domain, it can be prepared from immutable geometry and the exact schedule independently of evolving pixel shadow state. Precompute the complete activation sequence, preserving first-step special handling; then evaluate pixel recurrences using that sequence. A sparse OR over positive bush is valid only if false*NaN/Inf poisoning and negative cases are excluded or reproduced. Include source precision before conversion to float32 scratch.

This can reduce global synchronization and control work from L*N to L*Nb, but remaining pixel recurrence is not L*Nb. Keep original step-major fallback until a full state equivalence proof is tested.

## Certified suffix
For remaining schedule suffix r, use actual stored decrement suffix minima, not assumed monotonic real angles. Bound potential building/canopy/trunk heights with original rounded subtraction and include zero-padding possibility. If all future updates cannot affect any needed output, skip that suffix. No arbitrary radius cutoff. No elevation normalization. Positive-bush and wall-height outputs require their own proof; no reuse of a building-mask-only proof.

The gain is proportional to eliminated sample visits after subtracting bound construction/search overhead. Count raw, existing-absorption, and certificate-pruned samples separately. Existing absorption and new certificates overlap; speedups do not multiply.

## Hierarchy and packetization
Only create a flat compiled hierarchy if measured bound/candidate statistics show enough savings. It must enclose the exact discrete coordinates and preserve update order. Grouping independent receivers may improve SIMD lane efficiency, but extra gather/scatter and exception order matter. Do not sort rays or patches inside one receiver.

## SVF accumulation
The annulus sum can avoid full-plane temporary writes by keeping each original multiplication and accumulator update in a pixel-owned loop. Summing weights first changes rounding and is excluded. Preserve clipping, cardinal interval endpoints, vegetation corrections and patch tables for all supported options. Implement after source audit confirms a significant residual, not because the loop looks large.

## Geometry tests
Open, dense, sparse, vegetation, positive bush, negative elevations, shallow sun, zenith/azimuth boundaries, scale changes, first-step, padding, walls, nonfinite guards and aspect ties. Compare all visibility and SVF fields, not only TMRT. Small grids can test long rays by exact schedule injection into the kernel reference; final logical workload resolution remains unchanged.
