	.build_version macos, 26, 0
	.section	__TEXT,__text,regular,pure_instructions
	.globl	__ZN18longwave_primary_b23make_longwave_primary_b12_3clocals_3e26_longwave_primary_b_packedB3v21B90c8tJTC_2fWQAliW1xhDEoY6EEMEUOEMISPGsAQMVj4QniQ4IXKQEMXwoMGLoQDDVsQR1NHAS2hQ9XgStYwm4ogLE0AE5ArrayIfLi3E1C7mutable7alignedE5ArrayIfLi3E1C7mutable7alignedE5ArrayIfLi3E1C7mutable7alignedE5ArrayIbLi3E1C7mutable7alignedE5ArrayIbLi3E1C7mutable7alignedE5ArrayIfLi1E1C7mutable7alignedE5ArrayIfLi1E1C7mutable7alignedE5ArrayIfLi1E1C7mutable7alignedE5ArrayIbLi1E1C7mutable7alignedE5ArrayIfLi1E1A7mutable7alignedE5ArrayIfLi1E1A7mutable7alignedEff5ArrayIfLi2E1C7mutable7alignedEfx
	.p2align	2
__ZN18longwave_primary_b23make_longwave_primary_b12_3clocals_3e26_longwave_primary_b_packedB3v21B90c8tJTC_2fWQAliW1xhDEoY6EEMEUOEMISPGsAQMVj4QniQ4IXKQEMXwoMGLoQDDVsQR1NHAS2hQ9XgStYwm4ogLE0AE5ArrayIfLi3E1C7mutable7alignedE5ArrayIfLi3E1C7mutable7alignedE5ArrayIfLi3E1C7mutable7alignedE5ArrayIbLi3E1C7mutable7alignedE5ArrayIbLi3E1C7mutable7alignedE5ArrayIfLi1E1C7mutable7alignedE5ArrayIfLi1E1C7mutable7alignedE5ArrayIfLi1E1C7mutable7alignedE5ArrayIbLi1E1C7mutable7alignedE5ArrayIfLi1E1A7mutable7alignedE5ArrayIfLi1E1A7mutable7alignedEff5ArrayIfLi2E1C7mutable7alignedEfx:
	.cfi_startproc
	stp	d11, d10, [sp, #-128]!
	stp	d9, d8, [sp, #16]
	stp	x28, x27, [sp, #32]
	stp	x26, x25, [sp, #48]
	stp	x24, x23, [sp, #64]
	stp	x22, x21, [sp, #80]
	stp	x20, x19, [sp, #96]
	stp	x29, x30, [sp, #112]
	sub	sp, sp, #1472
	.cfi_def_cfa_offset 1600
	.cfi_offset w30, -8
	.cfi_offset w29, -16
	.cfi_offset w19, -24
	.cfi_offset w20, -32
	.cfi_offset w21, -40
	.cfi_offset w22, -48
	.cfi_offset w23, -56
	.cfi_offset w24, -64
	.cfi_offset w25, -72
	.cfi_offset w26, -80
	.cfi_offset w27, -88
	.cfi_offset w28, -96
	.cfi_offset b8, -104
	.cfi_offset b9, -112
	.cfi_offset b10, -120
	.cfi_offset b11, -128
	mov.16b	v10, v2
	mov.16b	v9, v1
	mov.16b	v8, v0
	stp	x6, x7, [sp, #472]
	str	x1, [sp, #432]
	str	x0, [sp, #520]
	ldr	x8, [sp, #2400]
	str	x8, [sp, #544]
	ldr	x22, [sp, #2328]
	ldr	x23, [sp, #2272]
	ldr	x20, [sp, #2216]
	ldr	x8, [sp, #2160]
	str	x8, [sp, #552]
	ldr	x28, [sp, #2104]
	ldr	x8, [sp, #2048]
	str	x8, [sp, #560]
	ldr	x24, [sp, #1992]
	ldr	x25, [sp, #1904]
	ldr	x26, [sp, #1816]
	ldr	x21, [sp, #1728]
	ldr	x27, [sp, #1640]
	str	xzr, [sp, #1448]
	str	xzr, [sp, #1432]
	str	xzr, [sp, #1416]
	str	xzr, [sp, #1384]
	str	xzr, [sp, #1344]
	str	xzr, [sp, #1336]
	str	xzr, [sp, #1328]
	str	xzr, [sp, #1176]
	str	xzr, [sp, #1168]
	str	xzr, [sp, #1160]
	str	xzr, [sp, #1152]
	str	wzr, [sp, #1148]
	str	xzr, [sp, #928]
	str	xzr, [sp, #568]
Lloh0:
	adrp	x19, _NRT_incref@GOTPAGE
Lloh1:
	ldr	x19, [x19, _NRT_incref@GOTPAGEOFF]
	str	x2, [sp, #528]
	mov	x0, x2
	blr	x19
	str	x27, [sp, #488]
	mov	x0, x27
	blr	x19
	str	x21, [sp, #496]
	mov	x0, x21
	mov	x21, x20
	mov	x20, x23
	blr	x19
	str	x26, [sp, #536]
	mov	x0, x26
	blr	x19
	str	x25, [sp, #512]
	mov	x0, x25
	ldr	x25, [sp, #560]
	ldr	x23, [sp, #552]
	blr	x19
	mov	x0, x24
	blr	x19
	mov	x0, x25
	blr	x19
	str	x28, [sp, #504]
	mov	x0, x28
	blr	x19
	mov	x0, x23
	blr	x19
	mov	x0, x21
	blr	x19
	mov	x0, x20
	blr	x19
	str	x22, [sp, #464]
	mov	x0, x22
	blr	x19
	ldr	x19, [sp, #544]
	tbnz	x19, #63, LBB0_8
	lsl	x8, x19, #3
	sub	x22, x8, x19
	mov	w8, #7
	smulh	x8, x19, x8
	cmp	x8, x22, asr #63
Lloh2:
	adrp	x8, _.const.picklebuf.58e14eccb507b1e0206981740223e685cb8c3c57@GOTPAGE
Lloh3:
	ldr	x8, [x8, _.const.picklebuf.58e14eccb507b1e0206981740223e685cb8c3c57@GOTPAGEOFF]
	b.ne	LBB0_13
	mov	x9, #-2305843009213693952
	add	x9, x22, x9
	lsr	x9, x9, #62
	cmp	x9, #3
	b.lo	LBB0_13
	lsl	x0, x22, #2
Lloh4:
	adrp	x8, _NRT_MemInfo_alloc_aligned@GOTPAGE
Lloh5:
	ldr	x8, [x8, _NRT_MemInfo_alloc_aligned@GOTPAGEOFF]
	mov	w1, #32
	blr	x8
	cbz	x0, LBB0_9
	mov	x27, x0
	stp	x24, x20, [sp, #448]
	ldr	x28, [x0, #24]
	sub	x8, x19, #1
	str	xzr, [sp, #1456]
	str	xzr, [sp, #1448]
	mov	w9, #6
	str	x8, [sp, #1432]
	str	x9, [sp, #1440]
Lloh6:
	adrp	x8, _get_num_threads@GOTPAGE
Lloh7:
	ldr	x8, [x8, _get_num_threads@GOTPAGEOFF]
	blr	x8
	mov	x24, x0
Lloh8:
	adrp	x8, _get_parallel_chunksize@GOTPAGE
Lloh9:
	ldr	x8, [x8, _get_parallel_chunksize@GOTPAGEOFF]
	blr	x8
	cmp	x24, #1
	b.lt	LBB0_10
	mov	x23, x0
	str	x21, [sp, #440]
	add	x8, x19, #7
	asr	x21, x8, #3
Lloh10:
	adrp	x8, _get_sched_size@GOTPAGE
Lloh11:
	ldr	x8, [x8, _get_sched_size@GOTPAGEOFF]
	add	x2, sp, #1448
	add	x3, sp, #1432
	mov	x0, x24
	mov	w1, #2
	blr	x8
	mov	x25, x0
Lloh12:
	adrp	x20, _set_parallel_chunksize@GOTPAGE
Lloh13:
	ldr	x20, [x20, _set_parallel_chunksize@GOTPAGEOFF]
	mov	x0, #0
	blr	x20
	lsl	x0, x25, #2
Lloh14:
	adrp	x8, _allocate_sched@GOTPAGE
Lloh15:
	ldr	x8, [x8, _allocate_sched@GOTPAGEOFF]
	blr	x8
	mov	x24, x0
Lloh16:
	adrp	x8, _do_scheduling_unsigned@GOTPAGE
Lloh17:
	ldr	x8, [x8, _do_scheduling_unsigned@GOTPAGEOFF]
	add	x1, sp, #1448
	add	x2, sp, #1432
	mov	w0, #2
	mov	x3, x25
	mov	x4, x24
	mov	x5, #0
	blr	x8
	str	x24, [sp, #1416]
	str	x28, [sp, #1424]
	mov	w8, #4
	str	x25, [sp, #1384]
	str	x8, [sp, #1392]
	mov	w9, #7
	str	x19, [sp, #1400]
	str	x9, [sp, #1408]
	mov	w9, #32
	str	x9, [sp, #1344]
	str	xzr, [sp, #1352]
	mov	w9, #8
	mov	w10, #28
	str	x9, [sp, #1360]
	str	x10, [sp, #1368]
	str	x8, [sp, #1376]
	str	wzr, [sp, #1468]
Lloh18:
	adrp	x8, _numba_gil_ensure@GOTPAGE
Lloh19:
	ldr	x8, [x8, _numba_gil_ensure@GOTPAGEOFF]
	add	x0, sp, #1468
	blr	x8
Lloh20:
	adrp	x8, _PyEval_SaveThread@GOTPAGE
Lloh21:
	ldr	x8, [x8, _PyEval_SaveThread@GOTPAGEOFF]
	blr	x8
	mov	x25, x0
Lloh22:
	adrp	x26, _get_num_threads@GOTPAGE
Lloh23:
	ldr	x26, [x26, _get_num_threads@GOTPAGEOFF]
	blr	x26
	mov	x7, x0
Lloh24:
	adrp	x0, ___gufunc__._ZN13_3cdynamic_3e33__numba_parfor_gufunc_0x10c3c2c00B3v22B106c8tJTC_2fWQAliW1xhDEoY6EEMEUOEMISPGsAQMVj4QniQ4IXKQEMXwoMGLoQDDVsQR1NHAS2hQ9XgStYwaUTI24JtBVoOCV2YU4ogSjUBE5ArrayIyLi1E1C7mutable7alignedE5ArrayIfLi2E1C7mutable7alignedE@GOTPAGE
Lloh25:
	ldr	x0, [x0, ___gufunc__._ZN13_3cdynamic_3e33__numba_parfor_gufunc_0x10c3c2c00B3v22B106c8tJTC_2fWQAliW1xhDEoY6EEMEUOEMISPGsAQMVj4QniQ4IXKQEMXwoMGLoQDDVsQR1NHAS2hQ9XgStYwaUTI24JtBVoOCV2YU4ogSjUBE5ArrayIyLi1E1C7mutable7alignedE5ArrayIfLi2E1C7mutable7alignedE@GOTPAGEOFF]
Lloh26:
	adrp	x8, _numba_parallel_for@GOTPAGE
Lloh27:
	ldr	x8, [x8, _numba_parallel_for@GOTPAGEOFF]
	add	x1, sp, #1416
	add	x2, sp, #1384
	add	x3, sp, #1344
	mov	x4, #0
	mov	w5, #3
	mov	w6, #2
	blr	x8
Lloh28:
	adrp	x8, _PyEval_RestoreThread@GOTPAGE
Lloh29:
	ldr	x8, [x8, _PyEval_RestoreThread@GOTPAGEOFF]
	mov	x0, x25
	blr	x8
Lloh30:
	adrp	x8, _numba_gil_release@GOTPAGE
Lloh31:
	ldr	x8, [x8, _numba_gil_release@GOTPAGEOFF]
	add	x0, sp, #1468
	blr	x8
	mov	x0, x23
	blr	x20
Lloh32:
	adrp	x8, _deallocate_sched@GOTPAGE
Lloh33:
	ldr	x8, [x8, _deallocate_sched@GOTPAGEOFF]
	mov	x0, x24
	blr	x8
	sub	x8, x21, #1
	str	xzr, [sp, #1336]
	str	x8, [sp, #1328]
	blr	x26
	mov	x24, x0
Lloh34:
	adrp	x8, _get_parallel_chunksize@GOTPAGE
Lloh35:
	ldr	x8, [x8, _get_parallel_chunksize@GOTPAGEOFF]
	blr	x8
	mov	x1, x0
	mov	x0, x24
	cmp	x24, #0
	b.le	LBB0_11
	ldr	x9, [sp, #2392]
	ldr	x8, [sp, #2384]
	stp	x8, x9, [sp, #384]
	ldr	x9, [sp, #2376]
	ldr	x8, [sp, #2368]
	stp	x8, x9, [sp, #168]
	ldr	x9, [sp, #2360]
	ldr	x10, [sp, #2320]
	ldr	x8, [sp, #2312]
	str	x8, [sp, #192]
	ldr	x8, [sp, #2304]
	stp	x8, x9, [sp, #136]
	ldr	x8, [sp, #2264]
	stp	x8, x10, [sp, #408]
	ldr	x9, [sp, #2256]
	ldr	x10, [sp, #2248]
	ldr	x8, [sp, #2208]
	str	x8, [sp, #400]
	ldr	x8, [sp, #2200]
	stp	x8, x9, [sp, #152]
	ldr	x9, [sp, #2192]
	ldr	x8, [sp, #2152]
	str	x8, [sp, #288]
	ldr	x8, [sp, #2144]
	stp	x8, x9, [sp, #96]
	ldr	x9, [sp, #2136]
	ldr	x11, [sp, #2096]
	ldr	x8, [sp, #2088]
	stp	x10, x8, [sp, #120]
	ldr	x10, [sp, #2080]
	ldr	x8, [sp, #2040]
	stp	x8, x11, [sp, #360]
	ldr	x8, [sp, #2032]
	stp	x8, x9, [sp, #208]
	ldr	x8, [sp, #2024]
	stp	x8, x10, [sp, #48]
	ldr	x9, [sp, #1984]
	ldr	x10, [sp, #1976]
	ldr	x11, [sp, #1968]
	ldr	x8, [sp, #1960]
	str	x8, [sp, #88]
	ldr	x8, [sp, #1952]
	str	x8, [sp, #72]
	ldr	x8, [sp, #1944]
	str	x8, [sp, #40]
	ldr	x20, [sp, #1936]
	ldr	x8, [sp, #1896]
	stp	x8, x9, [sp, #344]
	ldr	x8, [sp, #1888]
	stp	x8, x10, [sp, #328]
	ldr	x8, [sp, #1880]
	stp	x8, x11, [sp, #312]
	ldr	x8, [sp, #1872]
	str	x8, [sp, #80]
	ldr	x8, [sp, #1864]
	str	x8, [sp, #64]
	ldr	x9, [sp, #1856]
	ldr	x8, [sp, #1848]
	str	x8, [sp, #200]
	ldr	x10, [sp, #1808]
	ldr	x8, [sp, #1800]
	stp	x8, x10, [sp, #296]
	ldr	x10, [sp, #1792]
	ldr	x8, [sp, #1784]
	stp	x8, x9, [sp, #24]
	str	x28, [sp, #112]
	ldr	x28, [sp, #1776]
	stp	x27, x22, [sp, #424]
	ldr	x22, [sp, #1768]
	ldr	x8, [sp, #1760]
	str	x8, [sp, #184]
	ldr	x8, [sp, #1720]
	stp	x8, x10, [sp, #272]
	ldr	x9, [sp, #1712]
	ldr	x8, [sp, #1704]
	stp	x8, x9, [sp, #256]
	ldr	x9, [sp, #1696]
	ldr	x27, [sp, #1688]
	ldr	x19, [sp, #1680]
	ldr	x21, [sp, #1672]
	ldr	x10, [sp, #1632]
	ldr	x8, [sp, #1624]
	stp	x8, x10, [sp, #240]
	ldr	x8, [sp, #1616]
	stp	x9, x8, [sp, #224]
	ldr	x26, [sp, #1608]
	ldr	x24, [sp, #1600]
	add	x2, sp, #1336
	add	x3, sp, #1328
	str	x1, [sp, #376]
	mov	w1, #1
Lloh36:
	adrp	x8, _get_sched_size@GOTPAGE
Lloh37:
	ldr	x8, [x8, _get_sched_size@GOTPAGEOFF]
	blr	x8
	mov	x25, x0
	mov	x0, #0
Lloh38:
	adrp	x8, _set_parallel_chunksize@GOTPAGE
Lloh39:
	ldr	x8, [x8, _set_parallel_chunksize@GOTPAGEOFF]
	blr	x8
	lsl	x0, x25, #1
Lloh40:
	adrp	x8, _allocate_sched@GOTPAGE
Lloh41:
	ldr	x8, [x8, _allocate_sched@GOTPAGEOFF]
	blr	x8
	mov	x23, x0
	add	x1, sp, #1336
	add	x2, sp, #1328
	mov	w0, #1
	mov	x3, x25
	mov	x4, x23
	mov	x5, #0
Lloh42:
	adrp	x8, _do_scheduling_unsigned@GOTPAGE
Lloh43:
	ldr	x8, [x8, _do_scheduling_unsigned@GOTPAGEOFF]
	blr	x8
	ldr	x8, [sp, #144]
	str	x8, [sp, #1192]
	str	x20, [sp, #1240]
	ldr	x8, [sp, #56]
	str	x8, [sp, #1248]
	ldr	x8, [sp, #120]
	str	x8, [sp, #1256]
	ldr	x8, [sp, #136]
	str	x8, [sp, #1264]
	ldr	x8, [sp, #104]
	str	x8, [sp, #1272]
	ldr	x8, [sp, #48]
	str	x8, [sp, #1280]
	str	x21, [sp, #1320]
	ldr	x8, [sp, #96]
	str	x8, [sp, #944]
	ldp	x9, x8, [sp, #168]
	str	x9, [sp, #952]
	str	x8, [sp, #960]
	str	x24, [sp, #992]
	str	x26, [sp, #1000]
	ldr	x8, [sp, #40]
	str	x8, [sp, #1008]
	ldr	x8, [sp, #72]
	str	x8, [sp, #1016]
	ldr	x8, [sp, #88]
	str	x8, [sp, #1024]
	ldr	x8, [sp, #128]
	str	x8, [sp, #1032]
	ldr	x8, [sp, #160]
	str	x8, [sp, #1040]
	ldr	x8, [sp, #192]
	str	x8, [sp, #1048]
	ldr	x8, [sp, #152]
	str	x8, [sp, #1056]
	ldr	x8, [sp, #32]
	str	x8, [sp, #1072]
	ldr	x8, [sp, #64]
	str	x8, [sp, #1080]
	ldr	x8, [sp, #80]
	str	x8, [sp, #1088]
	str	x22, [sp, #1096]
	str	x28, [sp, #1104]
	ldr	x8, [sp, #24]
	str	x8, [sp, #1112]
	str	x19, [sp, #1120]
	str	x27, [sp, #1128]
	add	x8, sp, #1168
	add	x9, sp, #1160
	str	x8, [sp, #1208]
	ldp	x10, x8, [sp, #208]
	str	x8, [sp, #1184]
	str	x23, [sp, #1176]
	ldr	x19, [sp, #112]
	str	x19, [sp, #1200]
	str	x10, [sp, #1168]
	ldr	x22, [sp, #544]
	str	x22, [sp, #1160]
	str	x9, [sp, #1216]
	str	s10, [sp, #1156]
	add	x8, sp, #1156
	str	x8, [sp, #1224]
	ldr	x8, [sp, #472]
	str	x8, [sp, #1232]
	str	s9, [sp, #1152]
	add	x8, sp, #1152
	ldr	x9, [sp, #200]
	str	x9, [sp, #1288]
	str	x8, [sp, #1296]
	str	s8, [sp, #1148]
	add	x8, sp, #1148
	str	x8, [sp, #1304]
	ldr	x8, [sp, #184]
	str	x8, [sp, #1312]
	mov	w8, #2
	str	x25, [sp, #928]
	str	x8, [sp, #936]
	str	x22, [sp, #968]
	mov	w24, #7
	str	x24, [sp, #976]
	ldr	x8, [sp, #480]
	str	x8, [sp, #984]
	str	x10, [sp, #1064]
	ldr	x8, [sp, #224]
	str	x8, [sp, #1136]
	mov	w8, #16
	str	x8, [sp, #568]
	movi.2d	v0, #0000000000000000
	add	x8, sp, #449
	stur	q0, [x8, #255]
	add	x8, sp, #433
	stur	q0, [x8, #255]
	add	x8, sp, #417
	stur	q0, [x8, #255]
	add	x8, sp, #401
	stur	q0, [x8, #255]
	add	x8, sp, #385
	stur	q0, [x8, #255]
	add	x8, sp, #369
	stur	q0, [x8, #255]
	add	x8, sp, #353
	stur	q0, [x8, #255]
	add	x8, sp, #337
	stur	q0, [x8, #255]
	add	x8, sp, #321
	stur	q0, [x8, #255]
	mov	w8, #8
	str	x8, [sp, #720]
	ldr	x8, [sp, #288]
	str	x8, [sp, #728]
	ldp	x9, x8, [sp, #384]
	str	x9, [sp, #736]
	str	x8, [sp, #744]
	mov	w20, #28
	mov	w21, #4
	str	x20, [sp, #752]
	str	x21, [sp, #760]
	ldp	x9, x8, [sp, #232]
	str	x9, [sp, #768]
	str	x8, [sp, #776]
	ldr	x8, [sp, #248]
	str	x8, [sp, #784]
	ldr	x8, [sp, #320]
	str	x8, [sp, #792]
	ldr	x8, [sp, #336]
	str	x8, [sp, #800]
	ldr	x8, [sp, #352]
	str	x8, [sp, #808]
	ldr	x8, [sp, #368]
	str	x8, [sp, #816]
	ldp	x9, x8, [sp, #408]
	str	x9, [sp, #824]
	str	x8, [sp, #832]
	ldr	x8, [sp, #400]
	str	x8, [sp, #840]
	ldr	x8, [sp, #360]
	str	x8, [sp, #848]
	ldr	x8, [sp, #312]
	str	x8, [sp, #856]
	ldr	x8, [sp, #328]
	str	x8, [sp, #864]
	ldr	x8, [sp, #344]
	str	x8, [sp, #872]
	ldr	x8, [sp, #280]
	str	x8, [sp, #880]
	ldp	x9, x8, [sp, #296]
	str	x9, [sp, #888]
	str	x8, [sp, #896]
	ldp	x9, x8, [sp, #256]
	str	x9, [sp, #904]
	str	x8, [sp, #912]
	ldr	x8, [sp, #272]
	str	x8, [sp, #920]
	str	wzr, [sp, #1468]
	add	x0, sp, #1468
Lloh44:
	adrp	x8, _numba_gil_ensure@GOTPAGE
Lloh45:
	ldr	x8, [x8, _numba_gil_ensure@GOTPAGEOFF]
	blr	x8
Lloh46:
	adrp	x8, _PyEval_SaveThread@GOTPAGE
Lloh47:
	ldr	x8, [x8, _PyEval_SaveThread@GOTPAGEOFF]
	blr	x8
	mov	x25, x0
Lloh48:
	adrp	x8, _get_num_threads@GOTPAGE
Lloh49:
	ldr	x8, [x8, _get_num_threads@GOTPAGEOFF]
	blr	x8
	mov	x7, x0
Lloh50:
	adrp	x0, ___gufunc__._ZN13_3cdynamic_3e33__numba_parfor_gufunc_0x10c777680B3v23B104c8tJTC_2fWQAliW1xhDEoY6EEMEUOEMISPGsAQMVj4QniQ4IXKQEMXwoMGLoQDDVsQR1NHAS2hQ9XgStYwaUTI24JtBVpeBJHUBAA_3dE5ArrayIyLi1E1C7mutable7alignedE5ArrayIfLi1E1C7mutable7alignedE5ArrayIfLi2E1C7mutable7alignedE5ArrayIfLi2E1C7mutable7alignedExxf5ArrayIfLi3E1C7mutable7alignedE5ArrayIbLi3E1C7mutable7alignedE5ArrayIfLi1E1C7mutable7alignedE5ArrayIfLi1E1A7mutable7alignedE5ArrayIfLi1E1A7mutable7alignedE5ArrayIbLi1E1C7mutable7alignedE5ArrayIfLi1E1C7mutable7alignedE5ArrayIbLi3E1C7mutable7alignedEff5ArrayIfLi3E1C7mutable7alignedE5ArrayIfLi3E1C7mutable7alignedE@GOTPAGE
Lloh51:
	ldr	x0, [x0, ___gufunc__._ZN13_3cdynamic_3e33__numba_parfor_gufunc_0x10c777680B3v23B104c8tJTC_2fWQAliW1xhDEoY6EEMEUOEMISPGsAQMVj4QniQ4IXKQEMXwoMGLoQDDVsQR1NHAS2hQ9XgStYwaUTI24JtBVpeBJHUBAA_3dE5ArrayIyLi1E1C7mutable7alignedE5ArrayIfLi1E1C7mutable7alignedE5ArrayIfLi2E1C7mutable7alignedE5ArrayIfLi2E1C7mutable7alignedExxf5ArrayIfLi3E1C7mutable7alignedE5ArrayIbLi3E1C7mutable7alignedE5ArrayIfLi1E1C7mutable7alignedE5ArrayIfLi1E1A7mutable7alignedE5ArrayIfLi1E1A7mutable7alignedE5ArrayIbLi1E1C7mutable7alignedE5ArrayIfLi1E1C7mutable7alignedE5ArrayIbLi3E1C7mutable7alignedEff5ArrayIfLi3E1C7mutable7alignedE5ArrayIfLi3E1C7mutable7alignedE@GOTPAGEOFF]
	add	x1, sp, #1176
	add	x2, sp, #928
	add	x3, sp, #568
	mov	x4, #0
	mov	w5, #26
	mov	w6, #19
Lloh52:
	adrp	x8, _numba_parallel_for@GOTPAGE
Lloh53:
	ldr	x8, [x8, _numba_parallel_for@GOTPAGEOFF]
	blr	x8
	mov	x0, x25
Lloh54:
	adrp	x8, _PyEval_RestoreThread@GOTPAGE
Lloh55:
	ldr	x8, [x8, _PyEval_RestoreThread@GOTPAGEOFF]
	blr	x8
	add	x0, sp, #1468
Lloh56:
	adrp	x8, _numba_gil_release@GOTPAGE
Lloh57:
	ldr	x8, [x8, _numba_gil_release@GOTPAGEOFF]
	blr	x8
	ldr	x0, [sp, #376]
Lloh58:
	adrp	x8, _set_parallel_chunksize@GOTPAGE
Lloh59:
	ldr	x8, [x8, _set_parallel_chunksize@GOTPAGEOFF]
	blr	x8
	mov	x0, x23
Lloh60:
	adrp	x8, _deallocate_sched@GOTPAGE
Lloh61:
	ldr	x8, [x8, _deallocate_sched@GOTPAGEOFF]
	blr	x8
	ldr	x8, [sp, #520]
	ldp	x10, x9, [sp, #424]
	stp	x10, xzr, [x8]
	stp	x9, x21, [x8, #16]
	stp	x19, x22, [x8, #32]
	stp	x24, x20, [x8, #48]
	str	x21, [x8, #64]
Lloh62:
	adrp	x19, _NRT_decref@GOTPAGE
Lloh63:
	ldr	x19, [x19, _NRT_decref@GOTPAGEOFF]
	ldr	x0, [sp, #488]
	blr	x19
	ldr	x0, [sp, #496]
	blr	x19
	ldr	x0, [sp, #536]
	blr	x19
	ldr	x0, [sp, #448]
	blr	x19
	ldr	x0, [sp, #552]
	blr	x19
	ldr	x0, [sp, #456]
	blr	x19
	ldr	x0, [sp, #440]
	blr	x19
	ldr	x0, [sp, #560]
	blr	x19
	ldr	x0, [sp, #512]
	blr	x19
	ldr	x0, [sp, #528]
	blr	x19
	ldr	x0, [sp, #464]
	blr	x19
	ldr	x0, [sp, #504]
	blr	x19
	mov	w0, #0
LBB0_7:
	add	sp, sp, #1472
	ldp	x29, x30, [sp, #112]
	ldp	x20, x19, [sp, #96]
	ldp	x22, x21, [sp, #80]
	ldp	x24, x23, [sp, #64]
	ldp	x26, x25, [sp, #48]
	ldp	x28, x27, [sp, #32]
	ldp	d9, d8, [sp, #16]
	ldp	d11, d10, [sp], #128
	ret
LBB0_8:
Lloh64:
	adrp	x8, _.const.picklebuf.331b8563bdb9dac81b38422273052c486fc1706b@GOTPAGE
Lloh65:
	ldr	x8, [x8, _.const.picklebuf.331b8563bdb9dac81b38422273052c486fc1706b@GOTPAGEOFF]
	b	LBB0_13
LBB0_9:
Lloh66:
	adrp	x8, _.const.picklebuf.ba289d81f05c7020f3477c15734804df65abe209@GOTPAGE
Lloh67:
	ldr	x8, [x8, _.const.picklebuf.ba289d81f05c7020f3477c15734804df65abe209@GOTPAGEOFF]
	b	LBB0_13
LBB0_10:
	str	x24, [sp]
Lloh68:
	adrp	x0, _printf_format@GOTPAGE
Lloh69:
	ldr	x0, [x0, _printf_format@GOTPAGEOFF]
	b	LBB0_12
LBB0_11:
	str	x0, [sp]
Lloh70:
	adrp	x0, _printf_format.1@GOTPAGE
Lloh71:
	ldr	x0, [x0, _printf_format.1@GOTPAGEOFF]
LBB0_12:
Lloh72:
	adrp	x8, _printf@GOTPAGE
Lloh73:
	ldr	x8, [x8, _printf@GOTPAGEOFF]
	blr	x8
Lloh74:
	adrp	x8, _.const.picklebuf.9d8bd6d541b3e336fd7917994940781bc68a3a8a@GOTPAGE
Lloh75:
	ldr	x8, [x8, _.const.picklebuf.9d8bd6d541b3e336fd7917994940781bc68a3a8a@GOTPAGEOFF]
LBB0_13:
	ldr	x9, [sp, #432]
	str	x8, [x9]
	mov	w0, #1
	b	LBB0_7
	.loh AdrpLdrGot	Lloh0, Lloh1
	.loh AdrpLdrGot	Lloh2, Lloh3
	.loh AdrpLdrGot	Lloh4, Lloh5
	.loh AdrpLdrGot	Lloh8, Lloh9
	.loh AdrpLdrGot	Lloh6, Lloh7
	.loh AdrpLdrGot	Lloh34, Lloh35
	.loh AdrpLdrGot	Lloh32, Lloh33
	.loh AdrpLdrGot	Lloh30, Lloh31
	.loh AdrpLdrGot	Lloh28, Lloh29
	.loh AdrpLdrGot	Lloh26, Lloh27
	.loh AdrpLdrGot	Lloh24, Lloh25
	.loh AdrpLdrGot	Lloh22, Lloh23
	.loh AdrpLdrGot	Lloh20, Lloh21
	.loh AdrpLdrGot	Lloh18, Lloh19
	.loh AdrpLdrGot	Lloh16, Lloh17
	.loh AdrpLdrGot	Lloh14, Lloh15
	.loh AdrpLdrGot	Lloh12, Lloh13
	.loh AdrpLdrGot	Lloh10, Lloh11
	.loh AdrpLdrGot	Lloh62, Lloh63
	.loh AdrpLdrGot	Lloh60, Lloh61
	.loh AdrpLdrGot	Lloh58, Lloh59
	.loh AdrpLdrGot	Lloh56, Lloh57
	.loh AdrpLdrGot	Lloh54, Lloh55
	.loh AdrpLdrGot	Lloh52, Lloh53
	.loh AdrpLdrGot	Lloh50, Lloh51
	.loh AdrpLdrGot	Lloh48, Lloh49
	.loh AdrpLdrGot	Lloh46, Lloh47
	.loh AdrpLdrGot	Lloh44, Lloh45
	.loh AdrpLdrGot	Lloh42, Lloh43
	.loh AdrpLdrGot	Lloh40, Lloh41
	.loh AdrpLdrGot	Lloh38, Lloh39
	.loh AdrpLdrGot	Lloh36, Lloh37
	.loh AdrpLdrGot	Lloh64, Lloh65
	.loh AdrpLdrGot	Lloh66, Lloh67
	.loh AdrpLdrGot	Lloh68, Lloh69
	.loh AdrpLdrGot	Lloh70, Lloh71
	.loh AdrpLdrGot	Lloh74, Lloh75
	.loh AdrpLdrGot	Lloh72, Lloh73
	.cfi_endproc

	.globl	__ZN7cpython18longwave_primary_b23make_longwave_primary_b12_3clocals_3e26_longwave_primary_b_packedB3v21B90c8tJTC_2fWQAliW1xhDEoY6EEMEUOEMISPGsAQMVj4QniQ4IXKQEMXwoMGLoQDDVsQR1NHAS2hQ9XgStYwm4ogLE0AE5ArrayIfLi3E1C7mutable7alignedE5ArrayIfLi3E1C7mutable7alignedE5ArrayIfLi3E1C7mutable7alignedE5ArrayIbLi3E1C7mutable7alignedE5ArrayIbLi3E1C7mutable7alignedE5ArrayIfLi1E1C7mutable7alignedE5ArrayIfLi1E1C7mutable7alignedE5ArrayIfLi1E1C7mutable7alignedE5ArrayIbLi1E1C7mutable7alignedE5ArrayIfLi1E1A7mutable7alignedE5ArrayIfLi1E1A7mutable7alignedEff5ArrayIfLi2E1C7mutable7alignedEfx
	.p2align	2
__ZN7cpython18longwave_primary_b23make_longwave_primary_b12_3clocals_3e26_longwave_primary_b_packedB3v21B90c8tJTC_2fWQAliW1xhDEoY6EEMEUOEMISPGsAQMVj4QniQ4IXKQEMXwoMGLoQDDVsQR1NHAS2hQ9XgStYwm4ogLE0AE5ArrayIfLi3E1C7mutable7alignedE5ArrayIfLi3E1C7mutable7alignedE5ArrayIfLi3E1C7mutable7alignedE5ArrayIbLi3E1C7mutable7alignedE5ArrayIbLi3E1C7mutable7alignedE5ArrayIfLi1E1C7mutable7alignedE5ArrayIfLi1E1C7mutable7alignedE5ArrayIfLi1E1C7mutable7alignedE5ArrayIbLi1E1C7mutable7alignedE5ArrayIfLi1E1A7mutable7alignedE5ArrayIfLi1E1A7mutable7alignedEff5ArrayIfLi2E1C7mutable7alignedEfx:
	.cfi_startproc
	stp	d11, d10, [sp, #-128]!
	stp	d9, d8, [sp, #16]
	stp	x28, x27, [sp, #32]
	stp	x26, x25, [sp, #48]
	stp	x24, x23, [sp, #64]
	stp	x22, x21, [sp, #80]
	stp	x20, x19, [sp, #96]
	stp	x29, x30, [sp, #112]
	add	x29, sp, #112
	sub	sp, sp, #2576
	.cfi_def_cfa w29, 16
	.cfi_offset w30, -8
	.cfi_offset w29, -16
	.cfi_offset w19, -24
	.cfi_offset w20, -32
	.cfi_offset w21, -40
	.cfi_offset w22, -48
	.cfi_offset w23, -56
	.cfi_offset w24, -64
	.cfi_offset w25, -72
	.cfi_offset w26, -80
	.cfi_offset w27, -88
	.cfi_offset w28, -96
	.cfi_offset b8, -104
	.cfi_offset b9, -112
	.cfi_offset b10, -120
	.cfi_offset b11, -128
	mov	x0, x1
	sub	x8, x29, #248
	sub	x9, x29, #240
	stp	x9, x8, [sp, #112]
	sub	x8, x29, #232
	sub	x9, x29, #224
	stp	x9, x8, [sp, #96]
	sub	x8, x29, #216
	sub	x9, x29, #208
	stp	x9, x8, [sp, #80]
	sub	x8, x29, #200
	sub	x9, x29, #192
	stp	x9, x8, [sp, #64]
	sub	x8, x29, #184
	sub	x9, x29, #176
	stp	x9, x8, [sp, #48]
	sub	x8, x29, #168
	sub	x9, x29, #160
	stp	x9, x8, [sp, #32]
	sub	x8, x29, #152
	sub	x9, x29, #144
	stp	x9, x8, [sp, #16]
	sub	x8, x29, #136
	sub	x9, x29, #128
	stp	x9, x8, [sp]
Lloh76:
	adrp	x1, "_.const.make_longwave_primary_b.<locals>._longwave_primary_b_packed"@GOTPAGE
Lloh77:
	ldr	x1, [x1, "_.const.make_longwave_primary_b.<locals>._longwave_primary_b_packed"@GOTPAGEOFF]
Lloh78:
	adrp	x8, _PyArg_UnpackTuple@GOTPAGE
Lloh79:
	ldr	x8, [x8, _PyArg_UnpackTuple@GOTPAGEOFF]
	mov	w2, #16
	mov	w3, #16
	blr	x8
	movi.2d	v0, #0000000000000000
	str	q0, [sp, #2064]
	str	q0, [sp, #2080]
	str	q0, [sp, #2096]
	str	q0, [sp, #2112]
	str	q0, [sp, #2128]
	str	xzr, [sp, #2144]
	str	q0, [sp, #1968]
	str	q0, [sp, #1984]
	str	q0, [sp, #2000]
	str	q0, [sp, #2016]
	str	q0, [sp, #2032]
	str	xzr, [sp, #2048]
	str	q0, [sp, #1904]
	str	q0, [sp, #1920]
	str	q0, [sp, #1936]
	str	xzr, [sp, #1952]
	str	xzr, [sp, #1888]
	str	q0, [sp, #1872]
	str	q0, [sp, #1856]
	str	q0, [sp, #1840]
	str	xzr, [sp, #1824]
	str	q0, [sp, #1808]
	str	q0, [sp, #1792]
	str	q0, [sp, #1776]
	str	xzr, [sp, #1760]
	str	q0, [sp, #1744]
	str	q0, [sp, #1728]
	str	q0, [sp, #1712]
	str	xzr, [sp, #1696]
	str	q0, [sp, #1680]
	str	q0, [sp, #1664]
	str	q0, [sp, #1648]
	str	xzr, [sp, #1632]
	str	q0, [sp, #1616]
	str	q0, [sp, #1600]
	str	q0, [sp, #1584]
	str	xzr, [sp, #1568]
	str	q0, [sp, #1552]
	str	q0, [sp, #1536]
	str	q0, [sp, #1520]
	str	q0, [sp, #1504]
	str	xzr, [sp, #1488]
	str	q0, [sp, #1472]
	str	q0, [sp, #1456]
	str	q0, [sp, #1440]
	str	q0, [sp, #1424]
	str	xzr, [sp, #1416]
	str	xzr, [sp, #1408]
	str	q0, [sp, #1392]
	str	q0, [sp, #1376]
	str	q0, [sp, #1360]
	str	q0, [sp, #1344]
	cbz	w0, LBB1_68
Lloh80:
	adrp	x8, __ZN08NumbaEnv18longwave_primary_b23make_longwave_primary_b12_3clocals_3e26_longwave_primary_b_packedB3v21B90c8tJTC_2fWQAliW1xhDEoY6EEMEUOEMISPGsAQMVj4QniQ4IXKQEMXwoMGLoQDDVsQR1NHAS2hQ9XgStYwm4ogLE0AE5ArrayIfLi3E1C7mutable7alignedE5ArrayIfLi3E1C7mutable7alignedE5ArrayIfLi3E1C7mutable7alignedE5ArrayIbLi3E1C7mutable7alignedE5ArrayIbLi3E1C7mutable7alignedE5ArrayIfLi1E1C7mutable7alignedE5ArrayIfLi1E1C7mutable7alignedE5ArrayIfLi1E1C7mutable7alignedE5ArrayIbLi1E1C7mutable7alignedE5ArrayIfLi1E1A7mutable7alignedE5ArrayIfLi1E1A7mutable7alignedEff5ArrayIfLi2E1C7mutable7alignedEfx@GOTPAGE
Lloh81:
	ldr	x8, [x8, __ZN08NumbaEnv18longwave_primary_b23make_longwave_primary_b12_3clocals_3e26_longwave_primary_b_packedB3v21B90c8tJTC_2fWQAliW1xhDEoY6EEMEUOEMISPGsAQMVj4QniQ4IXKQEMXwoMGLoQDDVsQR1NHAS2hQ9XgStYwm4ogLE0AE5ArrayIfLi3E1C7mutable7alignedE5ArrayIfLi3E1C7mutable7alignedE5ArrayIfLi3E1C7mutable7alignedE5ArrayIbLi3E1C7mutable7alignedE5ArrayIbLi3E1C7mutable7alignedE5ArrayIfLi1E1C7mutable7alignedE5ArrayIfLi1E1C7mutable7alignedE5ArrayIfLi1E1C7mutable7alignedE5ArrayIbLi1E1C7mutable7alignedE5ArrayIfLi1E1A7mutable7alignedE5ArrayIfLi1E1A7mutable7alignedEff5ArrayIfLi2E1C7mutable7alignedEfx@GOTPAGEOFF]
Lloh82:
	ldr	x27, [x8]
	cbz	x27, LBB1_40
	ldur	x0, [x29, #-128]
	str	q0, [sp, #2352]
	str	q0, [sp, #2368]
	str	q0, [sp, #2384]
	str	q0, [sp, #2400]
	str	q0, [sp, #2416]
	str	xzr, [sp, #2432]
Lloh83:
	adrp	x21, _NRT_adapt_ndarray_from_python@GOTPAGE
Lloh84:
	ldr	x21, [x21, _NRT_adapt_ndarray_from_python@GOTPAGEOFF]
	add	x1, sp, #2352
	blr	x21
	cbnz	w0, LBB1_41
	ldr	x8, [sp, #2376]
	cmp	x8, #4
	b.ne	LBB1_41
	ldr	x23, [sp, #2352]
	ldr	x22, [sp, #2384]
	ldr	x25, [sp, #2392]
	ldr	x28, [sp, #2400]
	ldr	x20, [sp, #2408]
	ldr	x19, [sp, #2416]
	ldr	x26, [sp, #2424]
	ldr	x24, [sp, #2432]
	ldur	x0, [x29, #-136]
	movi.2d	v0, #0000000000000000
	str	q0, [sp, #2256]
	str	q0, [sp, #2272]
	str	q0, [sp, #2288]
	str	q0, [sp, #2304]
	str	q0, [sp, #2320]
	str	xzr, [sp, #2336]
	add	x1, sp, #2256
	blr	x21
	cbnz	w0, LBB1_43
	ldr	x8, [sp, #2280]
	cmp	x8, #4
	b.ne	LBB1_43
	str	x24, [sp, #1280]
	ldr	x24, [sp, #2256]
	ldr	x8, [sp, #2288]
	str	x8, [sp, #1272]
	ldr	x8, [sp, #2296]
	str	x8, [sp, #1264]
	ldr	x8, [sp, #2304]
	str	x8, [sp, #1256]
	ldr	x8, [sp, #2312]
	str	x8, [sp, #1248]
	ldr	x8, [sp, #2320]
	str	x8, [sp, #1240]
	ldr	x8, [sp, #2328]
	str	x8, [sp, #1232]
	ldr	x8, [sp, #2336]
	str	x8, [sp, #1224]
	ldur	x0, [x29, #-144]
	movi.2d	v0, #0000000000000000
	str	q0, [sp, #2160]
	str	q0, [sp, #2176]
	str	q0, [sp, #2192]
	str	q0, [sp, #2208]
	str	q0, [sp, #2224]
	str	xzr, [sp, #2240]
	add	x1, sp, #2160
	blr	x21
	cbnz	w0, LBB1_44
	ldr	x8, [sp, #2184]
	cmp	x8, #4
	b.ne	LBB1_44
	str	x26, [sp, #1216]
	ldr	x26, [sp, #2160]
	ldr	x8, [sp, #2192]
	str	x8, [sp, #1208]
	ldr	x8, [sp, #2200]
	str	x8, [sp, #1200]
	ldr	x8, [sp, #2208]
	str	x8, [sp, #1192]
	ldr	x8, [sp, #2216]
	str	x8, [sp, #1184]
	ldr	x8, [sp, #2224]
	str	x8, [sp, #1176]
	ldr	x8, [sp, #2232]
	str	x8, [sp, #1168]
	ldr	x8, [sp, #2240]
	str	x8, [sp, #1160]
	ldur	x0, [x29, #-152]
	movi.2d	v0, #0000000000000000
	str	q0, [sp, #2064]
	str	q0, [sp, #2080]
	str	q0, [sp, #2096]
	str	q0, [sp, #2112]
	str	q0, [sp, #2128]
	str	xzr, [sp, #2144]
	add	x1, sp, #2064
	blr	x21
	cbnz	w0, LBB1_45
	ldr	x8, [sp, #2088]
	cmp	x8, #1
	b.ne	LBB1_45
	str	x19, [sp, #1152]
	ldr	x19, [sp, #2064]
	ldr	x8, [sp, #2096]
	str	x8, [sp, #1144]
	ldr	x8, [sp, #2104]
	str	x8, [sp, #1136]
	ldr	x8, [sp, #2112]
	str	x8, [sp, #1128]
	ldr	x8, [sp, #2120]
	str	x8, [sp, #1120]
	ldr	x8, [sp, #2128]
	str	x8, [sp, #1112]
	ldr	x8, [sp, #2136]
	str	x8, [sp, #1104]
	ldr	x8, [sp, #2144]
	str	x8, [sp, #1096]
	ldur	x0, [x29, #-160]
	movi.2d	v0, #0000000000000000
	str	q0, [sp, #1968]
	str	q0, [sp, #1984]
	str	q0, [sp, #2000]
	str	q0, [sp, #2016]
	str	q0, [sp, #2032]
	str	xzr, [sp, #2048]
	add	x1, sp, #1968
	blr	x21
	cbnz	w0, LBB1_46
	ldr	x8, [sp, #1992]
	cmp	x8, #1
	b.ne	LBB1_46
	str	x20, [sp, #1088]
	ldr	x20, [sp, #1968]
	ldr	x8, [sp, #2000]
	str	x8, [sp, #1072]
	ldr	x8, [sp, #2008]
	str	x8, [sp, #1064]
	ldr	x8, [sp, #2016]
	str	x8, [sp, #1056]
	ldr	x8, [sp, #2024]
	str	x8, [sp, #1048]
	ldr	x8, [sp, #2032]
	str	x8, [sp, #1040]
	ldr	x8, [sp, #2040]
	str	x8, [sp, #1032]
	ldr	x8, [sp, #2048]
	str	x8, [sp, #1080]
	ldur	x0, [x29, #-168]
	movi.2d	v0, #0000000000000000
	str	q0, [sp, #1904]
	str	q0, [sp, #1920]
	str	q0, [sp, #1936]
	str	xzr, [sp, #1952]
	add	x1, sp, #1904
	blr	x21
	cbnz	w0, LBB1_47
	ldr	x8, [sp, #1928]
	cmp	x8, #4
	b.ne	LBB1_47
	ldr	x8, [sp, #1904]
	str	x8, [sp, #1304]
	ldr	x8, [sp, #1936]
	str	x8, [sp, #1016]
	ldr	x8, [sp, #1944]
	str	x8, [sp, #1008]
	ldr	x8, [sp, #1952]
	str	x8, [sp, #1024]
	ldur	x0, [x29, #-176]
	movi.2d	v0, #0000000000000000
	str	q0, [sp, #1840]
	str	q0, [sp, #1856]
	str	q0, [sp, #1872]
	str	xzr, [sp, #1888]
	add	x1, sp, #1840
	blr	x21
	cbnz	w0, LBB1_48
	ldr	x8, [sp, #1864]
	cmp	x8, #4
	b.ne	LBB1_48
	ldr	x8, [sp, #1840]
	str	x8, [sp, #1296]
	ldr	x8, [sp, #1872]
	str	x8, [sp, #976]
	ldr	x8, [sp, #1880]
	str	x8, [sp, #968]
	ldr	x8, [sp, #1888]
	str	x8, [sp, #984]
	ldur	x0, [x29, #-184]
	movi.2d	v0, #0000000000000000
	str	q0, [sp, #1776]
	str	q0, [sp, #1792]
	str	q0, [sp, #1808]
	str	xzr, [sp, #1824]
	add	x1, sp, #1776
	blr	x21
	cbnz	w0, LBB1_49
	ldr	x8, [sp, #1800]
	cmp	x8, #4
	b.ne	LBB1_49
	ldr	x8, [sp, #1776]
	str	x8, [sp, #1288]
	ldr	x8, [sp, #1808]
	str	x8, [sp, #960]
	ldr	x8, [sp, #1816]
	str	x8, [sp, #952]
	ldr	x8, [sp, #1824]
	str	x8, [sp, #944]
	ldur	x0, [x29, #-192]
	movi.2d	v0, #0000000000000000
	str	q0, [sp, #1712]
	str	q0, [sp, #1728]
	str	q0, [sp, #1744]
	str	xzr, [sp, #1760]
	add	x1, sp, #1712
	blr	x21
	cbnz	w0, LBB1_50
	ldr	x8, [sp, #1736]
	cmp	x8, #1
	b.ne	LBB1_50
	ldr	x8, [sp, #1712]
	str	x8, [sp, #1336]
	ldr	x8, [sp, #1744]
	str	x8, [sp, #936]
	ldr	x8, [sp, #1752]
	str	x8, [sp, #928]
	ldr	x8, [sp, #1760]
	str	x8, [sp, #920]
	ldur	x0, [x29, #-200]
	movi.2d	v0, #0000000000000000
	str	q0, [sp, #1648]
	str	q0, [sp, #1664]
	str	q0, [sp, #1680]
	str	xzr, [sp, #1696]
	add	x1, sp, #1648
	blr	x21
	cbnz	w0, LBB1_51
	ldr	x8, [sp, #1672]
	cmp	x8, #4
	b.ne	LBB1_51
	ldr	x8, [sp, #1648]
	str	x8, [sp, #1328]
	ldr	x8, [sp, #1680]
	str	x8, [sp, #912]
	ldr	x8, [sp, #1688]
	str	x8, [sp, #904]
	ldr	x8, [sp, #1696]
	str	x8, [sp, #896]
	ldur	x0, [x29, #-208]
	movi.2d	v0, #0000000000000000
	str	q0, [sp, #1584]
	str	q0, [sp, #1600]
	str	q0, [sp, #1616]
	str	xzr, [sp, #1632]
	add	x1, sp, #1584
	blr	x21
	cbnz	w0, LBB1_52
	ldr	x8, [sp, #1608]
	cmp	x8, #4
	b.ne	LBB1_52
	str	x28, [sp, #872]
	str	x25, [sp, #880]
	str	x22, [sp, #888]
	str	x20, [sp, #992]
	str	x19, [sp, #1000]
	ldr	x8, [sp, #1584]
	str	x8, [sp, #1320]
	ldr	x8, [sp, #1616]
	str	x8, [sp, #864]
	ldr	x8, [sp, #1624]
	str	x8, [sp, #856]
	ldr	x8, [sp, #1632]
	str	x8, [sp, #848]
	ldur	x0, [x29, #-216]
Lloh85:
	adrp	x22, _PyNumber_Float@GOTPAGE
Lloh86:
	ldr	x22, [x22, _PyNumber_Float@GOTPAGEOFF]
	blr	x22
	mov	x20, x0
Lloh87:
	adrp	x25, _PyFloat_AsDouble@GOTPAGE
Lloh88:
	ldr	x25, [x25, _PyFloat_AsDouble@GOTPAGEOFF]
	blr	x25
	mov.16b	v8, v0
Lloh89:
	adrp	x28, _Py_DecRef@GOTPAGE
Lloh90:
	ldr	x28, [x28, _Py_DecRef@GOTPAGEOFF]
	mov	x0, x20
	blr	x28
Lloh91:
	adrp	x19, _PyErr_Occurred@GOTPAGE
Lloh92:
	ldr	x19, [x19, _PyErr_Occurred@GOTPAGEOFF]
	blr	x19
	cbnz	x0, LBB1_56
	ldur	x0, [x29, #-224]
	blr	x22
	mov	x20, x0
	blr	x25
	mov.16b	v9, v0
	mov	x0, x20
	blr	x28
	blr	x19
	cbnz	x0, LBB1_56
	ldur	x0, [x29, #-232]
	movi.2d	v0, #0000000000000000
	str	q0, [sp, #1504]
	str	q0, [sp, #1520]
	str	q0, [sp, #1536]
	str	q0, [sp, #1552]
	str	xzr, [sp, #1568]
	add	x1, sp, #1504
	blr	x21
	cbnz	w0, LBB1_53
	ldr	x8, [sp, #1528]
	cmp	x8, #4
	b.ne	LBB1_53
	str	x27, [sp, #816]
	str	x26, [sp, #824]
	str	x24, [sp, #832]
	str	x23, [sp, #840]
	ldr	x8, [sp, #1504]
	str	x8, [sp, #1312]
	ldr	x20, [sp, #1536]
	ldr	x23, [sp, #1544]
	ldr	x26, [sp, #1552]
	ldr	x24, [sp, #1560]
	ldr	x27, [sp, #1568]
	ldur	x0, [x29, #-240]
	blr	x22
	mov	x21, x0
	blr	x25
	mov.16b	v10, v0
	mov	x0, x21
	blr	x28
	blr	x19
	cbnz	x0, LBB1_55
	ldur	x0, [x29, #-248]
Lloh93:
	adrp	x8, _PyNumber_Long@GOTPAGE
Lloh94:
	ldr	x8, [x8, _PyNumber_Long@GOTPAGEOFF]
	blr	x8
	cbz	x0, LBB1_54
Lloh95:
	adrp	x8, _PyLong_AsLongLong@GOTPAGE
Lloh96:
	ldr	x8, [x8, _PyLong_AsLongLong@GOTPAGEOFF]
	mov	x22, x0
	blr	x8
	mov	x21, x0
	mov	x0, x22
	blr	x28
	blr	x19
	cbnz	x0, LBB1_55
LBB1_31:
	fcvt	s0, d8
	fcvt	s1, d9
	fcvt	s2, d10
	str	xzr, [sp, #1488]
	movi.2d	v3, #0000000000000000
	str	q3, [sp, #1472]
	str	q3, [sp, #1456]
	str	q3, [sp, #1440]
	str	q3, [sp, #1424]
	str	x21, [sp, #800]
	str	x27, [sp, #792]
	str	x24, [sp, #784]
	str	x26, [sp, #776]
	str	x23, [sp, #768]
	str	x20, [sp, #760]
	ldr	x8, [sp, #848]
	str	x8, [sp, #720]
	ldr	x8, [sp, #856]
	str	x8, [sp, #712]
	ldr	x8, [sp, #864]
	str	x8, [sp, #704]
	ldr	x8, [sp, #896]
	str	x8, [sp, #664]
	ldr	x8, [sp, #904]
	str	x8, [sp, #656]
	ldr	x8, [sp, #912]
	str	x8, [sp, #648]
	ldr	x8, [sp, #920]
	str	x8, [sp, #608]
	ldr	x8, [sp, #928]
	str	x8, [sp, #600]
	ldr	x8, [sp, #936]
	str	x8, [sp, #592]
	ldr	x8, [sp, #944]
	str	x8, [sp, #552]
	ldr	x8, [sp, #952]
	str	x8, [sp, #544]
	ldr	x8, [sp, #960]
	str	x8, [sp, #536]
	ldr	x9, [sp, #968]
	ldr	x8, [sp, #976]
	stp	x8, x9, [sp, #480]
	ldr	x9, [sp, #1008]
	ldr	x8, [sp, #1016]
	stp	x8, x9, [sp, #424]
	ldr	x9, [sp, #1032]
	ldr	x8, [sp, #1040]
	stp	x8, x9, [sp, #368]
	ldr	x9, [sp, #1048]
	ldr	x8, [sp, #1056]
	stp	x8, x9, [sp, #352]
	ldr	x9, [sp, #1064]
	ldr	x8, [sp, #1072]
	stp	x8, x9, [sp, #336]
	ldr	x8, [sp, #1312]
	str	x8, [sp, #728]
	ldr	x8, [sp, #1320]
	str	x8, [sp, #672]
	ldr	x8, [sp, #1328]
	str	x8, [sp, #616]
	ldr	x8, [sp, #1336]
	str	x8, [sp, #560]
	ldr	x21, [sp, #1288]
	ldr	x8, [sp, #984]
	stp	x8, x21, [sp, #496]
	ldr	x28, [sp, #1296]
	ldr	x8, [sp, #1024]
	stp	x8, x28, [sp, #440]
	ldr	x27, [sp, #1304]
	ldr	x8, [sp, #1080]
	stp	x8, x27, [sp, #384]
	ldr	x26, [sp, #992]
	ldr	x8, [sp, #1096]
	stp	x8, x26, [sp, #296]
	ldr	x9, [sp, #1104]
	ldr	x8, [sp, #1112]
	stp	x8, x9, [sp, #280]
	ldr	x9, [sp, #1120]
	ldr	x8, [sp, #1128]
	stp	x8, x9, [sp, #264]
	ldr	x9, [sp, #1136]
	ldr	x8, [sp, #1144]
	stp	x8, x9, [sp, #248]
	ldr	x25, [sp, #1000]
	ldr	x8, [sp, #1160]
	stp	x8, x25, [sp, #208]
	ldr	x9, [sp, #1168]
	ldr	x8, [sp, #1176]
	stp	x8, x9, [sp, #192]
	ldr	x9, [sp, #1184]
	ldr	x8, [sp, #1192]
	stp	x8, x9, [sp, #176]
	ldr	x9, [sp, #1200]
	ldr	x8, [sp, #1208]
	stp	x8, x9, [sp, #160]
	ldr	x22, [sp, #824]
	ldr	x8, [sp, #1224]
	stp	x8, x22, [sp, #120]
	ldr	x9, [sp, #1232]
	ldr	x8, [sp, #1240]
	stp	x8, x9, [sp, #104]
	ldr	x9, [sp, #1248]
	ldr	x8, [sp, #1256]
	stp	x8, x9, [sp, #88]
	ldr	x9, [sp, #1264]
	ldr	x8, [sp, #1272]
	stp	x8, x9, [sp, #72]
	ldr	x20, [sp, #832]
	ldr	x8, [sp, #1280]
	stp	x8, x20, [sp, #32]
	ldr	x9, [sp, #1216]
	ldr	x8, [sp, #1152]
	stp	x8, x9, [sp, #16]
	add	x0, sp, #1424
	add	x1, sp, #1416
	ldr	x9, [sp, #1088]
	ldr	x8, [sp, #872]
	stp	x8, x9, [sp]
Lloh97:
	adrp	x8, __ZN18longwave_primary_b23make_longwave_primary_b12_3clocals_3e26_longwave_primary_b_packedB3v21B90c8tJTC_2fWQAliW1xhDEoY6EEMEUOEMISPGsAQMVj4QniQ4IXKQEMXwoMGLoQDDVsQR1NHAS2hQ9XgStYwm4ogLE0AE5ArrayIfLi3E1C7mutable7alignedE5ArrayIfLi3E1C7mutable7alignedE5ArrayIfLi3E1C7mutable7alignedE5ArrayIbLi3E1C7mutable7alignedE5ArrayIbLi3E1C7mutable7alignedE5ArrayIfLi1E1C7mutable7alignedE5ArrayIfLi1E1C7mutable7alignedE5ArrayIfLi1E1C7mutable7alignedE5ArrayIbLi1E1C7mutable7alignedE5ArrayIfLi1E1A7mutable7alignedE5ArrayIfLi1E1A7mutable7alignedEff5ArrayIfLi2E1C7mutable7alignedEfx@GOTPAGE
Lloh98:
	ldr	x8, [x8, __ZN18longwave_primary_b23make_longwave_primary_b12_3clocals_3e26_longwave_primary_b_packedB3v21B90c8tJTC_2fWQAliW1xhDEoY6EEMEUOEMISPGsAQMVj4QniQ4IXKQEMXwoMGLoQDDVsQR1NHAS2hQ9XgStYwm4ogLE0AE5ArrayIfLi3E1C7mutable7alignedE5ArrayIfLi3E1C7mutable7alignedE5ArrayIfLi3E1C7mutable7alignedE5ArrayIbLi3E1C7mutable7alignedE5ArrayIbLi3E1C7mutable7alignedE5ArrayIfLi1E1C7mutable7alignedE5ArrayIfLi1E1C7mutable7alignedE5ArrayIfLi1E1C7mutable7alignedE5ArrayIbLi1E1C7mutable7alignedE5ArrayIfLi1E1A7mutable7alignedE5ArrayIfLi1E1A7mutable7alignedEff5ArrayIfLi2E1C7mutable7alignedEfx@GOTPAGEOFF]
	ldr	x19, [sp, #840]
	mov	x2, x19
	ldr	x6, [sp, #888]
	ldr	x7, [sp, #880]
	blr	x8
	mov	x23, x0
	ldr	x8, [sp, #1416]
	str	x8, [sp, #1208]
	ldr	x8, [sp, #1424]
	str	x8, [sp, #1280]
	ldr	x8, [sp, #1432]
	str	x8, [sp, #1272]
	ldr	x8, [sp, #1440]
	str	x8, [sp, #1264]
	ldr	x8, [sp, #1448]
	str	x8, [sp, #1256]
	ldr	x8, [sp, #1456]
	str	x8, [sp, #1248]
	ldr	x8, [sp, #1464]
	str	x8, [sp, #1240]
	ldr	x8, [sp, #1472]
	str	x8, [sp, #1232]
	ldr	x8, [sp, #1480]
	str	x8, [sp, #1224]
	ldr	x8, [sp, #1488]
	str	x8, [sp, #1216]
Lloh99:
	adrp	x24, _NRT_decref@GOTPAGE
Lloh100:
	ldr	x24, [x24, _NRT_decref@GOTPAGEOFF]
	mov	x0, x19
	blr	x24
	mov	x0, x20
	blr	x24
	mov	x0, x22
	blr	x24
	mov	x0, x25
	blr	x24
	mov	x0, x26
	blr	x24
	mov	x0, x27
	blr	x24
	mov	x0, x28
	blr	x24
	mov	x0, x21
	blr	x24
	ldr	x0, [sp, #1336]
	blr	x24
	ldr	x0, [sp, #1328]
	blr	x24
	ldr	x0, [sp, #1320]
	blr	x24
	ldr	x0, [sp, #1312]
	blr	x24
	cbnz	w23, LBB1_37
	ldr	x8, [sp, #816]
	ldr	x0, [x8, #24]
	cbz	x0, LBB1_34
Lloh101:
	adrp	x8, _PyList_GetItem@GOTPAGE
Lloh102:
	ldr	x8, [x8, _PyList_GetItem@GOTPAGEOFF]
	mov	x1, #0
	blr	x8
	mov	x19, x0
	b	LBB1_35
LBB1_34:
Lloh103:
	adrp	x0, _PyExc_RuntimeError@GOTPAGE
Lloh104:
	ldr	x0, [x0, _PyExc_RuntimeError@GOTPAGEOFF]
Lloh105:
	adrp	x1, "_.const.`env.consts` is NULL in `read_const`"@GOTPAGE
Lloh106:
	ldr	x1, [x1, "_.const.`env.consts` is NULL in `read_const`"@GOTPAGEOFF]
Lloh107:
	adrp	x8, _PyErr_SetString@GOTPAGE
Lloh108:
	ldr	x8, [x8, _PyErr_SetString@GOTPAGEOFF]
	blr	x8
	mov	x19, #0
LBB1_35:
Lloh109:
	adrp	x0, _.const.pickledata.dfbcfdd39fcb26f4d0c680954487b8c0b53bb8a3@GOTPAGE
Lloh110:
	ldr	x0, [x0, _.const.pickledata.dfbcfdd39fcb26f4d0c680954487b8c0b53bb8a3@GOTPAGEOFF]
Lloh111:
	adrp	x2, _.const.pickledata.dfbcfdd39fcb26f4d0c680954487b8c0b53bb8a3.sha1@GOTPAGE
Lloh112:
	ldr	x2, [x2, _.const.pickledata.dfbcfdd39fcb26f4d0c680954487b8c0b53bb8a3.sha1@GOTPAGEOFF]
Lloh113:
	adrp	x8, _numba_unpickle@GOTPAGE
Lloh114:
	ldr	x8, [x8, _numba_unpickle@GOTPAGEOFF]
	mov	w1, #32
	blr	x8
	mov	x1, x0
	ldr	x20, [sp, #1280]
	str	x20, [sp, #1344]
	ldr	x8, [sp, #1272]
	str	x8, [sp, #1352]
	ldr	x8, [sp, #1264]
	str	x8, [sp, #1360]
	ldr	x8, [sp, #1256]
	str	x8, [sp, #1368]
	ldr	x8, [sp, #1248]
	str	x8, [sp, #1376]
	ldr	x8, [sp, #1240]
	str	x8, [sp, #1384]
	ldr	x8, [sp, #1232]
	str	x8, [sp, #1392]
	ldr	x8, [sp, #1224]
	str	x8, [sp, #1400]
	ldr	x8, [sp, #1216]
	str	x8, [sp, #1408]
Lloh115:
	adrp	x8, _NRT_adapt_ndarray_to_python_acqref@GOTPAGE
Lloh116:
	ldr	x8, [x8, _NRT_adapt_ndarray_to_python_acqref@GOTPAGEOFF]
	add	x0, sp, #1344
	mov	w2, #2
	mov	w3, #1
	mov	x4, x19
	blr	x8
	mov	x19, x0
	mov	x0, x20
	blr	x24
LBB1_36:
	mov	x0, x19
	add	sp, sp, #2576
	ldp	x29, x30, [sp, #112]
	ldp	x20, x19, [sp, #96]
	ldp	x22, x21, [sp, #80]
	ldp	x24, x23, [sp, #64]
	ldp	x26, x25, [sp, #48]
	ldp	x28, x27, [sp, #32]
	ldp	d9, d8, [sp, #16]
	ldp	d11, d10, [sp], #128
	ret
LBB1_37:
Lloh117:
	adrp	x8, _PyErr_Clear@GOTPAGE
Lloh118:
	ldr	x8, [x8, _PyErr_Clear@GOTPAGEOFF]
	blr	x8
	ldr	x19, [sp, #1208]
	ldr	w1, [x19, #8]
	ldr	x0, [x19]
	ldr	w8, [x19, #32]
	cmp	w8, #1
	b.lt	LBB1_69
	sxtw	x1, w1
Lloh119:
	adrp	x8, _PyBytes_FromStringAndSize@GOTPAGE
Lloh120:
	ldr	x8, [x8, _PyBytes_FromStringAndSize@GOTPAGEOFF]
	blr	x8
	mov	x20, x0
	ldp	x0, x8, [x19, #16]
	blr	x8
	cbz	x0, LBB1_72
	mov	x1, x0
Lloh121:
	adrp	x8, _numba_runtime_build_excinfo_struct@GOTPAGE
Lloh122:
	ldr	x8, [x8, _numba_runtime_build_excinfo_struct@GOTPAGEOFF]
	mov	x0, x20
	blr	x8
	mov	x20, x0
Lloh123:
	adrp	x8, _NRT_Free@GOTPAGE
Lloh124:
	ldr	x8, [x8, _NRT_Free@GOTPAGEOFF]
	mov	x0, x19
	blr	x8
	mov	x0, x20
	b	LBB1_70
LBB1_40:
Lloh125:
	adrp	x0, _PyExc_RuntimeError@GOTPAGE
Lloh126:
	ldr	x0, [x0, _PyExc_RuntimeError@GOTPAGEOFF]
Lloh127:
	adrp	x1, "_.const.missing Environment: _ZN08NumbaEnv18longwave_primary_b23make_longwave_primary_b12_3clocals_3e26_longwave_primary_b_packedB3v21B90c8tJTC_2fWQAliW1xhDEoY6EEMEUOEMISPGsAQMVj4QniQ4IXKQEMXwoMGLoQDDVsQR1NHAS2hQ9XgStYwm4ogLE0AE5ArrayIfLi3E1C7mutable7alignedE5ArrayIfLi3E1C7mutable7alignedE5ArrayIfLi3E1C7mutable7alignedE5ArrayIbLi3E1C7mutable7alignedE5ArrayIbLi3E1C7mutable7alignedE5ArrayIfLi1E1C7mutable7alignedE5ArrayIfLi1E1C7mutable7alignedE5ArrayIfLi1E1C7mutable7alignedE5ArrayIbLi1E1C7mutable7alignedE5ArrayIfLi1E1A7mutable7alignedE5ArrayIfLi1E1A7mutable7alignedEff5ArrayIfLi2E1C7mutable7alignedEfx"@GOTPAGE
Lloh128:
	ldr	x1, [x1, "_.const.missing Environment: _ZN08NumbaEnv18longwave_primary_b23make_longwave_primary_b12_3clocals_3e26_longwave_primary_b_packedB3v21B90c8tJTC_2fWQAliW1xhDEoY6EEMEUOEMISPGsAQMVj4QniQ4IXKQEMXwoMGLoQDDVsQR1NHAS2hQ9XgStYwm4ogLE0AE5ArrayIfLi3E1C7mutable7alignedE5ArrayIfLi3E1C7mutable7alignedE5ArrayIfLi3E1C7mutable7alignedE5ArrayIbLi3E1C7mutable7alignedE5ArrayIbLi3E1C7mutable7alignedE5ArrayIfLi1E1C7mutable7alignedE5ArrayIfLi1E1C7mutable7alignedE5ArrayIfLi1E1C7mutable7alignedE5ArrayIbLi1E1C7mutable7alignedE5ArrayIfLi1E1A7mutable7alignedE5ArrayIfLi1E1A7mutable7alignedEff5ArrayIfLi2E1C7mutable7alignedEfx"@GOTPAGEOFF]
	b	LBB1_42
LBB1_41:
Lloh129:
	adrp	x0, _PyExc_TypeError@GOTPAGE
Lloh130:
	ldr	x0, [x0, _PyExc_TypeError@GOTPAGEOFF]
Lloh131:
	adrp	x1, "_.const.can't unbox array from PyObject into native value.  The object maybe of a different type"@GOTPAGE
Lloh132:
	ldr	x1, [x1, "_.const.can't unbox array from PyObject into native value.  The object maybe of a different type"@GOTPAGEOFF]
LBB1_42:
Lloh133:
	adrp	x8, _PyErr_SetString@GOTPAGE
Lloh134:
	ldr	x8, [x8, _PyErr_SetString@GOTPAGEOFF]
	blr	x8
	b	LBB1_68
LBB1_43:
Lloh135:
	adrp	x0, _PyExc_TypeError@GOTPAGE
Lloh136:
	ldr	x0, [x0, _PyExc_TypeError@GOTPAGEOFF]
Lloh137:
	adrp	x1, "_.const.can't unbox array from PyObject into native value.  The object maybe of a different type"@GOTPAGE
Lloh138:
	ldr	x1, [x1, "_.const.can't unbox array from PyObject into native value.  The object maybe of a different type"@GOTPAGEOFF]
Lloh139:
	adrp	x8, _PyErr_SetString@GOTPAGE
Lloh140:
	ldr	x8, [x8, _PyErr_SetString@GOTPAGEOFF]
	blr	x8
	b	LBB1_66
LBB1_44:
Lloh141:
	adrp	x0, _PyExc_TypeError@GOTPAGE
Lloh142:
	ldr	x0, [x0, _PyExc_TypeError@GOTPAGEOFF]
Lloh143:
	adrp	x1, "_.const.can't unbox array from PyObject into native value.  The object maybe of a different type"@GOTPAGE
Lloh144:
	ldr	x1, [x1, "_.const.can't unbox array from PyObject into native value.  The object maybe of a different type"@GOTPAGEOFF]
Lloh145:
	adrp	x8, _PyErr_SetString@GOTPAGE
Lloh146:
	ldr	x8, [x8, _PyErr_SetString@GOTPAGEOFF]
	blr	x8
	b	LBB1_65
LBB1_45:
Lloh147:
	adrp	x0, _PyExc_TypeError@GOTPAGE
Lloh148:
	ldr	x0, [x0, _PyExc_TypeError@GOTPAGEOFF]
Lloh149:
	adrp	x1, "_.const.can't unbox array from PyObject into native value.  The object maybe of a different type"@GOTPAGE
Lloh150:
	ldr	x1, [x1, "_.const.can't unbox array from PyObject into native value.  The object maybe of a different type"@GOTPAGEOFF]
Lloh151:
	adrp	x8, _PyErr_SetString@GOTPAGE
Lloh152:
	ldr	x8, [x8, _PyErr_SetString@GOTPAGEOFF]
	blr	x8
	b	LBB1_64
LBB1_46:
Lloh153:
	adrp	x0, _PyExc_TypeError@GOTPAGE
Lloh154:
	ldr	x0, [x0, _PyExc_TypeError@GOTPAGEOFF]
Lloh155:
	adrp	x1, "_.const.can't unbox array from PyObject into native value.  The object maybe of a different type"@GOTPAGE
Lloh156:
	ldr	x1, [x1, "_.const.can't unbox array from PyObject into native value.  The object maybe of a different type"@GOTPAGEOFF]
Lloh157:
	adrp	x8, _PyErr_SetString@GOTPAGE
Lloh158:
	ldr	x8, [x8, _PyErr_SetString@GOTPAGEOFF]
	blr	x8
	b	LBB1_63
LBB1_47:
Lloh159:
	adrp	x0, _PyExc_TypeError@GOTPAGE
Lloh160:
	ldr	x0, [x0, _PyExc_TypeError@GOTPAGEOFF]
Lloh161:
	adrp	x1, "_.const.can't unbox array from PyObject into native value.  The object maybe of a different type"@GOTPAGE
Lloh162:
	ldr	x1, [x1, "_.const.can't unbox array from PyObject into native value.  The object maybe of a different type"@GOTPAGEOFF]
Lloh163:
	adrp	x8, _PyErr_SetString@GOTPAGE
Lloh164:
	ldr	x8, [x8, _PyErr_SetString@GOTPAGEOFF]
	blr	x8
	b	LBB1_62
LBB1_48:
Lloh165:
	adrp	x0, _PyExc_TypeError@GOTPAGE
Lloh166:
	ldr	x0, [x0, _PyExc_TypeError@GOTPAGEOFF]
Lloh167:
	adrp	x1, "_.const.can't unbox array from PyObject into native value.  The object maybe of a different type"@GOTPAGE
Lloh168:
	ldr	x1, [x1, "_.const.can't unbox array from PyObject into native value.  The object maybe of a different type"@GOTPAGEOFF]
Lloh169:
	adrp	x8, _PyErr_SetString@GOTPAGE
Lloh170:
	ldr	x8, [x8, _PyErr_SetString@GOTPAGEOFF]
	blr	x8
	ldr	x21, [sp, #1304]
	b	LBB1_61
LBB1_49:
Lloh171:
	adrp	x0, _PyExc_TypeError@GOTPAGE
Lloh172:
	ldr	x0, [x0, _PyExc_TypeError@GOTPAGEOFF]
Lloh173:
	adrp	x1, "_.const.can't unbox array from PyObject into native value.  The object maybe of a different type"@GOTPAGE
Lloh174:
	ldr	x1, [x1, "_.const.can't unbox array from PyObject into native value.  The object maybe of a different type"@GOTPAGEOFF]
Lloh175:
	adrp	x8, _PyErr_SetString@GOTPAGE
Lloh176:
	ldr	x8, [x8, _PyErr_SetString@GOTPAGEOFF]
	blr	x8
	ldr	x21, [sp, #1304]
	ldr	x22, [sp, #1296]
	b	LBB1_60
LBB1_50:
Lloh177:
	adrp	x0, _PyExc_TypeError@GOTPAGE
Lloh178:
	ldr	x0, [x0, _PyExc_TypeError@GOTPAGEOFF]
Lloh179:
	adrp	x1, "_.const.can't unbox array from PyObject into native value.  The object maybe of a different type"@GOTPAGE
Lloh180:
	ldr	x1, [x1, "_.const.can't unbox array from PyObject into native value.  The object maybe of a different type"@GOTPAGEOFF]
Lloh181:
	adrp	x8, _PyErr_SetString@GOTPAGE
Lloh182:
	ldr	x8, [x8, _PyErr_SetString@GOTPAGEOFF]
	blr	x8
	ldr	x21, [sp, #1304]
	ldr	x22, [sp, #1296]
	ldr	x25, [sp, #1288]
	b	LBB1_59
LBB1_51:
Lloh183:
	adrp	x0, _PyExc_TypeError@GOTPAGE
Lloh184:
	ldr	x0, [x0, _PyExc_TypeError@GOTPAGEOFF]
Lloh185:
	adrp	x1, "_.const.can't unbox array from PyObject into native value.  The object maybe of a different type"@GOTPAGE
Lloh186:
	ldr	x1, [x1, "_.const.can't unbox array from PyObject into native value.  The object maybe of a different type"@GOTPAGEOFF]
Lloh187:
	adrp	x8, _PyErr_SetString@GOTPAGE
Lloh188:
	ldr	x8, [x8, _PyErr_SetString@GOTPAGEOFF]
	blr	x8
	b	LBB1_58
LBB1_52:
Lloh189:
	adrp	x0, _PyExc_TypeError@GOTPAGE
Lloh190:
	ldr	x0, [x0, _PyExc_TypeError@GOTPAGEOFF]
Lloh191:
	adrp	x1, "_.const.can't unbox array from PyObject into native value.  The object maybe of a different type"@GOTPAGE
Lloh192:
	ldr	x1, [x1, "_.const.can't unbox array from PyObject into native value.  The object maybe of a different type"@GOTPAGEOFF]
Lloh193:
	adrp	x8, _PyErr_SetString@GOTPAGE
Lloh194:
	ldr	x8, [x8, _PyErr_SetString@GOTPAGEOFF]
	blr	x8
	b	LBB1_57
LBB1_53:
Lloh195:
	adrp	x0, _PyExc_TypeError@GOTPAGE
Lloh196:
	ldr	x0, [x0, _PyExc_TypeError@GOTPAGEOFF]
Lloh197:
	adrp	x1, "_.const.can't unbox array from PyObject into native value.  The object maybe of a different type"@GOTPAGE
Lloh198:
	ldr	x1, [x1, "_.const.can't unbox array from PyObject into native value.  The object maybe of a different type"@GOTPAGEOFF]
Lloh199:
	adrp	x8, _PyErr_SetString@GOTPAGE
Lloh200:
	ldr	x8, [x8, _PyErr_SetString@GOTPAGEOFF]
	blr	x8
	b	LBB1_56
LBB1_54:
	mov	x21, #0
	blr	x19
	cbz	x0, LBB1_31
LBB1_55:
Lloh201:
	adrp	x8, _NRT_decref@GOTPAGE
Lloh202:
	ldr	x8, [x8, _NRT_decref@GOTPAGEOFF]
	ldr	x0, [sp, #1312]
	blr	x8
	ldr	x23, [sp, #840]
	ldr	x24, [sp, #832]
	ldr	x26, [sp, #824]
LBB1_56:
Lloh203:
	adrp	x8, _NRT_decref@GOTPAGE
Lloh204:
	ldr	x8, [x8, _NRT_decref@GOTPAGEOFF]
	ldr	x0, [sp, #1320]
	blr	x8
	ldr	x19, [sp, #1000]
	ldr	x20, [sp, #992]
LBB1_57:
Lloh205:
	adrp	x8, _NRT_decref@GOTPAGE
Lloh206:
	ldr	x8, [x8, _NRT_decref@GOTPAGEOFF]
	ldr	x0, [sp, #1328]
	blr	x8
LBB1_58:
	ldr	x21, [sp, #1304]
	ldr	x22, [sp, #1296]
	ldr	x25, [sp, #1288]
	ldr	x0, [sp, #1336]
Lloh207:
	adrp	x8, _NRT_decref@GOTPAGE
Lloh208:
	ldr	x8, [x8, _NRT_decref@GOTPAGEOFF]
	blr	x8
LBB1_59:
Lloh209:
	adrp	x8, _NRT_decref@GOTPAGE
Lloh210:
	ldr	x8, [x8, _NRT_decref@GOTPAGEOFF]
	mov	x0, x25
	blr	x8
LBB1_60:
Lloh211:
	adrp	x8, _NRT_decref@GOTPAGE
Lloh212:
	ldr	x8, [x8, _NRT_decref@GOTPAGEOFF]
	mov	x0, x22
	blr	x8
LBB1_61:
Lloh213:
	adrp	x8, _NRT_decref@GOTPAGE
Lloh214:
	ldr	x8, [x8, _NRT_decref@GOTPAGEOFF]
	mov	x0, x21
	blr	x8
LBB1_62:
Lloh215:
	adrp	x8, _NRT_decref@GOTPAGE
Lloh216:
	ldr	x8, [x8, _NRT_decref@GOTPAGEOFF]
	mov	x0, x20
	blr	x8
LBB1_63:
Lloh217:
	adrp	x8, _NRT_decref@GOTPAGE
Lloh218:
	ldr	x8, [x8, _NRT_decref@GOTPAGEOFF]
	mov	x0, x19
	blr	x8
LBB1_64:
Lloh219:
	adrp	x8, _NRT_decref@GOTPAGE
Lloh220:
	ldr	x8, [x8, _NRT_decref@GOTPAGEOFF]
	mov	x0, x26
	blr	x8
LBB1_65:
Lloh221:
	adrp	x8, _NRT_decref@GOTPAGE
Lloh222:
	ldr	x8, [x8, _NRT_decref@GOTPAGEOFF]
	mov	x0, x24
	blr	x8
LBB1_66:
Lloh223:
	adrp	x8, _NRT_decref@GOTPAGE
Lloh224:
	ldr	x8, [x8, _NRT_decref@GOTPAGEOFF]
	mov	x0, x23
LBB1_67:
	blr	x8
LBB1_68:
	mov	x19, #0
	b	LBB1_36
LBB1_69:
	ldr	x2, [x19, #16]
Lloh225:
	adrp	x8, _numba_unpickle@GOTPAGE
Lloh226:
	ldr	x8, [x8, _numba_unpickle@GOTPAGEOFF]
	blr	x8
LBB1_70:
	cbz	x0, LBB1_68
Lloh227:
	adrp	x8, _numba_do_raise@GOTPAGE
Lloh228:
	ldr	x8, [x8, _numba_do_raise@GOTPAGEOFF]
	b	LBB1_67
LBB1_72:
Lloh229:
	adrp	x0, _PyExc_RuntimeError@GOTPAGE
Lloh230:
	ldr	x0, [x0, _PyExc_RuntimeError@GOTPAGEOFF]
Lloh231:
	adrp	x1, "_.const.Error creating Python tuple from runtime exception arguments"@GOTPAGE
Lloh232:
	ldr	x1, [x1, "_.const.Error creating Python tuple from runtime exception arguments"@GOTPAGEOFF]
	b	LBB1_42
	.loh AdrpLdrGot	Lloh78, Lloh79
	.loh AdrpLdrGot	Lloh76, Lloh77
	.loh AdrpLdrGotLdr	Lloh80, Lloh81, Lloh82
	.loh AdrpLdrGot	Lloh83, Lloh84
	.loh AdrpLdrGot	Lloh91, Lloh92
	.loh AdrpLdrGot	Lloh89, Lloh90
	.loh AdrpLdrGot	Lloh87, Lloh88
	.loh AdrpLdrGot	Lloh85, Lloh86
	.loh AdrpLdrGot	Lloh93, Lloh94
	.loh AdrpLdrGot	Lloh95, Lloh96
	.loh AdrpLdrGot	Lloh99, Lloh100
	.loh AdrpLdrGot	Lloh97, Lloh98
	.loh AdrpLdrGot	Lloh101, Lloh102
	.loh AdrpLdrGot	Lloh107, Lloh108
	.loh AdrpLdrGot	Lloh105, Lloh106
	.loh AdrpLdrGot	Lloh103, Lloh104
	.loh AdrpLdrGot	Lloh115, Lloh116
	.loh AdrpLdrGot	Lloh113, Lloh114
	.loh AdrpLdrGot	Lloh111, Lloh112
	.loh AdrpLdrGot	Lloh109, Lloh110
	.loh AdrpLdrGot	Lloh117, Lloh118
	.loh AdrpLdrGot	Lloh119, Lloh120
	.loh AdrpLdrGot	Lloh123, Lloh124
	.loh AdrpLdrGot	Lloh121, Lloh122
	.loh AdrpLdrGot	Lloh127, Lloh128
	.loh AdrpLdrGot	Lloh125, Lloh126
	.loh AdrpLdrGot	Lloh131, Lloh132
	.loh AdrpLdrGot	Lloh129, Lloh130
	.loh AdrpLdrGot	Lloh133, Lloh134
	.loh AdrpLdrGot	Lloh139, Lloh140
	.loh AdrpLdrGot	Lloh137, Lloh138
	.loh AdrpLdrGot	Lloh135, Lloh136
	.loh AdrpLdrGot	Lloh145, Lloh146
	.loh AdrpLdrGot	Lloh143, Lloh144
	.loh AdrpLdrGot	Lloh141, Lloh142
	.loh AdrpLdrGot	Lloh151, Lloh152
	.loh AdrpLdrGot	Lloh149, Lloh150
	.loh AdrpLdrGot	Lloh147, Lloh148
	.loh AdrpLdrGot	Lloh157, Lloh158
	.loh AdrpLdrGot	Lloh155, Lloh156
	.loh AdrpLdrGot	Lloh153, Lloh154
	.loh AdrpLdrGot	Lloh163, Lloh164
	.loh AdrpLdrGot	Lloh161, Lloh162
	.loh AdrpLdrGot	Lloh159, Lloh160
	.loh AdrpLdrGot	Lloh169, Lloh170
	.loh AdrpLdrGot	Lloh167, Lloh168
	.loh AdrpLdrGot	Lloh165, Lloh166
	.loh AdrpLdrGot	Lloh175, Lloh176
	.loh AdrpLdrGot	Lloh173, Lloh174
	.loh AdrpLdrGot	Lloh171, Lloh172
	.loh AdrpLdrGot	Lloh181, Lloh182
	.loh AdrpLdrGot	Lloh179, Lloh180
	.loh AdrpLdrGot	Lloh177, Lloh178
	.loh AdrpLdrGot	Lloh187, Lloh188
	.loh AdrpLdrGot	Lloh185, Lloh186
	.loh AdrpLdrGot	Lloh183, Lloh184
	.loh AdrpLdrGot	Lloh193, Lloh194
	.loh AdrpLdrGot	Lloh191, Lloh192
	.loh AdrpLdrGot	Lloh189, Lloh190
	.loh AdrpLdrGot	Lloh199, Lloh200
	.loh AdrpLdrGot	Lloh197, Lloh198
	.loh AdrpLdrGot	Lloh195, Lloh196
	.loh AdrpLdrGot	Lloh201, Lloh202
	.loh AdrpLdrGot	Lloh203, Lloh204
	.loh AdrpLdrGot	Lloh205, Lloh206
	.loh AdrpLdrGot	Lloh207, Lloh208
	.loh AdrpLdrGot	Lloh209, Lloh210
	.loh AdrpLdrGot	Lloh211, Lloh212
	.loh AdrpLdrGot	Lloh213, Lloh214
	.loh AdrpLdrGot	Lloh215, Lloh216
	.loh AdrpLdrGot	Lloh217, Lloh218
	.loh AdrpLdrGot	Lloh219, Lloh220
	.loh AdrpLdrGot	Lloh221, Lloh222
	.loh AdrpLdrGot	Lloh223, Lloh224
	.loh AdrpLdrGot	Lloh225, Lloh226
	.loh AdrpLdrGot	Lloh227, Lloh228
	.loh AdrpLdrGot	Lloh231, Lloh232
	.loh AdrpLdrGot	Lloh229, Lloh230
	.cfi_endproc

	.globl	_cfunc._ZN18longwave_primary_b23make_longwave_primary_b12_3clocals_3e26_longwave_primary_b_packedB3v21B90c8tJTC_2fWQAliW1xhDEoY6EEMEUOEMISPGsAQMVj4QniQ4IXKQEMXwoMGLoQDDVsQR1NHAS2hQ9XgStYwm4ogLE0AE5ArrayIfLi3E1C7mutable7alignedE5ArrayIfLi3E1C7mutable7alignedE5ArrayIfLi3E1C7mutable7alignedE5ArrayIbLi3E1C7mutable7alignedE5ArrayIbLi3E1C7mutable7alignedE5ArrayIfLi1E1C7mutable7alignedE5ArrayIfLi1E1C7mutable7alignedE5ArrayIfLi1E1C7mutable7alignedE5ArrayIbLi1E1C7mutable7alignedE5ArrayIfLi1E1A7mutable7alignedE5ArrayIfLi1E1A7mutable7alignedEff5ArrayIfLi2E1C7mutable7alignedEfx
	.p2align	2
_cfunc._ZN18longwave_primary_b23make_longwave_primary_b12_3clocals_3e26_longwave_primary_b_packedB3v21B90c8tJTC_2fWQAliW1xhDEoY6EEMEUOEMISPGsAQMVj4QniQ4IXKQEMXwoMGLoQDDVsQR1NHAS2hQ9XgStYwm4ogLE0AE5ArrayIfLi3E1C7mutable7alignedE5ArrayIfLi3E1C7mutable7alignedE5ArrayIfLi3E1C7mutable7alignedE5ArrayIbLi3E1C7mutable7alignedE5ArrayIbLi3E1C7mutable7alignedE5ArrayIfLi1E1C7mutable7alignedE5ArrayIfLi1E1C7mutable7alignedE5ArrayIfLi1E1C7mutable7alignedE5ArrayIbLi1E1C7mutable7alignedE5ArrayIfLi1E1A7mutable7alignedE5ArrayIfLi1E1A7mutable7alignedEff5ArrayIfLi2E1C7mutable7alignedEfx:
	.cfi_startproc
	stp	d9, d8, [sp, #-112]!
	stp	x28, x27, [sp, #16]
	stp	x26, x25, [sp, #32]
	stp	x24, x23, [sp, #48]
	stp	x22, x21, [sp, #64]
	stp	x20, x19, [sp, #80]
	stp	x29, x30, [sp, #96]
	add	x29, sp, #96
	sub	sp, sp, #928
	.cfi_def_cfa w29, 16
	.cfi_offset w30, -8
	.cfi_offset w29, -16
	.cfi_offset w19, -24
	.cfi_offset w20, -32
	.cfi_offset w21, -40
	.cfi_offset w22, -48
	.cfi_offset w23, -56
	.cfi_offset w24, -64
	.cfi_offset w25, -72
	.cfi_offset w26, -80
	.cfi_offset w27, -88
	.cfi_offset w28, -96
	.cfi_offset b8, -104
	.cfi_offset b9, -112
	stur	x5, [x29, #-200]
	mov	x5, x4
	mov	x4, x0
	mov	x19, x8
	add	x8, x29, #9
	ldur	q3, [x8, #255]
	add	x8, x29, #25
	ldur	q4, [x8, #255]
	add	x8, x29, #169
	ldur	q5, [x8, #255]
	add	x8, x29, #281
	ldur	q6, [x8, #255]
	add	x8, x29, #393
	ldur	q7, [x8, #255]
	add	x8, x29, #505
	ldur	q16, [x8, #255]
	add	x8, x29, #521
	ldur	q17, [x8, #255]
	ldr	q18, [x29, #16]
	ldp	x2, x9, [x29, #32]
	ldur	q19, [x29, #72]
	ldur	q20, [x29, #88]
	ldur	q21, [x29, #104]
	ldp	x10, x11, [x29, #120]
	ldp	q22, q23, [x29, #160]
	ldr	q24, [x29, #192]
	ldp	x12, x13, [x29, #208]
	ldur	q25, [x29, #248]
	ldp	x14, x15, [x29, #296]
	ldp	q26, q27, [x29, #336]
	ldr	q28, [x29, #368]
	ldp	x16, x17, [x29, #384]
	ldp	x0, x1, [x29, #440]
	ldr	q29, [x29, #480]
	ldp	x3, x20, [x29, #496]
	ldr	x21, [x29, #552]
	ldr	x22, [x29, #560]
	ldr	q30, [x29, #592]
	ldr	x23, [x29, #608]
	ldr	x24, [x29, #616]
	ldr	x25, [x29, #664]
	ldr	x26, [x29, #672]
	ldr	q31, [x29, #704]
	ldr	x27, [x29, #720]
	ldr	x28, [x29, #728]
	ldr	x30, [x29, #792]
	ldr	x8, [x29, #800]
	stur	xzr, [x29, #-112]
	movi.2d	v8, #0000000000000000
	stp	q8, q8, [x29, #-144]
	stp	q8, q8, [x29, #-176]
	stur	xzr, [x29, #-184]
	str	x8, [sp, #800]
	str	x30, [sp, #792]
	str	x28, [sp, #728]
	str	x27, [sp, #720]
	str	q31, [sp, #704]
	str	x26, [sp, #672]
	str	x25, [sp, #664]
	str	x24, [sp, #616]
	str	x23, [sp, #608]
	str	q30, [sp, #592]
	str	x22, [sp, #560]
	str	x21, [sp, #552]
	stp	x3, x20, [sp, #496]
	str	q29, [sp, #480]
	stp	x0, x1, [sp, #440]
	stp	x16, x17, [sp, #384]
	stp	q27, q28, [sp, #352]
	str	q26, [sp, #336]
	stp	x14, x15, [sp, #296]
	stur	q25, [sp, #248]
	stp	x12, x13, [sp, #208]
	stp	q23, q24, [sp, #176]
	str	q22, [sp, #160]
	stp	x10, x11, [sp, #120]
	stur	q21, [sp, #104]
	stur	q20, [sp, #88]
	stur	q19, [sp, #72]
	stp	x2, x9, [sp, #32]
	str	q18, [sp, #16]
	stp	x6, x7, [sp]
	add	x8, sp, #776
	str	q17, [x8]
	add	x8, sp, #760
	str	q16, [x8]
	add	x8, sp, #648
	str	q7, [x8]
	add	x8, sp, #536
	str	q6, [x8]
	add	x8, sp, #424
	add	x9, sp, #280
	str	q5, [x8]
	add	x8, sp, #264
	sub	x0, x29, #176
	sub	x1, x29, #184
	str	q4, [x9]
	str	q3, [x8]
Lloh233:
	adrp	x8, __ZN18longwave_primary_b23make_longwave_primary_b12_3clocals_3e26_longwave_primary_b_packedB3v21B90c8tJTC_2fWQAliW1xhDEoY6EEMEUOEMISPGsAQMVj4QniQ4IXKQEMXwoMGLoQDDVsQR1NHAS2hQ9XgStYwm4ogLE0AE5ArrayIfLi3E1C7mutable7alignedE5ArrayIfLi3E1C7mutable7alignedE5ArrayIfLi3E1C7mutable7alignedE5ArrayIbLi3E1C7mutable7alignedE5ArrayIbLi3E1C7mutable7alignedE5ArrayIfLi1E1C7mutable7alignedE5ArrayIfLi1E1C7mutable7alignedE5ArrayIfLi1E1C7mutable7alignedE5ArrayIbLi1E1C7mutable7alignedE5ArrayIfLi1E1A7mutable7alignedE5ArrayIfLi1E1A7mutable7alignedEff5ArrayIfLi2E1C7mutable7alignedEfx@GOTPAGE
Lloh234:
	ldr	x8, [x8, __ZN18longwave_primary_b23make_longwave_primary_b12_3clocals_3e26_longwave_primary_b_packedB3v21B90c8tJTC_2fWQAliW1xhDEoY6EEMEUOEMISPGsAQMVj4QniQ4IXKQEMXwoMGLoQDDVsQR1NHAS2hQ9XgStYwm4ogLE0AE5ArrayIfLi3E1C7mutable7alignedE5ArrayIfLi3E1C7mutable7alignedE5ArrayIfLi3E1C7mutable7alignedE5ArrayIbLi3E1C7mutable7alignedE5ArrayIbLi3E1C7mutable7alignedE5ArrayIfLi1E1C7mutable7alignedE5ArrayIfLi1E1C7mutable7alignedE5ArrayIfLi1E1C7mutable7alignedE5ArrayIbLi1E1C7mutable7alignedE5ArrayIfLi1E1A7mutable7alignedE5ArrayIfLi1E1A7mutable7alignedEff5ArrayIfLi2E1C7mutable7alignedEfx@GOTPAGEOFF]
	mov	x2, x4
	mov	x6, x5
	ldur	x7, [x29, #-200]
	blr	x8
	ldp	x20, x8, [x29, #-184]
	ldp	x23, x24, [x29, #-168]
	ldp	x25, x26, [x29, #-152]
	ldp	x27, x28, [x29, #-136]
	ldp	x21, x22, [x29, #-120]
	stur	wzr, [x29, #-188]
	cbnz	w0, LBB2_2
LBB2_1:
	stp	x8, x23, [x19]
	stp	x24, x25, [x19, #16]
	stp	x26, x27, [x19, #32]
	stp	x28, x21, [x19, #48]
	str	x22, [x19, #64]
	add	sp, sp, #928
	ldp	x29, x30, [sp, #96]
	ldp	x20, x19, [sp, #80]
	ldp	x22, x21, [sp, #64]
	ldp	x24, x23, [sp, #48]
	ldp	x26, x25, [sp, #32]
	ldp	x28, x27, [sp, #16]
	ldp	d9, d8, [sp], #112
	ret
LBB2_2:
	stur	x8, [x29, #-200]
Lloh235:
	adrp	x8, _numba_gil_ensure@GOTPAGE
Lloh236:
	ldr	x8, [x8, _numba_gil_ensure@GOTPAGEOFF]
	sub	x0, x29, #188
	blr	x8
Lloh237:
	adrp	x8, _PyErr_Clear@GOTPAGE
Lloh238:
	ldr	x8, [x8, _PyErr_Clear@GOTPAGEOFF]
	blr	x8
	ldr	w1, [x20, #8]
	ldr	x0, [x20]
	ldr	w8, [x20, #32]
	cmp	w8, #0
	b.le	LBB2_7
	sxtw	x1, w1
Lloh239:
	adrp	x8, _PyBytes_FromStringAndSize@GOTPAGE
Lloh240:
	ldr	x8, [x8, _PyBytes_FromStringAndSize@GOTPAGEOFF]
	blr	x8
	stur	x0, [x29, #-208]
	ldp	x0, x8, [x20, #16]
	blr	x8
	cbz	x0, LBB2_8
	mov	x1, x0
Lloh241:
	adrp	x8, _numba_runtime_build_excinfo_struct@GOTPAGE
Lloh242:
	ldr	x8, [x8, _numba_runtime_build_excinfo_struct@GOTPAGEOFF]
	ldur	x0, [x29, #-208]
	blr	x8
	stur	x0, [x29, #-208]
Lloh243:
	adrp	x8, _NRT_Free@GOTPAGE
Lloh244:
	ldr	x8, [x8, _NRT_Free@GOTPAGEOFF]
	mov	x0, x20
	blr	x8
	ldur	x0, [x29, #-208]
	cbz	x0, LBB2_6
LBB2_5:
Lloh245:
	adrp	x8, _numba_do_raise@GOTPAGE
Lloh246:
	ldr	x8, [x8, _numba_do_raise@GOTPAGEOFF]
	blr	x8
LBB2_6:
Lloh247:
	adrp	x0, "_.const.<numba.core.cpu.CPUContext>"@GOTPAGE
Lloh248:
	ldr	x0, [x0, "_.const.<numba.core.cpu.CPUContext>"@GOTPAGEOFF]
Lloh249:
	adrp	x8, _PyUnicode_FromString@GOTPAGE
Lloh250:
	ldr	x8, [x8, _PyUnicode_FromString@GOTPAGEOFF]
	blr	x8
	mov	x20, x0
Lloh251:
	adrp	x8, _PyErr_WriteUnraisable@GOTPAGE
Lloh252:
	ldr	x8, [x8, _PyErr_WriteUnraisable@GOTPAGEOFF]
	blr	x8
Lloh253:
	adrp	x8, _Py_DecRef@GOTPAGE
Lloh254:
	ldr	x8, [x8, _Py_DecRef@GOTPAGEOFF]
	mov	x0, x20
	blr	x8
Lloh255:
	adrp	x8, _numba_gil_release@GOTPAGE
Lloh256:
	ldr	x8, [x8, _numba_gil_release@GOTPAGEOFF]
	sub	x0, x29, #188
	blr	x8
	ldur	x8, [x29, #-200]
	b	LBB2_1
LBB2_7:
	ldr	x2, [x20, #16]
Lloh257:
	adrp	x8, _numba_unpickle@GOTPAGE
Lloh258:
	ldr	x8, [x8, _numba_unpickle@GOTPAGEOFF]
	blr	x8
	cbnz	x0, LBB2_5
	b	LBB2_6
LBB2_8:
Lloh259:
	adrp	x0, _PyExc_RuntimeError@GOTPAGE
Lloh260:
	ldr	x0, [x0, _PyExc_RuntimeError@GOTPAGEOFF]
Lloh261:
	adrp	x1, "_.const.Error creating Python tuple from runtime exception arguments.1"@GOTPAGE
Lloh262:
	ldr	x1, [x1, "_.const.Error creating Python tuple from runtime exception arguments.1"@GOTPAGEOFF]
Lloh263:
	adrp	x8, _PyErr_SetString@GOTPAGE
Lloh264:
	ldr	x8, [x8, _PyErr_SetString@GOTPAGEOFF]
	blr	x8
	mov	x8, #0
	mov	x23, #0
	mov	x24, #0
	mov	x25, #0
	mov	x26, #0
	mov	x27, #0
	mov	x28, #0
	mov	x21, #0
	mov	x22, #0
	b	LBB2_1
	.loh AdrpLdrGot	Lloh233, Lloh234
	.loh AdrpLdrGot	Lloh237, Lloh238
	.loh AdrpLdrGot	Lloh235, Lloh236
	.loh AdrpLdrGot	Lloh239, Lloh240
	.loh AdrpLdrGot	Lloh243, Lloh244
	.loh AdrpLdrGot	Lloh241, Lloh242
	.loh AdrpLdrGot	Lloh245, Lloh246
	.loh AdrpLdrGot	Lloh255, Lloh256
	.loh AdrpLdrGot	Lloh253, Lloh254
	.loh AdrpLdrGot	Lloh251, Lloh252
	.loh AdrpLdrGot	Lloh249, Lloh250
	.loh AdrpLdrGot	Lloh247, Lloh248
	.loh AdrpLdrGot	Lloh257, Lloh258
	.loh AdrpLdrGot	Lloh263, Lloh264
	.loh AdrpLdrGot	Lloh261, Lloh262
	.loh AdrpLdrGot	Lloh259, Lloh260
	.cfi_endproc

	.globl	___gufunc__._ZN13_3cdynamic_3e33__numba_parfor_gufunc_0x10c3c2c00B3v22B106c8tJTC_2fWQAliW1xhDEoY6EEMEUOEMISPGsAQMVj4QniQ4IXKQEMXwoMGLoQDDVsQR1NHAS2hQ9XgStYwaUTI24JtBVoOCV2YU4ogSjUBE5ArrayIyLi1E1C7mutable7alignedE5ArrayIfLi2E1C7mutable7alignedE
	.weak_definition	___gufunc__._ZN13_3cdynamic_3e33__numba_parfor_gufunc_0x10c3c2c00B3v22B106c8tJTC_2fWQAliW1xhDEoY6EEMEUOEMISPGsAQMVj4QniQ4IXKQEMXwoMGLoQDDVsQR1NHAS2hQ9XgStYwaUTI24JtBVoOCV2YU4ogSjUBE5ArrayIyLi1E1C7mutable7alignedE5ArrayIfLi2E1C7mutable7alignedE
	.p2align	2
___gufunc__._ZN13_3cdynamic_3e33__numba_parfor_gufunc_0x10c3c2c00B3v22B106c8tJTC_2fWQAliW1xhDEoY6EEMEUOEMISPGsAQMVj4QniQ4IXKQEMXwoMGLoQDDVsQR1NHAS2hQ9XgStYwaUTI24JtBVoOCV2YU4ogSjUBE5ArrayIyLi1E1C7mutable7alignedE5ArrayIfLi2E1C7mutable7alignedE:
	.cfi_startproc
	sub	sp, sp, #128
	stp	x28, x27, [sp, #32]
	stp	x26, x25, [sp, #48]
	stp	x24, x23, [sp, #64]
	stp	x22, x21, [sp, #80]
	stp	x20, x19, [sp, #96]
	stp	x29, x30, [sp, #112]
	.cfi_def_cfa_offset 128
	.cfi_offset w30, -8
	.cfi_offset w29, -16
	.cfi_offset w19, -24
	.cfi_offset w20, -32
	.cfi_offset w21, -40
	.cfi_offset w22, -48
	.cfi_offset w23, -56
	.cfi_offset w24, -64
	.cfi_offset w25, -72
	.cfi_offset w26, -80
	.cfi_offset w27, -88
	.cfi_offset w28, -96
	ldr	x21, [x1]
	cmp	x21, #1
	b.lt	LBB3_7
	mov	x22, #0
	ldr	x8, [x1, #24]
	ldp	x24, x10, [x0]
	ldp	x26, x9, [x2]
	stp	x9, x10, [sp, #8]
	str	x8, [sp, #24]
	lsl	x28, x8, #2
	mov	x25, #9223372036854775806
Lloh265:
	adrp	x27, _bzero@GOTPAGE
Lloh266:
	ldr	x27, [x27, _bzero@GOTPAGEOFF]
	b	LBB3_3
LBB3_2:
	add	x22, x22, #1
	cmp	x22, x21
	b.eq	LBB3_7
LBB3_3:
	madd	x10, x22, x26, x24
	ldr	x8, [x10]
	ldr	x9, [x10, #16]
	sub	x11, x9, x8
	cmp	x11, x25
	b.hi	LBB3_2
	ldr	x11, [x10, #8]
	ldr	x10, [x10, #24]
	sub	x10, x10, x11
	cmp	x10, x25
	csinc	x10, xzr, x10, hi
	cmp	x10, #1
	b.lt	LBB3_2
	ldp	x13, x12, [sp, #8]
	madd	x12, x22, x13, x12
	ldr	x13, [sp, #24]
	madd	x11, x8, x13, x11
	lsl	x19, x10, #2
	add	x20, x12, x11, lsl #2
	mvn	x9, x9
	add	x23, x9, x8
LBB3_6:
	mov	x0, x20
	mov	x1, x19
	blr	x27
	add	x20, x20, x28
	adds	x23, x23, #1
	b.lo	LBB3_6
	b	LBB3_2
LBB3_7:
	ldp	x29, x30, [sp, #112]
	ldp	x20, x19, [sp, #96]
	ldp	x22, x21, [sp, #80]
	ldp	x24, x23, [sp, #64]
	ldp	x26, x25, [sp, #48]
	ldp	x28, x27, [sp, #32]
	add	sp, sp, #128
	ret
	.loh AdrpLdrGot	Lloh265, Lloh266
	.cfi_endproc

	.globl	_NRT_decref
	.weak_def_can_be_hidden	_NRT_decref
	.p2align	2
_NRT_decref:
	.cfi_startproc
	cbz	x0, LBB4_2
	dmb	ish
	mov	x8, #-1
	ldadd	x8, x8, [x0]
	cmp	x8, #1
	b.eq	LBB4_3
LBB4_2:
	ret
LBB4_3:
	dmb	ishld
Lloh267:
	adrp	x1, _NRT_MemInfo_call_dtor@GOTPAGE
Lloh268:
	ldr	x1, [x1, _NRT_MemInfo_call_dtor@GOTPAGEOFF]
	br	x1
	.loh AdrpLdrGot	Lloh267, Lloh268
	.cfi_endproc

	.globl	___gufunc__._ZN13_3cdynamic_3e33__numba_parfor_gufunc_0x10c777680B3v23B104c8tJTC_2fWQAliW1xhDEoY6EEMEUOEMISPGsAQMVj4QniQ4IXKQEMXwoMGLoQDDVsQR1NHAS2hQ9XgStYwaUTI24JtBVpeBJHUBAA_3dE5ArrayIyLi1E1C7mutable7alignedE5ArrayIfLi1E1C7mutable7alignedE5ArrayIfLi2E1C7mutable7alignedE5ArrayIfLi2E1C7mutable7alignedExxf5ArrayIfLi3E1C7mutable7alignedE5ArrayIbLi3E1C7mutable7alignedE5ArrayIfLi1E1C7mutable7alignedE5ArrayIfLi1E1A7mutable7alignedE5ArrayIfLi1E1A7mutable7alignedE5ArrayIbLi1E1C7mutable7alignedE5ArrayIfLi1E1C7mutable7alignedE5ArrayIbLi3E1C7mutable7alignedEff5ArrayIfLi3E1C7mutable7alignedE5ArrayIfLi3E1C7mutable7alignedE
	.weak_definition	___gufunc__._ZN13_3cdynamic_3e33__numba_parfor_gufunc_0x10c777680B3v23B104c8tJTC_2fWQAliW1xhDEoY6EEMEUOEMISPGsAQMVj4QniQ4IXKQEMXwoMGLoQDDVsQR1NHAS2hQ9XgStYwaUTI24JtBVpeBJHUBAA_3dE5ArrayIyLi1E1C7mutable7alignedE5ArrayIfLi1E1C7mutable7alignedE5ArrayIfLi2E1C7mutable7alignedE5ArrayIfLi2E1C7mutable7alignedExxf5ArrayIfLi3E1C7mutable7alignedE5ArrayIbLi3E1C7mutable7alignedE5ArrayIfLi1E1C7mutable7alignedE5ArrayIfLi1E1A7mutable7alignedE5ArrayIfLi1E1A7mutable7alignedE5ArrayIbLi1E1C7mutable7alignedE5ArrayIfLi1E1C7mutable7alignedE5ArrayIbLi3E1C7mutable7alignedEff5ArrayIfLi3E1C7mutable7alignedE5ArrayIfLi3E1C7mutable7alignedE
	.p2align	2
___gufunc__._ZN13_3cdynamic_3e33__numba_parfor_gufunc_0x10c777680B3v23B104c8tJTC_2fWQAliW1xhDEoY6EEMEUOEMISPGsAQMVj4QniQ4IXKQEMXwoMGLoQDDVsQR1NHAS2hQ9XgStYwaUTI24JtBVpeBJHUBAA_3dE5ArrayIyLi1E1C7mutable7alignedE5ArrayIfLi1E1C7mutable7alignedE5ArrayIfLi2E1C7mutable7alignedE5ArrayIfLi2E1C7mutable7alignedExxf5ArrayIfLi3E1C7mutable7alignedE5ArrayIbLi3E1C7mutable7alignedE5ArrayIfLi1E1C7mutable7alignedE5ArrayIfLi1E1A7mutable7alignedE5ArrayIfLi1E1A7mutable7alignedE5ArrayIbLi1E1C7mutable7alignedE5ArrayIfLi1E1C7mutable7alignedE5ArrayIbLi3E1C7mutable7alignedEff5ArrayIfLi3E1C7mutable7alignedE5ArrayIfLi3E1C7mutable7alignedE:
	.cfi_startproc
	stp	x28, x27, [sp, #-96]!
	stp	x26, x25, [sp, #16]
	stp	x24, x23, [sp, #32]
	stp	x22, x21, [sp, #48]
	stp	x20, x19, [sp, #64]
	stp	x29, x30, [sp, #80]
	add	x29, sp, #80
	sub	sp, sp, #1680
	.cfi_def_cfa w29, 16
	.cfi_offset w30, -8
	.cfi_offset w29, -16
	.cfi_offset w19, -24
	.cfi_offset w20, -32
	.cfi_offset w21, -40
	.cfi_offset w22, -48
	.cfi_offset w23, -56
	.cfi_offset w24, -64
	.cfi_offset w25, -72
	.cfi_offset w26, -80
	.cfi_offset w27, -88
	.cfi_offset w28, -96
	ldp	x9, x8, [x1]
	str	x8, [sp, #1408]
	ldp	x10, x11, [x1, #16]
	str	x10, [sp, #1400]
	ldp	x10, x8, [x1, #32]
	stp	x10, x11, [x29, #-208]
	stur	x8, [x29, #-216]
	ldp	x10, x8, [x1, #48]
	stp	x8, x10, [x29, #-232]
	ldp	x10, x8, [x1, #64]
	stp	x8, x10, [x29, #-248]
	ldp	x10, x8, [x1, #80]
	stur	x10, [x29, #-256]
	str	x8, [sp, #1496]
	ldp	x10, x8, [x1, #96]
	str	x10, [sp, #1488]
	str	x8, [sp, #1392]
	ldp	x10, x8, [x1, #112]
	str	x10, [sp, #1384]
	str	x8, [sp, #1376]
	ldp	x10, x8, [x1, #128]
	str	x10, [sp, #1368]
	str	x8, [sp, #1360]
	ldp	x10, x8, [x1, #144]
	str	x10, [sp, #1480]
	str	x8, [sp, #1472]
	ldp	x10, x8, [x1, #160]
	str	x10, [sp, #1464]
	str	x8, [sp, #1456]
	ldp	x10, x8, [x1, #176]
	str	x10, [sp, #1448]
	str	x8, [sp, #1440]
	ldp	x10, x8, [x1, #192]
	str	x10, [sp, #1432]
	str	x8, [sp, #1424]
	ldr	x8, [x1, #208]
	str	x8, [sp, #1416]
	ldp	x20, x11, [x0]
	ldp	x12, x27, [x0, #16]
	ldp	x28, x23, [x0, #32]
	ldp	x24, x25, [x0, #48]
	ldp	x1, x3, [x0, #64]
	ldp	x4, x5, [x0, #80]
	ldp	x6, x7, [x0, #96]
	ldp	x30, x10, [x0, #112]
	ldp	x26, x19, [x0, #128]
	ldr	x21, [x0, #144]
	ldr	x0, [x2]
	str	x0, [sp, #1144]
	ldr	x0, [x2, #8]
	str	x0, [sp, #1136]
	ldr	x0, [x2, #160]
	str	x0, [sp, #1352]
	ldr	x0, [x2, #168]
	str	x0, [sp, #1344]
	ldr	x0, [x2, #16]
	str	x0, [sp, #1128]
	ldr	x0, [x2, #24]
	str	x0, [sp, #1120]
	ldr	x0, [x2, #176]
	str	x0, [sp, #1336]
	ldr	x0, [x2, #184]
	str	x0, [sp, #1328]
	ldr	x0, [x2, #32]
	str	x0, [sp, #1112]
	ldr	x0, [x2, #40]
	str	x0, [sp, #1104]
	ldr	x0, [x2, #48]
	str	x0, [sp, #1096]
	ldr	x0, [x2, #56]
	str	x0, [sp, #1088]
	ldr	x0, [x2, #192]
	str	x0, [sp, #1320]
	ldr	x0, [x2, #200]
	str	x0, [sp, #1312]
	ldr	x0, [x2, #208]
	str	x0, [sp, #1304]
	ldr	x0, [x2, #216]
	str	x0, [sp, #1296]
	ldr	x0, [x2, #224]
	str	x0, [sp, #1288]
	ldr	x0, [x2, #232]
	str	x0, [sp, #1280]
	ldr	x0, [x2, #64]
	str	x0, [sp, #1080]
	ldr	x0, [x2, #72]
	str	x0, [sp, #1072]
	ldr	x0, [x2, #240]
	str	x0, [sp, #1272]
	ldr	x0, [x2, #248]
	str	x0, [sp, #1264]
	ldr	x0, [x2, #80]
	str	x0, [sp, #1064]
	ldr	x0, [x2, #88]
	str	x0, [sp, #1056]
	ldr	x0, [x2, #256]
	str	x0, [sp, #1256]
	ldr	x0, [x2, #264]
	str	x0, [sp, #1248]
	ldr	x0, [x2, #96]
	str	x0, [sp, #1048]
	ldr	x0, [x2, #104]
	str	x0, [sp, #1040]
	ldr	x0, [x2, #272]
	str	x0, [sp, #1240]
	ldr	x0, [x2, #280]
	str	x0, [sp, #1232]
	ldr	x0, [x2, #288]
	str	x0, [sp, #1224]
	ldr	x0, [x2, #296]
	str	x0, [sp, #1216]
	ldr	x0, [x2, #112]
	str	x0, [sp, #1032]
	ldr	x0, [x2, #120]
	str	x0, [sp, #1024]
	ldr	x0, [x2, #128]
	str	x0, [sp, #1016]
	ldr	x0, [x2, #136]
	str	x0, [sp, #1008]
	ldr	x0, [x2, #304]
	str	x0, [sp, #1208]
	ldr	x0, [x2, #312]
	str	x0, [sp, #1200]
	ldr	x0, [x2, #320]
	str	x0, [sp, #1192]
	ldr	x0, [x2, #328]
	str	x0, [sp, #1184]
	ldr	x0, [x2, #152]
	str	x0, [sp, #1176]
	ldr	x0, [x2, #144]
	str	x0, [sp, #1000]
	ldr	x0, [x2, #336]
	str	x0, [sp, #1168]
	ldr	x0, [x2, #344]
	str	x0, [sp, #1160]
	ldr	x0, [x2, #352]
	str	x0, [sp, #1152]
	stur	xzr, [x29, #-104]
	stur	wzr, [x29, #-108]
	cmp	x9, #1
	b.lt	LBB5_11
	mov	x0, x10
	ldp	x10, x8, [x29, #-208]
	mul	x8, x10, x8
	str	x8, [sp, #992]
	ldp	x10, x8, [x29, #-224]
	mul	x8, x10, x8
	str	x8, [sp, #984]
	ldp	x10, x8, [x29, #-240]
	mul	x8, x10, x8
	ldur	x10, [x29, #-248]
	mul	x8, x8, x10
	str	x8, [sp, #976]
	ldur	x8, [x29, #-256]
	ldr	x10, [sp, #1496]
	mul	x8, x10, x8
	ldr	x10, [sp, #1488]
	mul	x8, x8, x10
	str	x8, [sp, #968]
	ldr	x8, [sp, #1480]
	ldr	x10, [sp, #1472]
	mul	x8, x10, x8
	ldr	x10, [sp, #1464]
	mul	x8, x8, x10
	str	x8, [sp, #960]
	ldr	x8, [sp, #1456]
	ldr	x10, [sp, #1448]
	mul	x8, x10, x8
	ldr	x10, [sp, #1440]
	mul	x8, x8, x10
	str	x8, [sp, #952]
	ldr	x8, [sp, #1432]
	ldr	x10, [sp, #1424]
	mul	x8, x10, x8
	ldr	x10, [sp, #1416]
	mul	x8, x8, x10
	str	x8, [sp, #944]
LBB5_2:
	stp	x5, x7, [x29, #-192]
	stp	x6, x12, [x29, #-176]
	stp	x21, x11, [x29, #-160]
	stp	x19, x1, [x29, #-144]
	stp	x0, x9, [x29, #-128]
	ldr	x8, [x28]
	ldr	x9, [x23]
	ldr	s0, [x24]
	ldr	s1, [x0]
	ldr	s2, [x26]
	ldr	x10, [sp, #1152]
	str	x10, [sp, #936]
	ldr	x10, [sp, #1160]
	str	x10, [sp, #928]
	ldr	x10, [sp, #1168]
	str	x10, [sp, #920]
	ldr	x10, [sp, #1416]
	str	x10, [sp, #912]
	ldr	x10, [sp, #1424]
	str	x10, [sp, #904]
	ldr	x10, [sp, #1432]
	str	x10, [sp, #896]
	str	x21, [sp, #888]
	mov	w0, #4
	str	x0, [sp, #880]
	ldr	x10, [sp, #944]
	str	x10, [sp, #872]
	ldr	x10, [sp, #1184]
	str	x10, [sp, #848]
	ldr	x10, [sp, #1192]
	str	x10, [sp, #840]
	ldr	x10, [sp, #1200]
	str	x10, [sp, #832]
	ldr	x10, [sp, #1440]
	str	x10, [sp, #824]
	ldr	x10, [sp, #1448]
	str	x10, [sp, #816]
	ldr	x10, [sp, #1456]
	str	x10, [sp, #808]
	str	x19, [sp, #800]
	str	x0, [sp, #792]
	ldr	x10, [sp, #952]
	str	x10, [sp, #784]
	movi.2d	v3, #0000000000000000
	str	q3, [sp, #768]
	ldr	x10, [sp, #1208]
	str	x10, [sp, #760]
	ldr	x10, [sp, #1216]
	str	x10, [sp, #752]
	ldr	x10, [sp, #1224]
	str	x10, [sp, #744]
	ldr	x10, [sp, #1464]
	str	x10, [sp, #736]
	ldr	x10, [sp, #1472]
	str	x10, [sp, #728]
	ldr	x10, [sp, #1480]
	str	x10, [sp, #720]
	str	x30, [sp, #712]
	mov	w22, #1
	str	x22, [sp, #704]
	ldr	x10, [sp, #960]
	str	x10, [sp, #696]
	ldr	x10, [sp, #1232]
	str	x10, [sp, #672]
	ldr	x10, [sp, #1360]
	str	x10, [sp, #664]
	str	x7, [sp, #656]
	str	x0, [sp, #648]
	str	x10, [sp, #640]
	str	q3, [sp, #624]
	ldr	x10, [sp, #1240]
	str	x10, [sp, #616]
	ldr	x10, [sp, #1368]
	str	x10, [sp, #608]
	str	x6, [sp, #600]
	str	x22, [sp, #592]
	str	x10, [sp, #584]
	ldr	x10, [sp, #1248]
	str	x10, [sp, #560]
	ldr	x10, [sp, #1376]
	str	x10, [sp, #552]
	str	x5, [sp, #544]
	str	x0, [sp, #536]
	str	x10, [sp, #528]
	str	q3, [sp, #512]
	ldr	x10, [sp, #1256]
	str	x10, [sp, #504]
	ldr	x10, [sp, #1384]
	stp	x4, x10, [sp, #488]
	stp	x10, x0, [sp, #472]
	ldr	x10, [sp, #1264]
	str	x10, [sp, #448]
	ldr	x10, [sp, #1392]
	stp	x3, x10, [sp, #432]
	stp	x10, x0, [sp, #416]
	str	q3, [sp, #400]
	ldr	x10, [sp, #1272]
	str	x10, [sp, #392]
	ldr	x10, [sp, #1280]
	str	x10, [sp, #384]
	ldr	x10, [sp, #1288]
	str	x10, [sp, #376]
	ldr	x10, [sp, #1488]
	str	x10, [sp, #368]
	ldr	x10, [sp, #1496]
	str	x10, [sp, #360]
	ldur	x10, [x29, #-256]
	stp	x1, x10, [sp, #344]
	ldr	x10, [sp, #968]
	stp	x10, x22, [sp, #328]
	ldr	x10, [sp, #1296]
	str	x10, [sp, #304]
	ldr	x10, [sp, #1304]
	str	x10, [sp, #296]
	ldr	x10, [sp, #1312]
	str	x10, [sp, #288]
	ldur	x10, [x29, #-248]
	str	x10, [sp, #280]
	ldur	x10, [x29, #-240]
	str	x10, [sp, #272]
	ldur	x10, [x29, #-232]
	stp	x25, x10, [sp, #256]
	ldr	x10, [sp, #976]
	stp	x10, x0, [sp, #240]
	str	q3, [sp, #224]
	stp	x8, x9, [sp, #208]
	ldr	x9, [sp, #1320]
	ldr	x8, [sp, #1328]
	stp	x8, x9, [sp, #192]
	ldur	x8, [x29, #-224]
	str	x8, [sp, #184]
	ldur	x8, [x29, #-216]
	stp	x27, x8, [sp, #168]
	ldr	x8, [sp, #984]
	stp	x8, x0, [sp, #152]
	stur	q3, [sp, #136]
	ldr	x9, [sp, #1336]
	ldr	x8, [sp, #1344]
	stp	x8, x9, [sp, #120]
	ldur	x8, [x29, #-208]
	str	x8, [sp, #112]
	ldur	x8, [x29, #-200]
	stp	x12, x8, [sp, #96]
	ldr	x8, [sp, #992]
	stp	x8, x0, [sp, #80]
	str	q3, [sp, #64]
	ldr	x9, [sp, #1352]
	ldr	x8, [sp, #1400]
	stp	x8, x9, [sp, #48]
	stp	x0, x11, [sp, #32]
	str	x8, [sp, #24]
	stur	q3, [sp, #8]
	ldr	x8, [sp, #1176]
	str	x8, [sp]
	add	x8, sp, #856
	add	x9, sp, #680
	add	x10, sp, #568
	add	x11, sp, #456
	add	x12, sp, #312
	sub	x0, x29, #96
	sub	x1, x29, #104
	str	q3, [x8]
	str	q3, [x9]
	str	q3, [x10]
	str	q3, [x11]
	str	q3, [x12]
	mov	x2, #0
	mov	x19, x3
	mov	x3, #0
	mov	x21, x4
	ldr	x4, [sp, #1408]
	mov	w5, #8
	mov	x6, x20
	mov	x7, x4
	mov	x22, x30
Lloh269:
	adrp	x8, __ZN13_3cdynamic_3e33__numba_parfor_gufunc_0x10c777680B3v23B104c8tJTC_2fWQAliW1xhDEoY6EEMEUOEMISPGsAQMVj4QniQ4IXKQEMXwoMGLoQDDVsQR1NHAS2hQ9XgStYwaUTI24JtBVpeBJHUBAA_3dE5ArrayIyLi1E1C7mutable7alignedE5ArrayIfLi1E1C7mutable7alignedE5ArrayIfLi2E1C7mutable7alignedE5ArrayIfLi2E1C7mutable7alignedExxf5ArrayIfLi3E1C7mutable7alignedE5ArrayIbLi3E1C7mutable7alignedE5ArrayIfLi1E1C7mutable7alignedE5ArrayIfLi1E1A7mutable7alignedE5ArrayIfLi1E1A7mutable7alignedE5ArrayIbLi1E1C7mutable7alignedE5ArrayIfLi1E1C7mutable7alignedE5ArrayIbLi3E1C7mutable7alignedEff5ArrayIfLi3E1C7mutable7alignedE5ArrayIfLi3E1C7mutable7alignedE@GOTPAGE
Lloh270:
	ldr	x8, [x8, __ZN13_3cdynamic_3e33__numba_parfor_gufunc_0x10c777680B3v23B104c8tJTC_2fWQAliW1xhDEoY6EEMEUOEMISPGsAQMVj4QniQ4IXKQEMXwoMGLoQDDVsQR1NHAS2hQ9XgStYwaUTI24JtBVpeBJHUBAA_3dE5ArrayIyLi1E1C7mutable7alignedE5ArrayIfLi1E1C7mutable7alignedE5ArrayIfLi2E1C7mutable7alignedE5ArrayIfLi2E1C7mutable7alignedExxf5ArrayIfLi3E1C7mutable7alignedE5ArrayIbLi3E1C7mutable7alignedE5ArrayIfLi1E1C7mutable7alignedE5ArrayIfLi1E1A7mutable7alignedE5ArrayIfLi1E1A7mutable7alignedE5ArrayIbLi1E1C7mutable7alignedE5ArrayIfLi1E1C7mutable7alignedE5ArrayIbLi3E1C7mutable7alignedEff5ArrayIfLi3E1C7mutable7alignedE5ArrayIfLi3E1C7mutable7alignedE@GOTPAGEOFF]
	blr	x8
	cbnz	w0, LBB5_4
	ldr	x8, [sp, #1016]
	add	x26, x26, x8
	ldr	x8, [sp, #1024]
	ldur	x10, [x29, #-128]
	add	x10, x10, x8
	ldr	x8, [sp, #1096]
	add	x24, x24, x8
	ldr	x8, [sp, #1104]
	add	x23, x23, x8
	ldr	x8, [sp, #1112]
	add	x28, x28, x8
	ldr	x8, [sp, #1144]
	add	x20, x20, x8
	ldr	x8, [sp, #1136]
	ldur	x11, [x29, #-152]
	add	x11, x11, x8
	ldr	x8, [sp, #1128]
	ldp	x0, x12, [x29, #-176]
	add	x12, x12, x8
	ldr	x8, [sp, #1120]
	add	x27, x27, x8
	ldr	x8, [sp, #1088]
	add	x25, x25, x8
	ldr	x8, [sp, #1080]
	ldur	x1, [x29, #-136]
	add	x1, x1, x8
	ldr	x8, [sp, #1072]
	add	x3, x19, x8
	ldr	x8, [sp, #1064]
	add	x4, x21, x8
	ldr	x8, [sp, #1056]
	ldp	x5, x7, [x29, #-192]
	add	x5, x5, x8
	ldr	x8, [sp, #1048]
	add	x6, x0, x8
	ldr	x8, [sp, #1040]
	add	x7, x7, x8
	ldr	x8, [sp, #1032]
	add	x30, x22, x8
	ldr	x8, [sp, #1008]
	ldur	x19, [x29, #-144]
	add	x19, x19, x8
	ldr	x8, [sp, #1000]
	ldur	x21, [x29, #-160]
	add	x21, x21, x8
	ldur	x9, [x29, #-120]
	subs	x9, x9, #1
	mov	x0, x10
	b.ne	LBB5_2
	b	LBB5_11
LBB5_4:
	ldur	x19, [x29, #-104]
Lloh271:
	adrp	x8, _numba_gil_ensure@GOTPAGE
Lloh272:
	ldr	x8, [x8, _numba_gil_ensure@GOTPAGEOFF]
	sub	x0, x29, #108
	blr	x8
Lloh273:
	adrp	x8, _PyErr_Clear@GOTPAGE
Lloh274:
	ldr	x8, [x8, _PyErr_Clear@GOTPAGEOFF]
	blr	x8
	ldr	w1, [x19, #8]
	ldr	x0, [x19]
	ldr	w8, [x19, #32]
	cmp	w8, #1
	b.lt	LBB5_8
	sxtw	x1, w1
Lloh275:
	adrp	x8, _PyBytes_FromStringAndSize@GOTPAGE
Lloh276:
	ldr	x8, [x8, _PyBytes_FromStringAndSize@GOTPAGEOFF]
	blr	x8
	mov	x20, x0
	ldp	x0, x8, [x19, #16]
	blr	x8
	cbz	x0, LBB5_12
	mov	x1, x0
Lloh277:
	adrp	x8, _numba_runtime_build_excinfo_struct@GOTPAGE
Lloh278:
	ldr	x8, [x8, _numba_runtime_build_excinfo_struct@GOTPAGEOFF]
	mov	x0, x20
	blr	x8
	mov	x20, x0
Lloh279:
	adrp	x8, _NRT_Free@GOTPAGE
Lloh280:
	ldr	x8, [x8, _NRT_Free@GOTPAGEOFF]
	mov	x0, x19
	blr	x8
	cbz	x20, LBB5_10
	mov	x0, x20
	b	LBB5_9
LBB5_8:
	ldr	x2, [x19, #16]
Lloh281:
	adrp	x8, _numba_unpickle@GOTPAGE
Lloh282:
	ldr	x8, [x8, _numba_unpickle@GOTPAGEOFF]
	blr	x8
	cbz	x0, LBB5_10
LBB5_9:
Lloh283:
	adrp	x8, _numba_do_raise@GOTPAGE
Lloh284:
	ldr	x8, [x8, _numba_do_raise@GOTPAGEOFF]
	blr	x8
LBB5_10:
Lloh285:
	adrp	x8, _numba_gil_release@GOTPAGE
Lloh286:
	ldr	x8, [x8, _numba_gil_release@GOTPAGEOFF]
	sub	x0, x29, #108
	blr	x8
LBB5_11:
	add	sp, sp, #1680
	ldp	x29, x30, [sp, #80]
	ldp	x20, x19, [sp, #64]
	ldp	x22, x21, [sp, #48]
	ldp	x24, x23, [sp, #32]
	ldp	x26, x25, [sp, #16]
	ldp	x28, x27, [sp], #96
	ret
LBB5_12:
Lloh287:
	adrp	x0, _PyExc_RuntimeError@GOTPAGE
Lloh288:
	ldr	x0, [x0, _PyExc_RuntimeError@GOTPAGEOFF]
Lloh289:
	adrp	x1, "_.const.Error creating Python tuple from runtime exception arguments.11"@GOTPAGE
Lloh290:
	ldr	x1, [x1, "_.const.Error creating Python tuple from runtime exception arguments.11"@GOTPAGEOFF]
Lloh291:
	adrp	x8, _PyErr_SetString@GOTPAGE
Lloh292:
	ldr	x8, [x8, _PyErr_SetString@GOTPAGEOFF]
	blr	x8
	b	LBB5_11
	.loh AdrpLdrGot	Lloh269, Lloh270
	.loh AdrpLdrGot	Lloh273, Lloh274
	.loh AdrpLdrGot	Lloh271, Lloh272
	.loh AdrpLdrGot	Lloh275, Lloh276
	.loh AdrpLdrGot	Lloh279, Lloh280
	.loh AdrpLdrGot	Lloh277, Lloh278
	.loh AdrpLdrGot	Lloh281, Lloh282
	.loh AdrpLdrGot	Lloh283, Lloh284
	.loh AdrpLdrGot	Lloh285, Lloh286
	.loh AdrpLdrGot	Lloh291, Lloh292
	.loh AdrpLdrGot	Lloh289, Lloh290
	.loh AdrpLdrGot	Lloh287, Lloh288
	.cfi_endproc

	.globl	__ZN13_3cdynamic_3e33__numba_parfor_gufunc_0x10c777680B3v23B104c8tJTC_2fWQAliW1xhDEoY6EEMEUOEMISPGsAQMVj4QniQ4IXKQEMXwoMGLoQDDVsQR1NHAS2hQ9XgStYwaUTI24JtBVpeBJHUBAA_3dE5ArrayIyLi1E1C7mutable7alignedE5ArrayIfLi1E1C7mutable7alignedE5ArrayIfLi2E1C7mutable7alignedE5ArrayIfLi2E1C7mutable7alignedExxf5ArrayIfLi3E1C7mutable7alignedE5ArrayIbLi3E1C7mutable7alignedE5ArrayIfLi1E1C7mutable7alignedE5ArrayIfLi1E1A7mutable7alignedE5ArrayIfLi1E1A7mutable7alignedE5ArrayIbLi1E1C7mutable7alignedE5ArrayIfLi1E1C7mutable7alignedE5ArrayIbLi3E1C7mutable7alignedEff5ArrayIfLi3E1C7mutable7alignedE5ArrayIfLi3E1C7mutable7alignedE
	.weak_def_can_be_hidden	__ZN13_3cdynamic_3e33__numba_parfor_gufunc_0x10c777680B3v23B104c8tJTC_2fWQAliW1xhDEoY6EEMEUOEMISPGsAQMVj4QniQ4IXKQEMXwoMGLoQDDVsQR1NHAS2hQ9XgStYwaUTI24JtBVpeBJHUBAA_3dE5ArrayIyLi1E1C7mutable7alignedE5ArrayIfLi1E1C7mutable7alignedE5ArrayIfLi2E1C7mutable7alignedE5ArrayIfLi2E1C7mutable7alignedExxf5ArrayIfLi3E1C7mutable7alignedE5ArrayIbLi3E1C7mutable7alignedE5ArrayIfLi1E1C7mutable7alignedE5ArrayIfLi1E1A7mutable7alignedE5ArrayIfLi1E1A7mutable7alignedE5ArrayIbLi1E1C7mutable7alignedE5ArrayIfLi1E1C7mutable7alignedE5ArrayIbLi3E1C7mutable7alignedEff5ArrayIfLi3E1C7mutable7alignedE5ArrayIfLi3E1C7mutable7alignedE
	.p2align	2
__ZN13_3cdynamic_3e33__numba_parfor_gufunc_0x10c777680B3v23B104c8tJTC_2fWQAliW1xhDEoY6EEMEUOEMISPGsAQMVj4QniQ4IXKQEMXwoMGLoQDDVsQR1NHAS2hQ9XgStYwaUTI24JtBVpeBJHUBAA_3dE5ArrayIyLi1E1C7mutable7alignedE5ArrayIfLi1E1C7mutable7alignedE5ArrayIfLi2E1C7mutable7alignedE5ArrayIfLi2E1C7mutable7alignedExxf5ArrayIfLi3E1C7mutable7alignedE5ArrayIbLi3E1C7mutable7alignedE5ArrayIfLi1E1C7mutable7alignedE5ArrayIfLi1E1A7mutable7alignedE5ArrayIfLi1E1A7mutable7alignedE5ArrayIbLi1E1C7mutable7alignedE5ArrayIfLi1E1C7mutable7alignedE5ArrayIbLi3E1C7mutable7alignedEff5ArrayIfLi3E1C7mutable7alignedE5ArrayIfLi3E1C7mutable7alignedE:
	.cfi_startproc
	stp	d15, d14, [sp, #-160]!
	stp	d13, d12, [sp, #16]
	stp	d11, d10, [sp, #32]
	stp	d9, d8, [sp, #48]
	stp	x28, x27, [sp, #64]
	stp	x26, x25, [sp, #80]
	stp	x24, x23, [sp, #96]
	stp	x22, x21, [sp, #112]
	stp	x20, x19, [sp, #128]
	stp	x29, x30, [sp, #144]
	sub	sp, sp, #656
	.cfi_def_cfa_offset 816
	.cfi_offset w30, -8
	.cfi_offset w29, -16
	.cfi_offset w19, -24
	.cfi_offset w20, -32
	.cfi_offset w21, -40
	.cfi_offset w22, -48
	.cfi_offset w23, -56
	.cfi_offset w24, -64
	.cfi_offset w25, -72
	.cfi_offset w26, -80
	.cfi_offset w27, -88
	.cfi_offset w28, -96
	.cfi_offset b8, -104
	.cfi_offset b9, -112
	.cfi_offset b10, -120
	.cfi_offset b11, -128
	.cfi_offset b12, -136
	.cfi_offset b13, -144
	.cfi_offset b14, -152
	.cfi_offset b15, -160
	stp	q1, q2, [sp, #48]
	str	q0, [sp, #32]
	str	x6, [sp, #648]
	str	x1, [sp, #640]
	str	x0, [sp, #152]
	ldr	x9, [sp, #1672]
	ldr	x8, [sp, #1584]
	stp	x9, x8, [sp, #168]
	ldr	x8, [sp, #1496]
	str	x8, [sp, #184]
	ldr	x24, [sp, #1440]
	ldr	x26, [sp, #1384]
	ldr	x21, [sp, #1328]
	ldr	x25, [sp, #1272]
	ldr	x28, [sp, #1216]
	ldr	x20, [sp, #1128]
	ldr	x22, [sp, #1040]
	ldr	x23, [sp, #952]
	ldr	x27, [sp, #880]
	ldr	x0, [sp, #824]
Lloh293:
	adrp	x19, _NRT_incref@GOTPAGE
Lloh294:
	ldr	x19, [x19, _NRT_incref@GOTPAGEOFF]
	str	x0, [sp, #144]
	blr	x19
	str	x27, [sp, #136]
	mov	x0, x27
	blr	x19
	str	x23, [sp, #128]
	mov	x0, x23
	blr	x19
	mov	x0, x22
	blr	x19
	str	x20, [sp, #120]
	mov	x0, x20
	blr	x19
	str	x28, [sp, #112]
	mov	x0, x28
	blr	x19
	str	x25, [sp, #104]
	mov	x0, x25
	blr	x19
	str	x21, [sp, #96]
	mov	x0, x21
	blr	x19
	str	x26, [sp, #88]
	mov	x0, x26
	blr	x19
	str	x24, [sp, #80]
	mov	x0, x24
	blr	x19
	ldr	x0, [sp, #184]
	blr	x19
	ldr	x0, [sp, #176]
	blr	x19
	ldr	x0, [sp, #168]
	blr	x19
	ldr	x9, [sp, #648]
	ldp	x8, x19, [x9]
	str	x8, [sp, #408]
Lloh295:
	adrp	x20, _NRT_MemInfo_alloc_aligned@GOTPAGE
Lloh296:
	ldr	x20, [x20, _NRT_MemInfo_alloc_aligned@GOTPAGEOFF]
	mov	w0, #32
	mov	w1, #32
	blr	x20
	cbz	x0, LBB6_54
	mov	x21, x0
	str	x22, [sp, #24]
	ldr	x27, [x0, #24]
	mov	w0, #320
	mov	w1, #32
	blr	x20
	str	x0, [sp, #160]
	cbz	x0, LBB6_55
	str	x21, [sp, #16]
	mov	x8, #9223372036854775806
	ldr	x9, [sp, #408]
	sub	x9, x19, x9
	str	x9, [sp, #400]
	cmp	x9, x8
	ldp	q14, q13, [sp, #48]
	ldr	q15, [sp, #32]
	b.hi	LBB6_52
	mov	x23, #0
	ldr	x7, [sp, #1096]
	ldr	x8, [sp, #1088]
	mul	x14, x8, x7
	ldr	x9, [sp, #1032]
	str	x9, [sp, #392]
	ldr	x12, [sp, #1024]
	ldr	x20, [sp, #408]
	madd	x15, x20, x8, x12
	ldr	x25, [sp, #1728]
	ldr	x9, [sp, #1720]
	mul	x17, x9, x25
	ldr	x8, [sp, #1704]
	str	x8, [sp, #648]
	madd	x1, x20, x9, x12
	ldr	x28, [sp, #1640]
	ldr	x10, [sp, #1632]
	ldr	x22, [sp, #1616]
	mul	x2, x10, x28
	ldr	x19, [sp, #1552]
	ldr	x11, [sp, #1544]
	madd	x4, x20, x10, x12
	ldr	x21, [sp, #1528]
	ldr	x16, [sp, #1472]
	ldr	x13, [sp, #928]
	ldr	x0, [sp, #912]
	lsl	x24, x13, #2
	madd	x0, x20, x24, x0
	mul	x26, x19, x11
	ldr	x30, [sp, #1184]
	ldr	x5, [sp, #1176]
	sub	x6, x12, #1
	madd	x8, x20, x11, x6
	str	x8, [sp, #632]
	ldr	x11, [sp, #1160]
	ldr	x3, [sp, #160]
	ldr	x3, [x3, #24]
	lsl	x13, x14, #2
	lsl	x14, x15, #2
	mul	x9, x30, x5
	ldr	x15, [sp, #1072]
	sub	x14, x14, #4
	lsl	x10, x17, #2
	lsl	x17, x1, #2
	sub	x8, x17, #4
	lsl	x17, x2, #2
	lsl	x1, x4, #2
	mov	x4, x13
	sub	x1, x1, #4
	madd	x2, x20, x5, x6
	madd	x5, x20, x13, x15
	madd	x13, x14, x7, x15
	str	x13, [sp, #336]
	orr	x14, x25, x7
	orr	x15, x14, x28
	movi.2d	v0, #0000000000000000
	ubfx	x13, x14, #61, #1
	mov	x14, x10
	ldr	x10, [sp, #648]
	madd	x8, x8, x25, x10
	str	x8, [sp, #328]
	ubfx	x8, x15, #61, #1
	stp	x8, x13, [sp, #256]
	fmov	s1, #1.00000000
	movi.2d	v2, #0000000000000000
	fmov.4s	v3, #1.00000000
	movi.4h	v4, #1
	madd	x15, x20, x14, x10
	madd	x8, x1, x28, x22
	str	x8, [sp, #312]
	madd	x10, x20, x17, x22
	str	x19, [sp, #640]
	ldr	x8, [sp, #632]
	madd	x8, x8, x19, x21
	str	x8, [sp, #248]
	fmov	s5, #0.50000000
	movi.4s	v6, #63, lsl #24
	stp	x9, x26, [sp, #424]
	madd	x6, x20, x26, x21
	str	x30, [sp, #632]
	madd	x1, x2, x30, x11
	str	x1, [sp, #232]
	madd	x9, x20, x9, x11
	ldr	x11, [sp, #1416]
	str	x11, [sp, #624]
	ldr	x11, [sp, #1376]
	str	x11, [sp, #616]
	sub	x11, x27, x0
	str	x11, [sp, #200]
	stp	x24, x28, [sp, #376]
	neg	x11, x24
	str	x11, [sp, #192]
	lsl	x2, x20, #3
	ldr	x11, [sp, #1360]
	str	x11, [sp, #608]
	ldr	x19, [sp, #1320]
	ldr	x21, [sp, #1304]
	ldr	x24, [sp, #1248]
	ldr	x8, [sp, #1000]
	ldr	x11, [sp, #992]
	stp	x11, x8, [sp, #280]
	ldr	x11, [sp, #984]
	str	x11, [sp, #272]
	ldr	x8, [sp, #392]
	sub	x11, x8, x2
	stp	x11, x10, [sp, #296]
	stp	x25, x7, [sp, #208]
	lsl	x26, x7, #2
	lsl	x1, x25, #2
	lsl	x7, x28, #2
	add	x11, x0, #32
	str	x11, [sp, #512]
	str	x9, [sp, #224]
	str	x9, [sp, #544]
	str	x6, [sp, #240]
	str	x6, [sp, #536]
	str	x10, [sp, #576]
	ldr	x10, [sp, #856]
	str	x15, [sp, #320]
	str	x15, [sp, #568]
	stp	x5, x17, [sp, #344]
	str	x5, [sp, #560]
	sub	x9, x8, x2
	mov	x5, x20
	stp	x14, x4, [sp, #360]
	b	LBB6_5
LBB6_4:
	ldr	x5, [sp, #448]
	add	x5, x5, #1
	ldp	x14, x4, [sp, #360]
	ldr	x9, [sp, #560]
	add	x9, x9, x4
	str	x9, [sp, #560]
	ldr	x9, [sp, #568]
	add	x9, x9, x14
	str	x9, [sp, #568]
	ldr	x17, [sp, #352]
	ldr	x9, [sp, #576]
	add	x9, x9, x17
	str	x9, [sp, #576]
	ldp	x9, x8, [sp, #424]
	ldr	x11, [sp, #536]
	add	x11, x11, x8
	str	x11, [sp, #536]
	ldr	x11, [sp, #544]
	add	x11, x11, x9
	str	x11, [sp, #544]
	ldr	x9, [sp, #376]
	ldr	x11, [sp, #512]
	add	x11, x11, x9
	str	x11, [sp, #512]
	add	x0, x0, x9
	add	x2, x2, #8
	ldr	x9, [sp, #400]
	cmp	x20, x9
	add	x23, x20, #1
	ldr	x9, [sp, #440]
	b.eq	LBB6_52
LBB6_5:
	str	x2, [sp, #520]
	subs	x11, x9, #8
	str	x11, [sp, #440]
	mov	w15, #8
	csel	x25, x9, x15, lt
	stp	q0, q0, [x3, #288]
	ldr	x9, [sp, #408]
	add	x9, x23, x9
	ldr	x11, [sp, #392]
	sub	x9, x11, x9, lsl #3
	stp	q0, q0, [x3, #256]
	cmp	x9, #8
	csel	x22, x9, x15, lt
	ldr	x9, [sp, #296]
	sub	x9, x9, x23, lsl #3
	stp	q0, q0, [x3, #224]
	cmp	x9, #8
	csel	x8, x9, x15, lt
	str	x8, [sp, #592]
	mul	x9, x23, x4
	ldr	x15, [sp, #344]
	add	x15, x15, x9
	str	x15, [sp, #504]
	stp	q0, q0, [x3, #192]
	ldr	x15, [sp, #336]
	add	x8, x15, x9
	stp	x5, x8, [sp, #448]
	mul	x9, x23, x14
	ldr	x14, [sp, #320]
	add	x14, x14, x9
	str	x14, [sp, #496]
	ldr	x14, [sp, #328]
	add	x8, x14, x9
	stp	q0, q0, [x3, #160]
	str	x23, [sp, #528]
	mul	x9, x23, x17
	ldp	x15, x14, [sp, #304]
	add	x13, x15, x9
	stp	x8, x13, [sp, #480]
	add	x8, x14, x9
	str	x8, [sp, #472]
	stp	q0, q0, [x3, #128]
	sub	x9, x11, x5, lsl #3
	str	x9, [sp, #648]
	stp	q0, q0, [x3, #96]
	stp	q0, q0, [x3, #64]
	stp	q0, q0, [x3, #32]
	ldr	x9, [sp, #384]
	ubfx	x8, x9, #61, #1
	str	x8, [sp, #464]
	stp	q0, q0, [x3]
	cmp	x12, #1
	b.lt	LBB6_25
	mov	x11, #0
	and	x6, x25, #0xfffffffffffffff8
	str	x0, [sp, #416]
	ldr	x0, [sp, #592]
	lsl	x9, x0, #2
	ldr	x15, [sp, #528]
	ldp	x14, x17, [sp, #424]
	mul	x14, x15, x14
	mul	x15, x15, x17
	ldr	x8, [sp, #456]
	add	x17, x8, x9
	cmp	x3, x17
	cset	w17, lo
	add	x2, x3, #256
	add	x2, x2, x9
	ldr	x30, [sp, #504]
	cmp	x30, x2
	csel	w4, wzr, w17, hs
	ldr	x8, [sp, #480]
	add	x5, x8, x9
	cmp	x3, x5
	cset	w5, lo
	mov	x13, x21
	mov	x21, x19
	ldr	x19, [sp, #496]
	cmp	x19, x2
	csel	w20, wzr, w5, hs
	orr	w4, w20, w4
	ldr	x8, [sp, #472]
	add	x20, x8, x9
	cmp	x3, x20
	cset	w20, lo
	ldr	x8, [sp, #488]
	cmp	x8, x2
	csel	w23, wzr, w20, hs
	ldr	x28, [sp, #256]
	orr	w23, w28, w23
	orr	w4, w23, w4
	ldr	x23, [sp, #248]
	add	x23, x23, x0
	add	x23, x23, x15
	cmp	x3, x23
	ldp	x28, x23, [sp, #224]
	add	x23, x23, x0
	add	x23, x23, x14
	add	x14, x28, x14
	ldr	x28, [sp, #240]
	add	x15, x28, x15
	ccmp	x15, x2, #2, lo
	ldr	x15, [sp, #640]
	ccmp	x15, #0, #8, hs
	csinc	w15, w4, wzr, pl
	cmp	x3, x23
	ccmp	x14, x2, #2, lo
	ldr	x14, [sp, #632]
	ccmp	x14, #0, #8, hs
	csinc	w14, w15, wzr, pl
	add	x15, x3, #224
	add	x9, x15, x9
	cmp	x30, x9
	csel	w15, wzr, w17, hs
	cmp	x19, x9
	mov	x19, x21
	mov	x21, x13
	csel	w17, wzr, w5, hs
	orr	w15, w17, w15
	cmp	x8, x9
	csel	w9, wzr, w20, hs
	ldr	x17, [sp, #264]
	orr	w9, w9, w17
	orr	w9, w9, w15
	ldr	x8, [sp, #464]
	orr	w9, w8, w9
	and	x8, x0, #0xfffffffffffffffc
	str	x8, [sp, #552]
	cmp	x22, #8
	cset	w15, lo
	orr	w8, w15, w14
	str	w8, [sp, #604]
	cmp	x0, #4
	ldr	x0, [sp, #416]
	csinc	w8, w9, wzr, hs
	str	w8, [sp, #588]
	ldr	x9, [sp, #544]
	ldr	x4, [sp, #536]
	ldr	x30, [sp, #576]
	ldr	x28, [sp, #568]
	ldr	x14, [sp, #560]
	b	LBB6_8
LBB6_7:
	add	x11, x11, #1
	add	x14, x14, x26
	add	x28, x28, x1
	add	x30, x30, x7
	ldr	x13, [sp, #640]
	add	x4, x4, x13
	ldr	x8, [sp, #632]
	add	x9, x9, x8
	cmp	x12, x11
	b.eq	LBB6_25
LBB6_8:
	mul	x17, x11, x19
	ldr	s7, [x21, x17]
	ldr	x15, [sp, #616]
	mul	x17, x11, x15
	ldr	x15, [sp, #608]
	ldr	s16, [x15, x17]
	ldr	s18, [x16, x11, lsl #2]
	ldr	s17, [x24, x11, lsl #2]
	ldr	s19, [x10, x11, lsl #2]
	ldr	x15, [sp, #624]
	ldrb	w17, [x15, x11]
	cbz	w17, LBB6_12
	ldr	x15, [sp, #648]
	cmp	x15, #1
	b.lt	LBB6_7
	fmul	s21, s14, s18
	fmul	s20, s21, s19
	fmul	s21, s21, s17
	ldr	w8, [sp, #604]
	tbz	w8, #0, LBB6_15
	mov	x5, #0
	b	LBB6_18
LBB6_12:
	ldr	x15, [sp, #648]
	cmp	x15, #1
	b.lt	LBB6_7
	fmul	s20, s14, s18
	fmul	s18, s20, s19
	fmul	s17, s20, s17
	ldr	w8, [sp, #588]
	tbz	w8, #0, LBB6_20
	mov	x17, #0
	b	LBB6_23
LBB6_15:
	mov	x23, #0
	add	x15, x3, #224
	ldp	q24, q25, [x15]
	mov	w5, #160
	add	x17, x3, #256
	add	x15, x3, #160
	ldp	q23, q22, [x15]
LBB6_16:
	ldr	d26, [x4, x23]
	cmtst.8b	v27, v26, v26
	ldr	d26, [x9, x23]
	cmtst.8b	v26, v26, v26
	add	x15, x14, x5
	ldp	q28, q29, [x15, #-160]
	fcmeq.4s	v30, v29, v3
	fcmeq.4s	v31, v28, v3
	uzp1.8h	v30, v31, v30
	add	x15, x28, x5
	ldp	q31, q8, [x15, #-160]
	fcmeq.4s	v9, v8, v3
	fcmeq.4s	v10, v31, v3
	uzp1.8h	v9, v10, v9
	and.16b	v30, v30, v9
	xtn.8b	v30, v30
	fcmeq.4s	v8, v8, #0.0
	add	x15, x30, x5
	fcmeq.4s	v31, v31, #0.0
	uzp1.8h	v31, v31, v8
	ldp	q8, q9, [x15, #-160]
	fcmeq.4s	v10, v9, #0.0
	fcmeq.4s	v11, v8, #0.0
	uzp1.8h	v10, v11, v10
	orr.16b	v31, v31, v10
	xtn.8b	v31, v31
	fsub.4s	v29, v3, v29
	fsub.4s	v28, v3, v28
	fmul.4s	v28, v28, v8
	fmul.4s	v29, v29, v9
	fcmeq.4s	v29, v29, v3
	fcmeq.4s	v28, v28, v3
	uzp1.8h	v28, v28, v29
	xtn.8b	v28, v28
	ldp	q29, q8, [x17, #-256]
	zip2.8b	v9, v30, v0
	and.8b	v9, v9, v4
	ushll.4s	v9, v9, #0
	ucvtf.4s	v9, v9
	zip1.8b	v30, v30, v0
	and.8b	v30, v30, v4
	ushll.4s	v30, v30, #0
	ucvtf.4s	v30, v30
	fmul.4s	v10, v30, v7[0]
	fmul.4s	v11, v9, v7[0]
	fadd.4s	v8, v8, v11
	fadd.4s	v29, v29, v10
	stp	q29, q8, [x17, #-256]
	fmul.4s	v29, v9, v16[0]
	fmul.4s	v30, v30, v16[0]
	fadd.4s	v23, v23, v30
	fadd.4s	v22, v22, v29
	stp	q23, q22, [x17, #-96]
	zip2.8b	v22, v31, v0
	and.8b	v22, v22, v4
	ushll.4s	v22, v22, #0
	ucvtf.4s	v22, v22
	zip1.8b	v23, v31, v0
	and.8b	v23, v23, v4
	ushll.4s	v23, v23, #0
	ucvtf.4s	v23, v23
	fmul.4s	v29, v23, v20[0]
	fmul.4s	v30, v22, v20[0]
	fmul.4s	v31, v23, v21[0]
	fmul.4s	v8, v22, v21[0]
	ldp	q23, q22, [x17, #-64]
	fadd.4s	v22, v30, v22
	fadd.4s	v23, v29, v23
	stp	q23, q22, [x17, #-64]
	ldp	q29, q30, [x17, #-224]
	fadd.4s	v30, v8, v30
	fadd.4s	v29, v31, v29
	stp	q29, q30, [x17, #-224]
	zip1.8b	v29, v27, v0
	and.8b	v29, v29, v4
	ushll.4s	v29, v29, #0
	ucvtf.4s	v29, v29
	zip2.8b	v27, v27, v0
	and.8b	v27, v27, v4
	ushll.4s	v27, v27, #0
	ucvtf.4s	v27, v27
	fmul.4s	v27, v27, v13[0]
	fmul.4s	v29, v29, v13[0]
	fmul.4s	v29, v29, v18[0]
	fmul.4s	v30, v27, v18[0]
	fmul.4s	v31, v30, v19[0]
	fmul.4s	v8, v29, v19[0]
	zip2.8b	v27, v28, v0
	and.8b	v27, v27, v4
	ushll.4s	v27, v27, #0
	ucvtf.4s	v27, v27
	zip1.8b	v28, v28, v0
	and.8b	v28, v28, v4
	ushll.4s	v28, v28, #0
	ucvtf.4s	v28, v28
	fmul.4s	v8, v8, v28
	fmul.4s	v31, v31, v27
	zip2.8b	v9, v26, v0
	and.8b	v9, v9, v4
	ushll.4s	v9, v9, #0
	ucvtf.4s	v9, v9
	zip1.8b	v26, v26, v0
	and.8b	v26, v26, v4
	ushll.4s	v26, v26, #0
	ucvtf.4s	v26, v26
	fmul.4s	v26, v26, v14[0]
	fmul.4s	v9, v9, v14[0]
	fmul.4s	v9, v9, v18[0]
	fmul.4s	v26, v26, v18[0]
	fmul.4s	v10, v9, v19[0]
	ldp	q11, q12, [x17]
	fmul.4s	v10, v10, v27
	fadd.4s	v25, v25, v10
	fmul.4s	v10, v26, v19[0]
	fmul.4s	v10, v10, v28
	fadd.4s	v31, v31, v12
	fadd.4s	v24, v24, v10
	fadd.4s	v8, v8, v11
	stp	q8, q31, [x17]
	stp	q24, q25, [x17, #-32]
	fmul.4s	v24, v30, v17[0]
	fmul.4s	v25, v29, v17[0]
	ldp	q29, q30, [x17, #-160]
	fmul.4s	v25, v25, v28
	fmul.4s	v24, v24, v27
	fadd.4s	v24, v24, v30
	fadd.4s	v25, v25, v29
	stp	q25, q24, [x17, #-160]
	fmul.4s	v24, v9, v17[0]
	ldp	q25, q29, [x17, #-192]
	fmul.4s	v26, v26, v17[0]
	add	x23, x23, #8
	fmul.4s	v26, v26, v28
	fmul.4s	v24, v24, v27
	fadd.4s	v24, v24, v29
	fadd.4s	v25, v26, v25
	stp	q25, q24, [x17, #-192]
	add	x17, x17, #32
	add	x5, x5, #32
	mov.16b	v24, v8
	mov.16b	v25, v31
	cmp	x6, x23
	b.ne	LBB6_16
	and	x5, x22, #0xfffffffffffffff8
	and	x8, x22, #0xfffffffffffffff8
	cmp	x22, x8
	b.eq	LBB6_7
LBB6_18:
	add	x15, x3, #160
	add	x17, x15, x5, lsl #2
LBB6_19:
	ldr	s22, [x14, x5, lsl #2]
	ldr	s23, [x28, x5, lsl #2]
	ldr	s24, [x30, x5, lsl #2]
	ldrb	w23, [x4, x5]
	ldrb	w15, [x9, x5]
	fcmp	s23, s1
	add	x5, x5, #1
	fccmp	s22, s1, #0, eq
	cset	w2, eq
	fcmp	s23, #0.0
	cset	w20, eq
	fcmp	s24, #0.0
	csinc	w20, w20, wzr, ne
	fsub	s22, s1, s22
	fmul	s22, s22, s24
	ldur	s23, [x17, #-160]
	ucvtf	s24, w2
	fmul	s25, s7, s24
	fadd	s23, s23, s25
	stur	s23, [x17, #-160]
	ldr	s23, [x17]
	fmul	s24, s16, s24
	fadd	s23, s24, s23
	str	s23, [x17]
	ucvtf	s23, w20
	fmul	s24, s20, s23
	fmul	s23, s21, s23
	ldr	s25, [x17, #32]
	fadd	s24, s24, s25
	ldur	s25, [x17, #-128]
	fadd	s23, s23, s25
	cmp	w23, #0
	fcsel	s25, s1, s2, ne
	fmul	s25, s13, s25
	str	s24, [x17, #32]
	fmul	s24, s18, s25
	fmul	s25, s19, s24
	fcmp	s22, s1
	fcsel	s22, s1, s2, eq
	fmul	s25, s25, s22
	stur	s23, [x17, #-128]
	cmp	w15, #0
	fcsel	s23, s1, s2, ne
	fmul	s23, s14, s23
	fmul	s23, s18, s23
	ldr	s26, [x17, #96]
	fadd	s25, s25, s26
	fmul	s26, s19, s23
	fmul	s26, s26, s22
	fmul	s24, s17, s24
	fmul	s24, s24, s22
	fmul	s23, s17, s23
	fmul	s22, s23, s22
	str	s25, [x17, #96]
	ldr	s23, [x17, #64]
	fadd	s23, s26, s23
	ldur	s25, [x17, #-64]
	fadd	s24, s24, s25
	str	s23, [x17, #64]
	stur	s24, [x17, #-64]
	ldur	s23, [x17, #-96]
	fadd	s22, s22, s23
	stur	s22, [x17, #-96]
	add	x17, x17, #4
	cmp	x25, x5
	b.ne	LBB6_19
	b	LBB6_7
LBB6_20:
	and	x17, x25, #0xfffffffffffffffc
	add	x5, x3, #224
	mov	w23, #160
LBB6_21:
	add	x15, x14, x23
	ldur	q19, [x15, #-160]
	add	x15, x28, x23
	ldur	q20, [x15, #-160]
	add	x15, x30, x23
	ldur	q21, [x15, #-160]
	fcmeq.4s	v22, v19, v3
	fcmeq.4s	v23, v20, v3
	and.16b	v22, v22, v23
	xtn.4h	v22, v22
	and.8b	v22, v22, v4
	fcmeq.4s	v20, v20, #0.0
	fcmeq.4s	v23, v21, #0.0
	orr.16b	v20, v20, v23
	xtn.4h	v20, v20
	and.8b	v20, v20, v4
	fsub.4s	v19, v3, v19
	fmul.4s	v19, v19, v21
	fcmeq.4s	v19, v19, v3
	xtn.4h	v19, v19
	and.8b	v19, v19, v4
	ldur	q21, [x5, #-224]
	ushll.4s	v22, v22, #0
	ucvtf.4s	v22, v22
	fmul.4s	v23, v22, v7[0]
	fadd.4s	v21, v21, v23
	stur	q21, [x5, #-224]
	ldur	q21, [x5, #-64]
	fmul.4s	v22, v22, v16[0]
	fadd.4s	v21, v21, v22
	stur	q21, [x5, #-64]
	ushll.4s	v20, v20, #0
	ucvtf.4s	v20, v20
	fmul.4s	v21, v20, v18[0]
	fmul.4s	v20, v20, v17[0]
	ldur	q22, [x5, #-32]
	fadd.4s	v21, v21, v22
	stur	q21, [x5, #-32]
	ldur	q21, [x5, #-192]
	fadd.4s	v20, v20, v21
	stur	q20, [x5, #-192]
	ushll.4s	v19, v19, #0
	ucvtf.4s	v19, v19
	fmul.4s	v20, v19, v18[0]
	fmul.4s	v19, v19, v17[0]
	ldr	q21, [x5]
	fadd.4s	v20, v20, v21
	str	q20, [x5]
	ldur	q20, [x5, #-160]
	fadd.4s	v19, v19, v20
	stur	q19, [x5, #-160]
	add	x23, x23, #16
	add	x5, x5, #16
	subs	x17, x17, #4
	b.ne	LBB6_21
	ldr	x8, [sp, #592]
	and	x17, x8, #0xfffffffffffffffc
	ldr	x13, [sp, #552]
	cmp	x8, x13
	b.eq	LBB6_7
LBB6_23:
	add	x15, x3, #160
	add	x5, x15, x17, lsl #2
LBB6_24:
	ldr	s19, [x14, x17, lsl #2]
	ldr	s20, [x28, x17, lsl #2]
	ldr	s21, [x30, x17, lsl #2]
	add	x17, x17, #1
	fcmp	s20, s1
	fccmp	s19, s1, #0, eq
	cset	w15, eq
	fcmp	s20, #0.0
	cset	w2, eq
	fcmp	s21, #0.0
	csinc	w2, w2, wzr, ne
	fsub	s19, s1, s19
	fmul	s19, s19, s21
	ucvtf	s20, w15
	ldur	s21, [x5, #-160]
	fmul	s22, s7, s20
	fadd	s21, s21, s22
	ldr	s22, [x5]
	fmul	s20, s16, s20
	stur	s21, [x5, #-160]
	fadd	s20, s22, s20
	str	s20, [x5]
	ucvtf	s20, w2
	fmul	s21, s18, s20
	fmul	s20, s17, s20
	ldr	s22, [x5, #32]
	fadd	s21, s21, s22
	ldur	s22, [x5, #-128]
	fadd	s20, s20, s22
	fcmp	s19, s1
	str	s21, [x5, #32]
	fcsel	s19, s1, s2, eq
	fmul	s21, s18, s19
	fmul	s19, s17, s19
	ldr	s22, [x5, #64]
	fadd	s21, s21, s22
	stur	s20, [x5, #-128]
	str	s21, [x5, #64]
	ldur	s20, [x5, #-96]
	fadd	s19, s19, s20
	stur	s19, [x5, #-96]
	add	x5, x5, #4
	cmp	x25, x17
	b.ne	LBB6_24
	b	LBB6_7
LBB6_25:
	ldr	x9, [sp, #648]
	cmp	x9, #1
	ldr	x20, [sp, #528]
	add	x30, x3, #288
	ldr	x2, [sp, #520]
	mov	w15, #4059
	movk	w15, #16457, lsl #16
	b.lt	LBB6_39
	mov	x9, #0
	ldr	x8, [sp, #592]
	cmp	x8, #4
	b.lo	LBB6_38
	sub	x11, x27, x3
	cmp	x11, #64
	b.lo	LBB6_38
	ldp	x14, x11, [sp, #192]
	madd	x11, x14, x20, x11
	cmp	x11, #64
	b.lo	LBB6_38
	dup.4s	v7, w15
	ldr	x8, [sp, #592]
	cmp	x8, #16
	b.hs	LBB6_31
	mov	x9, #0
	b	LBB6_35
LBB6_31:
	and	x9, x25, #0xfffffffffffffff0
	add	x11, x27, #32
	ldr	x14, [sp, #512]
	add	x17, x3, #32
LBB6_32:
	ldp	q16, q17, [x17, #-32]
	ldp	q18, q19, [x17], #64
	ldp	q20, q21, [x14, #-32]
	ldp	q22, q23, [x14], #64
	fadd.4s	v16, v16, v20
	fadd.4s	v17, v17, v21
	fadd.4s	v18, v18, v22
	fadd.4s	v19, v19, v23
	fmul.4s	v16, v16, v15[0]
	fmul.4s	v17, v17, v15[0]
	fmul.4s	v18, v18, v15[0]
	fmul.4s	v19, v19, v15[0]
	fmul.4s	v16, v16, v6
	fmul.4s	v17, v17, v6
	fmul.4s	v18, v18, v6
	fmul.4s	v19, v19, v6
	fdiv.4s	v16, v16, v7
	fdiv.4s	v17, v17, v7
	fdiv.4s	v18, v18, v7
	fdiv.4s	v19, v19, v7
	stp	q16, q17, [x11, #-32]
	stp	q18, q19, [x11], #64
	subs	x9, x9, #16
	b.ne	LBB6_32
	ldr	x8, [sp, #592]
	and	x9, x8, #0xfffffffffffffff0
	cmp	x8, x9
	b.eq	LBB6_39
	ldr	x8, [sp, #592]
	tst	x8, #0xc
	b.eq	LBB6_38
LBB6_35:
	and	x8, x25, #0xfffffffffffffffc
	sub	x11, x9, x8
	lsl	x9, x9, #2
LBB6_36:
	ldr	q16, [x3, x9]
	ldr	q17, [x0, x9]
	fadd.4s	v16, v16, v17
	fmul.4s	v16, v16, v15[0]
	fmul.4s	v16, v16, v6
	fdiv.4s	v16, v16, v7
	str	q16, [x27, x9]
	add	x9, x9, #16
	adds	x11, x11, #4
	b.ne	LBB6_36
	ldr	x8, [sp, #592]
	and	x9, x8, #0xfffffffffffffffc
	cmp	x8, x9
	b.eq	LBB6_39
LBB6_38:
	ldr	s7, [x3, x9, lsl #2]
	ldr	s16, [x0, x9, lsl #2]
	fadd	s7, s7, s16
	fmul	s7, s15, s7
	fmul	s7, s7, s5
	fmov	s16, w15
	fdiv	s7, s7, s16
	str	s7, [x27, x9, lsl #2]
	add	x9, x9, #1
	cmp	x25, x9
	b.ne	LBB6_38
LBB6_39:
	cmp	x12, #1
	b.lt	LBB6_50
	ldr	x9, [sp, #648]
	cmp	x9, #1
	b.lt	LBB6_4
	mov	x9, #0
	lsl	x11, x22, #2
	add	x14, x30, x11
	ldr	x15, [sp, #216]
	ubfx	x15, x15, #61, #1
	ldr	x8, [sp, #456]
	add	x17, x8, x11
	add	x4, x3, #128
	cmp	x4, x17
	ldr	x17, [sp, #208]
	ubfx	x17, x17, #61, #1
	ldp	x5, x2, [sp, #496]
	ccmp	x2, x14, #2, lo
	csinc	w15, w15, wzr, hs
	ldp	x8, x13, [sp, #480]
	add	x2, x8, x11
	cmp	x4, x2
	ldr	x2, [sp, #520]
	ccmp	x5, x14, #2, lo
	csinc	w17, w17, wzr, hs
	orr	w15, w15, w17
	ldr	x8, [sp, #472]
	add	x17, x8, x11
	cmp	x4, x17
	ccmp	x13, x14, #2, lo
	csinc	w15, w15, wzr, hs
	add	x11, x27, x11
	cmp	x4, x11
	ccmp	x27, x14, #2, lo
	csinc	w14, w15, wzr, hs
	and	x11, x22, #0xfffffffffffffffc
	cmp	x22, #4
	cset	w15, lo
	ldr	x8, [sp, #464]
	orr	w15, w15, w8
	orr	w14, w15, w14
	ldr	x17, [sp, #560]
	ldr	x4, [sp, #568]
	ldr	x5, [sp, #576]
	b	LBB6_43
LBB6_42:
	add	x9, x9, #1
	add	x5, x5, x7
	add	x4, x4, x1
	add	x17, x17, x26
	cmp	x12, x9
	b.eq	LBB6_50
LBB6_43:
	ldr	s7, [x16, x9, lsl #2]
	ldr	s16, [x24, x9, lsl #2]
	ldr	s17, [x10, x9, lsl #2]
	tbz	w14, #0, LBB6_45
	mov	x23, #0
	b	LBB6_48
LBB6_45:
	mov	x6, #0
	add	x23, x3, #288
	and	x28, x25, #0xfffffffffffffffc
LBB6_46:
	ldr	q18, [x17, x6]
	ldr	q19, [x4, x6]
	ldr	q20, [x5, x6]
	fcmeq.4s	v18, v18, #0.0
	fcmeq.4s	v19, v19, #0.0
	orr.16b	v18, v18, v19
	fcmeq.4s	v19, v20, #0.0
	orr.16b	v18, v18, v19
	xtn.4h	v18, v18
	and.8b	v18, v18, v4
	ldr	q19, [x27, x6]
	fmul.4s	v19, v19, v7[0]
	fmul.4s	v20, v19, v17[0]
	ushll.4s	v18, v18, #0
	ucvtf.4s	v18, v18
	fmul.4s	v20, v20, v18
	fmul.4s	v19, v19, v16[0]
	fmul.4s	v18, v19, v18
	ldr	q19, [x23]
	fadd.4s	v19, v19, v20
	str	q19, [x23]
	ldur	q19, [x23, #-160]
	fadd.4s	v18, v19, v18
	stur	q18, [x23, #-160]
	add	x6, x6, #16
	add	x23, x23, #16
	subs	x28, x28, #4
	b.ne	LBB6_46
	and	x23, x22, #0xfffffffffffffffc
	cmp	x22, x11
	b.eq	LBB6_42
LBB6_48:
	add	x6, x30, x23, lsl #2
LBB6_49:
	ldr	s18, [x17, x23, lsl #2]
	ldr	s19, [x4, x23, lsl #2]
	ldr	s20, [x5, x23, lsl #2]
	fcmp	s18, #0.0
	ldr	s18, [x27, x23, lsl #2]
	add	x23, x23, #1
	cset	w15, eq
	fcmp	s19, #0.0
	csinc	w15, w15, wzr, ne
	fcmp	s20, #0.0
	csinc	w15, w15, wzr, ne
	fmul	s18, s7, s18
	ucvtf	s19, w15
	fmul	s20, s17, s18
	fmul	s20, s20, s19
	fmul	s18, s16, s18
	fmul	s18, s18, s19
	ldr	s19, [x6]
	fadd	s19, s19, s20
	str	s19, [x6]
	ldur	s19, [x6, #-160]
	fadd	s18, s19, s18
	stur	s18, [x6, #-160]
	add	x6, x6, #4
	cmp	x25, x23
	b.ne	LBB6_49
	b	LBB6_42
LBB6_50:
	add	x9, x3, #160
	mov	x11, x2
	ldr	x14, [sp, #648]
	cmp	x14, #1
	ldp	x17, x15, [sp, #280]
	ldr	x4, [sp, #272]
	b.lt	LBB6_4
LBB6_51:
	ldur	s7, [x9, #-160]
	ldur	s16, [x9, #-128]
	fadd	s7, s7, s16
	ldur	s16, [x9, #-96]
	fadd	s7, s7, s16
	ldur	s16, [x9, #-64]
	fadd	s7, s7, s16
	ldur	s16, [x9, #-32]
	fadd	s7, s7, s16
	and	x14, x17, x11, asr #63
	add	x14, x14, x11
	mul	x14, x14, x15
	add	x14, x4, x14, lsl #2
	str	s7, [x14]
	ldr	s7, [x9]
	ldr	s16, [x9, #32]
	fadd	s7, s7, s16
	ldr	s16, [x9, #64]
	fadd	s7, s7, s16
	ldr	s16, [x9, #96]
	fadd	s7, s7, s16
	ldr	s16, [x9, #128]
	fadd	s7, s7, s16
	str	s7, [x14, #4]
	ldr	s7, [x9]
	str	s7, [x14, #8]
	ldr	s7, [x9, #32]
	str	s7, [x14, #12]
	ldr	s7, [x9, #64]
	str	s7, [x14, #16]
	ldr	s7, [x9, #96]
	str	s7, [x14, #20]
	ldr	s7, [x9, #128]
	str	s7, [x14, #24]
	add	x11, x11, #1
	add	x9, x9, #4
	subs	x25, x25, #1
	b.ne	LBB6_51
	b	LBB6_4
LBB6_52:
Lloh297:
	adrp	x19, _NRT_decref@GOTPAGE
Lloh298:
	ldr	x19, [x19, _NRT_decref@GOTPAGEOFF]
	ldr	x0, [sp, #168]
	blr	x19
	ldr	x0, [sp, #176]
	blr	x19
	ldr	x0, [sp, #184]
	blr	x19
	ldr	x0, [sp, #80]
	blr	x19
	ldr	x0, [sp, #88]
	blr	x19
	ldr	x0, [sp, #96]
	blr	x19
	ldr	x0, [sp, #104]
	blr	x19
	ldr	x0, [sp, #112]
	blr	x19
	ldr	x0, [sp, #120]
	blr	x19
	ldr	x0, [sp, #24]
	blr	x19
	ldr	x0, [sp, #16]
	blr	x19
	ldr	x0, [sp, #128]
	blr	x19
	ldr	x0, [sp, #136]
	blr	x19
	ldr	x0, [sp, #144]
	blr	x19
	ldr	x0, [sp, #160]
	blr	x19
	mov	w0, #0
	ldr	x8, [sp, #152]
	str	xzr, [x8]
LBB6_53:
	add	sp, sp, #656
	ldp	x29, x30, [sp, #144]
	ldp	x20, x19, [sp, #128]
	ldp	x22, x21, [sp, #112]
	ldp	x24, x23, [sp, #96]
	ldp	x26, x25, [sp, #80]
	ldp	x28, x27, [sp, #64]
	ldp	d9, d8, [sp, #48]
	ldp	d11, d10, [sp, #32]
	ldp	d13, d12, [sp, #16]
	ldp	d15, d14, [sp], #160
	ret
LBB6_54:
Lloh299:
	adrp	x8, _.const.picklebuf.ba289d81f05c7020f3477c15734804df65abe209.14@GOTPAGE
Lloh300:
	ldr	x8, [x8, _.const.picklebuf.ba289d81f05c7020f3477c15734804df65abe209.14@GOTPAGEOFF]
	b	LBB6_56
LBB6_55:
Lloh301:
	adrp	x8, _.const.picklebuf.ba289d81f05c7020f3477c15734804df65abe209.9@GOTPAGE
Lloh302:
	ldr	x8, [x8, _.const.picklebuf.ba289d81f05c7020f3477c15734804df65abe209.9@GOTPAGEOFF]
LBB6_56:
	ldr	x9, [sp, #640]
	str	x8, [x9]
	mov	w0, #1
	b	LBB6_53
	.loh AdrpLdrGot	Lloh295, Lloh296
	.loh AdrpLdrGot	Lloh293, Lloh294
	.loh AdrpLdrGot	Lloh297, Lloh298
	.loh AdrpLdrGot	Lloh299, Lloh300
	.loh AdrpLdrGot	Lloh301, Lloh302
	.cfi_endproc

	.globl	_NRT_incref
	.weak_def_can_be_hidden	_NRT_incref
	.p2align	2
_NRT_incref:
	cbz	x0, LBB7_2
	mov	w8, #1
	ldadd	x8, x8, [x0]
LBB7_2:
	ret

	.section	__TEXT,__const
	.p2align	4, 0x0
_printf_format:
	.asciz	"num_threads: %d\n"

	.p2align	4, 0x0
_.const.pickledata.9d8bd6d541b3e336fd7917994940781bc68a3a8a:
	.ascii	"\200\004\225e\000\000\000\000\000\000\000\214\bbuiltins\224\214\fRuntimeError\224\223\224\214@Invalid number of threads. This likely indicates a bug in Numba.\224\205\224N\207\224."

	.p2align	4, 0x0
_.const.pickledata.9d8bd6d541b3e336fd7917994940781bc68a3a8a.sha1:
	.ascii	"\235\213\326\325A\263\3436\375y\027\231I@x\033\306\212:\212"

	.section	__DATA,__const
	.p2align	4, 0x0
_.const.picklebuf.9d8bd6d541b3e336fd7917994940781bc68a3a8a:
	.quad	_.const.pickledata.9d8bd6d541b3e336fd7917994940781bc68a3a8a
	.long	112
	.space	4
	.quad	_.const.pickledata.9d8bd6d541b3e336fd7917994940781bc68a3a8a.sha1
	.quad	0
	.long	0
	.space	4

	.section	__TEXT,__const
	.p2align	4, 0x0
_printf_format.1:
	.asciz	"num_threads: %d\n"

	.p2align	4, 0x0
"_.const.make_longwave_primary_b.<locals>._longwave_primary_b_packed":
	.asciz	"make_longwave_primary_b.<locals>._longwave_primary_b_packed"

	.comm	__ZN08NumbaEnv18longwave_primary_b23make_longwave_primary_b12_3clocals_3e26_longwave_primary_b_packedB3v21B90c8tJTC_2fWQAliW1xhDEoY6EEMEUOEMISPGsAQMVj4QniQ4IXKQEMXwoMGLoQDDVsQR1NHAS2hQ9XgStYwm4ogLE0AE5ArrayIfLi3E1C7mutable7alignedE5ArrayIfLi3E1C7mutable7alignedE5ArrayIfLi3E1C7mutable7alignedE5ArrayIbLi3E1C7mutable7alignedE5ArrayIbLi3E1C7mutable7alignedE5ArrayIfLi1E1C7mutable7alignedE5ArrayIfLi1E1C7mutable7alignedE5ArrayIfLi1E1C7mutable7alignedE5ArrayIbLi1E1C7mutable7alignedE5ArrayIfLi1E1A7mutable7alignedE5ArrayIfLi1E1A7mutable7alignedEff5ArrayIfLi2E1C7mutable7alignedEfx,8,3
	.p2align	4, 0x0
"_.const.missing Environment: _ZN08NumbaEnv18longwave_primary_b23make_longwave_primary_b12_3clocals_3e26_longwave_primary_b_packedB3v21B90c8tJTC_2fWQAliW1xhDEoY6EEMEUOEMISPGsAQMVj4QniQ4IXKQEMXwoMGLoQDDVsQR1NHAS2hQ9XgStYwm4ogLE0AE5ArrayIfLi3E1C7mutable7alignedE5ArrayIfLi3E1C7mutable7alignedE5ArrayIfLi3E1C7mutable7alignedE5ArrayIbLi3E1C7mutable7alignedE5ArrayIbLi3E1C7mutable7alignedE5ArrayIfLi1E1C7mutable7alignedE5ArrayIfLi1E1C7mutable7alignedE5ArrayIfLi1E1C7mutable7alignedE5ArrayIbLi1E1C7mutable7alignedE5ArrayIfLi1E1A7mutable7alignedE5ArrayIfLi1E1A7mutable7alignedEff5ArrayIfLi2E1C7mutable7alignedEfx":
	.asciz	"missing Environment: _ZN08NumbaEnv18longwave_primary_b23make_longwave_primary_b12_3clocals_3e26_longwave_primary_b_packedB3v21B90c8tJTC_2fWQAliW1xhDEoY6EEMEUOEMISPGsAQMVj4QniQ4IXKQEMXwoMGLoQDDVsQR1NHAS2hQ9XgStYwm4ogLE0AE5ArrayIfLi3E1C7mutable7alignedE5ArrayIfLi3E1C7mutable7alignedE5ArrayIfLi3E1C7mutable7alignedE5ArrayIbLi3E1C7mutable7alignedE5ArrayIbLi3E1C7mutable7alignedE5ArrayIfLi1E1C7mutable7alignedE5ArrayIfLi1E1C7mutable7alignedE5ArrayIfLi1E1C7mutable7alignedE5ArrayIbLi1E1C7mutable7alignedE5ArrayIfLi1E1A7mutable7alignedE5ArrayIfLi1E1A7mutable7alignedEff5ArrayIfLi2E1C7mutable7alignedEfx"

	.p2align	4, 0x0
"_.const.can't unbox array from PyObject into native value.  The object maybe of a different type":
	.asciz	"can't unbox array from PyObject into native value.  The object maybe of a different type"

	.p2align	4, 0x0
"_.const.`env.consts` is NULL in `read_const`":
	.asciz	"`env.consts` is NULL in `read_const`"

	.p2align	4, 0x0
_.const.pickledata.dfbcfdd39fcb26f4d0c680954487b8c0b53bb8a3:
	.ascii	"\200\004\225\025\000\000\000\000\000\000\000\214\005numpy\224\214\007ndarray\224\223\224."

	.p2align	4, 0x0
_.const.pickledata.dfbcfdd39fcb26f4d0c680954487b8c0b53bb8a3.sha1:
	.ascii	"\337\274\375\323\237\313&\364\320\306\200\225D\207\270\300\265;\270\243"

	.p2align	4, 0x0
"_.const.Error creating Python tuple from runtime exception arguments":
	.asciz	"Error creating Python tuple from runtime exception arguments"

	.p2align	4, 0x0
"_.const.Error creating Python tuple from runtime exception arguments.1":
	.asciz	"Error creating Python tuple from runtime exception arguments"

	.p2align	4, 0x0
"_.const.<numba.core.cpu.CPUContext>":
	.asciz	"<numba.core.cpu.CPUContext>"

	.comm	__ZN08NumbaEnv5numba2np8arrayobj11ol_np_empty12_3clocals_3e4implB3v14B42c8tJTIeFIjxB2IKSgI4CrvQClcaMQ5hEEUSJJgA_3dE8UniTupleIxLi2EE18class_28float32_29,8,3
	.p2align	4, 0x0
_.const.pickledata.331b8563bdb9dac81b38422273052c486fc1706b:
	.ascii	"\200\004\225B\000\000\000\000\000\000\000\214\bbuiltins\224\214\nValueError\224\223\224\214\037negative dimensions not allowed\224\205\224N\207\224."

	.p2align	4, 0x0
_.const.pickledata.331b8563bdb9dac81b38422273052c486fc1706b.sha1:
	.ascii	"3\033\205c\275\271\332\310\0338B\"s\005,Ho\301pk"

	.section	__DATA,__const
	.p2align	4, 0x0
_.const.picklebuf.331b8563bdb9dac81b38422273052c486fc1706b:
	.quad	_.const.pickledata.331b8563bdb9dac81b38422273052c486fc1706b
	.long	77
	.space	4
	.quad	_.const.pickledata.331b8563bdb9dac81b38422273052c486fc1706b.sha1
	.quad	0
	.long	0
	.space	4

	.section	__TEXT,__const
	.p2align	4, 0x0
_.const.pickledata.58e14eccb507b1e0206981740223e685cb8c3c57:
	.ascii	"\200\004\225~\000\000\000\000\000\000\000\214\bbuiltins\224\214\nValueError\224\223\224\214[array is too big; `arr.size * arr.dtype.itemsize` is larger than the maximum possible size.\224\205\224N\207\224."

	.p2align	4, 0x0
_.const.pickledata.58e14eccb507b1e0206981740223e685cb8c3c57.sha1:
	.ascii	"X\341N\314\265\007\261\340 i\201t\002#\346\205\313\214<W"

	.section	__DATA,__const
	.p2align	4, 0x0
_.const.picklebuf.58e14eccb507b1e0206981740223e685cb8c3c57:
	.quad	_.const.pickledata.58e14eccb507b1e0206981740223e685cb8c3c57
	.long	137
	.space	4
	.quad	_.const.pickledata.58e14eccb507b1e0206981740223e685cb8c3c57.sha1
	.quad	0
	.long	0
	.space	4

	.comm	__ZN08NumbaEnv5numba2np8arrayobj15_call_allocatorB2v4B42c8tJTC_2fWQA93W1AaAIYBPIqRBFCjDSZRVAJmaQIAEN29typeref_5b_3cclass_20_27numba4core5types8npytypes14Array_27_3e_5dExj,8,3
	.section	__TEXT,__const
	.p2align	4, 0x0
_.const.pickledata.ba289d81f05c7020f3477c15734804df65abe209:
	.ascii	"\200\004\225K\000\000\000\000\000\000\000\214\bbuiltins\224\214\013MemoryError\224\223\224\214'Allocation failed (probably too large).\224\205\224N\207\224."

	.p2align	4, 0x0
_.const.pickledata.ba289d81f05c7020f3477c15734804df65abe209.sha1:
	.ascii	"\272(\235\201\360\\p \363G|\025sH\004\337e\253\342\t"

	.section	__DATA,__const
	.p2align	4, 0x0
_.const.picklebuf.ba289d81f05c7020f3477c15734804df65abe209:
	.quad	_.const.pickledata.ba289d81f05c7020f3477c15734804df65abe209
	.long	86
	.space	4
	.quad	_.const.pickledata.ba289d81f05c7020f3477c15734804df65abe209.sha1
	.quad	0
	.long	0
	.space	4

	.comm	__ZN08NumbaEnv13_3cdynamic_3e33__numba_parfor_gufunc_0x10c3c2c00B3v22B106c8tJTC_2fWQAliW1xhDEoY6EEMEUOEMISPGsAQMVj4QniQ4IXKQEMXwoMGLoQDDVsQR1NHAS2hQ9XgStYwaUTI24JtBVoOCV2YU4ogSjUBE5ArrayIyLi1E1C7mutable7alignedE5ArrayIfLi2E1C7mutable7alignedE,8,3
	.section	__TEXT,__const
	.p2align	4, 0x0
"_.const.Error creating Python tuple from runtime exception arguments.11":
	.asciz	"Error creating Python tuple from runtime exception arguments"

	.p2align	4, 0x0
_.const.pickledata.ba289d81f05c7020f3477c15734804df65abe209.15:
	.ascii	"\200\004\225K\000\000\000\000\000\000\000\214\bbuiltins\224\214\013MemoryError\224\223\224\214'Allocation failed (probably too large).\224\205\224N\207\224."

	.p2align	4, 0x0
_.const.pickledata.ba289d81f05c7020f3477c15734804df65abe209.sha1.16:
	.ascii	"\272(\235\201\360\\p \363G|\025sH\004\337e\253\342\t"

	.section	__DATA,__const
	.p2align	4, 0x0
_.const.picklebuf.ba289d81f05c7020f3477c15734804df65abe209.14:
	.quad	_.const.pickledata.ba289d81f05c7020f3477c15734804df65abe209.15
	.long	86
	.space	4
	.quad	_.const.pickledata.ba289d81f05c7020f3477c15734804df65abe209.sha1.16
	.quad	0
	.long	0
	.space	4

	.section	__TEXT,__const
	.p2align	4, 0x0
_.const.pickledata.ba289d81f05c7020f3477c15734804df65abe209.10:
	.ascii	"\200\004\225K\000\000\000\000\000\000\000\214\bbuiltins\224\214\013MemoryError\224\223\224\214'Allocation failed (probably too large).\224\205\224N\207\224."

	.p2align	4, 0x0
_.const.pickledata.ba289d81f05c7020f3477c15734804df65abe209.sha1.11:
	.ascii	"\272(\235\201\360\\p \363G|\025sH\004\337e\253\342\t"

	.section	__DATA,__const
	.p2align	4, 0x0
_.const.picklebuf.ba289d81f05c7020f3477c15734804df65abe209.9:
	.quad	_.const.pickledata.ba289d81f05c7020f3477c15734804df65abe209.10
	.long	86
	.space	4
	.quad	_.const.pickledata.ba289d81f05c7020f3477c15734804df65abe209.sha1.11
	.quad	0
	.long	0
	.space	4

	.comm	__ZN08NumbaEnv13_3cdynamic_3e33__numba_parfor_gufunc_0x10c777680B3v23B104c8tJTC_2fWQAliW1xhDEoY6EEMEUOEMISPGsAQMVj4QniQ4IXKQEMXwoMGLoQDDVsQR1NHAS2hQ9XgStYwaUTI24JtBVpeBJHUBAA_3dE5ArrayIyLi1E1C7mutable7alignedE5ArrayIfLi1E1C7mutable7alignedE5ArrayIfLi2E1C7mutable7alignedE5ArrayIfLi2E1C7mutable7alignedExxf5ArrayIfLi3E1C7mutable7alignedE5ArrayIbLi3E1C7mutable7alignedE5ArrayIfLi1E1C7mutable7alignedE5ArrayIfLi1E1A7mutable7alignedE5ArrayIfLi1E1A7mutable7alignedE5ArrayIbLi1E1C7mutable7alignedE5ArrayIfLi1E1C7mutable7alignedE5ArrayIbLi3E1C7mutable7alignedEff5ArrayIfLi3E1C7mutable7alignedE5ArrayIfLi3E1C7mutable7alignedE,8,3
	.comm	__ZN08NumbaEnv5numba2np8arrayobj11ol_np_empty12_3clocals_3e4implB3v17B54c8tJTIeFIjxB2IKSgI4CrvQCk0Z4yRYcWsBAw4hWqFpgsIBZmgA_3dEx18class_28float32_29,8,3
	.comm	__ZN08NumbaEnv5numba2np8arrayobj11ol_np_empty12_3clocals_3e4implB3v19B54c8tJTIeFIjxB2IKSgI4CrvQCk0Z4yRYcWsBAw4hWqFpgsIBZmgA_3dE8UniTupleIxLi2EE18class_28float32_29,8,3
	.comm	__ZN08NumbaEnv5numba2np8arrayobj15_call_allocatorB3v18B42c8tJTC_2fWQA93W1AaAIYBPIqRBFCjDSZRVAJmaQIAEN29typeref_5b_3cclass_20_27numba4core5types8npytypes14Array_27_3e_5dExj,8,3
	.comm	__ZN08NumbaEnv5numba2np8arrayobj18_ol_array_allocate12_3clocals_3e4implB2v5B42c8tJTIeFIjxB2IKSgI4CrvQClcaMQ5hEEUSJJgA_3dEN29typeref_5b_3cclass_20_27numba4core5types8npytypes14Array_27_3e_5dExj,8,3
	.comm	__ZN08NumbaEnv5numba7cpython8builtins6ol_min12_3clocals_3e4implB3v20B54c8tJTIeFIjxB2IKSgI4CrvQCk0Z4yRYcWsBAw4hWqFpgsIBZmgA_3dE15StarArgUniTupleIxLi2EE,8,3
.subsections_via_symbols
