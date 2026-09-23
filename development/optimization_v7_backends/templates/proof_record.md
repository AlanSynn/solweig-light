# Candidate proof and review record

Status: proposed / implemented / independently_verified / rejected / blocked.
Source SHA and actual native dependency/profile/compiler/ISA fingerprints:
Author identity and reviewer identity (must differ):
Assigned input corpus and untouched baseline capture hash:

## Scope

Actual called function; A/B/C boundary; supported dtypes/scalar origins/shapes/strides;
all outputs/state/mutations/errors; original loop and cast order; fallback conditions.

## Proof

State map and induction for both patch sweeps; intermediate typed operations;
no new FMA/reassociation/reciprocal change; alias/lifetime/async safety;
raw/nonfinite/signed-zero and tail treatment; compiler IR evidence.

## Executed checks

Exact commands, source/env, scope and output logs. Abstract tests versus real kernel
versus TIFF separated. Retained counterexamples/failures. Any missing reference.

## Cost and selection

Full adapter/pipeline results, compile/packing/transfer costs, native pool,
workspace and fallback counts. All numbers measured or explicitly hypothetical.

## Independent verdict

Accept / conditions / reject / unavailable with reasons; condition closure hashes.
No source changes after this record are covered without an affected re-review.
