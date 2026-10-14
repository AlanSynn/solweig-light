# D04: Ground-view preparation, finite states and chronology

Candidates G01-G07. Sources S05/S06/S10/S11. The model has 18 directions, original sample sequences and water-dependent mutation order. Keep all of them.

## Initial, low-cost change: serial prepared route
Prepared source expressions and multicore execution are separate decisions. The current engine chooses prepared_gvf_step only when requested H>1. Implement an admitted serial prepared call with parallel=False under H=1, using the same guard union and data ownership as the current prepared path. Do not claim a speedup from H=2 as proof H=1 benefits.

Retain first-direction pre-water Lup, mutation of Tg at the original checkpoint, later-direction Lup, Lwall source rank and alias behavior. The preparation path already encodes stronger alias exclusions. Preserve these rather than broadening admission for convenience. Alias cases retain the characterized per-direction path.

Compare the original serial route with prepared serial and prepared parallel at matched budgets. Default no-env cell must retain main resource semantics. Multi-tile H=1 throughput is a separate metric from one-tile latency.

## Conditional prefix proof
For a binary building flag, original ground visibility f updates monotonically with min. Once f=0, later finite ground terms can be zero, but wall and bush quantities may still change. Let kb be first blocked position in the ACTUAL sample history, including source hold at out-of-range slices. The ground contribution can use the exact prefix only under no-op zero/sign/overflow guarantees.

Wall contributions cannot be dropped. Where they are repeated additions of a fixed c, prepare A_c(0)=+0 and A_c(n+1)=RN(A_c(n)+c). Lookup by exact activation count reproduces all roundings; n*c does not. Different first/second search checkpoints may need different counts. Proof must cover all 16 intermediates before claiming final equivalence.

Expected work model, not measured speed:

    old = Td * N * D * R * c_step
    new = Cprepare + Td * N * D * (kbar*c_step + c_state)

Open scenes with kbar≈R may lose. Table kinds must remain few enough to amortize. Store kb as a bounded integer ND descriptor, not a full NDR address tensor. Cache only geometry-dependent descriptors; dynamic sunwall still belongs to timestep work.

## Static subfield reuse
Unshadowed albedo total/cardinal fields may depend only on geometry/material. Trace the graph to prove this before caching. Never cache full Lup/radiance or full GVF merely because geometry is static. Include albedo, scale, directions, preprocessing and math profile in identity. Evaluate cost of five extra full fields against saved recurrence across daytime steps.

## Thermal maps
TsWaveDelay updates carry chronological state. A compiled same-step pointwise chain may combine reads/writes across independent map instances, but old buffers must remain live until all neighboring reads finish. No affine closed-form, prefix scan, independent-hour task or chronological reorder. Preserve firstdaytime, timeadd, TgOut1, all directional Tgmap fields and type tags in checkpoints.

## Tests and termination
L1 compare all intermediate gather channels and mutation side effects. L2 actual 24/48-hour day/night and restart with landcover, water fixture, no landcover, aliasing and nonfloat32 fallbacks. Run required physics checks separately from upstream parity. If G01 is beneficial and prefix work is low ROI, ship G01 and stop this family rather than implementing every theoretical variant.
