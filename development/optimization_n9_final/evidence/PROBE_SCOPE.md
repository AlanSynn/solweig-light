# Executed in this chat: isolated decode experiment only

The supplied core is a manual transcription of the current producer's arithmetic and loop order, not an imported SOLWEIG function. Its results are compared with an independent bit encoder/expectation. All API/mmap/owner/classifier/native/pipeline behavior remains untested here.

Initial experiment: generic versus literal mode branch. The raw implementation regressed at B=128 and B=1024; preserved in decoder_probe_result.json. A second narrowly causal variant kept the original raw full-gang/tail loop structure; both original candidates are retained in decoder_probe.py and decoder_probe_result_v2.json. No architecture or threshold changes were made after the measurements.

Second run: 64 width/start/shape cases, 57,984 independently expected uint32 payload values, 15 reserved-code error checks across the three functions. Each timing cell contains nine alternating paired/triple batches, each five calls; reported medians are local raw data, not statistical certification. Fastest selection is not a project candidate recommendation. In particular raw speed is approximately tied and small changes can reverse with noise.

Width=8, P=153, B=1024, generic/raw-preserved observed ratios were approximately 1.63 binary, 1.36 mixed, 1.03 raw. Wrapper/packing/leases/parallel scheduling and application output are excluded. x86 code inspection found fewer integer divide instruction lines in the literal versions, but this does not certify the corresponding M1 compiler's output. Inspect that target independently.
