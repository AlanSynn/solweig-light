# D10: Real-algebra and operational alternatives, NOT default authorization

Candidates Q01-Q06. These are included because the user requested a broad search space. They are not silently permitted implementations. Current exact/scientific contracts remain frozen.

## Band operator factorization
If a real-valued component is L[x,t]=sum_p V[x,p]w[p]E[band(p),t], define H[x,b]=sum_{p in b}V[x,p]w[p]. Then L=sum_b H[x,b]E[b,t]. Eligible sky work changes O(TNP) to O(NP+TN*Bands), but original per-patch float32 multiplication and ordered rounding generally differ. Reflection and dynamic sun/shade masks are not automatically included. Existing rejected angular-moment experiments must be read before repeating this family.

A new numerical-policy study would need two separate rounding-error analyses, for original and factored graphs, plus empirical adversarial testing. For finite sums a gamma_n*sum(abs(terms)) style bound can guide analysis, but actual mixed precision, multiplication rounding, cancellation, zeros and nonfinite behavior must be included. Scientific uncertainty is not permission to relax software parity after failure.

Tmrt=(S/c)^(1/4)-273.2, c=absL*SBC. For S bounded away from zero, dTmrt/dS=1/(4*c^(1/4)*S^(3/4)). This can bound amplification of a PROVEN radiation error over a known positive S interval. It does not certify UTCI/WBGT or arbitrary low/negative S. Those have their own nonlinear/iterative propagation. No new tolerance is chosen from observed candidate failure.

## BLAS, tensor contraction, FFT and scans
A matrix formulation may improve arithmetic intensity but BLAS/tree reduction/FMA changes operation order. Many shadow/ground-view paths are not translationally invariant linear operators because visibility, discrete schedules, padding and mutations matter. FFT convolution and continuous horizon replacement cannot be called exact without a discrete operator proof. Time scans are incompatible with chronological nonlinear state unless a separate exact composition law is proven; real affine algebra alone is insufficient under rounding.

## Operational changes
Fewer outputs, weaker content checks, less frequent checkpoints, shortened rays, fewer patches, lower resolution and reduced timesteps can all be faster because they change the task. None can count toward the unchanged-DX/default optimization goal. If later authorized, publish a new named policy and compare equal workloads within that policy. Hardware, power and extra cores are explicit resource changes, not code improvements.

## Research closure
Design-only items receive a documented boundary and remain disabled. They must not keep the exact campaign open, spawn endless experiments or become fallback excuses when the exact candidate fails. The release can close successfully with a qualified CPU optimization or unchanged retained implementation and honest limitations.
