	.arch armv8.2-a+dotprod+crc+fp16+rcpc
	.file	"ab_tu_base.cpp"
	.text
	.align	2
	.p2align 5,,15
	.global	_ZN7ab_base13simd_quad_pi5EPKtit
	.type	_ZN7ab_base13simd_quad_pi5EPKtit, %function
_ZN7ab_base13simd_quad_pi5EPKtit:
.LFB3139:
	.cfi_startproc
	and	w2, w2, 65535
	cmp	w1, 31
	bgt	.L2
	cmp	w1, 15
	ble	.L3
	dup	v30.8h, w2
	ld1	{v28.8h - v29.8h}, [x0]
	cmeq	v31.8h, v30.8h, v28.8h
	cmeq	v29.8h, v30.8h, v29.8h
	orr	v31.16b, v31.16b, v29.16b
	umaxv	h31, v31.8h
	umov	w3, v31.h[0]
	tst	w3, 65535
	bne	.L4
	cmp	w1, 16
	beq	.L11
	add	x4, x0, 32
	mov	w7, 11
	neg	x4, x4, lsr 1
	sub	w5, w1, #17
	and	w6, w4, 7
	add	w3, w6, 8
	cmp	w3, w7
	csel	w3, w3, w7, cs
	cmp	w3, w5
	bhi	.L35
	cbz	w6, .L36
	ldrh	w3, [x0, 32]
	cmp	w2, w3
	bls	.L26
	tst	x4, 6
	beq	.L37
	ldrh	w3, [x0, 34]
	cmp	w2, w3
	bls	.L26
	cmp	w6, 2
	bls	.L38
	ldrh	w3, [x0, 36]
	cmp	w2, w3
	bls	.L26
	tbz	x4, 2, .L39
	ldrh	w3, [x0, 38]
	cmp	w2, w3
	bls	.L26
	cmp	w6, 4
	beq	.L40
	ldrh	w3, [x0, 40]
	cmp	w2, w3
	bls	.L26
	cmp	w6, 5
	beq	.L41
	ldrh	w3, [x0, 42]
	cmp	w2, w3
	bls	.L26
	cmp	w6, 7
	bne	.L42
	ldrh	w3, [x0, 44]
	cmp	w2, w3
	bls	.L26
	mov	w5, 23
.L8:
	add	w3, w6, 16
	ubfiz	x3, x3, 1, 6
	ldr	q31, [x0, x3]
	cmhs	v31.8h, v31.8h, v30.8h
	umaxp	v31.4s, v31.4s, v31.4s
	fmov	x3, d31
	cbnz	x3, .L10
	sub	w3, w1, #24
	cmp	w3, w6
	beq	.L11
	add	w5, w5, 8
.L7:
	lsl	w4, w5, 1
	ldrh	w3, [x0, x4]
	cmp	w3, w2
	bcs	.L26
	add	w3, w5, 1
	cmp	w1, w3
	ble	.L11
	add	w4, w4, 2
	ldrh	w3, [x0, x4]
	cmp	w3, w2
	bcs	.L26
	add	w3, w5, 2
	cmp	w3, w1
	bge	.L11
.L34:
	add	x4, x0, x4
	ldrh	w3, [x4, 2]
	cmp	w2, w3
	bls	.L26
	add	w3, w5, 3
	cmp	w1, w3
	ble	.L11
	ldrh	w3, [x4, 4]
	cmp	w2, w3
	bls	.L26
	add	w3, w5, 4
	cmp	w1, w3
	ble	.L11
	ldrh	w3, [x4, 6]
	cmp	w2, w3
	bls	.L26
	add	w3, w5, 5
	cmp	w3, w1
	bge	.L11
	ldrh	w3, [x4, 8]
	cmp	w2, w3
	bls	.L26
	add	w3, w5, 6
	cmp	w1, w3
	ble	.L11
	ldrh	w3, [x4, 10]
	cmp	w2, w3
	bls	.L26
	add	w3, w5, 7
	cmp	w1, w3
	ble	.L11
	ldrh	w3, [x4, 12]
	cmp	w3, w2
	bcs	.L26
	add	w3, w5, 8
	cmp	w3, w1
	bge	.L11
	ldrh	w3, [x4, 14]
	cmp	w2, w3
	bls	.L26
	add	w3, w5, 9
	cmp	w1, w3
	ble	.L11
	ldrh	w3, [x4, 16]
	cmp	w2, w3
	bls	.L26
	add	w3, w5, 10
	cmp	w1, w3
	ble	.L11
	ldrh	w3, [x4, 18]
	cmp	w2, w3
	bls	.L26
	add	w3, w5, 11
	cmp	w1, w3
	ble	.L11
	ldrh	w3, [x4, 20]
	cmp	w2, w3
	bls	.L26
	add	w3, w5, 12
	cmp	w1, w3
	ble	.L11
	ldrh	w3, [x4, 22]
	cmp	w2, w3
	bls	.L26
	add	w3, w5, 13
	cmp	w1, w3
	ble	.L11
	ldrh	w3, [x4, 24]
	cmp	w2, w3
	bls	.L26
	add	w5, w5, 14
	cmp	w1, w5
	ble	.L11
	ldrh	w3, [x0, 60]
	cmp	w2, w3
	bls	.L26
	.p2align 5,,15
.L11:
	mov	w0, 0
.L88:
	ret
	.p2align 2,,3
.L2:
	asr	w9, w1, 5
	mov	w5, 0
	mov	w4, w9
	cmp	w1, 127
	ble	.L89
	.p2align 5,,15
.L18:
	asr	w7, w4, 2
	add	w3, w5, w7, lsl 1
	add	w6, w7, w5
	add	w6, w6, 1
	add	w11, w7, w7, lsl 1
	add	w8, w3, 1
	sbfiz	x6, x6, 5, 32
	add	w3, w7, w3
	sub	x6, x6, #1
	sbfiz	x8, x8, 5, 32
	add	w3, w3, 1
	ldrh	w10, [x0, x6, lsl 1]
	sbfiz	x3, x3, 5, 32
	sub	x6, x8, #1
	ldrh	w8, [x0, x6, lsl 1]
	sub	x3, x3, #1
	sub	w4, w4, w11
	ldrh	w6, [x0, x3, lsl 1]
	cmp	w10, w2
	cset	w3, cc
	cmp	w8, w2
	cinc	w3, w3, cc
	cmp	w6, w2
	cinc	w3, w3, cc
	madd	w5, w3, w7, w5
	add	w3, w5, w4, asr 1
	lsl	w3, w3, 5
	add	x3, x0, w3, sxtw 1
	prfm	PLDL1KEEP, [x3]
	cmp	w4, 3
	bgt	.L18
	b	.L89
	.p2align 2,,3
.L21:
	asr	w3, w4, 1
	add	w6, w3, w5
	sub	w4, w4, w3
	add	w3, w6, 1
	sbfiz	x3, x3, 5, 32
	sub	x3, x3, #1
	ldrh	w3, [x0, x3, lsl 1]
	cmp	w3, w2
	csel	w5, w5, w6, cs
.L89:
	cmp	w4, 1
	bgt	.L21
	add	w3, w5, 1
	sbfiz	x4, x3, 5, 32
	sub	x4, x4, #1
	ldrh	w4, [x0, x4, lsl 1]
	cmp	w4, w2
	csel	w3, w3, w5, cc
	cmp	w3, w9
	blt	.L93
	lsl	w5, w9, 5
	cmp	w1, w5
	ble	.L11
	ubfiz	x4, x9, 6, 32
	mov	w11, 11
	add	x7, x0, x4
	sub	w8, w1, w5
	neg	x7, x7, lsr 1
	sub	w10, w8, #1
	and	w6, w7, 7
	add	w3, w6, 8
	cmp	w3, w11
	csel	w3, w3, w11, cs
	cmp	w3, w10
	bhi	.L24
	cbz	w6, .L25
	ldrh	w3, [x0, x4]
	cmp	w2, w3
	bls	.L26
	add	w4, w5, 1
	tst	x7, 6
	beq	.L45
	ubfiz	x4, x4, 1, 32
	ldrh	w3, [x0, x4]
	cmp	w2, w3
	bls	.L26
	cmp	w6, 2
	bls	.L94
	add	x4, x0, x4
	ldrh	w3, [x4, 2]
	cmp	w2, w3
	bls	.L26
	tbz	x7, 2, .L95
	ldrh	w3, [x4, 4]
	cmp	w2, w3
	bls	.L26
	cmp	w6, 4
	beq	.L96
	ldrh	w3, [x4, 6]
	cmp	w2, w3
	bls	.L26
	cmp	w6, 5
	beq	.L97
	ldrh	w3, [x4, 8]
	cmp	w2, w3
	bls	.L26
	cmp	w6, 7
	bne	.L98
	ldrh	w3, [x4, 10]
	cmp	w2, w3
	bls	.L26
	add	w5, w5, 7
.L25:
	add	w3, w6, w9, lsl 5
	sub	w8, w8, w6
	dup	v30.8h, w2
	lsr	w7, w8, 3
	mov	w4, 0
	add	x3, x0, x3, lsl 1
	add	x6, x3, w7, uxtw 4
	b	.L33
	.p2align 2,,3
.L32:
	add	w4, w4, 8
	cmp	x6, x3
	beq	.L99
.L33:
	ldr	q31, [x3]
	add	x3, x3, 16
	cmhs	v31.8h, v31.8h, v30.8h
	umaxp	v31.4s, v31.4s, v31.4s
	fmov	x9, d31
	cbz	x9, .L32
	add	w5, w5, w4
.L24:
	ubfiz	x4, x5, 1, 32
	ldrh	w3, [x0, x4]
	cmp	w2, w3
	bls	.L26
	add	w3, w5, 1
	cmp	w1, w3
	ble	.L11
	add	x0, x0, x4
	ldrh	w3, [x0, 2]
	cmp	w2, w3
	bls	.L26
	add	w3, w5, 2
	cmp	w1, w3
	ble	.L11
	ldrh	w3, [x0, 4]
	cmp	w2, w3
	bls	.L26
	add	w3, w5, 3
	cmp	w1, w3
	ble	.L11
	ldrh	w3, [x0, 6]
	cmp	w2, w3
	bls	.L26
	add	w3, w5, 4
	cmp	w1, w3
	ble	.L11
	ldrh	w3, [x0, 8]
	cmp	w2, w3
	bls	.L26
	add	w3, w5, 5
	cmp	w1, w3
	ble	.L11
	ldrh	w3, [x0, 10]
	cmp	w2, w3
	bls	.L26
	add	w3, w5, 6
	cmp	w1, w3
	ble	.L11
	ldrh	w3, [x0, 12]
	cmp	w2, w3
	bls	.L26
	add	w3, w5, 7
	cmp	w1, w3
	ble	.L11
	ldrh	w3, [x0, 14]
	cmp	w2, w3
	bls	.L26
	add	w3, w5, 8
	cmp	w1, w3
	ble	.L11
	ldrh	w3, [x0, 16]
	cmp	w2, w3
	bls	.L26
	add	w3, w5, 9
	cmp	w1, w3
	ble	.L11
	ldrh	w3, [x0, 18]
	cmp	w2, w3
	bls	.L26
	add	w3, w5, 10
	cmp	w1, w3
	ble	.L11
	ldrh	w3, [x0, 20]
	cmp	w2, w3
	bls	.L26
	add	w3, w5, 11
	cmp	w1, w3
	ble	.L11
	ldrh	w3, [x0, 22]
	cmp	w2, w3
	bls	.L26
	add	w3, w5, 12
	cmp	w1, w3
	ble	.L11
	ldrh	w3, [x0, 24]
	cmp	w2, w3
	bls	.L26
	add	w3, w5, 13
	cmp	w1, w3
	ble	.L11
	ldrh	w3, [x0, 26]
	cmp	w2, w3
	bls	.L26
	add	w3, w5, 14
	cmp	w1, w3
	ble	.L11
	ldrh	w3, [x0, 28]
	cmp	w2, w3
	bls	.L26
	add	w5, w5, 15
	cmp	w1, w5
	ble	.L11
	ldrh	w3, [x0, 30]
	cmp	w2, w3
	bhi	.L11
.L26:
	cmp	w2, w3
	cset	w0, eq
	ret
	.p2align 2,,3
.L93:
	lsl	w3, w3, 5
	add	x3, x0, w3, sxtw 1
	ld1	{v30.8h - v31.8h}, [x3], 32
	dup	v27.8h, w2
	ld1	{v28.8h - v29.8h}, [x3]
	cmeq	v31.8h, v27.8h, v31.8h
	cmeq	v30.8h, v27.8h, v30.8h
	cmeq	v29.8h, v29.8h, v27.8h
	cmeq	v28.8h, v28.8h, v27.8h
	orr	v30.16b, v31.16b, v30.16b
	orr	v28.16b, v29.16b, v28.16b
	orr	v30.16b, v28.16b, v30.16b
	umaxv	h30, v30.8h
	umov	w0, v30.h[0]
	tst	w0, 65535
	cset	w0, ne
	ret
	.p2align 2,,3
.L3:
	cmp	w1, 7
	bgt	.L13
	cmp	w1, 0
	ble	.L11
	ldrh	w3, [x0]
	cmp	w2, w3
	bls	.L26
	cmp	w1, 1
	beq	.L11
	ldrh	w3, [x0, 2]
	cmp	w2, w3
	bls	.L26
	cmp	w1, 2
	beq	.L11
	ldrh	w3, [x0, 4]
	cmp	w2, w3
	bls	.L26
	cmp	w1, 3
	beq	.L11
	ldrh	w3, [x0, 6]
	cmp	w2, w3
	bls	.L26
	cmp	w1, 4
	beq	.L11
	ldrh	w3, [x0, 8]
	cmp	w2, w3
	bls	.L26
	cmp	w1, 5
	beq	.L11
	ldrh	w3, [x0, 10]
	cmp	w2, w3
	bls	.L26
	cmp	w1, 7
	bne	.L11
	ldrh	w3, [x0, 12]
	cmp	w2, w3
	bls	.L26
	mov	w0, 0
	b	.L88
	.p2align 2,,3
.L13:
	dup	v26.8h, w2
	ldr	q25, [x0]
	cmeq	v25.8h, v26.8h, v25.8h
	umaxv	h25, v25.8h
	umov	w3, v25.h[0]
	tst	w3, 65535
	bne	.L4
	cmp	w1, 8
	beq	.L11
	ldrh	w3, [x0, 16]
	cmp	w2, w3
	bls	.L26
	cmp	w1, 9
	beq	.L11
	ldrh	w3, [x0, 18]
	cmp	w2, w3
	bls	.L26
	cmp	w1, 10
	beq	.L11
	ldrh	w3, [x0, 20]
	cmp	w2, w3
	bls	.L26
	cmp	w1, 11
	beq	.L11
	ldrh	w3, [x0, 22]
	cmp	w2, w3
	bls	.L26
	cmp	w1, 12
	beq	.L11
	ldrh	w3, [x0, 24]
	cmp	w2, w3
	bls	.L26
	cmp	w1, 13
	beq	.L11
	ldrh	w3, [x0, 26]
	cmp	w2, w3
	bls	.L26
	cmp	w1, 15
	bne	.L11
	ldrh	w3, [x0, 28]
	cmp	w2, w3
	bls	.L26
	mov	w0, 0
	b	.L88
	.p2align 2,,3
.L4:
	mov	w0, 1
	ret
	.p2align 2,,3
.L99:
	lsl	w7, w7, 3
	cmp	w7, w8
	beq	.L11
	add	w5, w5, w7
	b	.L24
.L10:
	lsl	w4, w5, 1
	ldrh	w3, [x0, x4]
	cmp	w2, w3
	bls	.L26
	add	w4, w4, 2
	ldrh	w3, [x0, x4]
	cmp	w2, w3
	bhi	.L34
	b	.L26
.L36:
	mov	w5, 16
	b	.L8
.L35:
	mov	w5, 16
	b	.L7
.L45:
	mov	w5, w4
	b	.L25
.L94:
	add	w5, w5, 2
	b	.L25
.L95:
	add	w5, w5, 3
	b	.L25
.L96:
	add	w5, w5, 4
	b	.L25
.L97:
	add	w5, w5, 5
	b	.L25
.L37:
	mov	w5, 17
	b	.L8
.L38:
	mov	w5, 18
	b	.L8
.L98:
	add	w5, w5, 6
	b	.L25
.L39:
	mov	w5, 19
	b	.L8
.L40:
	mov	w5, 20
	b	.L8
.L41:
	mov	w5, 21
	b	.L8
.L42:
	mov	w5, 22
	b	.L8
	.cfi_endproc
.LFE3139:
	.size	_ZN7ab_base13simd_quad_pi5EPKtit, .-_ZN7ab_base13simd_quad_pi5EPKtit
	.align	2
	.p2align 5,,15
	.global	_ZN7ab_base19simd_quad_pi5_spineEPKtS1_it
	.type	_ZN7ab_base19simd_quad_pi5_spineEPKtS1_it, %function
_ZN7ab_base19simd_quad_pi5_spineEPKtS1_it:
.LFB3140:
	.cfi_startproc
	and	w3, w3, 65535
	cmp	w2, 31
	bgt	.L101
	cmp	w2, 15
	ble	.L102
	dup	v30.8h, w3
	ld1	{v28.8h - v29.8h}, [x0]
	cmeq	v31.8h, v30.8h, v28.8h
	cmeq	v29.8h, v30.8h, v29.8h
	orr	v31.16b, v31.16b, v29.16b
	umaxv	h31, v31.8h
	umov	w1, v31.h[0]
	tst	w1, 65535
	bne	.L103
	cmp	w2, 16
	beq	.L110
	add	x4, x0, 32
	mov	w7, 11
	neg	x4, x4, lsr 1
	sub	w5, w2, #17
	and	w6, w4, 7
	add	w1, w6, 8
	cmp	w1, w7
	csel	w1, w1, w7, cs
	cmp	w1, w5
	bhi	.L150
	cbz	w6, .L151
	ldrh	w1, [x0, 32]
	cmp	w3, w1
	bls	.L140
	tst	x4, 6
	beq	.L152
	ldrh	w1, [x0, 34]
	cmp	w3, w1
	bls	.L140
	cmp	w6, 2
	bls	.L153
	ldrh	w1, [x0, 36]
	cmp	w3, w1
	bls	.L140
	tbz	x4, 2, .L154
	ldrh	w1, [x0, 38]
	cmp	w3, w1
	bls	.L140
	cmp	w6, 4
	beq	.L155
	ldrh	w1, [x0, 40]
	cmp	w3, w1
	bls	.L140
	cmp	w6, 5
	beq	.L156
	ldrh	w1, [x0, 42]
	cmp	w3, w1
	bls	.L140
	cmp	w6, 7
	bne	.L157
	ldrh	w1, [x0, 44]
	cmp	w3, w1
	bls	.L140
	mov	w5, 23
.L107:
	add	w1, w6, 16
	ubfiz	x1, x1, 1, 6
	ldr	q31, [x0, x1]
	cmhs	v31.8h, v31.8h, v30.8h
	umaxp	v31.4s, v31.4s, v31.4s
	fmov	x1, d31
	cbnz	x1, .L109
	sub	w1, w2, #24
	cmp	w1, w6
	beq	.L110
	add	w5, w5, 8
.L106:
	lsl	w4, w5, 1
	ldrh	w1, [x0, x4]
	cmp	w3, w1
	bls	.L140
	add	w1, w5, 1
	cmp	w2, w1
	ble	.L110
	add	w4, w4, 2
	ldrh	w1, [x0, x4]
	cmp	w1, w3
	bcs	.L140
	add	w1, w5, 2
	cmp	w2, w1
	ble	.L110
.L149:
	add	x4, x0, x4
	ldrh	w1, [x4, 2]
	cmp	w3, w1
	bls	.L140
	add	w1, w5, 3
	cmp	w2, w1
	ble	.L110
	ldrh	w1, [x4, 4]
	cmp	w3, w1
	bls	.L140
	add	w1, w5, 4
	cmp	w2, w1
	ble	.L110
	ldrh	w1, [x4, 6]
	cmp	w3, w1
	bls	.L140
	add	w1, w5, 5
	cmp	w2, w1
	ble	.L110
	ldrh	w1, [x4, 8]
	cmp	w3, w1
	bls	.L140
	add	w1, w5, 6
	cmp	w1, w2
	bge	.L110
	ldrh	w1, [x4, 10]
	cmp	w3, w1
	bls	.L140
	add	w1, w5, 7
	cmp	w1, w2
	bge	.L110
	ldrh	w1, [x4, 12]
	cmp	w3, w1
	bls	.L140
	add	w1, w5, 8
	cmp	w2, w1
	ble	.L110
	ldrh	w1, [x4, 14]
	cmp	w3, w1
	bls	.L140
	add	w1, w5, 9
	cmp	w2, w1
	ble	.L110
	ldrh	w1, [x4, 16]
	cmp	w3, w1
	bls	.L140
	add	w1, w5, 10
	cmp	w2, w1
	ble	.L110
	ldrh	w1, [x4, 18]
	cmp	w3, w1
	bls	.L140
	add	w1, w5, 11
	cmp	w1, w2
	bge	.L110
	ldrh	w1, [x4, 20]
	cmp	w3, w1
	bls	.L140
	add	w1, w5, 12
	cmp	w2, w1
	ble	.L110
	ldrh	w1, [x4, 22]
	cmp	w3, w1
	bls	.L140
	add	w1, w5, 13
	cmp	w2, w1
	ble	.L110
	ldrh	w1, [x4, 24]
	cmp	w3, w1
	bls	.L140
	add	w5, w5, 14
	cmp	w2, w5
	ble	.L110
	ldrh	w1, [x0, 60]
	cmp	w3, w1
	bls	.L140
	.p2align 5,,15
.L110:
	mov	w0, 0
.L252:
	ret
	.p2align 2,,3
.L101:
	asr	w12, w2, 5
	cmp	w2, 127
	ble	.L259
	prfm	PLDL1KEEP, [x1]
	mov	w5, 0
	mov	w4, w12
	.p2align 5,,15
.L132:
	asr	w6, w4, 2
	add	w7, w5, w6, lsl 1
	add	w8, w6, w5
	ldrh	w10, [x1, w8, sxtw 1]
	add	w11, w6, w6, lsl 1
	add	w8, w7, w6
	ldrh	w9, [x1, w7, sxtw 1]
	sub	w4, w4, w11
	ldrh	w8, [x1, w8, sxtw 1]
	cmp	w10, w3
	cset	w7, cc
	cmp	w9, w3
	cinc	w7, w7, cc
	cmp	w8, w3
	cinc	w7, w7, cc
	madd	w5, w7, w6, w5
	cmp	w4, 3
	bgt	.L132
	cmp	w4, 1
	ble	.L260
	.p2align 5,,15
.L135:
	asr	w7, w4, 1
	add	w6, w7, w5
	sub	w4, w4, w7
	ldrh	w7, [x1, w6, sxtw 1]
	cmp	w7, w3
	csel	w5, w5, w6, cs
	cmp	w4, 1
	bgt	.L135
.L260:
	ldrh	w1, [x1, w5, sxtw 1]
	cmp	w1, w3
	cinc	w5, w5, cc
	cmp	w5, w12
	blt	.L261
	lsl	w5, w12, 5
	cmp	w2, w5
	ble	.L110
	ubfiz	x4, x12, 6, 32
	mov	w10, 11
	add	x7, x0, x4
	sub	w8, w2, w5
	neg	x7, x7, lsr 1
	sub	w9, w8, #1
	and	w6, w7, 7
	add	w1, w6, 8
	cmp	w1, w10
	csel	w1, w1, w10, cs
	cmp	w9, w1
	bcc	.L138
	cbz	w6, .L139
	ldrh	w1, [x0, x4]
	cmp	w3, w1
	bls	.L140
	add	w4, w5, 1
	tst	x7, 6
	beq	.L172
	ubfiz	x4, x4, 1, 32
	ldrh	w1, [x0, x4]
	cmp	w3, w1
	bls	.L140
	cmp	w6, 2
	bls	.L262
	add	x4, x0, x4
	ldrh	w1, [x4, 2]
	cmp	w3, w1
	bls	.L140
	tbz	x7, 2, .L263
	ldrh	w1, [x4, 4]
	cmp	w3, w1
	bls	.L140
	cmp	w6, 4
	beq	.L264
	ldrh	w1, [x4, 6]
	cmp	w3, w1
	bls	.L140
	cmp	w6, 5
	beq	.L265
	ldrh	w1, [x4, 8]
	cmp	w3, w1
	bls	.L140
	cmp	w6, 7
	bne	.L266
	ldrh	w1, [x4, 10]
	cmp	w3, w1
	bls	.L140
	add	w5, w5, 7
.L139:
	add	w1, w6, w12, lsl 5
	sub	w8, w8, w6
	dup	v30.8h, w3
	mov	w4, 0
	and	w6, w8, -8
	add	x1, x0, x1, lsl 1
	b	.L147
	.p2align 2,,3
.L146:
	add	w4, w4, 8
	cmp	w6, w4
	beq	.L267
.L147:
	ldr	q31, [x1]
	add	x1, x1, 16
	cmhs	v31.8h, v31.8h, v30.8h
	umaxp	v31.4s, v31.4s, v31.4s
	fmov	x7, d31
	cbz	x7, .L146
	add	w5, w5, w4
.L138:
	ubfiz	x4, x5, 1, 32
	ldrh	w1, [x0, x4]
	cmp	w3, w1
	bls	.L140
	add	w1, w5, 1
	cmp	w2, w1
	ble	.L110
	add	x0, x0, x4
	ldrh	w1, [x0, 2]
	cmp	w3, w1
	bls	.L140
	add	w1, w5, 2
	cmp	w2, w1
	ble	.L110
	ldrh	w1, [x0, 4]
	cmp	w3, w1
	bls	.L140
	add	w1, w5, 3
	cmp	w2, w1
	ble	.L110
	ldrh	w1, [x0, 6]
	cmp	w3, w1
	bls	.L140
	add	w1, w5, 4
	cmp	w2, w1
	ble	.L110
	ldrh	w1, [x0, 8]
	cmp	w3, w1
	bls	.L140
	add	w1, w5, 5
	cmp	w2, w1
	ble	.L110
	ldrh	w1, [x0, 10]
	cmp	w3, w1
	bls	.L140
	add	w1, w5, 6
	cmp	w2, w1
	ble	.L110
	ldrh	w1, [x0, 12]
	cmp	w3, w1
	bls	.L140
	add	w1, w5, 7
	cmp	w2, w1
	ble	.L110
	ldrh	w1, [x0, 14]
	cmp	w3, w1
	bls	.L140
	add	w1, w5, 8
	cmp	w2, w1
	ble	.L110
	ldrh	w1, [x0, 16]
	cmp	w3, w1
	bls	.L140
	add	w1, w5, 9
	cmp	w2, w1
	ble	.L110
	ldrh	w1, [x0, 18]
	cmp	w3, w1
	bls	.L140
	add	w1, w5, 10
	cmp	w2, w1
	ble	.L110
	ldrh	w1, [x0, 20]
	cmp	w3, w1
	bls	.L140
	add	w1, w5, 11
	cmp	w2, w1
	ble	.L110
	ldrh	w1, [x0, 22]
	cmp	w3, w1
	bls	.L140
	add	w1, w5, 12
	cmp	w2, w1
	ble	.L110
	ldrh	w1, [x0, 24]
	cmp	w3, w1
	bls	.L140
	add	w1, w5, 13
	cmp	w2, w1
	ble	.L110
	ldrh	w1, [x0, 26]
	cmp	w3, w1
	bls	.L140
	add	w1, w5, 14
	cmp	w2, w1
	ble	.L110
	ldrh	w1, [x0, 28]
	cmp	w3, w1
	bls	.L140
	add	w5, w5, 15
	cmp	w2, w5
	ble	.L110
.L255:
	ldrh	w1, [x0, 30]
	cmp	w3, w1
	bhi	.L110
.L140:
	cmp	w3, w1
	cset	w0, eq
	ret
	.p2align 2,,3
.L102:
	cmp	w2, 7
	bgt	.L112
	cmp	w2, 0
	ble	.L110
	ldrh	w1, [x0]
	cmp	w3, w1
	bls	.L140
	cmp	w2, 1
	beq	.L110
	ldrh	w1, [x0, 2]
	cmp	w3, w1
	bls	.L140
	cmp	w2, 2
	beq	.L110
	ldrh	w1, [x0, 4]
	cmp	w3, w1
	bls	.L140
	cmp	w2, 3
	beq	.L110
	ldrh	w1, [x0, 6]
	cmp	w3, w1
	bls	.L140
	cmp	w2, 4
	beq	.L110
	ldrh	w1, [x0, 8]
	cmp	w3, w1
	bls	.L140
	cmp	w2, 5
	beq	.L110
	ldrh	w1, [x0, 10]
	cmp	w3, w1
	bls	.L140
	cmp	w2, 7
	bne	.L110
	ldrh	w1, [x0, 12]
	cmp	w3, w1
	bls	.L140
	mov	w0, 0
	b	.L252
	.p2align 2,,3
.L261:
	lsl	w5, w5, 5
	add	x5, x0, w5, sxtw 1
	ld1	{v30.8h - v31.8h}, [x5], 32
	dup	v27.8h, w3
	ld1	{v28.8h - v29.8h}, [x5]
	cmeq	v31.8h, v27.8h, v31.8h
	cmeq	v30.8h, v27.8h, v30.8h
	cmeq	v29.8h, v29.8h, v27.8h
	cmeq	v28.8h, v28.8h, v27.8h
	orr	v30.16b, v31.16b, v30.16b
	orr	v28.16b, v29.16b, v28.16b
	orr	v30.16b, v28.16b, v30.16b
	umaxv	h30, v30.8h
	umov	w0, v30.h[0]
	tst	w0, 65535
	cset	w0, ne
	ret
	.p2align 2,,3
.L259:
	cmp	w12, 1
	beq	.L117
	mov	w5, 0
	mov	w4, w12
	.p2align 5,,15
.L119:
	asr	w1, w4, 1
	add	w6, w1, w5
	sub	w4, w4, w1
	add	w1, w6, 1
	sbfiz	x1, x1, 5, 32
	sub	x1, x1, #1
	ldrh	w1, [x0, x1, lsl 1]
	cmp	w1, w3
	csel	w5, w5, w6, cs
	cmp	w4, 1
	bgt	.L119
	add	w1, w5, 1
	sbfiz	x4, x1, 5, 32
	sub	x4, x4, #1
	ldrh	w4, [x0, x4, lsl 1]
	cmp	w4, w3
	csel	w1, w1, w5, cc
	cmp	w12, w1
	bgt	.L148
.L121:
	lsl	w4, w12, 5
	cmp	w2, w4
	ble	.L110
	ubfiz	x5, x12, 6, 32
	mov	w10, 11
	add	x7, x0, x5
	sub	w8, w2, w4
	neg	x7, x7, lsr 1
	sub	w9, w8, #1
	and	w6, w7, 7
	add	w1, w6, 8
	cmp	w1, w10
	csel	w1, w1, w10, cs
	cmp	w1, w9
	bhi	.L122
	cbz	w6, .L123
	ldrh	w1, [x0, x5]
	cmp	w3, w1
	bls	.L140
	add	w5, w4, 1
	tst	x7, 6
	beq	.L159
	ubfiz	x5, x5, 1, 32
	ldrh	w1, [x0, x5]
	cmp	w3, w1
	bls	.L140
	cmp	w6, 2
	bls	.L268
	add	x5, x0, x5
	ldrh	w1, [x5, 2]
	cmp	w3, w1
	bls	.L140
	tbz	x7, 2, .L269
	ldrh	w1, [x5, 4]
	cmp	w3, w1
	bls	.L140
	cmp	w6, 4
	beq	.L270
	ldrh	w1, [x5, 6]
	cmp	w3, w1
	bls	.L140
	cmp	w6, 5
	beq	.L271
	ldrh	w1, [x5, 8]
	cmp	w3, w1
	bls	.L140
	cmp	w6, 7
	bne	.L272
	ldrh	w1, [x5, 10]
	cmp	w3, w1
	bls	.L140
	add	w4, w4, 7
.L123:
	add	w1, w6, w12, lsl 5
	dup	v31.8h, w3
	lsl	x5, x1, 1
	add	x1, x0, x1, lsl 1
	ldr	q30, [x0, x5]
	cmhs	v30.8h, v30.8h, v31.8h
	umaxp	v30.4s, v30.4s, v30.4s
	fmov	x5, d30
	cbnz	x5, .L160
	sub	w8, w8, w6
	lsr	w5, w8, 3
	cmp	w5, 1
	beq	.L131
	ldr	q30, [x1, 16]
	cmhs	v30.8h, v30.8h, v31.8h
	umaxp	v30.4s, v30.4s, v30.4s
	fmov	x6, d30
	cbnz	x6, .L161
	cmp	w5, 2
	beq	.L131
	ldr	q30, [x1, 32]
	cmhs	v30.8h, v30.8h, v31.8h
	umaxp	v30.4s, v30.4s, v30.4s
	fmov	x6, d30
	cbnz	x6, .L162
	cmp	w5, 3
	beq	.L131
	ldr	q30, [x1, 48]
	cmhs	v30.8h, v30.8h, v31.8h
	umaxp	v30.4s, v30.4s, v30.4s
	fmov	x6, d30
	cbnz	x6, .L163
	cmp	w5, 4
	beq	.L131
	ldr	q30, [x1, 64]
	cmhs	v30.8h, v30.8h, v31.8h
	umaxp	v30.4s, v30.4s, v30.4s
	fmov	x6, d30
	cbnz	x6, .L164
	cmp	w5, 5
	beq	.L131
	ldr	q30, [x1, 80]
	cmhs	v30.8h, v30.8h, v31.8h
	umaxp	v30.4s, v30.4s, v30.4s
	fmov	x6, d30
	cbnz	x6, .L165
	cmp	w5, 6
	beq	.L131
	ldr	q30, [x1, 96]
	cmhs	v30.8h, v30.8h, v31.8h
	umaxp	v30.4s, v30.4s, v30.4s
	fmov	x6, d30
	cbnz	x6, .L166
	cmp	w5, 7
	beq	.L131
	ldr	q30, [x1, 112]
	cmhs	v30.8h, v30.8h, v31.8h
	umaxp	v30.4s, v30.4s, v30.4s
	fmov	x6, d30
	cbnz	x6, .L167
	cmp	w5, 8
	beq	.L131
	ldr	q30, [x1, 128]
	cmhs	v30.8h, v30.8h, v31.8h
	umaxp	v30.4s, v30.4s, v30.4s
	fmov	x6, d30
	cbnz	x6, .L168
	cmp	w5, 9
	beq	.L131
	ldr	q30, [x1, 144]
	cmhs	v30.8h, v30.8h, v31.8h
	umaxp	v30.4s, v30.4s, v30.4s
	fmov	x6, d30
	cbnz	x6, .L169
	cmp	w5, 10
	beq	.L131
	ldr	q30, [x1, 160]
	cmhs	v30.8h, v30.8h, v31.8h
	umaxp	v30.4s, v30.4s, v30.4s
	fmov	x6, d30
	cbnz	x6, .L170
	cmp	w5, 11
	beq	.L131
	ldr	q30, [x1, 176]
	cmhs	v31.8h, v30.8h, v31.8h
	umaxp	v31.4s, v31.4s, v31.4s
	fmov	x1, d31
	cbnz	x1, .L273
.L131:
	lsl	w5, w5, 3
	cmp	w5, w8
	beq	.L110
	add	w4, w4, w5
.L122:
	ubfiz	x5, x4, 1, 32
	ldrh	w1, [x0, x5]
	cmp	w3, w1
	bls	.L140
	add	w1, w4, 1
	cmp	w2, w1
	ble	.L110
	add	x0, x0, x5
	ldrh	w1, [x0, 2]
	cmp	w3, w1
	bls	.L140
	add	w1, w4, 2
	cmp	w2, w1
	ble	.L110
	ldrh	w1, [x0, 4]
	cmp	w3, w1
	bls	.L140
	add	w1, w4, 3
	cmp	w2, w1
	ble	.L110
	ldrh	w1, [x0, 6]
	cmp	w3, w1
	bls	.L140
	add	w1, w4, 4
	cmp	w2, w1
	ble	.L110
	ldrh	w1, [x0, 8]
	cmp	w3, w1
	bls	.L140
	add	w1, w4, 5
	cmp	w2, w1
	ble	.L110
	ldrh	w1, [x0, 10]
	cmp	w3, w1
	bls	.L140
	add	w1, w4, 6
	cmp	w2, w1
	ble	.L110
	ldrh	w1, [x0, 12]
	cmp	w3, w1
	bls	.L140
	add	w1, w4, 7
	cmp	w2, w1
	ble	.L110
	ldrh	w1, [x0, 14]
	cmp	w3, w1
	bls	.L140
	add	w1, w4, 8
	cmp	w2, w1
	ble	.L110
	ldrh	w1, [x0, 16]
	cmp	w3, w1
	bls	.L140
	add	w1, w4, 9
	cmp	w2, w1
	ble	.L110
	ldrh	w1, [x0, 18]
	cmp	w3, w1
	bls	.L140
	add	w1, w4, 10
	cmp	w2, w1
	ble	.L110
	ldrh	w1, [x0, 20]
	cmp	w3, w1
	bls	.L140
	add	w1, w4, 11
	cmp	w2, w1
	ble	.L110
	ldrh	w1, [x0, 22]
	cmp	w3, w1
	bls	.L140
	add	w1, w4, 12
	cmp	w2, w1
	ble	.L110
	ldrh	w1, [x0, 24]
	cmp	w3, w1
	bls	.L140
	add	w1, w4, 13
	cmp	w2, w1
	ble	.L110
	ldrh	w1, [x0, 26]
	cmp	w3, w1
	bls	.L140
	add	w1, w4, 14
	cmp	w2, w1
	ble	.L110
	ldrh	w1, [x0, 28]
	cmp	w3, w1
	bls	.L140
	add	w4, w4, 15
	cmp	w2, w4
	bgt	.L255
	mov	w0, 0
	b	.L252
	.p2align 2,,3
.L112:
	dup	v21.8h, w3
	ldr	q20, [x0]
	cmeq	v20.8h, v21.8h, v20.8h
	umaxv	h20, v20.8h
	umov	w1, v20.h[0]
	tst	w1, 65535
	bne	.L103
	cmp	w2, 8
	beq	.L110
	ldrh	w1, [x0, 16]
	cmp	w3, w1
	bls	.L140
	cmp	w2, 9
	beq	.L110
	ldrh	w1, [x0, 18]
	cmp	w3, w1
	bls	.L140
	cmp	w2, 10
	beq	.L110
	ldrh	w1, [x0, 20]
	cmp	w3, w1
	bls	.L140
	cmp	w2, 11
	beq	.L110
	ldrh	w1, [x0, 22]
	cmp	w3, w1
	bls	.L140
	cmp	w2, 12
	beq	.L110
	ldrh	w1, [x0, 24]
	cmp	w3, w1
	bls	.L140
	cmp	w2, 13
	beq	.L110
	ldrh	w1, [x0, 26]
	cmp	w3, w1
	bls	.L140
	cmp	w2, 15
	bne	.L110
	ldrh	w1, [x0, 28]
	cmp	w3, w1
	bls	.L140
	mov	w0, 0
	b	.L252
	.p2align 2,,3
.L103:
	mov	w0, 1
	ret
.L109:
	lsl	w4, w5, 1
	ldrh	w1, [x0, x4]
	cmp	w3, w1
	bls	.L140
	add	w4, w4, 2
	ldrh	w1, [x0, x4]
	cmp	w3, w1
	bhi	.L149
	b	.L140
	.p2align 2,,3
.L267:
	cmp	w8, w6
	beq	.L110
	add	w5, w5, w6
	b	.L138
.L117:
	ldrh	w1, [x0, 62]
	cmp	w1, w3
	bcc	.L121
	mov	w1, 0
.L148:
	lsl	w1, w1, 5
	add	x0, x0, w1, sxtw 1
	ld1	{v25.8h - v26.8h}, [x0], 32
	dup	v22.8h, w3
	ld1	{v23.8h - v24.8h}, [x0]
	cmeq	v25.8h, v22.8h, v25.8h
	cmeq	v26.8h, v22.8h, v26.8h
	cmeq	v23.8h, v23.8h, v22.8h
	cmeq	v24.8h, v24.8h, v22.8h
	orr	v26.16b, v25.16b, v26.16b
	orr	v24.16b, v23.16b, v24.16b
	orr	v26.16b, v24.16b, v26.16b
	umaxv	h26, v26.8h
	umov	w0, v26.h[0]
	tst	w0, 65535
	cset	w0, ne
	ret
.L151:
	mov	w5, 16
	b	.L107
.L150:
	mov	w5, 16
	b	.L106
.L172:
	mov	w5, w4
	b	.L139
.L152:
	mov	w5, 17
	b	.L107
.L262:
	add	w5, w5, 2
	b	.L139
.L153:
	mov	w5, 18
	b	.L107
.L154:
	mov	w5, 19
	b	.L107
.L263:
	add	w5, w5, 3
	b	.L139
.L155:
	mov	w5, 20
	b	.L107
.L264:
	add	w5, w5, 4
	b	.L139
.L265:
	add	w5, w5, 5
	b	.L139
.L156:
	mov	w5, 21
	b	.L107
.L266:
	add	w5, w5, 6
	b	.L139
.L157:
	mov	w5, 22
	b	.L107
.L160:
	mov	w1, 0
	add	w4, w4, w1
	b	.L122
.L161:
	mov	w1, 8
	add	w4, w4, w1
	b	.L122
.L162:
	mov	w1, 16
	add	w4, w4, w1
	b	.L122
.L163:
	mov	w1, 24
	add	w4, w4, w1
	b	.L122
.L268:
	add	w4, w4, 2
	b	.L123
.L159:
	mov	w4, w5
	b	.L123
.L165:
	mov	w1, 40
	add	w4, w4, w1
	b	.L122
.L164:
	mov	w1, 32
	add	w4, w4, w1
	b	.L122
.L270:
	add	w4, w4, 4
	b	.L123
.L269:
	add	w4, w4, 3
	b	.L123
.L168:
	mov	w1, 64
	add	w4, w4, w1
	b	.L122
.L167:
	mov	w1, 56
	add	w4, w4, w1
	b	.L122
.L166:
	mov	w1, 48
	add	w4, w4, w1
	b	.L122
.L272:
	add	w4, w4, 6
	b	.L123
.L271:
	add	w4, w4, 5
	b	.L123
.L273:
	mov	w1, 88
	add	w4, w4, w1
	b	.L122
.L170:
	mov	w1, 80
	add	w4, w4, w1
	b	.L122
.L169:
	mov	w1, 72
	add	w4, w4, w1
	b	.L122
	.cfi_endproc
.LFE3140:
	.size	_ZN7ab_base19simd_quad_pi5_spineEPKtS1_it, .-_ZN7ab_base19simd_quad_pi5_spineEPKtS1_it
	.align	2
	.p2align 5,,15
	.global	_ZN7ab_base25simd_quad_pi5_build_spineEPKtiPt
	.type	_ZN7ab_base25simd_quad_pi5_build_spineEPKtiPt, %function
_ZN7ab_base25simd_quad_pi5_build_spineEPKtiPt:
.LFB3141:
	.cfi_startproc
	cmp	w1, 31
	ble	.L274
	mov	w3, 0
	asr	w1, w1, 5
	add	x0, x0, 62
	.p2align 5,,15
.L276:
	ubfiz	x4, x3, 6, 32
	ldrh	w4, [x0, x4]
	strh	w4, [x2, x3, lsl 1]
	add	x3, x3, 1
	cmp	w1, w3
	bgt	.L276
.L274:
	ret
	.cfi_endproc
.LFE3141:
	.size	_ZN7ab_base25simd_quad_pi5_build_spineEPKtiPt, .-_ZN7ab_base25simd_quad_pi5_build_spineEPKtiPt
	.align	2
	.p2align 5,,15
	.global	_ZN7ab_base23simd_quad_pi5_spine_256EPKtS1_t
	.type	_ZN7ab_base23simd_quad_pi5_spine_256EPKtS1_t, %function
_ZN7ab_base23simd_quad_pi5_spine_256EPKtS1_t:
.LFB3142:
	.cfi_startproc
	ldrh	w3, [x1, 4]
	and	w2, w2, 65535
	ldrh	w5, [x1, 8]
	ldrh	w4, [x1, 12]
	cmp	w3, w2
	cset	w3, cc
	prfm	PLDL1KEEP, [x1]
	cmp	w5, w2
	cinc	w3, w3, cc
	cmp	w4, w2
	cinc	w3, w3, cc
	ubfiz	x5, x3, 2, 3
	lsl	w4, w3, 1
	ldrh	w5, [x1, x5]
	add	w4, w4, 1
	ldrh	w1, [x1, w4, uxtw 1]
	cmp	w5, w2
	cset	w4, cc
	add	w3, w4, w3, lsl 1
	cmp	w1, w2
	cinc	w3, w3, cc
	cmp	w3, 8
	beq	.L280
	ubfiz	x3, x3, 6, 6
	dup	v27.8h, w2
	add	x0, x0, x3
	ld1	{v30.8h - v31.8h}, [x0], 32
	ld1	{v28.8h - v29.8h}, [x0]
	cmeq	v31.8h, v27.8h, v31.8h
	cmeq	v30.8h, v27.8h, v30.8h
	orr	v30.16b, v31.16b, v30.16b
	cmeq	v28.8h, v28.8h, v27.8h
	cmeq	v29.8h, v29.8h, v27.8h
	orr	v29.16b, v28.16b, v29.16b
	orr	v30.16b, v29.16b, v30.16b
	umaxv	h30, v30.8h
	umov	w0, v30.h[0]
	tst	w0, 65535
	cset	w0, ne
	ret
	.p2align 2,,3
.L280:
	mov	w0, 0
	ret
	.cfi_endproc
.LFE3142:
	.size	_ZN7ab_base23simd_quad_pi5_spine_256EPKtS1_t, .-_ZN7ab_base23simd_quad_pi5_spine_256EPKtS1_t
	.align	2
	.p2align 5,,15
	.global	_ZN7ab_base23simd_quad_pi5_spine_512EPKtS1_t
	.type	_ZN7ab_base23simd_quad_pi5_spine_512EPKtS1_t, %function
_ZN7ab_base23simd_quad_pi5_spine_512EPKtS1_t:
.LFB3143:
	.cfi_startproc
	ldrh	w4, [x1, 8]
	and	w2, w2, 65535
	ldrh	w5, [x1, 16]
	ldrh	w3, [x1, 24]
	cmp	w4, w2
	cset	w4, cc
	prfm	PLDL1KEEP, [x1]
	cmp	w5, w2
	cinc	w4, w4, cc
	cmp	w3, w2
	cinc	w4, w4, cc
	lsl	w4, w4, 2
	add	w3, w4, 1
	ubfiz	x3, x3, 1, 6
	add	x5, x1, x3
	ldrh	w6, [x1, x3]
	ldrh	w3, [x5, 2]
	ldrh	w5, [x5, 4]
	cmp	w3, w2
	cset	w3, cc
	cmp	w6, w2
	cinc	w3, w3, cc
	cmp	w5, w2
	cinc	w3, w3, cc
	add	w3, w3, w4
	ubfiz	x4, x3, 1, 6
	ldrh	w1, [x1, x4]
	cmp	w1, w2
	bcs	.L282
	add	w3, w3, 1
	mov	w1, 0
	cmp	w3, 16
	beq	.L283
.L282:
	ubfiz	x3, x3, 6, 7
	dup	v27.8h, w2
	add	x0, x0, x3
	ld1	{v30.8h - v31.8h}, [x0], 32
	ld1	{v28.8h - v29.8h}, [x0]
	cmeq	v31.8h, v27.8h, v31.8h
	cmeq	v30.8h, v27.8h, v30.8h
	orr	v30.16b, v31.16b, v30.16b
	cmeq	v28.8h, v28.8h, v27.8h
	cmeq	v29.8h, v29.8h, v27.8h
	orr	v29.16b, v28.16b, v29.16b
	orr	v30.16b, v29.16b, v30.16b
	umaxv	h30, v30.8h
	umov	w0, v30.h[0]
	tst	w0, 65535
	cset	w1, ne
.L283:
	mov	w0, w1
	ret
	.cfi_endproc
.LFE3143:
	.size	_ZN7ab_base23simd_quad_pi5_spine_512EPKtS1_t, .-_ZN7ab_base23simd_quad_pi5_spine_512EPKtS1_t
	.align	2
	.p2align 5,,15
	.global	_ZN7ab_base24simd_quad_pi5_spine_1024EPKtS1_t
	.type	_ZN7ab_base24simd_quad_pi5_spine_1024EPKtS1_t, %function
_ZN7ab_base24simd_quad_pi5_spine_1024EPKtS1_t:
.LFB3144:
	.cfi_startproc
	ldrh	w4, [x1, 16]
	and	w2, w2, 65535
	ldrh	w5, [x1, 32]
	ldrh	w3, [x1, 48]
	cmp	w4, w2
	cset	w4, cc
	prfm	PLDL1KEEP, [x1]
	cmp	w5, w2
	cinc	w4, w4, cc
	cmp	w3, w2
	cinc	w4, w4, cc
	lsl	w4, w4, 3
	add	w5, w4, 2
	add	x3, x1, x5, lsl 1
	ldrh	w6, [x1, x5, lsl 1]
	ldrh	w7, [x3, 4]
	ldrh	w5, [x3, 8]
	cmp	w7, w2
	cset	w3, cc
	cmp	w6, w2
	cinc	w3, w3, cc
	cmp	w5, w2
	cinc	w3, w3, cc
	add	w3, w4, w3, lsl 1
	add	w4, w3, 1
	ldrh	w5, [x1, w3, uxtw 1]
	ubfiz	x4, x4, 1, 8
	ldrh	w1, [x1, x4]
	cmp	w5, w2
	cinc	w3, w3, cc
	cmp	w1, w2
	cinc	w3, w3, cc
	cmp	w3, 32
	beq	.L288
	ubfiz	x3, x3, 6, 9
	dup	v27.8h, w2
	add	x0, x0, x3
	ld1	{v30.8h - v31.8h}, [x0], 32
	ld1	{v28.8h - v29.8h}, [x0]
	cmeq	v31.8h, v27.8h, v31.8h
	cmeq	v30.8h, v27.8h, v30.8h
	orr	v30.16b, v31.16b, v30.16b
	cmeq	v28.8h, v28.8h, v27.8h
	cmeq	v29.8h, v29.8h, v27.8h
	orr	v29.16b, v28.16b, v29.16b
	orr	v30.16b, v29.16b, v30.16b
	umaxv	h30, v30.8h
	umov	w0, v30.h[0]
	tst	w0, 65535
	cset	w0, ne
	ret
	.p2align 2,,3
.L288:
	mov	w0, 0
	ret
	.cfi_endproc
.LFE3144:
	.size	_ZN7ab_base24simd_quad_pi5_spine_1024EPKtS1_t, .-_ZN7ab_base24simd_quad_pi5_spine_1024EPKtS1_t
	.align	2
	.p2align 5,,15
	.global	_ZN7ab_base24simd_quad_pi5_spine_2048EPKtS1_t
	.type	_ZN7ab_base24simd_quad_pi5_spine_2048EPKtS1_t, %function
_ZN7ab_base24simd_quad_pi5_spine_2048EPKtS1_t:
.LFB3145:
	.cfi_startproc
	ldrh	w3, [x1, 32]
	and	w2, w2, 65535
	ldrh	w5, [x1, 64]
	ldrh	w4, [x1, 96]
	cmp	w3, w2
	cset	w3, cc
	prfm	PLDL1KEEP, [x1]
	cmp	w5, w2
	cinc	w3, w3, cc
	cmp	w4, w2
	cinc	w3, w3, cc
	lsl	w3, w3, 4
	add	w5, w3, 4
	add	x4, x1, x5, lsl 1
	ldrh	w6, [x1, x5, lsl 1]
	ldrh	w7, [x4, 8]
	ldrh	w5, [x4, 16]
	cmp	w7, w2
	cset	w4, cc
	cmp	w6, w2
	cinc	w4, w4, cc
	cmp	w5, w2
	cinc	w4, w4, cc
	add	w4, w3, w4, lsl 2
	add	w3, w4, 1
	ubfiz	x3, x3, 1, 9
	add	x5, x1, x3
	ldrh	w6, [x1, x3]
	ldrh	w3, [x5, 2]
	ldrh	w5, [x5, 4]
	cmp	w3, w2
	cset	w3, cc
	cmp	w6, w2
	cinc	w3, w3, cc
	cmp	w5, w2
	cinc	w3, w3, cc
	add	w3, w3, w4
	ubfiz	x4, x3, 1, 9
	ldrh	w1, [x1, x4]
	cmp	w1, w2
	bcs	.L290
	add	w3, w3, 1
	mov	w1, 0
	cmp	w3, 64
	beq	.L291
.L290:
	ubfiz	x3, x3, 6, 10
	dup	v27.8h, w2
	add	x0, x0, x3
	ld1	{v30.8h - v31.8h}, [x0], 32
	ld1	{v28.8h - v29.8h}, [x0]
	cmeq	v31.8h, v27.8h, v31.8h
	cmeq	v30.8h, v27.8h, v30.8h
	orr	v30.16b, v31.16b, v30.16b
	cmeq	v28.8h, v28.8h, v27.8h
	cmeq	v29.8h, v29.8h, v27.8h
	orr	v29.16b, v28.16b, v29.16b
	orr	v30.16b, v29.16b, v30.16b
	umaxv	h30, v30.8h
	umov	w0, v30.h[0]
	tst	w0, 65535
	cset	w1, ne
.L291:
	mov	w0, w1
	ret
	.cfi_endproc
.LFE3145:
	.size	_ZN7ab_base24simd_quad_pi5_spine_2048EPKtS1_t, .-_ZN7ab_base24simd_quad_pi5_spine_2048EPKtS1_t
	.align	2
	.p2align 5,,15
	.global	_ZN7ab_base24simd_quad_pi5_spine_4096EPKtS1_t
	.type	_ZN7ab_base24simd_quad_pi5_spine_4096EPKtS1_t, %function
_ZN7ab_base24simd_quad_pi5_spine_4096EPKtS1_t:
.LFB3146:
	.cfi_startproc
	ldrh	w3, [x1, 64]
	and	w2, w2, 65535
	ldrh	w5, [x1, 128]
	ldrh	w4, [x1, 192]
	cmp	w3, w2
	cset	w3, cc
	prfm	PLDL1KEEP, [x1]
	cmp	w5, w2
	cinc	w3, w3, cc
	cmp	w4, w2
	cinc	w3, w3, cc
	lsl	w3, w3, 5
	add	w5, w3, 8
	add	x4, x1, x5, lsl 1
	ldrh	w6, [x1, x5, lsl 1]
	ldrh	w7, [x4, 16]
	ldrh	w5, [x4, 32]
	cmp	w7, w2
	cset	w4, cc
	cmp	w6, w2
	cinc	w4, w4, cc
	cmp	w5, w2
	cinc	w4, w4, cc
	add	w4, w3, w4, lsl 3
	add	w5, w4, 2
	add	x3, x1, x5, lsl 1
	ldrh	w6, [x1, x5, lsl 1]
	ldrh	w7, [x3, 4]
	ldrh	w5, [x3, 8]
	cmp	w7, w2
	cset	w3, cc
	cmp	w6, w2
	cinc	w3, w3, cc
	cmp	w5, w2
	cinc	w3, w3, cc
	add	w3, w4, w3, lsl 1
	add	w4, w3, 1
	ldrh	w5, [x1, w3, uxtw 1]
	ubfiz	x4, x4, 1, 11
	ldrh	w1, [x1, x4]
	cmp	w5, w2
	cinc	w3, w3, cc
	cmp	w1, w2
	cinc	w3, w3, cc
	cmp	w3, 128
	beq	.L296
	ubfiz	x3, x3, 6, 12
	dup	v27.8h, w2
	add	x0, x0, x3
	ld1	{v30.8h - v31.8h}, [x0], 32
	ld1	{v28.8h - v29.8h}, [x0]
	cmeq	v31.8h, v27.8h, v31.8h
	cmeq	v30.8h, v27.8h, v30.8h
	orr	v30.16b, v31.16b, v30.16b
	cmeq	v28.8h, v28.8h, v27.8h
	cmeq	v29.8h, v29.8h, v27.8h
	orr	v29.16b, v28.16b, v29.16b
	orr	v30.16b, v29.16b, v30.16b
	umaxv	h30, v30.8h
	umov	w0, v30.h[0]
	tst	w0, 65535
	cset	w0, ne
	ret
	.p2align 2,,3
.L296:
	mov	w0, 0
	ret
	.cfi_endproc
.LFE3146:
	.size	_ZN7ab_base24simd_quad_pi5_spine_4096EPKtS1_t, .-_ZN7ab_base24simd_quad_pi5_spine_4096EPKtS1_t
	.ident	"GCC: (GNU) 17.0.0 20260704 (experimental)"
	.section	.note.GNU-stack,"",@progbits
