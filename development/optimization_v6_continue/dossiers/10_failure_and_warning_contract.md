# D10: failures, warnings and effects are part of an exact specialization

A liveness proof over numeric outputs is incomplete when removed operations can mutate an alias, trigger shape/type errors, emit a warning promoted to error or detect corruption. Default fast paths must not silently change those contracts.

## Use three domains

- Public general domain: original full path and original validation/order, including unsupported inputs.
- Validated owned core domain: private normalized buffers with fixed dtypes/profile and known shape/ownership. Prove that removed numeric nodes have no externally required effects for this domain.
- Instrumented/strict-error domain: retain full diagnostic evaluation unless a precise substitute preserves effects. Do not set np.seterr(ignore) merely to enlarge admission.

Warnings filtered by caller configuration, `np.seterr(raise)`, Python warning filters, mutable input subclasses and scalar views can change the domain. A new guard may be cheaper than all removed math, but must actually certify the skipped operations. Finiteness alone does not rule out divide-by-zero, invalid roots or overflow. Conservative safe bounds/domain checks and original fallback are valid; dropping such inputs from tests is not.

## Boundary examples

Anisotropic Lside may evaluate log(1-SVF) before returning Lup/2. SVF=1 can expose warning/error behavior even though the log does not feed the return. Do not globally early-return public calls without a rule for this. The reduced cylinder kernel's cardinal arithmetic can overflow independently; either prove supported ranges or preserve strict diagnostic fallback.

Multi-worker geometry can finish out of serial order. 'Every tile result is equal' does not prove the same partial public artifacts after a failure. Start with private native precomputation and original ordered publication; expand only with a well-defined ordered commit frontier.

A fused export reader can notice a numeric mismatch before the old CRC-first verifier. Consume/validate the whole structural stream before surfacing mismatch, or invoke the old validator on failure to preserve classification. Producer-side hashes are not stored-byte verification.

Cache identity reuse must survive external input mutation and corrupt payload. Removing a redundant producer does not mean removing the existing guards/ownership that make one result trustworthy. Never forge or restamp an old manifest as proof.

## Pragmatic completion

Exact exception-message byte identity is not automatically required where the established project contract specifies only failure class/condition; use the authoritative contract. Do not invent a stronger global requirement that causes endless work, and do not silently weaken an existing one. Record the actual supported contract and negative tests. A narrower well-proved fast path with a full fallback is preferable to a broad unsafe rewrite or indefinite abstraction redesign.
