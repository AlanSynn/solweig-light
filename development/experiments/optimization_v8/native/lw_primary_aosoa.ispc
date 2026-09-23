// lw_primary_aosoa.ispc -- N8-13 native consumer of the direct AoSoA lane
// layout (dossier 02_direct_aosoa; producer: N8-11 experiments/
// optimization_v8/layout/direct_aosoa.py).
//
// Typed graph: IDENTICAL to lw_primary.ispc (B7-20), the exact port of
// solweig_light.radiation.cylinder_longwave._longwave_primary frozen at
// 16cdc56c (kernel bodies identical to the B7-02 freeze at dca2035c,
// reducer blob 27ba6ce4...). Two ordered patch sweeps, ten float32
// accumulators a0..a9 per pixel, reflection barrier on the completed
// first-sweep a0+lup, f64 surface chains for the f64 specialization
// (a = RN32(f64(a) + c64)), true IEEE division by the stored float32 pi
// bits 0x40490FDB, number (not branch) multiplies for every predicate, no
// tree reductions. Only the input ADDRESSING changes:
//
//   sh/vs/vb  arrive as the producer's uint32 [G,P,W] payload viewed
//             float32 (zero-cost .view(np.float32), W=8, G=ceil(B/8),
//             native element ((g*P+p)*W+lane) == the original V[x,p]
//             IEEE-754 bit pattern for x=g*W+lane);
//   sun/shade arrive as uint8 0/1 in the same [G,P,W] layout.
//
// Execution model: one ISPC gang (neon-i32x8, programCount==8) processes
// exactly ONE AoSoA gang -- ISPC lane l IS data lane l -- so every
// per-(g,p) 8-lane load is one CONTIGUOUS vector access: no gather, which
// is the entire point of the layout (the B7 dense kernel's per-(x,p)
// loads are P-strided gathers). Gangs iterate in a plain uniform loop:
// the kernel is single-threaded and parallelism stays at the block level.
//
// Padding lanes (x >= B in the final gang) are NEVER read: the producer
// never writes them and the consumer redirects every off-lane AoSoA/lup
// index to an always-valid lane/row BEFORE the load (lane_r = valid ?
// lane : 0; the tail gang's lane 0 is valid by construction) and masks
// the output store. Full gangs contain no padding by construction and
// use raw unmasked contiguous loads/stores.
//
// float32 rounding node map: unchanged from lw_primary.ispc --
//   np.float32(f32 + f32)      -> f32 add
//   np.float32(f32 + f64chain) -> f64 add + f64->f32 round-to-nearest-even
//   bool * float               -> (bool ? 1.0 : 0.0) * float number multiply
//   np.float32(np.pi)          -> bit reinterpretation of 0x40490FDB
//
// Build contract (unchanged): -O2 --opt=disable-fma --math-lib=default,
// no --fast-math, target neon-i32x8. The emitted assembly is audited for
// fused multiply-add mnemonics and for approximate-reciprocal mnemonics
// (vrecpe/vrecps/vrsqrte/vrsqrts) that would replace the true division;
// the audit ships with the generation manifest and the N8-13 evidence.

static inline float f32_pi() {
    uniform uint32 bits = 0x40490FDBu; // np.float32(np.pi), exact bits
    return *((uniform float *uniform)&bits);
}

// Compile-time lane-width pin (ISPC 1.31 has no static_assert): the W=8
// AoSoA layout requires an 8-lane gang, so a non-neon-i32x8 build fails
// to compile instead of silently misindexing.
static uniform int _lw_aosoa_lane_width_check[(programCount == 8) ? 1 : -1];

// BODY: one AoSoA gang's worth of the frozen per-pixel graph.
//   GANG: uniform gang index g. LANE: (guaranteed-valid) lane index used
//   for every [G,P,W] payload read. ROW: the (valid) pixel row used for
//   the lup read. MASK: store mask -- literal 1 for full gangs (folds to
//   unmasked stores), `lane < tail` for the final partial gang.
// Lanes are independent (no cross-lane operation anywhere), so per-lane
// semantics are exactly the frozen kernel's per-pixel semantics.
#define LW_AOSOA_BODY(ST, GANG, LANE, ROW, MASK)                                          \
    {                                                                                     \
        float a0 = 0.0f, a1 = 0.0f, a2 = 0.0f, a3 = 0.0f, a4 = 0.0f;                      \
        float a5 = 0.0f, a6 = 0.0f, a7 = 0.0f, a8 = 0.0f, a9 = 0.0f;                      \
        const int64 base = ((GANG) * P) * 8;                                              \
        for (uniform int64 p = 0; p < P; ++p) {                                           \
            const int64 idx = base + p * 8 + (LANE);                                      \
            const float shv = sh[idx];                                                    \
            const float vsv = vs[idx];                                                    \
            const float vbv = vb[idx];                                                    \
            const bool sky = (shv == 1.0f) && (vsv == 1.0f);                              \
            const bool veg = (vsv == 0.0f) || (vbv == 0.0f);                              \
            const bool building = ((1.0f - shv) * vbv) == 1.0f;                           \
            const float skyf = sky ? 1.0f : 0.0f;                                         \
            const float vegf = veg ? 1.0f : 0.0f;                                         \
            const float buif = building ? 1.0f : 0.0f;                                    \
            a0 = a0 + skyf * sky_down[p * sd_str];                                        \
            a5 = a5 + skyf * sky_side[p * ss_str];                                        \
            const ST vside = (((ST)surface_sh * (ST)solid[p]) * (ST)cosine[p]) * (ST)vegf;    \
            const ST vdown = (((ST)surface_sh * (ST)solid[p]) * (ST)sine[p]) * (ST)vegf;      \
            a6 = (float)((ST)a6 + vside);                                                 \
            a1 = (float)((ST)a1 + vdown);                                                 \
            if (solar_gate[p] != 0) {                                                     \
                const float sunf = (sun[idx] != 0) ? 1.0f : 0.0f;                         \
                const float shaf = (shade[idx] != 0) ? 1.0f : 0.0f;                       \
                const ST sun_side = ((((ST)surface_sun * (ST)sunf) * (ST)solid[p]) * (ST)cosine[p]) * (ST)buif;      \
                const ST shade_side = ((((ST)surface_sh * (ST)shaf) * (ST)solid[p]) * (ST)cosine[p]) * (ST)buif;     \
                const ST sun_down = ((((ST)surface_sun * (ST)sunf) * (ST)solid[p]) * (ST)sine[p]) * (ST)buif;        \
                const ST shade_down = ((((ST)surface_sh * (ST)shaf) * (ST)solid[p]) * (ST)sine[p]) * (ST)buif;       \
                a8 = (float)((ST)a8 + sun_side);                                          \
                a7 = (float)((ST)a7 + shade_side);                                        \
                a3 = (float)((ST)a3 + sun_down);                                          \
                a2 = (float)((ST)a2 + shade_down);                                        \
            } else {                                                                      \
                const ST shade_side = (((ST)surface_sh * (ST)solid[p]) * (ST)cosine[p]) * (ST)buif; \
                const ST shade_down = (((ST)surface_sh * (ST)solid[p]) * (ST)sine[p]) * (ST)buif;   \
                a7 = (float)((ST)a7 + shade_side);                                        \
                a2 = (float)((ST)a2 + shade_down);                                        \
            }                                                                             \
        }                                                                                 \
        const float r0 = a0 + lup[(ROW)];                                                 \
        const float r1 = r0 * reflection_factor;                                          \
        const float r2 = r1 * 0.5f;                                                       \
        const float reflected = r2 / f32_pi();                                            \
        for (uniform int64 p = 0; p < P; ++p) {                                           \
            const int64 idx = base + p * 8 + (LANE);                                      \
            const float shv = sh[idx];                                                    \
            const float vsv = vs[idx];                                                    \
            const float vbv = vb[idx];                                                    \
            const bool occl = (shv == 0.0f) || (vsv == 0.0f) || (vbv == 0.0f);            \
            const float occlf = occl ? 1.0f : 0.0f;                                       \
            a9 = a9 + ((reflected * solid[p]) * cosine[p]) * occlf;                       \
            a4 = a4 + ((reflected * solid[p]) * sine[p]) * occlf;                         \
        }                                                                                 \
        if ((MASK)) {                                                                     \
            const int64 orow = (((GANG) * 8 + (int64)programIndex) * 7);                  \
            out[orow + 0] = (((a0 + a1) + a2) + a3) + a4;                                 \
            out[orow + 1] = (((a5 + a6) + a7) + a8) + a9;                                 \
            out[orow + 2] = a5;                                                           \
            out[orow + 3] = a6;                                                           \
            out[orow + 4] = a7;                                                           \
            out[orow + 5] = a8;                                                           \
            out[orow + 6] = a9;                                                           \
        }                                                                                 \
    }

// SUFFIX/ST semantics identical to lw_primary.ispc: f32 keeps the surface
// chains float32; f64 computes them float64 and rounds once at the
// accumulator add (a = RN32(f64(a) + c64)).
#define LW_PRIMARY_AOSOA(SUFFIX, ST)                                                      \
export void lw_primary_##SUFFIX(                                                          \
        uniform const float *uniform sh,   /* [G,P,8] float32 view of uint32 payload */   \
        uniform const float *uniform vs,   /* [G,P,8] */                                  \
        uniform const float *uniform vb,   /* [G,P,8] */                                  \
        uniform const uint8 *uniform sun,  /* [G,P,8] uint8 0/1 */                        \
        uniform const uint8 *uniform shade,/* [G,P,8] uint8 0/1 */                        \
        uniform const float *uniform solid,     /* [P] */                                \
        uniform const float *uniform sine,       /* [P] */                               \
        uniform const float *uniform cosine,     /* [P] */                               \
        uniform const uint8 *uniform solar_gate, /* [P] uint8 0/1 */                     \
        uniform const float *uniform sky_down,   /* [P], element stride sd_str */         \
        uniform int64 sd_str,                                                           \
        uniform const float *uniform sky_side,   /* [P], element stride ss_str */         \
        uniform int64 ss_str,                                                           \
        uniform ST surface_sun, uniform ST surface_sh,                                    \
        uniform const float *uniform lup,        /* [B] */                               \
        uniform float reflection_factor,                                                \
        uniform int64 B, uniform int64 P,                                               \
        uniform float *uniform out)             /* [B*7], owned by caller */             \
{                                                                                       \
    const uniform int64 full = B / 8;   /* full gangs: every lane a valid pixel */       \
    const uniform int64 tail = B - full * 8;                                            \
    const int64 lane = (int64)programIndex;                                             \
    for (uniform int64 g = 0; g < full; ++g)                                             \
        LW_AOSOA_BODY(ST, g, lane, g * 8 + lane, 1)                                      \
    if (tail != 0) {                                                                    \
        /* Final partial gang: off-lane payload/lup indices redirect to the  */         \
        /* always-valid lane 0 / row gang*8 BEFORE the load, so padding     */         \
        /* bytes are never read; stores are masked to the valid lanes.      */         \
        const int64 lane_r = (lane < tail) ? lane : (int64)0;                           \
        LW_AOSOA_BODY(ST, full, lane_r, full * 8 + lane_r, lane < tail)                  \
    }                                                                                   \
}

LW_PRIMARY_AOSOA(f32, float)
LW_PRIMARY_AOSOA(f64, double)
