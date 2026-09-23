	.build_version macos, 26, 0
	.section	__TEXT,__text,regular,pure_instructions
	.globl	__ZN18longwave_primary_b23make_longwave_primary_b12_3clocals_3e26_longwave_primary_b_packedB2v9B38c8tJTIeFIjxB2IKSgI4CrvQClQZ6FczSBAA_3dE5ArrayIfLi3E1C7mutable7alignedE5ArrayIfLi3E1C7mutable7alignedE5ArrayIfLi3E1C7mutable7alignedE5ArrayIbLi3E1C7mutable7alignedE5ArrayIbLi3E1C7mutable7alignedE5ArrayIfLi1E1C7mutable7alignedE5ArrayIfLi1E1C7mutable7alignedE5ArrayIfLi1E1C7mutable7alignedE5ArrayIbLi1E1C7mutable7alignedE5ArrayIfLi1E1A7mutable7alignedE5ArrayIfLi1E1A7mutable7alignedEff5ArrayIfLi2E1C7mutable7alignedEfx
	.p2align	2
__ZN18longwave_primary_b23make_longwave_primary_b12_3clocals_3e26_longwave_primary_b_packedB2v9B38c8tJTIeFIjxB2IKSgI4CrvQClQZ6FczSBAA_3dE5ArrayIfLi3E1C7mutable7alignedE5ArrayIfLi3E1C7mutable7alignedE5ArrayIfLi3E1C7mutable7alignedE5ArrayIbLi3E1C7mutable7alignedE5ArrayIbLi3E1C7mutable7alignedE5ArrayIfLi1E1C7mutable7alignedE5ArrayIfLi1E1C7mutable7alignedE5ArrayIfLi1E1C7mutable7alignedE5ArrayIbLi1E1C7mutable7alignedE5ArrayIfLi1E1A7mutable7alignedE5ArrayIfLi1E1A7mutable7alignedEff5ArrayIfLi2E1C7mutable7alignedEfx:
	.cfi_startproc
	stp	d11, d10, [sp, #-128]!
	stp	d9, d8, [sp, #16]
	stp	x28, x27, [sp, #32]
	stp	x26, x25, [sp, #48]
	stp	x24, x23, [sp, #64]
	stp	x22, x21, [sp, #80]
	stp	x20, x19, [sp, #96]
	stp	x29, x30, [sp, #112]
	sub	sp, sp, #640
	.cfi_def_cfa_offset 768
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
	stp	q1, q2, [sp, #304]
	str	q0, [sp, #288]
	str	x1, [sp, #8]
	str	x0, [sp, #104]
	ldr	x8, [sp, #1568]
	stp	x6, x8, [sp, #344]
	ldr	x9, [sp, #1496]
	ldr	x27, [sp, #1440]
	ldr	x24, [sp, #1384]
	ldr	x23, [sp, #1328]
	ldr	x22, [sp, #1272]
	ldr	x8, [sp, #1216]
	stp	x8, x9, [sp, #120]
	ldr	x25, [sp, #1160]
	ldr	x28, [sp, #1072]
	ldr	x20, [sp, #984]
	ldr	x21, [sp, #896]
	ldr	x26, [sp, #808]
Lloh0:
	adrp	x19, _NRT_incref@GOTPAGE
Lloh1:
	ldr	x19, [x19, _NRT_incref@GOTPAGEOFF]
	str	x2, [sp, #112]
	mov	x0, x2
	blr	x19
	str	x26, [sp, #80]
	mov	x0, x26
	mov	x26, x27
	blr	x19
	str	x21, [sp, #88]
	mov	x0, x21
	ldr	x21, [sp, #128]
	blr	x19
	str	x20, [sp, #96]
	mov	x0, x20
	ldr	x20, [sp, #352]
	ldr	x27, [sp, #120]
	blr	x19
	mov	x0, x28
	blr	x19
	mov	x0, x25
	blr	x19
	mov	x0, x27
	blr	x19
	mov	x0, x22
	blr	x19
	mov	x0, x23
	blr	x19
	mov	x0, x24
	blr	x19
	mov	x0, x26
	blr	x19
	mov	x0, x21
	blr	x19
	tbnz	x20, #63, LBB0_82
	lsl	x8, x20, #3
	sub	x19, x8, x20
	mov	w8, #7
	smulh	x8, x20, x8
	cmp	x8, x19, asr #63
Lloh2:
	adrp	x9, _.const.picklebuf.58e14eccb507b1e0206981740223e685cb8c3c57@GOTPAGE
Lloh3:
	ldr	x9, [x9, _.const.picklebuf.58e14eccb507b1e0206981740223e685cb8c3c57@GOTPAGEOFF]
	b.ne	LBB0_83
	mov	x8, #-2305843009213693952
	add	x8, x19, x8
	lsr	x8, x8, #62
	cmp	x8, #3
	b.lo	LBB0_83
	str	x25, [sp, #72]
	lsl	x25, x19, #2
Lloh4:
	adrp	x8, _NRT_MemInfo_alloc_aligned@GOTPAGE
Lloh5:
	ldr	x8, [x8, _NRT_MemInfo_alloc_aligned@GOTPAGEOFF]
	mov	x0, x25
	mov	w1, #32
	blr	x8
Lloh6:
	adrp	x9, _.const.picklebuf.ba289d81f05c7020f3477c15734804df65abe209@GOTPAGE
Lloh7:
	ldr	x9, [x9, _.const.picklebuf.ba289d81f05c7020f3477c15734804df65abe209@GOTPAGEOFF]
	cbz	x0, LBB0_83
	stp	x19, x23, [sp, #24]
	stp	x26, x24, [sp, #40]
	stp	x28, x22, [sp, #56]
	str	x0, [sp, #16]
	ldr	x0, [x0, #24]
Lloh8:
	adrp	x8, _bzero@GOTPAGE
Lloh9:
	ldr	x8, [x8, _bzero@GOTPAGEOFF]
	str	x0, [sp, #152]
	mov	x1, x25
	blr	x8
	add	x8, x20, #7
	lsr	x8, x8, #3
	str	x8, [sp, #280]
	cbz	x8, LBB0_79
	mov	x27, #0
	mov	x25, #0
	ldr	x8, [sp, #1544]
	ldr	x15, [sp, #1528]
	ldr	x19, [sp, #1488]
	ldr	x23, [sp, #1472]
	ldr	x21, [sp, #1432]
	ldr	x22, [sp, #1416]
	ldr	x26, [sp, #1200]
	ldr	x9, [sp, #1192]
	str	x9, [sp, #632]
	ldr	x16, [sp, #1128]
	ldr	x9, [sp, #1120]
	ldr	x17, [sp, #1104]
	ldr	x0, [sp, #1040]
	ldr	x10, [sp, #1032]
	ldr	x1, [sp, #952]
	ldr	x11, [sp, #944]
	ldr	x2, [sp, #776]
	ldr	x12, [sp, #768]
	mul	x12, x2, x12
	lsl	x12, x12, #2
	str	x12, [sp, #464]
	ldr	x3, [sp, #864]
	ldr	x12, [sp, #856]
	sub	x13, x26, #1
	mul	x14, x2, x13
	mul	x12, x3, x12
	lsl	x12, x12, #2
	str	x12, [sp, #456]
	mul	x12, x3, x13
	mul	x11, x1, x11
	lsl	x11, x11, #2
	str	x11, [sp, #448]
	mul	x11, x1, x13
	lsl	x8, x8, #2
	str	x8, [sp, #240]
	neg	x8, x8
	str	x8, [sp, #136]
	mul	x8, x0, x10
	str	x8, [sp, #376]
	mul	x8, x16, x9
	str	x8, [sp, #368]
	ldr	x10, [sp, #1016]
	ldr	x4, [sp, #928]
	ldr	x5, [sp, #840]
	ldr	x8, [sp, #344]
	add	x9, x8, x14, lsl #2
	str	x9, [sp, #216]
	add	x9, x5, x12, lsl #2
	str	x9, [sp, #208]
	add	x9, x4, x11, lsl #2
	str	x9, [sp, #200]
	str	x0, [sp, #568]
	madd	x11, x0, x13, x10
	str	x16, [sp, #576]
	madd	x9, x16, x13, x17
	stp	x9, x11, [sp, #168]
	stp	x3, x2, [sp, #248]
	lsl	x9, x2, #2
	str	x9, [sp, #624]
	fmov	s8, #1.00000000
	movi.2d	v9, #0000000000000000
	movi.4h	v10, #1
	fmov	s11, #0.50000000
	lsl	x9, x3, #2
	str	x9, [sp, #616]
	str	x1, [sp, #264]
	lsl	x9, x1, #2
	str	x9, [sp, #608]
	add	x9, x15, #32
	stp	x9, x10, [sp, #496]
	ldr	x9, [sp, #152]
	add	x11, x9, #12
	str	x11, [sp, #160]
	str	x9, [sp, #480]
	str	x15, [sp, #144]
	stp	x10, x17, [sp, #184]
	str	x17, [sp, #512]
	ldr	x9, [sp, #1360]
	str	x9, [sp, #560]
	stp	x5, x4, [sp, #224]
	str	x4, [sp, #544]
	ldr	x9, [sp, #1304]
	str	x9, [sp, #600]
	str	x5, [sp, #536]
	str	x8, [sp, #528]
	mov	x10, x20
	ldr	x8, [sp, #1248]
	str	x8, [sp, #592]
	str	x22, [sp, #272]
	b	LBB0_8
LBB0_6:
Lloh10:
	adrp	x8, _NRT_decref@GOTPAGE
Lloh11:
	ldr	x8, [x8, _NRT_decref@GOTPAGEOFF]
	blr	x8
	ldr	x0, [sp, #384]
LBB0_7:
	add	x25, x25, #1
Lloh12:
	adrp	x8, _NRT_decref@GOTPAGE
Lloh13:
	ldr	x8, [x8, _NRT_decref@GOTPAGEOFF]
	blr	x8
	ldp	x8, x10, [sp, #456]
	ldr	x9, [sp, #528]
	add	x9, x9, x10
	str	x9, [sp, #528]
	ldr	x9, [sp, #536]
	add	x9, x9, x8
	str	x9, [sp, #536]
	ldr	x8, [sp, #448]
	ldr	x9, [sp, #544]
	add	x9, x9, x8
	str	x9, [sp, #544]
	ldp	x8, x10, [sp, #368]
	ldr	x9, [sp, #504]
	add	x9, x9, x10
	str	x9, [sp, #504]
	ldr	x9, [sp, #512]
	add	x9, x9, x8
	str	x9, [sp, #512]
	ldr	x8, [sp, #240]
	ldr	x9, [sp, #496]
	add	x9, x9, x8
	str	x9, [sp, #496]
	ldr	x15, [sp, #520]
	add	x15, x15, x8
	ldr	x8, [sp, #480]
	add	x8, x8, #224
	str	x8, [sp, #480]
	add	x27, x27, #8
	ldr	x8, [sp, #280]
	cmp	x25, x8
	ldr	x20, [sp, #352]
	ldr	x10, [sp, #440]
	b.eq	LBB0_79
LBB0_8:
	str	x15, [sp, #520]
	mov	x22, x21
	mov	x21, x23
	mov	x23, x19
	mov	x9, x25
	mov	x25, x27
	mov	x8, x10
	subs	x10, x10, #8
	str	x10, [sp, #440]
	mov	w10, #8
	csel	x24, x8, x10, lt
	mov	x19, x9
	sub	x8, x20, x9, lsl #3
	cmp	x8, #8
	str	x8, [sp, #584]
	csel	x28, x8, x10, lt
	mov	w0, #320
	mov	w1, #32
Lloh14:
	adrp	x27, _NRT_MemInfo_alloc_aligned@GOTPAGE
Lloh15:
	ldr	x27, [x27, _NRT_MemInfo_alloc_aligned@GOTPAGEOFF]
	blr	x27
	cbz	x0, LBB0_80
	str	x0, [sp, #384]
	ldr	x20, [x0, #24]
	movi.2d	v0, #0000000000000000
	stp	q0, q0, [x20, #288]
	stp	q0, q0, [x20, #256]
	stp	q0, q0, [x20, #224]
	stp	q0, q0, [x20, #192]
	stp	q0, q0, [x20, #160]
	stp	q0, q0, [x20, #128]
	stp	q0, q0, [x20, #96]
	stp	q0, q0, [x20, #64]
	stp	q0, q0, [x20, #32]
	stp	q0, q0, [x20]
	mov	w0, #32
	mov	w1, #32
	blr	x27
	cbz	x0, LBB0_81
	and	x8, x24, #0xfffffffffffffffc
	neg	x8, x8
	str	x8, [sp, #488]
	lsl	x10, x28, #2
	ldr	x8, [sp, #464]
	mul	x8, x8, x19
	ldr	x9, [sp, #344]
	add	x9, x9, x8
	str	x9, [sp, #432]
	ldp	x11, x9, [sp, #216]
	add	x8, x11, x8
	add	x8, x8, x10
	str	x8, [sp, #408]
	ldr	x8, [sp, #456]
	mul	x8, x8, x19
	add	x9, x9, x8
	str	x9, [sp, #424]
	ldr	x9, [sp, #208]
	add	x8, x9, x8
	add	x8, x8, x10
	str	x8, [sp, #400]
	ldr	x8, [sp, #448]
	mul	x8, x8, x19
	ldr	x9, [sp, #232]
	add	x9, x9, x8
	str	x9, [sp, #416]
	ldr	x9, [sp, #200]
	add	x8, x9, x8
	str	x10, [sp, #472]
	add	x4, x8, x10
	ldr	x8, [sp, #264]
	ubfx	x5, x8, #61, #1
	ldr	x8, [x0, #24]
	ldp	x10, x9, [sp, #248]
	ubfx	x6, x10, #61, #1
	ubfx	x9, x9, #61, #1
	str	x9, [sp, #392]
	cmp	x26, #1
	ldp	q29, q28, [sp, #288]
	mov	x27, x25
	mov	x25, x19
	mov	x19, x23
	mov	x23, x21
	mov	x21, x22
	ldr	x22, [sp, #272]
	fmov.4s	v30, #1.00000000
	b.lt	LBB0_30
	mov	x2, #0
	and	x3, x24, #0xfffffffffffffff8
	ldr	x9, [sp, #376]
	mul	x9, x9, x25
	ldp	x11, x10, [sp, #176]
	add	x10, x10, x9
	str	x10, [sp, #552]
	add	x11, x11, x28
	add	x9, x11, x9
	ldr	x11, [sp, #368]
	mul	x11, x11, x25
	ldr	x12, [sp, #192]
	add	x10, x12, x11
	str	x10, [sp, #360]
	ldr	x13, [sp, #168]
	add	x13, x13, x28
	add	x10, x13, x11
	ldr	x14, [sp, #472]
	add	x13, x20, x14
	add	x11, x20, #224
	add	x14, x11, x14
	add	x13, x13, #256
	ldp	x30, x7, [sp, #408]
	cmp	x20, x30
	ldp	x1, x17, [sp, #424]
	ccmp	x17, x13, #2, lo
	ldr	x11, [sp, #392]
	csinc	w15, w11, wzr, hs
	mov	x12, x25
	mov	x25, x27
	mov	x27, x4
	ldr	x4, [sp, #400]
	cmp	x20, x4
	ccmp	x1, x13, #2, lo
	csinc	w16, w6, wzr, hs
	orr	w15, w15, w16
	cmp	x20, x27
	ccmp	x7, x13, #2, lo
	csinc	w16, w5, wzr, hs
	orr	w15, w15, w16
	cmp	x20, x9
	ldr	x9, [sp, #552]
	ccmp	x9, x13, #2, lo
	ldr	x9, [sp, #568]
	ccmp	x9, #0, #8, hs
	csinc	w9, w15, wzr, pl
	cmp	x20, x10
	ldr	x10, [sp, #360]
	ccmp	x10, x13, #2, lo
	ldr	x10, [sp, #576]
	ccmp	x10, #0, #8, hs
	cset	w10, mi
	orr	w9, w9, w10
	str	w9, [sp, #552]
	cmp	x20, x30
	ccmp	x17, x14, #2, lo
	csinc	w9, w11, wzr, hs
	cmp	x20, x4
	mov	x4, x27
	mov	x27, x25
	mov	x25, x12
	ccmp	x1, x14, #2, lo
	csinc	w10, w6, wzr, hs
	orr	w9, w9, w10
	cmp	x20, x4
	ccmp	x7, x14, #2, lo
	csinc	w10, w5, wzr, hs
	orr	w30, w9, w10
	ldp	x9, x1, [sp, #504]
	ldr	x10, [sp, #544]
	ldr	x11, [sp, #536]
	ldr	x12, [sp, #528]
	b	LBB0_13
LBB0_12:
	add	x2, x2, #1
	ldr	x13, [sp, #624]
	add	x12, x12, x13
	ldr	x13, [sp, #616]
	add	x11, x11, x13
	ldr	x13, [sp, #608]
	add	x10, x10, x13
	ldr	x13, [sp, #568]
	add	x9, x9, x13
	ldr	x13, [sp, #576]
	add	x1, x1, x13
	cmp	x26, x2
	b.eq	LBB0_30
LBB0_13:
	mul	x13, x2, x21
	ldr	s0, [x22, x13]
	mul	x13, x2, x19
	ldr	s1, [x23, x13]
	ldr	x13, [sp, #632]
	ldr	s3, [x13, x2, lsl #2]
	ldr	x13, [sp, #592]
	ldr	s2, [x13, x2, lsl #2]
	ldr	x13, [sp, #600]
	ldr	s4, [x13, x2, lsl #2]
	ldr	x13, [sp, #560]
	ldrb	w13, [x13, x2]
	cbz	w13, LBB0_17
	ldr	x13, [sp, #584]
	cmp	x13, #1
	b.lt	LBB0_12
	cmp	x28, #8
	cset	w13, lo
	fmul	s6, s28, s3
	fmul	s5, s6, s4
	fmul	s6, s6, s2
	ldr	w14, [sp, #552]
	orr	w13, w13, w14
	tbz	w13, #0, LBB0_20
	mov	x14, #0
	b	LBB0_23
LBB0_17:
	ldr	x13, [sp, #584]
	cmp	x13, #1
	b.lt	LBB0_12
	cmp	x28, #4
	cset	w13, lo
	fmul	s5, s28, s3
	fmul	s3, s5, s4
	fmul	s2, s5, s2
	orr	w13, w13, w30
	tbz	w13, #0, LBB0_25
	mov	x13, #0
	b	LBB0_28
LBB0_20:
	mov	x13, #0
	add	x14, x20, #224
	ldp	q7, q16, [x14]
	mov	w14, #256
	add	x15, x20, #160
	mov	x16, x15
LBB0_21:
	ldr	d17, [x9, x13]
	cmtst.8b	v19, v17, v17
	ldr	d17, [x1, x13]
	cmtst.8b	v17, v17, v17
	add	x17, x12, x14
	ldp	q18, q20, [x17, #-256]
	fcmeq.4s	v21, v20, v30
	fcmeq.4s	v22, v18, v30
	uzp1.8h	v21, v22, v21
	add	x17, x11, x14
	ldp	q22, q23, [x17, #-256]
	fcmeq.4s	v24, v23, v30
	fcmeq.4s	v25, v22, v30
	uzp1.8h	v24, v25, v24
	and.16b	v21, v21, v24
	xtn.8b	v24, v21
	fcmeq.4s	v21, v23, #0.0
	add	x17, x10, x14
	fcmeq.4s	v22, v22, #0.0
	uzp1.8h	v21, v22, v21
	ldp	q22, q23, [x17, #-256]
	fcmeq.4s	v25, v23, #0.0
	fcmeq.4s	v26, v22, #0.0
	uzp1.8h	v25, v26, v25
	orr.16b	v21, v21, v25
	xtn.8b	v25, v21
	fsub.4s	v20, v30, v20
	fsub.4s	v18, v30, v18
	fmul.4s	v18, v18, v22
	fmul.4s	v20, v20, v23
	fcmeq.4s	v20, v20, v30
	fcmeq.4s	v18, v18, v30
	uzp1.8h	v18, v18, v20
	xtn.8b	v21, v18
	ldp	q18, q20, [x15, #-160]
	zip2.8b	v22, v24, v0
	and.8b	v22, v22, v10
	ushll.4s	v22, v22, #0
	ucvtf.4s	v22, v22
	zip1.8b	v23, v24, v0
	and.8b	v23, v23, v10
	ushll.4s	v23, v23, #0
	ucvtf.4s	v23, v23
	fmul.4s	v24, v23, v0[0]
	fmul.4s	v26, v22, v0[0]
	fadd.4s	v20, v20, v26
	fadd.4s	v18, v18, v24
	stp	q18, q20, [x15, #-160]
	ldp	q18, q20, [x15]
	fmul.4s	v23, v23, v1[0]
	fmul.4s	v22, v22, v1[0]
	fadd.4s	v20, v22, v20
	fadd.4s	v18, v23, v18
	stp	q18, q20, [x15]
	zip2.8b	v18, v25, v0
	and.8b	v18, v18, v10
	ushll.4s	v18, v18, #0
	ucvtf.4s	v18, v18
	zip1.8b	v20, v25, v0
	and.8b	v20, v20, v10
	ushll.4s	v20, v20, #0
	ucvtf.4s	v20, v20
	fmul.4s	v22, v20, v5[0]
	fmul.4s	v23, v20, v6[0]
	fmul.4s	v24, v18, v6[0]
	ldr	q25, [x16, #32]!
	ldr	q20, [x15, #48]
	fadd.4s	v22, v22, v25
	str	q22, [x16]
	ldp	q22, q25, [x15, #-128]
	fadd.4s	v24, v24, v25
	fadd.4s	v22, v23, v22
	stp	q22, q24, [x15, #-128]
	zip1.8b	v22, v19, v0
	and.8b	v22, v22, v10
	ushll.4s	v22, v22, #0
	ucvtf.4s	v22, v22
	zip2.8b	v19, v19, v0
	and.8b	v19, v19, v10
	ushll.4s	v19, v19, #0
	ucvtf.4s	v19, v19
	fmul.4s	v19, v19, v29[0]
	fmul.4s	v22, v22, v29[0]
	fmul.4s	v22, v22, v3[0]
	fmul.4s	v23, v19, v3[0]
	fmul.4s	v24, v23, v4[0]
	zip2.8b	v19, v21, v0
	and.8b	v19, v19, v10
	ushll.4s	v19, v19, #0
	ucvtf.4s	v19, v19
	zip1.8b	v21, v21, v0
	and.8b	v21, v21, v10
	ushll.4s	v21, v21, #0
	ucvtf.4s	v21, v21
	fmul.4s	v24, v24, v19
	zip2.8b	v25, v17, v0
	and.8b	v25, v25, v10
	ushll.4s	v25, v25, #0
	ucvtf.4s	v25, v25
	zip1.8b	v17, v17, v0
	and.8b	v17, v17, v10
	ushll.4s	v17, v17, #0
	ucvtf.4s	v17, v17
	fmul.4s	v17, v17, v28[0]
	fmul.4s	v25, v25, v28[0]
	fmul.4s	v25, v25, v3[0]
	fmul.4s	v17, v17, v3[0]
	fmul.4s	v26, v25, v4[0]
	fmul.4s	v26, v26, v19
	fadd.4s	v16, v26, v16
	ldp	q26, q27, [x15, #96]
	fadd.4s	v24, v24, v27
	fmul.4s	v27, v17, v4[0]
	fmul.4s	v27, v27, v21
	fadd.4s	v7, v27, v7
	fmul.4s	v27, v22, v4[0]
	fmul.4s	v27, v27, v21
	fadd.4s	v26, v27, v26
	stp	q26, q24, [x15, #96]
	stp	q7, q16, [x15, #64]
	fmul.4s	v16, v18, v5[0]
	fadd.4s	v16, v16, v20
	str	q16, [x15, #48]
	fmul.4s	v7, v23, v2[0]
	fmul.4s	v16, v22, v2[0]
	ldp	q18, q20, [x15, #-64]
	fmul.4s	v16, v16, v21
	fmul.4s	v7, v7, v19
	fadd.4s	v7, v7, v20
	fadd.4s	v16, v16, v18
	stp	q16, q7, [x15, #-64]
	fmul.4s	v7, v17, v2[0]
	ldp	q17, q16, [x15, #-96]
	fmul.4s	v18, v25, v2[0]
	add	x13, x13, #8
	add	x14, x14, #32
	fmul.4s	v18, v18, v19
	fmul.4s	v7, v7, v21
	fadd.4s	v7, v7, v17
	fadd.4s	v16, v18, v16
	stp	q7, q16, [x15, #-96]
	mov	x15, x16
	mov.16b	v7, v26
	mov.16b	v16, v24
	cmp	x3, x13
	b.ne	LBB0_21
	and	x14, x28, #0xfffffffffffffff8
	and	x13, x28, #0xfffffffffffffff8
	cmp	x28, x13
	b.eq	LBB0_12
LBB0_23:
	add	x13, x20, #160
	add	x13, x13, x14, lsl #2
LBB0_24:
	ldr	s7, [x12, x14, lsl #2]
	ldr	s16, [x11, x14, lsl #2]
	ldr	s17, [x10, x14, lsl #2]
	ldrb	w15, [x9, x14]
	ldrb	w16, [x1, x14]
	fcmp	s16, s8
	add	x14, x14, #1
	fccmp	s7, s8, #0, eq
	cset	w17, eq
	fcmp	s16, #0.0
	cset	w7, eq
	fcmp	s17, #0.0
	csinc	w7, w7, wzr, ne
	fsub	s7, s8, s7
	fmul	s7, s7, s17
	ldur	s16, [x13, #-160]
	ucvtf	s17, w17
	fmul	s18, s0, s17
	fadd	s16, s16, s18
	stur	s16, [x13, #-160]
	ldr	s16, [x13]
	fmul	s17, s1, s17
	fadd	s16, s17, s16
	str	s16, [x13]
	ucvtf	s16, w7
	fmul	s17, s5, s16
	fmul	s16, s6, s16
	ldr	s18, [x13, #32]
	fadd	s17, s17, s18
	ldur	s18, [x13, #-128]
	fadd	s16, s16, s18
	cmp	w15, #0
	fcsel	s18, s8, s9, ne
	fmul	s18, s29, s18
	str	s17, [x13, #32]
	fmul	s17, s3, s18
	fmul	s18, s4, s17
	fcmp	s7, s8
	fcsel	s7, s8, s9, eq
	fmul	s18, s18, s7
	stur	s16, [x13, #-128]
	cmp	w16, #0
	fcsel	s16, s8, s9, ne
	fmul	s16, s28, s16
	fmul	s16, s3, s16
	ldr	s19, [x13, #96]
	fadd	s18, s18, s19
	fmul	s19, s4, s16
	fmul	s19, s19, s7
	fmul	s17, s2, s17
	fmul	s17, s17, s7
	fmul	s16, s2, s16
	fmul	s7, s16, s7
	str	s18, [x13, #96]
	ldr	s16, [x13, #64]
	fadd	s16, s19, s16
	ldur	s18, [x13, #-64]
	fadd	s17, s17, s18
	str	s16, [x13, #64]
	stur	s17, [x13, #-64]
	ldur	s16, [x13, #-96]
	fadd	s7, s7, s16
	stur	s7, [x13, #-96]
	add	x13, x13, #4
	cmp	x24, x14
	b.ne	LBB0_24
	b	LBB0_12
LBB0_25:
	and	x13, x24, #0xfffffffffffffffc
	neg	x13, x13
	add	x14, x20, #160
	mov	w15, #224
LBB0_26:
	add	x16, x12, x15
	ldur	q4, [x16, #-224]
	add	x16, x11, x15
	ldur	q5, [x16, #-224]
	add	x16, x10, x15
	ldur	q6, [x16, #-224]
	fcmeq.4s	v7, v4, v30
	fcmeq.4s	v16, v5, v30
	and.16b	v7, v7, v16
	xtn.4h	v7, v7
	and.8b	v7, v7, v10
	fcmeq.4s	v5, v5, #0.0
	fcmeq.4s	v16, v6, #0.0
	orr.16b	v5, v5, v16
	xtn.4h	v5, v5
	and.8b	v5, v5, v10
	fsub.4s	v4, v30, v4
	fmul.4s	v4, v4, v6
	fcmeq.4s	v4, v4, v30
	xtn.4h	v4, v4
	and.8b	v4, v4, v10
	ldur	q6, [x14, #-160]
	ushll.4s	v7, v7, #0
	ucvtf.4s	v7, v7
	fmul.4s	v16, v7, v0[0]
	fadd.4s	v6, v6, v16
	stur	q6, [x14, #-160]
	ldr	q6, [x14]
	fmul.4s	v7, v7, v1[0]
	fadd.4s	v6, v6, v7
	str	q6, [x14]
	ushll.4s	v5, v5, #0
	ucvtf.4s	v5, v5
	fmul.4s	v6, v5, v3[0]
	fmul.4s	v5, v5, v2[0]
	ldr	q7, [x14, #32]
	fadd.4s	v6, v6, v7
	str	q6, [x14, #32]
	ldur	q6, [x14, #-128]
	fadd.4s	v5, v5, v6
	stur	q5, [x14, #-128]
	ushll.4s	v4, v4, #0
	ucvtf.4s	v4, v4
	fmul.4s	v5, v4, v3[0]
	fmul.4s	v4, v4, v2[0]
	ldr	q6, [x14, #64]
	fadd.4s	v5, v5, v6
	str	q5, [x14, #64]
	ldur	q5, [x14, #-96]
	fadd.4s	v4, v4, v5
	stur	q4, [x14, #-96]
	add	x15, x15, #16
	add	x14, x14, #16
	adds	x13, x13, #4
	b.ne	LBB0_26
	and	x13, x28, #0xfffffffffffffffc
	and	x14, x28, #0xfffffffffffffffc
	cmp	x28, x14
	b.eq	LBB0_12
LBB0_28:
	add	x14, x20, #224
	add	x14, x14, x13, lsl #2
LBB0_29:
	ldr	s4, [x12, x13, lsl #2]
	ldr	s5, [x11, x13, lsl #2]
	ldr	s6, [x10, x13, lsl #2]
	add	x13, x13, #1
	fcmp	s5, s8
	fccmp	s4, s8, #0, eq
	cset	w15, eq
	fcmp	s5, #0.0
	cset	w16, eq
	fcmp	s6, #0.0
	csinc	w16, w16, wzr, ne
	fsub	s4, s8, s4
	fmul	s4, s4, s6
	ucvtf	s5, w15
	ldur	s6, [x14, #-224]
	fmul	s7, s0, s5
	fadd	s6, s6, s7
	ldur	s7, [x14, #-64]
	fmul	s5, s1, s5
	stur	s6, [x14, #-224]
	fadd	s5, s7, s5
	stur	s5, [x14, #-64]
	ucvtf	s5, w16
	fmul	s6, s3, s5
	fmul	s5, s2, s5
	ldur	s7, [x14, #-32]
	fadd	s6, s6, s7
	ldur	s7, [x14, #-192]
	fadd	s5, s5, s7
	fcmp	s4, s8
	stur	s6, [x14, #-32]
	fcsel	s4, s8, s9, eq
	fmul	s6, s3, s4
	fmul	s4, s2, s4
	ldr	s7, [x14]
	fadd	s6, s6, s7
	stur	s5, [x14, #-192]
	str	s6, [x14]
	ldur	s5, [x14, #-160]
	fadd	s4, s4, s5
	stur	s4, [x14, #-160]
	add	x14, x14, #4
	cmp	x24, x13
	b.ne	LBB0_29
	b	LBB0_12
LBB0_30:
	ldr	x9, [sp, #584]
	cmp	x9, #1
	ldr	q17, [sp, #320]
	movi.4s	v18, #63, lsl #24
	mov	w15, #4059
	movk	w15, #16457, lsl #16
	ldr	x16, [sp, #520]
	b.lt	LBB0_34
	cmp	x28, #4
	b.hs	LBB0_49
	mov	x9, #0
LBB0_33:
	ldr	s0, [x20, x9, lsl #2]
	ldr	s1, [x16, x9, lsl #2]
	fadd	s0, s0, s1
	fmul	s0, s17, s0
	fmul	s0, s0, s11
	fmov	s1, w15
	fdiv	s0, s0, s1
	str	s0, [x8, x9, lsl #2]
	add	x9, x9, #1
	cmp	x24, x9
	b.ne	LBB0_33
LBB0_34:
	cmp	x26, #1
	ldr	x3, [sp, #488]
	b.lt	LBB0_44
	ldr	x9, [sp, #584]
	cmp	x9, #1
	b.lt	LBB0_6
	mov	x9, #0
	add	x10, x20, #288
	add	x11, x20, #128
	ldr	x15, [sp, #472]
	add	x12, x20, x15
	add	x12, x12, #288
	ldp	x14, x13, [sp, #400]
	cmp	x11, x13
	ldr	x13, [sp, #432]
	ccmp	x13, x12, #2, lo
	ldr	x13, [sp, #392]
	csinc	w13, w13, wzr, hs
	cmp	x11, x14
	ldr	x14, [sp, #424]
	ccmp	x14, x12, #2, lo
	csinc	w14, w6, wzr, hs
	orr	w13, w13, w14
	cmp	x11, x4
	ldr	x14, [sp, #416]
	ccmp	x14, x12, #2, lo
	csinc	w14, w5, wzr, hs
	orr	w13, w13, w14
	add	x14, x8, x15
	cmp	x11, x14
	ccmp	x8, x12, #2, lo
	csinc	w11, w13, wzr, hs
	and	x12, x28, #0xfffffffffffffffc
	ldr	x13, [sp, #528]
	ldr	x14, [sp, #536]
	ldr	x15, [sp, #544]
	b	LBB0_38
LBB0_37:
	add	x9, x9, #1
	ldr	x16, [sp, #608]
	add	x15, x15, x16
	ldr	x16, [sp, #616]
	add	x14, x14, x16
	ldr	x16, [sp, #624]
	add	x13, x13, x16
	cmp	x26, x9
	b.eq	LBB0_44
LBB0_38:
	cmp	x28, #4
	ldr	x16, [sp, #632]
	ldr	s0, [x16, x9, lsl #2]
	cset	w16, lo
	ldr	x17, [sp, #592]
	ldr	s1, [x17, x9, lsl #2]
	ldr	x17, [sp, #600]
	ldr	s2, [x17, x9, lsl #2]
	orr	w16, w16, w11
	tbz	w16, #0, LBB0_40
	mov	x16, #0
	b	LBB0_43
LBB0_40:
	mov	x16, #0
	mov	x17, x3
LBB0_41:
	add	x1, x10, x16
	ldr	q3, [x13, x16]
	ldr	q4, [x14, x16]
	ldr	q5, [x15, x16]
	fcmeq.4s	v3, v3, #0.0
	fcmeq.4s	v4, v4, #0.0
	orr.16b	v3, v3, v4
	fcmeq.4s	v4, v5, #0.0
	orr.16b	v3, v3, v4
	xtn.4h	v3, v3
	and.8b	v3, v3, v10
	ldr	q4, [x8, x16]
	fmul.4s	v4, v4, v0[0]
	fmul.4s	v5, v4, v2[0]
	ushll.4s	v3, v3, #0
	ucvtf.4s	v3, v3
	fmul.4s	v5, v5, v3
	fmul.4s	v4, v4, v1[0]
	fmul.4s	v3, v4, v3
	ldr	q4, [x1]
	fadd.4s	v4, v4, v5
	str	q4, [x1]
	ldur	q4, [x1, #-160]
	fadd.4s	v3, v4, v3
	stur	q3, [x1, #-160]
	add	x16, x16, #16
	adds	x17, x17, #4
	b.ne	LBB0_41
	and	x16, x28, #0xfffffffffffffffc
	cmp	x28, x12
	b.eq	LBB0_37
LBB0_43:
	lsl	x17, x16, #2
	add	x16, x16, #1
	ldr	s3, [x13, x17]
	ldr	s4, [x14, x17]
	add	x1, x10, x17
	ldr	s5, [x15, x17]
	fcmp	s3, #0.0
	cset	w2, eq
	fcmp	s4, #0.0
	csinc	w2, w2, wzr, ne
	fcmp	s5, #0.0
	csinc	w2, w2, wzr, ne
	ldr	s3, [x8, x17]
	fmul	s3, s0, s3
	fmul	s4, s2, s3
	ucvtf	s5, w2
	fmul	s4, s4, s5
	fmul	s3, s1, s3
	ldr	s6, [x1]
	fmul	s3, s3, s5
	fadd	s4, s6, s4
	str	s4, [x1]
	ldur	s4, [x1, #-160]
	fadd	s3, s4, s3
	stur	s3, [x1, #-160]
	cmp	x24, x16
	b.ne	LBB0_43
	b	LBB0_37
LBB0_44:
Lloh16:
	adrp	x8, _NRT_decref@GOTPAGE
Lloh17:
	ldr	x8, [x8, _NRT_decref@GOTPAGEOFF]
	blr	x8
	ldr	x8, [sp, #584]
	cmp	x8, #1
	ldr	x0, [sp, #384]
	b.lt	LBB0_7
	cmp	x28, #8
	b.hs	LBB0_53
LBB0_46:
	mov	x8, #0
LBB0_47:
	add	x9, x8, x27
	ldr	x10, [sp, #160]
	mov	w11, #28
	madd	x9, x9, x11, x10
	add	x10, x20, x8, lsl #2
	add	x10, x10, #160
	sub	x8, x8, x24
LBB0_48:
	ldur	s0, [x10, #-160]
	ldur	s1, [x10, #-128]
	fadd	s0, s0, s1
	ldur	s1, [x10, #-96]
	fadd	s0, s0, s1
	ldur	s1, [x10, #-64]
	fadd	s0, s0, s1
	ldur	s1, [x10, #-32]
	fadd	s0, s0, s1
	stur	s0, [x9, #-12]
	ldr	s0, [x10]
	ldr	s1, [x10, #32]
	fadd	s0, s0, s1
	ldr	s1, [x10, #64]
	fadd	s0, s0, s1
	ldr	s1, [x10, #96]
	fadd	s0, s0, s1
	ldr	s1, [x10, #128]
	fadd	s0, s0, s1
	stur	s0, [x9, #-8]
	ldr	s0, [x10]
	stur	s0, [x9, #-4]
	ldr	s0, [x10, #32]
	str	s0, [x9]
	ldr	s0, [x10, #64]
	str	s0, [x9, #4]
	ldr	s0, [x10, #96]
	str	s0, [x9, #8]
	ldr	s0, [x10, #128]
	str	s0, [x9, #12]
	add	x9, x9, #28
	add	x10, x10, #4
	adds	x8, x8, #1
	b.lo	LBB0_48
	b	LBB0_7
LBB0_49:
	mov	x9, #0
	sub	x10, x8, x20
	cmp	x10, #64
	b.lo	LBB0_33
	ldp	x11, x10, [sp, #136]
	neg	x10, x10
	madd	x10, x11, x25, x10
	add	x10, x10, x8
	cmp	x10, #64
	b.lo	LBB0_33
	dup.4s	v0, w15
	cmp	x28, #16
	b.hs	LBB0_72
	mov	x9, #0
	b	LBB0_76
LBB0_53:
	mov	x8, #0
	ldr	x9, [sp, #152]
	mov	w10, #224
	madd	x9, x25, x10, x9
	sub	x11, x28, #1
	mov	w10, #28
	umulh	x10, x11, x10
	cmp	xzr, x10
	cset	w10, ne
	lsl	x12, x11, #5
	sub	x11, x12, x11, lsl #2
	add	x12, x9, x11
	cmp	x12, x9
	b.lo	LBB0_47
	tbnz	w10, #0, LBB0_47
	add	x12, x9, #4
	add	x13, x12, x11
	cmp	x13, x12
	b.lo	LBB0_47
	tbnz	w10, #0, LBB0_47
	add	x12, x9, #8
	add	x13, x12, x11
	cmp	x13, x12
	b.lo	LBB0_47
	tbnz	w10, #0, LBB0_47
	add	x12, x9, #12
	add	x13, x12, x11
	cmp	x13, x12
	b.lo	LBB0_47
	tbnz	w10, #0, LBB0_47
	add	x12, x9, #16
	add	x13, x12, x11
	cmp	x13, x12
	b.lo	LBB0_47
	tbnz	w10, #0, LBB0_47
	add	x12, x9, #20
	add	x13, x12, x11
	cmp	x13, x12
	b.lo	LBB0_47
	tbnz	w10, #0, LBB0_47
	add	x12, x9, #24
	add	x11, x12, x11
	cmp	x11, x12
	b.lo	LBB0_47
	tbnz	w10, #0, LBB0_47
	mov	w8, #28
	madd	x8, x28, x8, x9
	cmp	x20, x8
	ldr	x11, [sp, #488]
	b.hs	LBB0_69
	ldr	x8, [sp, #472]
	add	x8, x20, x8
	add	x8, x8, #288
	cmp	x9, x8
	b.lo	LBB0_46
LBB0_69:
	add	x9, x20, #160
	and	x8, x28, #0xfffffffffffffffc
	ldr	x10, [sp, #480]
LBB0_70:
	ldur	q0, [x9, #-160]
	ldur	q1, [x9, #-128]
	ldur	q2, [x9, #-96]
	ldur	q3, [x9, #-64]
	ldur	q4, [x9, #-32]
	ldr	q5, [x9]
	ldr	q6, [x9, #32]
	ldr	q7, [x9, #64]
	ldr	q16, [x9, #96]
	ldr	q17, [x9, #128]
	fadd.4s	v0, v0, v1
	fadd.4s	v1, v5, v6
	fadd.4s	v0, v0, v2
	fadd.4s	v1, v1, v7
	fadd.4s	v0, v0, v3
	fadd.4s	v1, v1, v16
	fadd.4s	v0, v0, v4
	fadd.4s	v1, v1, v17
	trn2.4s	v2, v0, v1
	dup.4s	v3, v17[2]
	zip1.4s	v4, v0, v1
	zip1.4s	v18, v5, v6
	ext.16b	v18, v5, v18, #8
	trn1.4s	v19, v0, v1
	trn1.4s	v20, v7, v16
	mov.d	v4[1], v18[1]
	zip2.4s	v18, v5, v6
	mov.d	v18[1], v20[1]
	trn2.4s	v20, v16, v17
	mov.d	v19[0], v20[0]
	ext.16b	v2, v2, v0, #4
	zip1.4s	v20, v7, v16
	mov.s	v20[2], v17[0]
	mov.s	v2[0], v3[0]
	dup.4s	v0, v0[1]
	trn2.4s	v1, v1, v5
	mov.s	v20[3], v0[3]
	mov.s	v1[2], v6[1]
	dup.4s	v0, v7[1]
	mov.s	v1[3], v0[3]
	uzp2.4s	v0, v6, v7
	uzp2.4s	v0, v0, v6
	mov.s	v0[2], v16[3]
	mov.s	v2[3], v5[3]
	mov.s	v0[3], v17[3]
	stp	q2, q0, [x10, #80]
	stp	q1, q19, [x10, #32]
	stp	q4, q20, [x10]
	str	q18, [x10, #64]
	add	x10, x10, #112
	add	x9, x9, #16
	adds	x11, x11, #4
	b.ne	LBB0_70
	cmp	x28, x8
	b.eq	LBB0_7
	b	LBB0_47
LBB0_72:
	and	x9, x24, #0xfffffffffffffff0
	neg	x11, x9
	and	x10, x28, #0xc
	and	x9, x28, #0xfffffffffffffff0
	add	x12, x20, #32
	add	x13, x8, #32
	ldr	x14, [sp, #496]
LBB0_73:
	ldp	q1, q2, [x12, #-32]
	ldp	q3, q4, [x12], #64
	ldp	q5, q6, [x14, #-32]
	ldp	q7, q16, [x14], #64
	fadd.4s	v1, v1, v5
	fadd.4s	v2, v2, v6
	fadd.4s	v3, v3, v7
	fadd.4s	v4, v4, v16
	fmul.4s	v1, v1, v17[0]
	fmul.4s	v2, v2, v17[0]
	fmul.4s	v3, v3, v17[0]
	fmul.4s	v4, v4, v17[0]
	fmul.4s	v1, v1, v18
	fmul.4s	v2, v2, v18
	fmul.4s	v3, v3, v18
	fmul.4s	v4, v4, v18
	fdiv.4s	v1, v1, v0
	fdiv.4s	v2, v2, v0
	fdiv.4s	v3, v3, v0
	fdiv.4s	v4, v4, v0
	stp	q1, q2, [x13, #-32]
	stp	q3, q4, [x13], #64
	adds	x11, x11, #16
	b.ne	LBB0_73
	cmp	x28, x9
	b.eq	LBB0_34
	cbz	x10, LBB0_33
LBB0_76:
	and	x10, x24, #0xfffffffffffffffc
	sub	x10, x9, x10
	lsl	x11, x9, #2
	and	x9, x28, #0xfffffffffffffffc
LBB0_77:
	ldr	q1, [x20, x11]
	ldr	q2, [x16, x11]
	fadd.4s	v1, v1, v2
	fmul.4s	v1, v1, v17[0]
	fmul.4s	v1, v1, v18
	fdiv.4s	v1, v1, v0
	str	q1, [x8, x11]
	add	x11, x11, #16
	adds	x10, x10, #4
	b.ne	LBB0_77
	cmp	x28, x9
	b.ne	LBB0_33
	b	LBB0_34
LBB0_79:
	ldr	x11, [sp, #104]
	ldp	x8, x9, [sp, #16]
	stp	x8, xzr, [x11]
	mov	w8, #4
	stp	x9, x8, [x11, #16]
	ldr	x9, [sp, #152]
	stp	x9, x20, [x11, #32]
	mov	w9, #7
	mov	w10, #28
	stp	x9, x10, [x11, #48]
	str	x8, [x11, #64]
	ldr	x0, [sp, #80]
Lloh18:
	adrp	x19, _NRT_decref@GOTPAGE
Lloh19:
	ldr	x19, [x19, _NRT_decref@GOTPAGEOFF]
	blr	x19
	ldr	x0, [sp, #88]
	blr	x19
	ldr	x0, [sp, #96]
	blr	x19
	ldr	x0, [sp, #72]
	blr	x19
	ldr	x0, [sp, #32]
	blr	x19
	ldr	x0, [sp, #40]
	blr	x19
	ldr	x0, [sp, #48]
	blr	x19
	ldr	x0, [sp, #120]
	blr	x19
	ldr	x0, [sp, #56]
	blr	x19
	ldr	x0, [sp, #112]
	blr	x19
	ldr	x0, [sp, #128]
	blr	x19
	ldr	x0, [sp, #64]
	blr	x19
	mov	w0, #0
	b	LBB0_86
LBB0_80:
	ldr	x8, [sp, #8]
Lloh20:
	adrp	x9, _.const.picklebuf.ba289d81f05c7020f3477c15734804df65abe209@GOTPAGE
Lloh21:
	ldr	x9, [x9, _.const.picklebuf.ba289d81f05c7020f3477c15734804df65abe209@GOTPAGEOFF]
	b	LBB0_84
LBB0_81:
Lloh22:
	adrp	x8, _.const.picklebuf.ba289d81f05c7020f3477c15734804df65abe209.15@GOTPAGE
Lloh23:
	ldr	x8, [x8, _.const.picklebuf.ba289d81f05c7020f3477c15734804df65abe209.15@GOTPAGEOFF]
	ldr	x9, [sp, #8]
	str	x8, [x9]
	b	LBB0_85
LBB0_82:
Lloh24:
	adrp	x9, _.const.picklebuf.331b8563bdb9dac81b38422273052c486fc1706b@GOTPAGE
Lloh25:
	ldr	x9, [x9, _.const.picklebuf.331b8563bdb9dac81b38422273052c486fc1706b@GOTPAGEOFF]
LBB0_83:
	ldr	x8, [sp, #8]
LBB0_84:
	str	x9, [x8]
LBB0_85:
	mov	w0, #1
LBB0_86:
	add	sp, sp, #640
	ldp	x29, x30, [sp, #112]
	ldp	x20, x19, [sp, #96]
	ldp	x22, x21, [sp, #80]
	ldp	x24, x23, [sp, #64]
	ldp	x26, x25, [sp, #48]
	ldp	x28, x27, [sp, #32]
	ldp	d9, d8, [sp, #16]
	ldp	d11, d10, [sp], #128
	ret
	.loh AdrpLdrGot	Lloh0, Lloh1
	.loh AdrpLdrGot	Lloh2, Lloh3
	.loh AdrpLdrGot	Lloh6, Lloh7
	.loh AdrpLdrGot	Lloh4, Lloh5
	.loh AdrpLdrGot	Lloh8, Lloh9
	.loh AdrpLdrGot	Lloh10, Lloh11
	.loh AdrpLdrGot	Lloh12, Lloh13
	.loh AdrpLdrGot	Lloh14, Lloh15
	.loh AdrpLdrGot	Lloh16, Lloh17
	.loh AdrpLdrGot	Lloh18, Lloh19
	.loh AdrpLdrGot	Lloh20, Lloh21
	.loh AdrpLdrGot	Lloh22, Lloh23
	.loh AdrpLdrGot	Lloh24, Lloh25
	.cfi_endproc

	.globl	__ZN7cpython18longwave_primary_b23make_longwave_primary_b12_3clocals_3e26_longwave_primary_b_packedB2v9B38c8tJTIeFIjxB2IKSgI4CrvQClQZ6FczSBAA_3dE5ArrayIfLi3E1C7mutable7alignedE5ArrayIfLi3E1C7mutable7alignedE5ArrayIfLi3E1C7mutable7alignedE5ArrayIbLi3E1C7mutable7alignedE5ArrayIbLi3E1C7mutable7alignedE5ArrayIfLi1E1C7mutable7alignedE5ArrayIfLi1E1C7mutable7alignedE5ArrayIfLi1E1C7mutable7alignedE5ArrayIbLi1E1C7mutable7alignedE5ArrayIfLi1E1A7mutable7alignedE5ArrayIfLi1E1A7mutable7alignedEff5ArrayIfLi2E1C7mutable7alignedEfx
	.p2align	2
__ZN7cpython18longwave_primary_b23make_longwave_primary_b12_3clocals_3e26_longwave_primary_b_packedB2v9B38c8tJTIeFIjxB2IKSgI4CrvQClQZ6FczSBAA_3dE5ArrayIfLi3E1C7mutable7alignedE5ArrayIfLi3E1C7mutable7alignedE5ArrayIfLi3E1C7mutable7alignedE5ArrayIbLi3E1C7mutable7alignedE5ArrayIbLi3E1C7mutable7alignedE5ArrayIfLi1E1C7mutable7alignedE5ArrayIfLi1E1C7mutable7alignedE5ArrayIfLi1E1C7mutable7alignedE5ArrayIbLi1E1C7mutable7alignedE5ArrayIfLi1E1A7mutable7alignedE5ArrayIfLi1E1A7mutable7alignedEff5ArrayIfLi2E1C7mutable7alignedEfx:
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
	sub	sp, sp, #2320
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
Lloh26:
	adrp	x1, "_.const.make_longwave_primary_b.<locals>._longwave_primary_b_packed"@GOTPAGE
Lloh27:
	ldr	x1, [x1, "_.const.make_longwave_primary_b.<locals>._longwave_primary_b_packed"@GOTPAGEOFF]
Lloh28:
	adrp	x8, _PyArg_UnpackTuple@GOTPAGE
Lloh29:
	ldr	x8, [x8, _PyArg_UnpackTuple@GOTPAGEOFF]
	mov	w2, #16
	mov	w3, #16
	blr	x8
	movi.2d	v0, #0000000000000000
	str	q0, [sp, #1808]
	str	q0, [sp, #1824]
	str	q0, [sp, #1840]
	str	q0, [sp, #1856]
	str	q0, [sp, #1872]
	str	xzr, [sp, #1888]
	str	q0, [sp, #1712]
	str	q0, [sp, #1728]
	str	q0, [sp, #1744]
	str	q0, [sp, #1760]
	str	q0, [sp, #1776]
	str	xzr, [sp, #1792]
	str	q0, [sp, #1648]
	str	q0, [sp, #1664]
	str	q0, [sp, #1680]
	str	xzr, [sp, #1696]
	str	xzr, [sp, #1632]
	str	q0, [sp, #1616]
	str	q0, [sp, #1600]
	str	q0, [sp, #1584]
	str	xzr, [sp, #1568]
	str	q0, [sp, #1552]
	str	q0, [sp, #1536]
	str	q0, [sp, #1520]
	str	xzr, [sp, #1504]
	str	q0, [sp, #1488]
	str	q0, [sp, #1472]
	str	q0, [sp, #1456]
	str	xzr, [sp, #1440]
	str	q0, [sp, #1424]
	str	q0, [sp, #1408]
	str	q0, [sp, #1392]
	str	xzr, [sp, #1376]
	str	q0, [sp, #1360]
	str	q0, [sp, #1344]
	str	q0, [sp, #1328]
	str	xzr, [sp, #1312]
	str	q0, [sp, #1296]
	str	q0, [sp, #1280]
	str	q0, [sp, #1264]
	str	q0, [sp, #1248]
	str	xzr, [sp, #1232]
	str	q0, [sp, #1216]
	str	q0, [sp, #1200]
	str	q0, [sp, #1184]
	str	q0, [sp, #1168]
	str	xzr, [sp, #1160]
	str	xzr, [sp, #1152]
	str	q0, [sp, #1136]
	str	q0, [sp, #1120]
	str	q0, [sp, #1104]
	str	q0, [sp, #1088]
	cbz	w0, LBB1_68
Lloh30:
	adrp	x8, __ZN08NumbaEnv18longwave_primary_b23make_longwave_primary_b12_3clocals_3e26_longwave_primary_b_packedB2v9B38c8tJTIeFIjxB2IKSgI4CrvQClQZ6FczSBAA_3dE5ArrayIfLi3E1C7mutable7alignedE5ArrayIfLi3E1C7mutable7alignedE5ArrayIfLi3E1C7mutable7alignedE5ArrayIbLi3E1C7mutable7alignedE5ArrayIbLi3E1C7mutable7alignedE5ArrayIfLi1E1C7mutable7alignedE5ArrayIfLi1E1C7mutable7alignedE5ArrayIfLi1E1C7mutable7alignedE5ArrayIbLi1E1C7mutable7alignedE5ArrayIfLi1E1A7mutable7alignedE5ArrayIfLi1E1A7mutable7alignedEff5ArrayIfLi2E1C7mutable7alignedEfx@GOTPAGE
Lloh31:
	ldr	x8, [x8, __ZN08NumbaEnv18longwave_primary_b23make_longwave_primary_b12_3clocals_3e26_longwave_primary_b_packedB2v9B38c8tJTIeFIjxB2IKSgI4CrvQClQZ6FczSBAA_3dE5ArrayIfLi3E1C7mutable7alignedE5ArrayIfLi3E1C7mutable7alignedE5ArrayIfLi3E1C7mutable7alignedE5ArrayIbLi3E1C7mutable7alignedE5ArrayIbLi3E1C7mutable7alignedE5ArrayIfLi1E1C7mutable7alignedE5ArrayIfLi1E1C7mutable7alignedE5ArrayIfLi1E1C7mutable7alignedE5ArrayIbLi1E1C7mutable7alignedE5ArrayIfLi1E1A7mutable7alignedE5ArrayIfLi1E1A7mutable7alignedEff5ArrayIfLi2E1C7mutable7alignedEfx@GOTPAGEOFF]
Lloh32:
	ldr	x19, [x8]
	cbz	x19, LBB1_40
	ldur	x0, [x29, #-128]
	str	q0, [sp, #2096]
	str	q0, [sp, #2112]
	str	q0, [sp, #2128]
	str	q0, [sp, #2144]
	str	q0, [sp, #2160]
	str	xzr, [sp, #2176]
Lloh33:
	adrp	x21, _NRT_adapt_ndarray_from_python@GOTPAGE
Lloh34:
	ldr	x21, [x21, _NRT_adapt_ndarray_from_python@GOTPAGEOFF]
	add	x1, sp, #2096
	blr	x21
	cbnz	w0, LBB1_41
	ldr	x8, [sp, #2120]
	cmp	x8, #4
	b.ne	LBB1_41
	ldr	x26, [sp, #2096]
	ldr	x22, [sp, #2128]
	ldr	x23, [sp, #2144]
	ldr	x25, [sp, #2152]
	ldur	x0, [x29, #-136]
	movi.2d	v0, #0000000000000000
	str	q0, [sp, #2000]
	str	q0, [sp, #2016]
	str	q0, [sp, #2032]
	str	q0, [sp, #2048]
	str	q0, [sp, #2064]
	str	xzr, [sp, #2080]
	add	x1, sp, #2000
	blr	x21
	cbnz	w0, LBB1_43
	ldr	x8, [sp, #2024]
	cmp	x8, #4
	b.ne	LBB1_43
	ldr	x28, [sp, #2000]
	ldr	x27, [sp, #2032]
	ldr	x20, [sp, #2048]
	ldr	x24, [sp, #2056]
	ldur	x0, [x29, #-144]
	movi.2d	v0, #0000000000000000
	str	q0, [sp, #1904]
	str	q0, [sp, #1920]
	str	q0, [sp, #1936]
	str	q0, [sp, #1952]
	str	q0, [sp, #1968]
	str	xzr, [sp, #1984]
	add	x1, sp, #1904
	blr	x21
	cbnz	w0, LBB1_44
	ldr	x8, [sp, #1928]
	cmp	x8, #4
	b.ne	LBB1_44
	str	x24, [sp, #1024]
	ldr	x24, [sp, #1904]
	ldr	x8, [sp, #1936]
	str	x8, [sp, #1016]
	ldr	x8, [sp, #1952]
	str	x8, [sp, #1008]
	ldr	x8, [sp, #1960]
	str	x8, [sp, #1000]
	ldur	x0, [x29, #-152]
	movi.2d	v0, #0000000000000000
	str	q0, [sp, #1808]
	str	q0, [sp, #1824]
	str	q0, [sp, #1840]
	str	q0, [sp, #1856]
	str	q0, [sp, #1872]
	str	xzr, [sp, #1888]
	add	x1, sp, #1808
	blr	x21
	cbnz	w0, LBB1_45
	ldr	x8, [sp, #1832]
	cmp	x8, #1
	b.ne	LBB1_45
	str	x20, [sp, #992]
	ldr	x20, [sp, #1808]
	ldr	x8, [sp, #1840]
	str	x8, [sp, #984]
	ldr	x8, [sp, #1856]
	str	x8, [sp, #976]
	ldr	x8, [sp, #1864]
	str	x8, [sp, #968]
	ldur	x0, [x29, #-160]
	movi.2d	v0, #0000000000000000
	str	q0, [sp, #1712]
	str	q0, [sp, #1728]
	str	q0, [sp, #1744]
	str	q0, [sp, #1760]
	str	q0, [sp, #1776]
	str	xzr, [sp, #1792]
	add	x1, sp, #1712
	blr	x21
	cbnz	w0, LBB1_46
	ldr	x8, [sp, #1736]
	cmp	x8, #1
	b.ne	LBB1_46
	ldr	x8, [sp, #1712]
	str	x8, [sp, #1064]
	ldr	x8, [sp, #1744]
	str	x8, [sp, #960]
	ldr	x8, [sp, #1760]
	str	x8, [sp, #952]
	ldr	x8, [sp, #1768]
	str	x8, [sp, #944]
	ldur	x0, [x29, #-168]
	movi.2d	v0, #0000000000000000
	str	q0, [sp, #1648]
	str	q0, [sp, #1664]
	str	q0, [sp, #1680]
	str	xzr, [sp, #1696]
	add	x1, sp, #1648
	blr	x21
	cbnz	w0, LBB1_47
	ldr	x8, [sp, #1672]
	cmp	x8, #4
	b.ne	LBB1_47
	ldr	x8, [sp, #1648]
	str	x8, [sp, #1056]
	ldr	x8, [sp, #1680]
	str	x8, [sp, #936]
	ldr	x8, [sp, #1688]
	str	x8, [sp, #928]
	ldur	x0, [x29, #-176]
	movi.2d	v0, #0000000000000000
	str	q0, [sp, #1584]
	str	q0, [sp, #1600]
	str	q0, [sp, #1616]
	str	xzr, [sp, #1632]
	add	x1, sp, #1584
	blr	x21
	cbnz	w0, LBB1_48
	ldr	x8, [sp, #1608]
	cmp	x8, #4
	b.ne	LBB1_48
	ldr	x8, [sp, #1584]
	str	x8, [sp, #1048]
	ldr	x8, [sp, #1616]
	str	x8, [sp, #912]
	ldur	x0, [x29, #-184]
	movi.2d	v0, #0000000000000000
	str	q0, [sp, #1520]
	str	q0, [sp, #1536]
	str	q0, [sp, #1552]
	str	xzr, [sp, #1568]
	add	x1, sp, #1520
	blr	x21
	cbnz	w0, LBB1_49
	ldr	x8, [sp, #1544]
	cmp	x8, #4
	b.ne	LBB1_49
	ldr	x8, [sp, #1520]
	str	x8, [sp, #1040]
	ldr	x8, [sp, #1552]
	str	x8, [sp, #904]
	ldur	x0, [x29, #-192]
	movi.2d	v0, #0000000000000000
	str	q0, [sp, #1456]
	str	q0, [sp, #1472]
	str	q0, [sp, #1488]
	str	xzr, [sp, #1504]
	add	x1, sp, #1456
	blr	x21
	cbnz	w0, LBB1_50
	ldr	x8, [sp, #1480]
	cmp	x8, #1
	b.ne	LBB1_50
	ldr	x8, [sp, #1456]
	str	x8, [sp, #1032]
	ldr	x8, [sp, #1488]
	str	x8, [sp, #896]
	ldur	x0, [x29, #-200]
	movi.2d	v0, #0000000000000000
	str	q0, [sp, #1392]
	str	q0, [sp, #1408]
	str	q0, [sp, #1424]
	str	xzr, [sp, #1440]
	add	x1, sp, #1392
	blr	x21
	cbnz	w0, LBB1_51
	ldr	x8, [sp, #1416]
	cmp	x8, #4
	b.ne	LBB1_51
	ldr	x8, [sp, #1392]
	str	x8, [sp, #1080]
	ldr	x8, [sp, #1424]
	str	x8, [sp, #888]
	ldr	x8, [sp, #1440]
	str	x8, [sp, #880]
	ldur	x0, [x29, #-208]
	movi.2d	v0, #0000000000000000
	str	q0, [sp, #1328]
	str	q0, [sp, #1344]
	str	q0, [sp, #1360]
	str	xzr, [sp, #1376]
	add	x1, sp, #1328
	blr	x21
	cbnz	w0, LBB1_52
	ldr	x8, [sp, #1352]
	cmp	x8, #4
	b.ne	LBB1_52
	str	x27, [sp, #848]
	mov	x27, x26
	str	x25, [sp, #856]
	str	x23, [sp, #864]
	str	x22, [sp, #872]
	str	x20, [sp, #920]
	ldr	x8, [sp, #1328]
	str	x8, [sp, #1072]
	ldr	x8, [sp, #1360]
	str	x8, [sp, #840]
	ldr	x8, [sp, #1376]
	str	x8, [sp, #832]
	ldur	x0, [x29, #-216]
Lloh35:
	adrp	x22, _PyNumber_Float@GOTPAGE
Lloh36:
	ldr	x22, [x22, _PyNumber_Float@GOTPAGEOFF]
	blr	x22
	mov	x20, x0
Lloh37:
	adrp	x23, _PyFloat_AsDouble@GOTPAGE
Lloh38:
	ldr	x23, [x23, _PyFloat_AsDouble@GOTPAGEOFF]
	blr	x23
	mov.16b	v8, v0
Lloh39:
	adrp	x25, _Py_DecRef@GOTPAGE
Lloh40:
	ldr	x25, [x25, _Py_DecRef@GOTPAGEOFF]
	mov	x0, x20
	blr	x25
Lloh41:
	adrp	x26, _PyErr_Occurred@GOTPAGE
Lloh42:
	ldr	x26, [x26, _PyErr_Occurred@GOTPAGEOFF]
	blr	x26
	cbnz	x0, LBB1_56
	ldur	x0, [x29, #-224]
	blr	x22
	mov	x20, x0
	blr	x23
	mov.16b	v9, v0
	mov	x0, x20
	blr	x25
	blr	x26
	cbnz	x0, LBB1_56
	ldur	x0, [x29, #-232]
	movi.2d	v0, #0000000000000000
	str	q0, [sp, #1248]
	str	q0, [sp, #1264]
	str	q0, [sp, #1280]
	str	q0, [sp, #1296]
	str	xzr, [sp, #1312]
	add	x1, sp, #1248
	blr	x21
	cbnz	w0, LBB1_53
	ldr	x8, [sp, #1272]
	cmp	x8, #4
	b.ne	LBB1_53
	str	x19, [sp, #816]
	mov	x19, x28
	str	x27, [sp, #824]
	ldr	x28, [sp, #1248]
	ldr	x20, [sp, #1280]
	ldr	x27, [sp, #1296]
	ldur	x0, [x29, #-240]
	blr	x22
	mov	x21, x0
	blr	x23
	mov.16b	v10, v0
	mov	x0, x21
	blr	x25
	blr	x26
	cbnz	x0, LBB1_55
	ldur	x0, [x29, #-248]
Lloh43:
	adrp	x8, _PyNumber_Long@GOTPAGE
Lloh44:
	ldr	x8, [x8, _PyNumber_Long@GOTPAGEOFF]
	blr	x8
	cbz	x0, LBB1_54
Lloh45:
	adrp	x8, _PyLong_AsLongLong@GOTPAGE
Lloh46:
	ldr	x8, [x8, _PyLong_AsLongLong@GOTPAGEOFF]
	mov	x22, x0
	blr	x8
	mov	x21, x0
	mov	x0, x22
	blr	x25
	blr	x26
	cbnz	x0, LBB1_55
LBB1_31:
	fcvt	s0, d8
	fcvt	s1, d9
	fcvt	s2, d10
	str	xzr, [sp, #1232]
	movi.2d	v3, #0000000000000000
	str	q3, [sp, #1216]
	str	q3, [sp, #1200]
	str	q3, [sp, #1184]
	str	q3, [sp, #1168]
	str	x21, [sp, #800]
	str	x27, [sp, #776]
	str	x20, [sp, #760]
	ldr	x8, [sp, #832]
	str	x8, [sp, #720]
	ldr	x8, [sp, #840]
	str	x8, [sp, #704]
	ldr	x8, [sp, #880]
	str	x8, [sp, #664]
	ldr	x8, [sp, #888]
	str	x8, [sp, #648]
	ldr	x8, [sp, #896]
	str	x8, [sp, #592]
	ldr	x8, [sp, #904]
	str	x8, [sp, #536]
	ldr	x8, [sp, #912]
	str	x8, [sp, #480]
	ldr	x9, [sp, #928]
	ldr	x8, [sp, #936]
	stp	x8, x9, [sp, #424]
	ldr	x9, [sp, #944]
	ldr	x8, [sp, #952]
	stp	x8, x9, [sp, #352]
	ldr	x8, [sp, #960]
	str	x8, [sp, #336]
	ldr	x9, [sp, #968]
	ldr	x8, [sp, #976]
	stp	x8, x9, [sp, #264]
	ldr	x8, [sp, #984]
	str	x8, [sp, #248]
	ldr	x9, [sp, #1000]
	ldr	x8, [sp, #1008]
	stp	x8, x9, [sp, #176]
	ldr	x8, [sp, #1016]
	str	x8, [sp, #160]
	ldr	x8, [sp, #1024]
	str	x8, [sp, #96]
	str	x28, [sp, #728]
	ldr	x8, [sp, #1072]
	str	x8, [sp, #672]
	ldr	x8, [sp, #1080]
	str	x8, [sp, #616]
	ldr	x23, [sp, #1032]
	str	x23, [sp, #560]
	ldr	x21, [sp, #1040]
	str	x21, [sp, #504]
	str	x28, [sp, #1024]
	ldr	x28, [sp, #1048]
	str	x28, [sp, #448]
	ldr	x27, [sp, #1056]
	str	x27, [sp, #392]
	ldr	x26, [sp, #1064]
	str	x26, [sp, #304]
	ldr	x25, [sp, #920]
	str	x25, [sp, #216]
	mov	x22, x24
	str	x24, [sp, #128]
	ldr	x8, [sp, #992]
	str	x8, [sp, #88]
	ldr	x8, [sp, #848]
	str	x8, [sp, #72]
	mov	x20, x19
	str	x19, [sp, #40]
	add	x0, sp, #1168
	add	x1, sp, #1160
	ldr	x8, [sp, #856]
	str	x8, [sp, #8]
Lloh47:
	adrp	x8, __ZN18longwave_primary_b23make_longwave_primary_b12_3clocals_3e26_longwave_primary_b_packedB2v9B38c8tJTIeFIjxB2IKSgI4CrvQClQZ6FczSBAA_3dE5ArrayIfLi3E1C7mutable7alignedE5ArrayIfLi3E1C7mutable7alignedE5ArrayIfLi3E1C7mutable7alignedE5ArrayIbLi3E1C7mutable7alignedE5ArrayIbLi3E1C7mutable7alignedE5ArrayIfLi1E1C7mutable7alignedE5ArrayIfLi1E1C7mutable7alignedE5ArrayIfLi1E1C7mutable7alignedE5ArrayIbLi1E1C7mutable7alignedE5ArrayIfLi1E1A7mutable7alignedE5ArrayIfLi1E1A7mutable7alignedEff5ArrayIfLi2E1C7mutable7alignedEfx@GOTPAGE
Lloh48:
	ldr	x8, [x8, __ZN18longwave_primary_b23make_longwave_primary_b12_3clocals_3e26_longwave_primary_b_packedB2v9B38c8tJTIeFIjxB2IKSgI4CrvQClQZ6FczSBAA_3dE5ArrayIfLi3E1C7mutable7alignedE5ArrayIfLi3E1C7mutable7alignedE5ArrayIfLi3E1C7mutable7alignedE5ArrayIbLi3E1C7mutable7alignedE5ArrayIbLi3E1C7mutable7alignedE5ArrayIfLi1E1C7mutable7alignedE5ArrayIfLi1E1C7mutable7alignedE5ArrayIfLi1E1C7mutable7alignedE5ArrayIbLi1E1C7mutable7alignedE5ArrayIfLi1E1A7mutable7alignedE5ArrayIfLi1E1A7mutable7alignedEff5ArrayIfLi2E1C7mutable7alignedEfx@GOTPAGEOFF]
	ldr	x9, [sp, #864]
	str	x9, [sp]
	ldr	x19, [sp, #824]
	mov	x2, x19
	ldr	x6, [sp, #872]
	blr	x8
	str	w0, [sp, #1016]
	ldr	x8, [sp, #1160]
	str	x8, [sp, #936]
	ldr	x8, [sp, #1168]
	str	x8, [sp, #1008]
	ldr	x8, [sp, #1176]
	str	x8, [sp, #1000]
	ldr	x8, [sp, #1184]
	str	x8, [sp, #992]
	ldr	x8, [sp, #1192]
	str	x8, [sp, #984]
	ldr	x8, [sp, #1200]
	str	x8, [sp, #976]
	ldr	x8, [sp, #1208]
	str	x8, [sp, #968]
	ldr	x8, [sp, #1216]
	str	x8, [sp, #960]
	ldr	x8, [sp, #1224]
	str	x8, [sp, #952]
	ldr	x8, [sp, #1232]
	str	x8, [sp, #944]
Lloh49:
	adrp	x24, _NRT_decref@GOTPAGE
Lloh50:
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
	mov	x0, x23
	blr	x24
	ldr	x0, [sp, #1080]
	blr	x24
	ldr	x0, [sp, #1072]
	blr	x24
	ldr	x0, [sp, #1024]
	blr	x24
	ldr	w8, [sp, #1016]
	cbnz	w8, LBB1_37
	ldr	x8, [sp, #816]
	ldr	x0, [x8, #24]
	cbz	x0, LBB1_34
Lloh51:
	adrp	x8, _PyList_GetItem@GOTPAGE
Lloh52:
	ldr	x8, [x8, _PyList_GetItem@GOTPAGEOFF]
	mov	x1, #0
	blr	x8
	mov	x19, x0
	b	LBB1_35
LBB1_34:
Lloh53:
	adrp	x0, _PyExc_RuntimeError@GOTPAGE
Lloh54:
	ldr	x0, [x0, _PyExc_RuntimeError@GOTPAGEOFF]
Lloh55:
	adrp	x1, "_.const.`env.consts` is NULL in `read_const`"@GOTPAGE
Lloh56:
	ldr	x1, [x1, "_.const.`env.consts` is NULL in `read_const`"@GOTPAGEOFF]
Lloh57:
	adrp	x8, _PyErr_SetString@GOTPAGE
Lloh58:
	ldr	x8, [x8, _PyErr_SetString@GOTPAGEOFF]
	blr	x8
	mov	x19, #0
LBB1_35:
Lloh59:
	adrp	x0, _.const.pickledata.dfbcfdd39fcb26f4d0c680954487b8c0b53bb8a3@GOTPAGE
Lloh60:
	ldr	x0, [x0, _.const.pickledata.dfbcfdd39fcb26f4d0c680954487b8c0b53bb8a3@GOTPAGEOFF]
Lloh61:
	adrp	x2, _.const.pickledata.dfbcfdd39fcb26f4d0c680954487b8c0b53bb8a3.sha1@GOTPAGE
Lloh62:
	ldr	x2, [x2, _.const.pickledata.dfbcfdd39fcb26f4d0c680954487b8c0b53bb8a3.sha1@GOTPAGEOFF]
Lloh63:
	adrp	x8, _numba_unpickle@GOTPAGE
Lloh64:
	ldr	x8, [x8, _numba_unpickle@GOTPAGEOFF]
	mov	w1, #32
	blr	x8
	mov	x1, x0
	ldr	x20, [sp, #1008]
	str	x20, [sp, #1088]
	ldr	x8, [sp, #1000]
	str	x8, [sp, #1096]
	ldr	x8, [sp, #992]
	str	x8, [sp, #1104]
	ldr	x8, [sp, #984]
	str	x8, [sp, #1112]
	ldr	x8, [sp, #976]
	str	x8, [sp, #1120]
	ldr	x8, [sp, #968]
	str	x8, [sp, #1128]
	ldr	x8, [sp, #960]
	str	x8, [sp, #1136]
	ldr	x8, [sp, #952]
	str	x8, [sp, #1144]
	ldr	x8, [sp, #944]
	str	x8, [sp, #1152]
Lloh65:
	adrp	x8, _NRT_adapt_ndarray_to_python_acqref@GOTPAGE
Lloh66:
	ldr	x8, [x8, _NRT_adapt_ndarray_to_python_acqref@GOTPAGEOFF]
	add	x0, sp, #1088
	mov	w2, #2
	mov	w3, #1
	mov	x4, x19
	blr	x8
	mov	x19, x0
	mov	x0, x20
	blr	x24
LBB1_36:
	mov	x0, x19
	add	sp, sp, #2320
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
Lloh67:
	adrp	x8, _PyErr_Clear@GOTPAGE
Lloh68:
	ldr	x8, [x8, _PyErr_Clear@GOTPAGEOFF]
	blr	x8
	ldr	x20, [sp, #936]
	ldr	w1, [x20, #8]
	ldr	x0, [x20]
	ldr	w8, [x20, #32]
	cmp	w8, #1
	b.lt	LBB1_69
	sxtw	x1, w1
Lloh69:
	adrp	x8, _PyBytes_FromStringAndSize@GOTPAGE
Lloh70:
	ldr	x8, [x8, _PyBytes_FromStringAndSize@GOTPAGEOFF]
	blr	x8
	mov	x19, x0
	ldp	x0, x8, [x20, #16]
	blr	x8
	cbz	x0, LBB1_72
	mov	x1, x0
Lloh71:
	adrp	x8, _numba_runtime_build_excinfo_struct@GOTPAGE
Lloh72:
	ldr	x8, [x8, _numba_runtime_build_excinfo_struct@GOTPAGEOFF]
	mov	x0, x19
	blr	x8
	mov	x19, x0
Lloh73:
	adrp	x8, _NRT_Free@GOTPAGE
Lloh74:
	ldr	x8, [x8, _NRT_Free@GOTPAGEOFF]
	mov	x0, x20
	blr	x8
	mov	x0, x19
	b	LBB1_70
LBB1_40:
Lloh75:
	adrp	x0, _PyExc_RuntimeError@GOTPAGE
Lloh76:
	ldr	x0, [x0, _PyExc_RuntimeError@GOTPAGEOFF]
Lloh77:
	adrp	x1, "_.const.missing Environment: _ZN08NumbaEnv18longwave_primary_b23make_longwave_primary_b12_3clocals_3e26_longwave_primary_b_packedB2v9B38c8tJTIeFIjxB2IKSgI4CrvQClQZ6FczSBAA_3dE5ArrayIfLi3E1C7mutable7alignedE5ArrayIfLi3E1C7mutable7alignedE5ArrayIfLi3E1C7mutable7alignedE5ArrayIbLi3E1C7mutable7alignedE5ArrayIbLi3E1C7mutable7alignedE5ArrayIfLi1E1C7mutable7alignedE5ArrayIfLi1E1C7mutable7alignedE5ArrayIfLi1E1C7mutable7alignedE5ArrayIbLi1E1C7mutable7alignedE5ArrayIfLi1E1A7mutable7alignedE5ArrayIfLi1E1A7mutable7alignedEff5ArrayIfLi2E1C7mutable7alignedEfx"@GOTPAGE
Lloh78:
	ldr	x1, [x1, "_.const.missing Environment: _ZN08NumbaEnv18longwave_primary_b23make_longwave_primary_b12_3clocals_3e26_longwave_primary_b_packedB2v9B38c8tJTIeFIjxB2IKSgI4CrvQClQZ6FczSBAA_3dE5ArrayIfLi3E1C7mutable7alignedE5ArrayIfLi3E1C7mutable7alignedE5ArrayIfLi3E1C7mutable7alignedE5ArrayIbLi3E1C7mutable7alignedE5ArrayIbLi3E1C7mutable7alignedE5ArrayIfLi1E1C7mutable7alignedE5ArrayIfLi1E1C7mutable7alignedE5ArrayIfLi1E1C7mutable7alignedE5ArrayIbLi1E1C7mutable7alignedE5ArrayIfLi1E1A7mutable7alignedE5ArrayIfLi1E1A7mutable7alignedEff5ArrayIfLi2E1C7mutable7alignedEfx"@GOTPAGEOFF]
Lloh79:
	adrp	x8, _PyErr_SetString@GOTPAGE
Lloh80:
	ldr	x8, [x8, _PyErr_SetString@GOTPAGEOFF]
	blr	x8
	b	LBB1_36
LBB1_41:
Lloh81:
	adrp	x0, _PyExc_TypeError@GOTPAGE
Lloh82:
	ldr	x0, [x0, _PyExc_TypeError@GOTPAGEOFF]
Lloh83:
	adrp	x1, "_.const.can't unbox array from PyObject into native value.  The object maybe of a different type"@GOTPAGE
Lloh84:
	ldr	x1, [x1, "_.const.can't unbox array from PyObject into native value.  The object maybe of a different type"@GOTPAGEOFF]
LBB1_42:
Lloh85:
	adrp	x8, _PyErr_SetString@GOTPAGE
Lloh86:
	ldr	x8, [x8, _PyErr_SetString@GOTPAGEOFF]
	blr	x8
	b	LBB1_68
LBB1_43:
Lloh87:
	adrp	x0, _PyExc_TypeError@GOTPAGE
Lloh88:
	ldr	x0, [x0, _PyExc_TypeError@GOTPAGEOFF]
Lloh89:
	adrp	x1, "_.const.can't unbox array from PyObject into native value.  The object maybe of a different type"@GOTPAGE
Lloh90:
	ldr	x1, [x1, "_.const.can't unbox array from PyObject into native value.  The object maybe of a different type"@GOTPAGEOFF]
Lloh91:
	adrp	x8, _PyErr_SetString@GOTPAGE
Lloh92:
	ldr	x8, [x8, _PyErr_SetString@GOTPAGEOFF]
	blr	x8
	b	LBB1_66
LBB1_44:
Lloh93:
	adrp	x0, _PyExc_TypeError@GOTPAGE
Lloh94:
	ldr	x0, [x0, _PyExc_TypeError@GOTPAGEOFF]
Lloh95:
	adrp	x1, "_.const.can't unbox array from PyObject into native value.  The object maybe of a different type"@GOTPAGE
Lloh96:
	ldr	x1, [x1, "_.const.can't unbox array from PyObject into native value.  The object maybe of a different type"@GOTPAGEOFF]
Lloh97:
	adrp	x8, _PyErr_SetString@GOTPAGE
Lloh98:
	ldr	x8, [x8, _PyErr_SetString@GOTPAGEOFF]
	blr	x8
	b	LBB1_65
LBB1_45:
Lloh99:
	adrp	x0, _PyExc_TypeError@GOTPAGE
Lloh100:
	ldr	x0, [x0, _PyExc_TypeError@GOTPAGEOFF]
Lloh101:
	adrp	x1, "_.const.can't unbox array from PyObject into native value.  The object maybe of a different type"@GOTPAGE
Lloh102:
	ldr	x1, [x1, "_.const.can't unbox array from PyObject into native value.  The object maybe of a different type"@GOTPAGEOFF]
Lloh103:
	adrp	x8, _PyErr_SetString@GOTPAGE
Lloh104:
	ldr	x8, [x8, _PyErr_SetString@GOTPAGEOFF]
	blr	x8
	b	LBB1_64
LBB1_46:
Lloh105:
	adrp	x0, _PyExc_TypeError@GOTPAGE
Lloh106:
	ldr	x0, [x0, _PyExc_TypeError@GOTPAGEOFF]
Lloh107:
	adrp	x1, "_.const.can't unbox array from PyObject into native value.  The object maybe of a different type"@GOTPAGE
Lloh108:
	ldr	x1, [x1, "_.const.can't unbox array from PyObject into native value.  The object maybe of a different type"@GOTPAGEOFF]
Lloh109:
	adrp	x8, _PyErr_SetString@GOTPAGE
Lloh110:
	ldr	x8, [x8, _PyErr_SetString@GOTPAGEOFF]
	blr	x8
	b	LBB1_63
LBB1_47:
Lloh111:
	adrp	x0, _PyExc_TypeError@GOTPAGE
Lloh112:
	ldr	x0, [x0, _PyExc_TypeError@GOTPAGEOFF]
Lloh113:
	adrp	x1, "_.const.can't unbox array from PyObject into native value.  The object maybe of a different type"@GOTPAGE
Lloh114:
	ldr	x1, [x1, "_.const.can't unbox array from PyObject into native value.  The object maybe of a different type"@GOTPAGEOFF]
Lloh115:
	adrp	x8, _PyErr_SetString@GOTPAGE
Lloh116:
	ldr	x8, [x8, _PyErr_SetString@GOTPAGEOFF]
	blr	x8
	ldr	x21, [sp, #1064]
	b	LBB1_62
LBB1_48:
Lloh117:
	adrp	x0, _PyExc_TypeError@GOTPAGE
Lloh118:
	ldr	x0, [x0, _PyExc_TypeError@GOTPAGEOFF]
Lloh119:
	adrp	x1, "_.const.can't unbox array from PyObject into native value.  The object maybe of a different type"@GOTPAGE
Lloh120:
	ldr	x1, [x1, "_.const.can't unbox array from PyObject into native value.  The object maybe of a different type"@GOTPAGEOFF]
Lloh121:
	adrp	x8, _PyErr_SetString@GOTPAGE
Lloh122:
	ldr	x8, [x8, _PyErr_SetString@GOTPAGEOFF]
	blr	x8
	ldr	x21, [sp, #1064]
	ldr	x22, [sp, #1056]
	b	LBB1_61
LBB1_49:
Lloh123:
	adrp	x0, _PyExc_TypeError@GOTPAGE
Lloh124:
	ldr	x0, [x0, _PyExc_TypeError@GOTPAGEOFF]
Lloh125:
	adrp	x1, "_.const.can't unbox array from PyObject into native value.  The object maybe of a different type"@GOTPAGE
Lloh126:
	ldr	x1, [x1, "_.const.can't unbox array from PyObject into native value.  The object maybe of a different type"@GOTPAGEOFF]
Lloh127:
	adrp	x8, _PyErr_SetString@GOTPAGE
Lloh128:
	ldr	x8, [x8, _PyErr_SetString@GOTPAGEOFF]
	blr	x8
	ldr	x21, [sp, #1064]
	ldr	x22, [sp, #1056]
	ldr	x23, [sp, #1048]
	b	LBB1_60
LBB1_50:
Lloh129:
	adrp	x0, _PyExc_TypeError@GOTPAGE
Lloh130:
	ldr	x0, [x0, _PyExc_TypeError@GOTPAGEOFF]
Lloh131:
	adrp	x1, "_.const.can't unbox array from PyObject into native value.  The object maybe of a different type"@GOTPAGE
Lloh132:
	ldr	x1, [x1, "_.const.can't unbox array from PyObject into native value.  The object maybe of a different type"@GOTPAGEOFF]
Lloh133:
	adrp	x8, _PyErr_SetString@GOTPAGE
Lloh134:
	ldr	x8, [x8, _PyErr_SetString@GOTPAGEOFF]
	blr	x8
	ldr	x21, [sp, #1064]
	ldr	x22, [sp, #1056]
	ldr	x23, [sp, #1048]
	ldr	x25, [sp, #1040]
	b	LBB1_59
LBB1_51:
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
	b	LBB1_58
LBB1_52:
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
	b	LBB1_57
LBB1_53:
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
	b	LBB1_56
LBB1_54:
	mov	x21, #0
	blr	x26
	cbz	x0, LBB1_31
LBB1_55:
Lloh153:
	adrp	x8, _NRT_decref@GOTPAGE
Lloh154:
	ldr	x8, [x8, _NRT_decref@GOTPAGEOFF]
	mov	x0, x28
	blr	x8
	ldr	x27, [sp, #824]
	mov	x28, x19
LBB1_56:
Lloh155:
	adrp	x8, _NRT_decref@GOTPAGE
Lloh156:
	ldr	x8, [x8, _NRT_decref@GOTPAGEOFF]
	ldr	x0, [sp, #1072]
	blr	x8
	ldr	x20, [sp, #920]
	mov	x26, x27
LBB1_57:
Lloh157:
	adrp	x8, _NRT_decref@GOTPAGE
Lloh158:
	ldr	x8, [x8, _NRT_decref@GOTPAGEOFF]
	ldr	x0, [sp, #1080]
	blr	x8
LBB1_58:
	ldr	x21, [sp, #1064]
	ldr	x22, [sp, #1056]
	ldr	x23, [sp, #1048]
	ldr	x25, [sp, #1040]
	ldr	x0, [sp, #1032]
Lloh159:
	adrp	x8, _NRT_decref@GOTPAGE
Lloh160:
	ldr	x8, [x8, _NRT_decref@GOTPAGEOFF]
	blr	x8
LBB1_59:
Lloh161:
	adrp	x8, _NRT_decref@GOTPAGE
Lloh162:
	ldr	x8, [x8, _NRT_decref@GOTPAGEOFF]
	mov	x0, x25
	blr	x8
LBB1_60:
Lloh163:
	adrp	x8, _NRT_decref@GOTPAGE
Lloh164:
	ldr	x8, [x8, _NRT_decref@GOTPAGEOFF]
	mov	x0, x23
	blr	x8
LBB1_61:
Lloh165:
	adrp	x8, _NRT_decref@GOTPAGE
Lloh166:
	ldr	x8, [x8, _NRT_decref@GOTPAGEOFF]
	mov	x0, x22
	blr	x8
LBB1_62:
Lloh167:
	adrp	x8, _NRT_decref@GOTPAGE
Lloh168:
	ldr	x8, [x8, _NRT_decref@GOTPAGEOFF]
	mov	x0, x21
	blr	x8
LBB1_63:
Lloh169:
	adrp	x8, _NRT_decref@GOTPAGE
Lloh170:
	ldr	x8, [x8, _NRT_decref@GOTPAGEOFF]
	mov	x0, x20
	blr	x8
LBB1_64:
Lloh171:
	adrp	x8, _NRT_decref@GOTPAGE
Lloh172:
	ldr	x8, [x8, _NRT_decref@GOTPAGEOFF]
	mov	x0, x24
	blr	x8
LBB1_65:
Lloh173:
	adrp	x8, _NRT_decref@GOTPAGE
Lloh174:
	ldr	x8, [x8, _NRT_decref@GOTPAGEOFF]
	mov	x0, x28
	blr	x8
LBB1_66:
Lloh175:
	adrp	x8, _NRT_decref@GOTPAGE
Lloh176:
	ldr	x8, [x8, _NRT_decref@GOTPAGEOFF]
	mov	x0, x26
LBB1_67:
	blr	x8
LBB1_68:
	mov	x19, #0
	b	LBB1_36
LBB1_69:
	ldr	x2, [x20, #16]
Lloh177:
	adrp	x8, _numba_unpickle@GOTPAGE
Lloh178:
	ldr	x8, [x8, _numba_unpickle@GOTPAGEOFF]
	blr	x8
LBB1_70:
	cbz	x0, LBB1_68
Lloh179:
	adrp	x8, _numba_do_raise@GOTPAGE
Lloh180:
	ldr	x8, [x8, _numba_do_raise@GOTPAGEOFF]
	b	LBB1_67
LBB1_72:
Lloh181:
	adrp	x0, _PyExc_RuntimeError@GOTPAGE
Lloh182:
	ldr	x0, [x0, _PyExc_RuntimeError@GOTPAGEOFF]
Lloh183:
	adrp	x1, "_.const.Error creating Python tuple from runtime exception arguments"@GOTPAGE
Lloh184:
	ldr	x1, [x1, "_.const.Error creating Python tuple from runtime exception arguments"@GOTPAGEOFF]
	b	LBB1_42
	.loh AdrpLdrGot	Lloh28, Lloh29
	.loh AdrpLdrGot	Lloh26, Lloh27
	.loh AdrpLdrGotLdr	Lloh30, Lloh31, Lloh32
	.loh AdrpLdrGot	Lloh33, Lloh34
	.loh AdrpLdrGot	Lloh41, Lloh42
	.loh AdrpLdrGot	Lloh39, Lloh40
	.loh AdrpLdrGot	Lloh37, Lloh38
	.loh AdrpLdrGot	Lloh35, Lloh36
	.loh AdrpLdrGot	Lloh43, Lloh44
	.loh AdrpLdrGot	Lloh45, Lloh46
	.loh AdrpLdrGot	Lloh49, Lloh50
	.loh AdrpLdrGot	Lloh47, Lloh48
	.loh AdrpLdrGot	Lloh51, Lloh52
	.loh AdrpLdrGot	Lloh57, Lloh58
	.loh AdrpLdrGot	Lloh55, Lloh56
	.loh AdrpLdrGot	Lloh53, Lloh54
	.loh AdrpLdrGot	Lloh65, Lloh66
	.loh AdrpLdrGot	Lloh63, Lloh64
	.loh AdrpLdrGot	Lloh61, Lloh62
	.loh AdrpLdrGot	Lloh59, Lloh60
	.loh AdrpLdrGot	Lloh67, Lloh68
	.loh AdrpLdrGot	Lloh69, Lloh70
	.loh AdrpLdrGot	Lloh73, Lloh74
	.loh AdrpLdrGot	Lloh71, Lloh72
	.loh AdrpLdrGot	Lloh79, Lloh80
	.loh AdrpLdrGot	Lloh77, Lloh78
	.loh AdrpLdrGot	Lloh75, Lloh76
	.loh AdrpLdrGot	Lloh83, Lloh84
	.loh AdrpLdrGot	Lloh81, Lloh82
	.loh AdrpLdrGot	Lloh85, Lloh86
	.loh AdrpLdrGot	Lloh91, Lloh92
	.loh AdrpLdrGot	Lloh89, Lloh90
	.loh AdrpLdrGot	Lloh87, Lloh88
	.loh AdrpLdrGot	Lloh97, Lloh98
	.loh AdrpLdrGot	Lloh95, Lloh96
	.loh AdrpLdrGot	Lloh93, Lloh94
	.loh AdrpLdrGot	Lloh103, Lloh104
	.loh AdrpLdrGot	Lloh101, Lloh102
	.loh AdrpLdrGot	Lloh99, Lloh100
	.loh AdrpLdrGot	Lloh109, Lloh110
	.loh AdrpLdrGot	Lloh107, Lloh108
	.loh AdrpLdrGot	Lloh105, Lloh106
	.loh AdrpLdrGot	Lloh115, Lloh116
	.loh AdrpLdrGot	Lloh113, Lloh114
	.loh AdrpLdrGot	Lloh111, Lloh112
	.loh AdrpLdrGot	Lloh121, Lloh122
	.loh AdrpLdrGot	Lloh119, Lloh120
	.loh AdrpLdrGot	Lloh117, Lloh118
	.loh AdrpLdrGot	Lloh127, Lloh128
	.loh AdrpLdrGot	Lloh125, Lloh126
	.loh AdrpLdrGot	Lloh123, Lloh124
	.loh AdrpLdrGot	Lloh133, Lloh134
	.loh AdrpLdrGot	Lloh131, Lloh132
	.loh AdrpLdrGot	Lloh129, Lloh130
	.loh AdrpLdrGot	Lloh139, Lloh140
	.loh AdrpLdrGot	Lloh137, Lloh138
	.loh AdrpLdrGot	Lloh135, Lloh136
	.loh AdrpLdrGot	Lloh145, Lloh146
	.loh AdrpLdrGot	Lloh143, Lloh144
	.loh AdrpLdrGot	Lloh141, Lloh142
	.loh AdrpLdrGot	Lloh151, Lloh152
	.loh AdrpLdrGot	Lloh149, Lloh150
	.loh AdrpLdrGot	Lloh147, Lloh148
	.loh AdrpLdrGot	Lloh153, Lloh154
	.loh AdrpLdrGot	Lloh155, Lloh156
	.loh AdrpLdrGot	Lloh157, Lloh158
	.loh AdrpLdrGot	Lloh159, Lloh160
	.loh AdrpLdrGot	Lloh161, Lloh162
	.loh AdrpLdrGot	Lloh163, Lloh164
	.loh AdrpLdrGot	Lloh165, Lloh166
	.loh AdrpLdrGot	Lloh167, Lloh168
	.loh AdrpLdrGot	Lloh169, Lloh170
	.loh AdrpLdrGot	Lloh171, Lloh172
	.loh AdrpLdrGot	Lloh173, Lloh174
	.loh AdrpLdrGot	Lloh175, Lloh176
	.loh AdrpLdrGot	Lloh177, Lloh178
	.loh AdrpLdrGot	Lloh179, Lloh180
	.loh AdrpLdrGot	Lloh183, Lloh184
	.loh AdrpLdrGot	Lloh181, Lloh182
	.cfi_endproc

	.globl	_cfunc._ZN18longwave_primary_b23make_longwave_primary_b12_3clocals_3e26_longwave_primary_b_packedB2v9B38c8tJTIeFIjxB2IKSgI4CrvQClQZ6FczSBAA_3dE5ArrayIfLi3E1C7mutable7alignedE5ArrayIfLi3E1C7mutable7alignedE5ArrayIfLi3E1C7mutable7alignedE5ArrayIbLi3E1C7mutable7alignedE5ArrayIbLi3E1C7mutable7alignedE5ArrayIfLi1E1C7mutable7alignedE5ArrayIfLi1E1C7mutable7alignedE5ArrayIfLi1E1C7mutable7alignedE5ArrayIbLi1E1C7mutable7alignedE5ArrayIfLi1E1A7mutable7alignedE5ArrayIfLi1E1A7mutable7alignedEff5ArrayIfLi2E1C7mutable7alignedEfx
	.p2align	2
_cfunc._ZN18longwave_primary_b23make_longwave_primary_b12_3clocals_3e26_longwave_primary_b_packedB2v9B38c8tJTIeFIjxB2IKSgI4CrvQClQZ6FczSBAA_3dE5ArrayIfLi3E1C7mutable7alignedE5ArrayIfLi3E1C7mutable7alignedE5ArrayIfLi3E1C7mutable7alignedE5ArrayIbLi3E1C7mutable7alignedE5ArrayIbLi3E1C7mutable7alignedE5ArrayIfLi1E1C7mutable7alignedE5ArrayIfLi1E1C7mutable7alignedE5ArrayIfLi1E1C7mutable7alignedE5ArrayIbLi1E1C7mutable7alignedE5ArrayIfLi1E1A7mutable7alignedE5ArrayIfLi1E1A7mutable7alignedEff5ArrayIfLi2E1C7mutable7alignedEfx:
	.cfi_startproc
	stp	x28, x27, [sp, #-96]!
	stp	x26, x25, [sp, #16]
	stp	x24, x23, [sp, #32]
	stp	x22, x21, [sp, #48]
	stp	x20, x19, [sp, #64]
	stp	x29, x30, [sp, #80]
	add	x29, sp, #80
	sub	sp, sp, #992
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
	stp	x7, x6, [x29, #-200]
	stur	x4, [x29, #-184]
	mov	x28, x8
	ldr	x8, [x29, #40]
	stp	x8, x0, [x29, #-216]
	ldr	x9, [x29, #72]
	ldp	x10, x11, [x29, #88]
	stp	x10, x9, [x29, #-232]
	ldr	x8, [x29, #128]
	stp	x8, x11, [x29, #-248]
	ldr	x8, [x29, #160]
	stur	x8, [x29, #-256]
	ldr	x8, [x29, #176]
	str	x8, [sp, #808]
	ldr	x7, [x29, #184]
	ldr	x6, [x29, #216]
	ldr	x4, [x29, #248]
	ldp	x2, x1, [x29, #264]
	ldr	x3, [x29, #304]
	ldr	x5, [x29, #336]
	ldp	x0, x17, [x29, #352]
	ldr	x16, [x29, #392]
	ldp	x15, x14, [x29, #424]
	ldr	x13, [x29, #448]
	ldr	x12, [x29, #480]
	ldr	x11, [x29, #504]
	ldr	x10, [x29, #536]
	ldr	x30, [x29, #560]
	ldr	x9, [x29, #592]
	ldr	x8, [x29, #616]
	stur	xzr, [x29, #-96]
	movi.2d	v3, #0000000000000000
	stp	q3, q3, [x29, #-128]
	stp	q3, q3, [x29, #-160]
	stur	xzr, [x29, #-168]
	ldr	x19, [x29, #648]
	ldr	x20, [x29, #664]
	ldr	x21, [x29, #672]
	ldr	x22, [x29, #704]
	ldr	x23, [x29, #720]
	ldr	x24, [x29, #728]
	ldr	x25, [x29, #760]
	ldr	x26, [x29, #776]
	ldr	x27, [x29, #800]
	str	x27, [sp, #800]
	str	x26, [sp, #776]
	str	x25, [sp, #760]
	str	x24, [sp, #728]
	str	x23, [sp, #720]
	str	x22, [sp, #704]
	str	x21, [sp, #672]
	str	x20, [sp, #664]
	str	x19, [sp, #648]
	str	x8, [sp, #616]
	str	x9, [sp, #592]
	str	x30, [sp, #560]
	str	x10, [sp, #536]
	str	x11, [sp, #504]
	str	x12, [sp, #480]
	str	x13, [sp, #448]
	stp	x15, x14, [sp, #424]
	str	x16, [sp, #392]
	stp	x0, x17, [sp, #352]
	str	x5, [sp, #336]
	str	x3, [sp, #304]
	stp	x2, x1, [sp, #264]
	str	x4, [sp, #248]
	str	x6, [sp, #216]
	ldr	x8, [sp, #808]
	stp	x8, x7, [sp, #176]
	ldur	x8, [x29, #-256]
	str	x8, [sp, #160]
	ldur	x8, [x29, #-248]
	str	x8, [sp, #128]
	ldur	x8, [x29, #-240]
	str	x8, [sp, #96]
	ldur	x8, [x29, #-232]
	str	x8, [sp, #88]
	ldur	x8, [x29, #-224]
	str	x8, [sp, #72]
	ldur	x8, [x29, #-216]
	str	x8, [sp, #40]
Lloh185:
	adrp	x8, __ZN18longwave_primary_b23make_longwave_primary_b12_3clocals_3e26_longwave_primary_b_packedB2v9B38c8tJTIeFIjxB2IKSgI4CrvQClQZ6FczSBAA_3dE5ArrayIfLi3E1C7mutable7alignedE5ArrayIfLi3E1C7mutable7alignedE5ArrayIfLi3E1C7mutable7alignedE5ArrayIbLi3E1C7mutable7alignedE5ArrayIbLi3E1C7mutable7alignedE5ArrayIfLi1E1C7mutable7alignedE5ArrayIfLi1E1C7mutable7alignedE5ArrayIfLi1E1C7mutable7alignedE5ArrayIbLi1E1C7mutable7alignedE5ArrayIfLi1E1A7mutable7alignedE5ArrayIfLi1E1A7mutable7alignedEff5ArrayIfLi2E1C7mutable7alignedEfx@GOTPAGE
Lloh186:
	ldr	x8, [x8, __ZN18longwave_primary_b23make_longwave_primary_b12_3clocals_3e26_longwave_primary_b_packedB2v9B38c8tJTIeFIjxB2IKSgI4CrvQClQZ6FczSBAA_3dE5ArrayIfLi3E1C7mutable7alignedE5ArrayIfLi3E1C7mutable7alignedE5ArrayIfLi3E1C7mutable7alignedE5ArrayIbLi3E1C7mutable7alignedE5ArrayIbLi3E1C7mutable7alignedE5ArrayIfLi1E1C7mutable7alignedE5ArrayIfLi1E1C7mutable7alignedE5ArrayIfLi1E1C7mutable7alignedE5ArrayIbLi1E1C7mutable7alignedE5ArrayIfLi1E1A7mutable7alignedE5ArrayIfLi1E1A7mutable7alignedEff5ArrayIfLi2E1C7mutable7alignedEfx@GOTPAGEOFF]
	sub	x0, x29, #160
	sub	x1, x29, #168
	ldur	x9, [x29, #-200]
	str	x9, [sp, #8]
	ldur	x9, [x29, #-192]
	str	x9, [sp]
	ldur	x2, [x29, #-208]
	ldur	x6, [x29, #-184]
	blr	x8
	ldp	x19, x8, [x29, #-168]
	ldp	x22, x23, [x29, #-152]
	ldp	x24, x25, [x29, #-136]
	ldp	x26, x27, [x29, #-120]
	ldp	x20, x21, [x29, #-104]
	stur	wzr, [x29, #-172]
	cbnz	w0, LBB2_2
LBB2_1:
	stp	x8, x22, [x28]
	stp	x23, x24, [x28, #16]
	stp	x25, x26, [x28, #32]
	stp	x27, x20, [x28, #48]
	str	x21, [x28, #64]
	add	sp, sp, #992
	ldp	x29, x30, [sp, #80]
	ldp	x20, x19, [sp, #64]
	ldp	x22, x21, [sp, #48]
	ldp	x24, x23, [sp, #32]
	ldp	x26, x25, [sp, #16]
	ldp	x28, x27, [sp], #96
	ret
LBB2_2:
	stur	x8, [x29, #-184]
Lloh187:
	adrp	x8, _numba_gil_ensure@GOTPAGE
Lloh188:
	ldr	x8, [x8, _numba_gil_ensure@GOTPAGEOFF]
	sub	x0, x29, #172
	blr	x8
Lloh189:
	adrp	x8, _PyErr_Clear@GOTPAGE
Lloh190:
	ldr	x8, [x8, _PyErr_Clear@GOTPAGEOFF]
	blr	x8
	ldr	w1, [x19, #8]
	ldr	x0, [x19]
	ldr	w8, [x19, #32]
	cmp	w8, #1
	b.lt	LBB2_7
	sxtw	x1, w1
Lloh191:
	adrp	x8, _PyBytes_FromStringAndSize@GOTPAGE
Lloh192:
	ldr	x8, [x8, _PyBytes_FromStringAndSize@GOTPAGEOFF]
	blr	x8
	stur	x0, [x29, #-192]
	ldp	x0, x8, [x19, #16]
	blr	x8
	cbz	x0, LBB2_8
	mov	x1, x0
Lloh193:
	adrp	x8, _numba_runtime_build_excinfo_struct@GOTPAGE
Lloh194:
	ldr	x8, [x8, _numba_runtime_build_excinfo_struct@GOTPAGEOFF]
	ldur	x0, [x29, #-192]
	blr	x8
	stur	x0, [x29, #-192]
Lloh195:
	adrp	x8, _NRT_Free@GOTPAGE
Lloh196:
	ldr	x8, [x8, _NRT_Free@GOTPAGEOFF]
	mov	x0, x19
	blr	x8
	ldur	x0, [x29, #-192]
	cbz	x0, LBB2_6
LBB2_5:
Lloh197:
	adrp	x8, _numba_do_raise@GOTPAGE
Lloh198:
	ldr	x8, [x8, _numba_do_raise@GOTPAGEOFF]
	blr	x8
LBB2_6:
Lloh199:
	adrp	x0, "_.const.<numba.core.cpu.CPUContext>"@GOTPAGE
Lloh200:
	ldr	x0, [x0, "_.const.<numba.core.cpu.CPUContext>"@GOTPAGEOFF]
Lloh201:
	adrp	x8, _PyUnicode_FromString@GOTPAGE
Lloh202:
	ldr	x8, [x8, _PyUnicode_FromString@GOTPAGEOFF]
	blr	x8
	mov	x19, x0
Lloh203:
	adrp	x8, _PyErr_WriteUnraisable@GOTPAGE
Lloh204:
	ldr	x8, [x8, _PyErr_WriteUnraisable@GOTPAGEOFF]
	blr	x8
Lloh205:
	adrp	x8, _Py_DecRef@GOTPAGE
Lloh206:
	ldr	x8, [x8, _Py_DecRef@GOTPAGEOFF]
	mov	x0, x19
	blr	x8
Lloh207:
	adrp	x8, _numba_gil_release@GOTPAGE
Lloh208:
	ldr	x8, [x8, _numba_gil_release@GOTPAGEOFF]
	sub	x0, x29, #172
	blr	x8
	ldur	x8, [x29, #-184]
	b	LBB2_1
LBB2_7:
	ldr	x2, [x19, #16]
Lloh209:
	adrp	x8, _numba_unpickle@GOTPAGE
Lloh210:
	ldr	x8, [x8, _numba_unpickle@GOTPAGEOFF]
	blr	x8
	cbnz	x0, LBB2_5
	b	LBB2_6
LBB2_8:
Lloh211:
	adrp	x0, _PyExc_RuntimeError@GOTPAGE
Lloh212:
	ldr	x0, [x0, _PyExc_RuntimeError@GOTPAGEOFF]
Lloh213:
	adrp	x1, "_.const.Error creating Python tuple from runtime exception arguments.1"@GOTPAGE
Lloh214:
	ldr	x1, [x1, "_.const.Error creating Python tuple from runtime exception arguments.1"@GOTPAGEOFF]
Lloh215:
	adrp	x8, _PyErr_SetString@GOTPAGE
Lloh216:
	ldr	x8, [x8, _PyErr_SetString@GOTPAGEOFF]
	blr	x8
	mov	x8, #0
	mov	x22, #0
	mov	x23, #0
	mov	x24, #0
	mov	x25, #0
	mov	x26, #0
	mov	x27, #0
	mov	x20, #0
	mov	x21, #0
	b	LBB2_1
	.loh AdrpLdrGot	Lloh185, Lloh186
	.loh AdrpLdrGot	Lloh189, Lloh190
	.loh AdrpLdrGot	Lloh187, Lloh188
	.loh AdrpLdrGot	Lloh191, Lloh192
	.loh AdrpLdrGot	Lloh195, Lloh196
	.loh AdrpLdrGot	Lloh193, Lloh194
	.loh AdrpLdrGot	Lloh197, Lloh198
	.loh AdrpLdrGot	Lloh207, Lloh208
	.loh AdrpLdrGot	Lloh205, Lloh206
	.loh AdrpLdrGot	Lloh203, Lloh204
	.loh AdrpLdrGot	Lloh201, Lloh202
	.loh AdrpLdrGot	Lloh199, Lloh200
	.loh AdrpLdrGot	Lloh209, Lloh210
	.loh AdrpLdrGot	Lloh215, Lloh216
	.loh AdrpLdrGot	Lloh213, Lloh214
	.loh AdrpLdrGot	Lloh211, Lloh212
	.cfi_endproc

	.globl	_NRT_incref
	.weak_def_can_be_hidden	_NRT_incref
	.p2align	2
_NRT_incref:
	cbz	x0, LBB3_2
	mov	w8, #1
	ldadd	x8, x8, [x0]
LBB3_2:
	ret

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
Lloh217:
	adrp	x1, _NRT_MemInfo_call_dtor@GOTPAGE
Lloh218:
	ldr	x1, [x1, _NRT_MemInfo_call_dtor@GOTPAGEOFF]
	br	x1
	.loh AdrpLdrGot	Lloh217, Lloh218
	.cfi_endproc

	.section	__TEXT,__const
	.p2align	4, 0x0
"_.const.make_longwave_primary_b.<locals>._longwave_primary_b_packed":
	.asciz	"make_longwave_primary_b.<locals>._longwave_primary_b_packed"

	.comm	__ZN08NumbaEnv18longwave_primary_b23make_longwave_primary_b12_3clocals_3e26_longwave_primary_b_packedB2v9B38c8tJTIeFIjxB2IKSgI4CrvQClQZ6FczSBAA_3dE5ArrayIfLi3E1C7mutable7alignedE5ArrayIfLi3E1C7mutable7alignedE5ArrayIfLi3E1C7mutable7alignedE5ArrayIbLi3E1C7mutable7alignedE5ArrayIbLi3E1C7mutable7alignedE5ArrayIfLi1E1C7mutable7alignedE5ArrayIfLi1E1C7mutable7alignedE5ArrayIfLi1E1C7mutable7alignedE5ArrayIbLi1E1C7mutable7alignedE5ArrayIfLi1E1A7mutable7alignedE5ArrayIfLi1E1A7mutable7alignedEff5ArrayIfLi2E1C7mutable7alignedEfx,8,3
	.p2align	4, 0x0
"_.const.missing Environment: _ZN08NumbaEnv18longwave_primary_b23make_longwave_primary_b12_3clocals_3e26_longwave_primary_b_packedB2v9B38c8tJTIeFIjxB2IKSgI4CrvQClQZ6FczSBAA_3dE5ArrayIfLi3E1C7mutable7alignedE5ArrayIfLi3E1C7mutable7alignedE5ArrayIfLi3E1C7mutable7alignedE5ArrayIbLi3E1C7mutable7alignedE5ArrayIbLi3E1C7mutable7alignedE5ArrayIfLi1E1C7mutable7alignedE5ArrayIfLi1E1C7mutable7alignedE5ArrayIfLi1E1C7mutable7alignedE5ArrayIbLi1E1C7mutable7alignedE5ArrayIfLi1E1A7mutable7alignedE5ArrayIfLi1E1A7mutable7alignedEff5ArrayIfLi2E1C7mutable7alignedEfx":
	.asciz	"missing Environment: _ZN08NumbaEnv18longwave_primary_b23make_longwave_primary_b12_3clocals_3e26_longwave_primary_b_packedB2v9B38c8tJTIeFIjxB2IKSgI4CrvQClQZ6FczSBAA_3dE5ArrayIfLi3E1C7mutable7alignedE5ArrayIfLi3E1C7mutable7alignedE5ArrayIfLi3E1C7mutable7alignedE5ArrayIbLi3E1C7mutable7alignedE5ArrayIbLi3E1C7mutable7alignedE5ArrayIfLi1E1C7mutable7alignedE5ArrayIfLi1E1C7mutable7alignedE5ArrayIfLi1E1C7mutable7alignedE5ArrayIbLi1E1C7mutable7alignedE5ArrayIfLi1E1A7mutable7alignedE5ArrayIfLi1E1A7mutable7alignedEff5ArrayIfLi2E1C7mutable7alignedEfx"

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

	.comm	__ZN08NumbaEnv5numba2np8arrayobj11ol_np_zeros12_3clocals_3e4implB2v2B42c8tJTIeFIjxB2IKSgI4CrvQClcaMQ5hEEUSJJgA_3dE8UniTupleIxLi2EE18class_28float32_29,8,3
	.comm	__ZN08NumbaEnv5numba2np8arrayobj11ol_np_empty12_3clocals_3e4implB2v3B42c8tJTIeFIjxB2IKSgI4CrvQClcaMQ5hEEUSJJgA_3dE8UniTupleIxLi2EE18class_28float32_29,8,3
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

	.comm	__ZN08NumbaEnv5numba2np8arrayobj18ol_array_zero_fill12_3clocals_3e4implB2v6B42c8tJTIeFIjxB2IKSgI4CrvQClcaMQ5hEEUSJJgA_3dE5ArrayIfLi2E1C7mutable7alignedE,8,3
	.comm	__ZN08NumbaEnv5numba7cpython8builtins6ol_min12_3clocals_3e4implB2v7B42c8tJTIeFIjxB2IKSgI4CrvQClcaMQ5hEEUSJJgA_3dE15StarArgUniTupleIxLi2EE,8,3
	.comm	__ZN08NumbaEnv5numba2np8arrayobj11ol_np_empty12_3clocals_3e4implB2v8B42c8tJTIeFIjxB2IKSgI4CrvQClcaMQ5hEEUSJJgA_3dEx18class_28float32_29,8,3
	.comm	__ZN08NumbaEnv5numba2np8arrayobj15_call_allocatorB2v4B42c8tJTC_2fWQA93W1AaAIYBPIqRBFCjDSZRVAJmaQIAEN29typeref_5b_3cclass_20_27numba4core5types8npytypes14Array_27_3e_5dExj,8,3
	.comm	__ZN08NumbaEnv5numba2np8arrayobj18_ol_array_allocate12_3clocals_3e4implB2v5B42c8tJTIeFIjxB2IKSgI4CrvQClcaMQ5hEEUSJJgA_3dEN29typeref_5b_3cclass_20_27numba4core5types8npytypes14Array_27_3e_5dExj,8,3
	.section	__TEXT,__const
	.p2align	4, 0x0
_.const.pickledata.ba289d81f05c7020f3477c15734804df65abe209.16:
	.ascii	"\200\004\225K\000\000\000\000\000\000\000\214\bbuiltins\224\214\013MemoryError\224\223\224\214'Allocation failed (probably too large).\224\205\224N\207\224."

	.p2align	4, 0x0
_.const.pickledata.ba289d81f05c7020f3477c15734804df65abe209.sha1.17:
	.ascii	"\272(\235\201\360\\p \363G|\025sH\004\337e\253\342\t"

	.section	__DATA,__const
	.p2align	4, 0x0
_.const.picklebuf.ba289d81f05c7020f3477c15734804df65abe209.15:
	.quad	_.const.pickledata.ba289d81f05c7020f3477c15734804df65abe209.16
	.long	86
	.space	4
	.quad	_.const.pickledata.ba289d81f05c7020f3477c15734804df65abe209.sha1.17
	.quad	0
	.long	0
	.space	4

.subsections_via_symbols
