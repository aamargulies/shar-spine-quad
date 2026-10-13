	.arch armv8.2-a+dotprod+crc+fp16+rcpc
	.file	"ab_tu_cr.cpp"
	.text
	.align	2
	.p2align 5,,15
	.global	_ZN5ab_cr13simd_quad_pi5EPKtit
	.type	_ZN5ab_cr13simd_quad_pi5EPKtit, %function
_ZN5ab_cr13simd_quad_pi5EPKtit:
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
	beq	.L5
	add	x3, x0, 32
	mov	w7, 11
	neg	x3, x3, lsr 1
	sub	w6, w1, #17
	and	w4, w3, 7
	add	w5, w4, 8
	cmp	w5, w7
	csel	w5, w5, w7, cs
	cmp	w5, w6
	bhi	.L37
	cbz	w4, .L38
	ldrh	w5, [x0, 32]
	cmp	w2, w5
	beq	.L4
	bcc	.L5
	tst	x3, 6
	beq	.L39
	ldrh	w5, [x0, 34]
	cmp	w2, w5
	beq	.L4
	bcc	.L5
	cmp	w4, 2
	bls	.L40
	ldrh	w5, [x0, 36]
	cmp	w5, w2
	beq	.L4
	bhi	.L5
	tbz	x3, 2, .L41
	ldrh	w3, [x0, 38]
	cmp	w2, w3
	beq	.L4
	bcc	.L5
	cmp	w4, 4
	beq	.L42
	ldrh	w3, [x0, 40]
	cmp	w2, w3
	beq	.L4
	bcc	.L5
	cmp	w4, 5
	beq	.L43
	ldrh	w3, [x0, 42]
	cmp	w2, w3
	beq	.L4
	bcc	.L5
	cmp	w4, 7
	bne	.L44
	ldrh	w3, [x0, 44]
	cmp	w3, w2
	beq	.L4
	bhi	.L5
	mov	w3, 23
.L7:
	add	w5, w4, 16
	ubfiz	x5, x5, 1, 6
	ldr	q31, [x0, x5]
	cmeq	v29.8h, v31.8h, v30.8h
	umaxp	v29.4s, v29.4s, v29.4s
	fmov	x5, d29
	cbnz	x5, .L6
	cmhi	v31.8h, v31.8h, v30.8h
	umaxp	v31.4s, v31.4s, v31.4s
	fmov	x5, d31
	cbnz	x5, .L6
	sub	w5, w1, #24
	cmp	w5, w4
	beq	.L5
	add	w3, w3, 8
.L6:
	uxtw	x3, w3
	b	.L11
	.p2align 2,,3
.L95:
	bcc	.L5
	cmp	w1, w3
	ble	.L5
.L11:
	ldrh	w4, [x0, x3, lsl 1]
	add	x3, x3, 1
	cmp	w2, w4
	bne	.L95
	.p2align 5,,15
.L4:
	mov	w0, 1
.L15:
	ret
	.p2align 2,,3
.L2:
	asr	w9, w1, 5
	mov	w5, 0
	mov	w4, w9
	cmp	w1, 127
	ble	.L99
	.p2align 5,,15
.L17:
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
	bgt	.L17
	b	.L99
	.p2align 2,,3
.L20:
	asr	w3, w4, 1
	add	w6, w3, w5
	sub	w4, w4, w3
	add	w3, w6, 1
	sbfiz	x3, x3, 5, 32
	sub	x3, x3, #1
	ldrh	w3, [x0, x3, lsl 1]
	cmp	w3, w2
	csel	w5, w5, w6, cs
.L99:
	cmp	w4, 1
	bgt	.L20
	add	w3, w5, 1
	sbfiz	x4, x3, 5, 32
	sub	x4, x4, #1
	ldrh	w4, [x0, x4, lsl 1]
	cmp	w4, w2
	csel	w3, w3, w5, cc
	cmp	w3, w9
	blt	.L101
	lsl	w4, w9, 5
	cmp	w1, w4
	ble	.L5
	ubfiz	x8, x9, 6, 32
	mov	w11, 11
	add	x5, x0, x8
	sub	w7, w1, w4
	neg	x5, x5, lsr 1
	sub	w10, w7, #1
	and	w6, w5, 7
	add	w3, w6, 8
	cmp	w3, w11
	csel	w3, w3, w11, cs
	cmp	w3, w10
	bhi	.L23
	cbz	w6, .L24
	ldrh	w3, [x0, x8]
	cmp	w2, w3
	beq	.L4
	bcc	.L5
	add	w3, w4, 1
	tst	x5, 6
	beq	.L47
	ubfiz	x3, x3, 1, 32
	ldrh	w8, [x0, x3]
	cmp	w2, w8
	beq	.L4
	bcc	.L5
	cmp	w6, 2
	bls	.L102
	add	x3, x0, x3
	ldrh	w8, [x3, 2]
	cmp	w2, w8
	beq	.L4
	bcc	.L5
	tbz	x5, 2, .L103
	ldrh	w5, [x3, 4]
	cmp	w2, w5
	beq	.L4
	bcc	.L5
	cmp	w6, 4
	beq	.L104
	ldrh	w5, [x3, 6]
	cmp	w2, w5
	beq	.L4
	bcc	.L5
	cmp	w6, 5
	beq	.L105
	ldrh	w5, [x3, 8]
	cmp	w2, w5
	beq	.L4
	bcc	.L5
	cmp	w6, 7
	bne	.L106
	ldrh	w3, [x3, 10]
	cmp	w2, w3
	beq	.L4
	bcc	.L5
	add	w4, w4, 7
.L24:
	add	w3, w6, w9, lsl 5
	sub	w7, w7, w6
	dup	v29.8h, w2
	lsr	w8, w7, 3
	mov	w5, 0
	add	x3, x0, x3, lsl 1
	add	x6, x3, w8, uxtw 4
	b	.L33
	.p2align 2,,3
.L108:
	fmov	x9, d31
	cbnz	x9, .L31
	add	w5, w5, 8
	cmp	x6, x3
	beq	.L107
.L33:
	ldr	q31, [x3]
	add	x3, x3, 16
	cmeq	v30.8h, v31.8h, v29.8h
	cmhi	v31.8h, v31.8h, v29.8h
	umaxp	v30.4s, v30.4s, v30.4s
	umaxp	v31.4s, v31.4s, v31.4s
	fmov	x9, d30
	cbz	x9, .L108
.L31:
	add	w4, w4, w5
.L23:
	sxtw	x3, w4
	b	.L35
	.p2align 2,,3
.L97:
	bcc	.L5
	cmp	w1, w3
	ble	.L5
.L35:
	ldrh	w4, [x0, x3, lsl 1]
	add	x3, x3, 1
	cmp	w2, w4
	bne	.L97
	mov	w0, 1
	b	.L15
	.p2align 2,,3
.L101:
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
	ble	.L5
	ldrh	w3, [x0]
	cmp	w2, w3
	beq	.L4
	bcc	.L5
	cmp	w1, 1
	beq	.L5
	ldrh	w3, [x0, 2]
	cmp	w2, w3
	beq	.L4
	bcc	.L5
	cmp	w1, 2
	beq	.L5
	ldrh	w3, [x0, 4]
	cmp	w2, w3
	beq	.L4
	bcc	.L5
	cmp	w1, 3
	beq	.L5
	ldrh	w3, [x0, 6]
	cmp	w2, w3
	beq	.L4
	bcc	.L5
	cmp	w1, 4
	beq	.L5
	ldrh	w3, [x0, 8]
	cmp	w2, w3
	beq	.L4
	bcc	.L5
	cmp	w1, 5
	beq	.L5
	ldrh	w3, [x0, 10]
	cmp	w2, w3
	beq	.L4
	bcc	.L5
	cmp	w1, 7
	bne	.L5
	ldrh	w0, [x0, 12]
	cmp	w0, w2
	cset	w0, eq
	ret
	.p2align 2,,3
.L5:
	mov	w0, 0
	ret
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
	beq	.L5
	ldrh	w3, [x0, 16]
	cmp	w2, w3
	beq	.L4
	bcc	.L5
	cmp	w1, 9
	beq	.L5
	ldrh	w3, [x0, 18]
	cmp	w2, w3
	beq	.L4
	bcc	.L5
	cmp	w1, 10
	beq	.L5
	ldrh	w3, [x0, 20]
	cmp	w2, w3
	beq	.L4
	bcc	.L5
	cmp	w1, 11
	beq	.L5
	ldrh	w3, [x0, 22]
	cmp	w2, w3
	beq	.L4
	bcc	.L5
	cmp	w1, 12
	beq	.L5
	ldrh	w3, [x0, 24]
	cmp	w2, w3
	beq	.L4
	bcc	.L5
	cmp	w1, 13
	beq	.L5
	ldrh	w3, [x0, 26]
	cmp	w2, w3
	beq	.L4
	bcc	.L5
	cmp	w1, 15
	bne	.L5
	ldrh	w0, [x0, 28]
	cmp	w0, w2
	cset	w0, eq
	ret
	.p2align 2,,3
.L107:
	lsl	w8, w8, 3
	cmp	w8, w7
	beq	.L5
	add	w4, w4, w8
	b	.L23
.L38:
	mov	w3, 16
	b	.L7
.L37:
	mov	w3, 16
	b	.L6
.L47:
	mov	w4, w3
	b	.L24
.L102:
	add	w4, w4, 2
	b	.L24
.L103:
	add	w4, w4, 3
	b	.L24
.L104:
	add	w4, w4, 4
	b	.L24
.L39:
	mov	w3, 17
	b	.L7
.L105:
	add	w4, w4, 5
	b	.L24
.L40:
	mov	w3, 18
	b	.L7
.L106:
	add	w4, w4, 6
	b	.L24
.L42:
	mov	w3, 20
	b	.L7
.L41:
	mov	w3, 19
	b	.L7
.L43:
	mov	w3, 21
	b	.L7
.L44:
	mov	w3, 22
	b	.L7
	.cfi_endproc
.LFE3139:
	.size	_ZN5ab_cr13simd_quad_pi5EPKtit, .-_ZN5ab_cr13simd_quad_pi5EPKtit
	.align	2
	.p2align 5,,15
	.global	_ZN5ab_cr19simd_quad_pi5_spineEPKtS1_it
	.type	_ZN5ab_cr19simd_quad_pi5_spineEPKtS1_it, %function
_ZN5ab_cr19simd_quad_pi5_spineEPKtS1_it:
.LFB3140:
	.cfi_startproc
	and	w3, w3, 65535
	cmp	w2, 31
	bgt	.L110
	cmp	w2, 15
	ble	.L111
	dup	v30.8h, w3
	ld1	{v28.8h - v29.8h}, [x0]
	cmeq	v31.8h, v30.8h, v28.8h
	cmeq	v29.8h, v30.8h, v29.8h
	orr	v31.16b, v31.16b, v29.16b
	umaxv	h31, v31.8h
	umov	w1, v31.h[0]
	tst	w1, 65535
	bne	.L112
	cmp	w2, 16
	beq	.L113
	add	x1, x0, 32
	mov	w7, 11
	neg	x1, x1, lsr 1
	sub	w6, w2, #17
	and	w4, w1, 7
	add	w5, w4, 8
	cmp	w5, w7
	csel	w5, w5, w7, cs
	cmp	w5, w6
	bhi	.L164
	cbz	w4, .L165
	ldrh	w5, [x0, 32]
	cmp	w3, w5
	beq	.L112
	bcc	.L113
	tst	x1, 6
	beq	.L166
	ldrh	w5, [x0, 34]
	cmp	w3, w5
	beq	.L112
	bcc	.L113
	cmp	w4, 2
	bls	.L167
	ldrh	w5, [x0, 36]
	cmp	w3, w5
	beq	.L112
	bcc	.L113
	tbz	x1, 2, .L168
	ldrh	w1, [x0, 38]
	cmp	w1, w3
	beq	.L112
	bhi	.L113
	cmp	w4, 4
	beq	.L169
	ldrh	w1, [x0, 40]
	cmp	w3, w1
	beq	.L112
	bcc	.L113
	cmp	w4, 5
	beq	.L170
	ldrh	w1, [x0, 42]
	cmp	w3, w1
	beq	.L112
	bcc	.L113
	cmp	w4, 7
	bne	.L171
	ldrh	w1, [x0, 44]
	cmp	w3, w1
	beq	.L112
	bcc	.L113
	mov	w1, 23
.L115:
	add	w5, w4, 16
	ubfiz	x5, x5, 1, 6
	ldr	q31, [x0, x5]
	cmeq	v29.8h, v31.8h, v30.8h
	umaxp	v29.4s, v29.4s, v29.4s
	fmov	x5, d29
	cbnz	x5, .L114
	cmhi	v31.8h, v31.8h, v30.8h
	umaxp	v31.4s, v31.4s, v31.4s
	fmov	x5, d31
	cbnz	x5, .L114
	sub	w5, w2, #24
	cmp	w5, w4
	beq	.L113
	add	w1, w1, 8
.L114:
	uxtw	x1, w1
	b	.L119
	.p2align 2,,3
.L229:
	bcc	.L113
	cmp	w2, w1
	ble	.L113
.L119:
	ldrh	w4, [x0, x1, lsl 1]
	add	x1, x1, 1
	cmp	w3, w4
	bne	.L229
	.p2align 5,,15
.L112:
	mov	w0, 1
.L231:
	ret
	.p2align 2,,3
.L110:
	asr	w12, w2, 5
	cmp	w2, 127
	ble	.L237
	prfm	PLDL1KEEP, [x1]
	mov	w5, 0
	mov	w4, w12
	.p2align 5,,15
.L143:
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
	bgt	.L143
	cmp	w4, 1
	ble	.L238
	.p2align 5,,15
.L146:
	asr	w7, w4, 1
	add	w6, w7, w5
	sub	w4, w4, w7
	ldrh	w7, [x1, w6, sxtw 1]
	cmp	w7, w3
	csel	w5, w5, w6, cs
	cmp	w4, 1
	bgt	.L146
.L238:
	ldrh	w1, [x1, w5, sxtw 1]
	cmp	w1, w3
	cinc	w5, w5, cc
	cmp	w5, w12
	blt	.L239
	lsl	w1, w12, 5
	cmp	w2, w1
	ble	.L113
	ubfiz	x8, x12, 6, 32
	mov	w10, 11
	add	x5, x0, x8
	sub	w7, w2, w1
	neg	x5, x5, lsr 1
	sub	w9, w7, #1
	and	w6, w5, 7
	add	w4, w6, 8
	cmp	w4, w10
	csel	w4, w4, w10, cs
	cmp	w9, w4
	bcc	.L149
	cbz	w6, .L150
	ldrh	w4, [x0, x8]
	cmp	w3, w4
	beq	.L112
	bcc	.L113
	add	w4, w1, 1
	tst	x5, 6
	beq	.L175
	ubfiz	x4, x4, 1, 32
	ldrh	w8, [x0, x4]
	cmp	w3, w8
	beq	.L112
	bcc	.L113
	cmp	w6, 2
	bls	.L240
	add	x4, x0, x4
	ldrh	w8, [x4, 2]
	cmp	w3, w8
	beq	.L112
	bcc	.L113
	tbz	x5, 2, .L241
	ldrh	w5, [x4, 4]
	cmp	w3, w5
	beq	.L112
	bcc	.L113
	cmp	w6, 4
	beq	.L242
	ldrh	w5, [x4, 6]
	cmp	w3, w5
	beq	.L112
	bcc	.L113
	cmp	w6, 5
	beq	.L243
	ldrh	w5, [x4, 8]
	cmp	w3, w5
	beq	.L112
	bcc	.L113
	cmp	w6, 7
	bne	.L244
	ldrh	w4, [x4, 10]
	cmp	w3, w4
	beq	.L112
	bcc	.L113
	add	w1, w1, 7
.L150:
	add	w4, w6, w12, lsl 5
	sub	w7, w7, w6
	dup	v29.8h, w3
	mov	w5, 0
	and	w6, w7, -8
	add	x4, x0, x4, lsl 1
	b	.L159
	.p2align 2,,3
.L246:
	fmov	x8, d31
	cbnz	x8, .L157
	add	w5, w5, 8
	cmp	w6, w5
	beq	.L245
.L159:
	ldr	q31, [x4]
	add	x4, x4, 16
	cmeq	v30.8h, v29.8h, v31.8h
	cmhi	v31.8h, v31.8h, v29.8h
	umaxp	v30.4s, v30.4s, v30.4s
	umaxp	v31.4s, v31.4s, v31.4s
	fmov	x8, d30
	cbz	x8, .L246
.L157:
	add	w1, w1, w5
.L149:
	sxtw	x1, w1
	b	.L161
	.p2align 2,,3
.L234:
	bcc	.L113
	cmp	w2, w1
	ble	.L113
.L161:
	ldrh	w4, [x0, x1, lsl 1]
	add	x1, x1, 1
	cmp	w3, w4
	bne	.L234
	mov	w0, 1
	b	.L231
	.p2align 2,,3
.L111:
	cmp	w2, 7
	bgt	.L121
	cmp	w2, 0
	ble	.L113
	ldrh	w1, [x0]
	cmp	w3, w1
	beq	.L112
	bcc	.L113
	cmp	w2, 1
	beq	.L113
	ldrh	w1, [x0, 2]
	cmp	w3, w1
	beq	.L112
	bcc	.L113
	cmp	w2, 2
	beq	.L113
	ldrh	w1, [x0, 4]
	cmp	w3, w1
	beq	.L112
	bcc	.L113
	cmp	w2, 3
	beq	.L113
	ldrh	w1, [x0, 6]
	cmp	w3, w1
	beq	.L112
	bcc	.L113
	cmp	w2, 4
	beq	.L113
	ldrh	w1, [x0, 8]
	cmp	w3, w1
	beq	.L112
	bcc	.L113
	cmp	w2, 5
	beq	.L113
	ldrh	w1, [x0, 10]
	cmp	w3, w1
	beq	.L112
	bcc	.L113
	cmp	w2, 7
	bne	.L113
	ldrh	w0, [x0, 12]
	cmp	w0, w3
	cset	w0, eq
	ret
	.p2align 2,,3
.L239:
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
.L237:
	cmp	w12, 1
	beq	.L125
	mov	w5, 0
	mov	w4, w12
	.p2align 5,,15
.L127:
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
	bgt	.L127
	add	w1, w5, 1
	sbfiz	x4, x1, 5, 32
	sub	x4, x4, #1
	ldrh	w4, [x0, x4, lsl 1]
	cmp	w4, w3
	csel	w1, w1, w5, cc
	cmp	w12, w1
	bgt	.L163
.L129:
	lsl	w1, w12, 5
	cmp	w2, w1
	ble	.L113
	ubfiz	x8, x12, 6, 32
	mov	w10, 11
	add	x5, x0, x8
	sub	w7, w2, w1
	neg	x5, x5, lsr 1
	sub	w9, w7, #1
	and	w6, w5, 7
	add	w4, w6, 8
	cmp	w4, w10
	csel	w4, w4, w10, cs
	cmp	w4, w9
	bhi	.L130
	cbz	w6, .L131
	ldrh	w4, [x0, x8]
	cmp	w3, w4
	beq	.L112
	bcc	.L113
	add	w4, w1, 1
	tst	x5, 6
	beq	.L173
	ubfiz	x4, x4, 1, 32
	ldrh	w8, [x0, x4]
	cmp	w3, w8
	beq	.L112
	bcc	.L113
	cmp	w6, 2
	bls	.L247
	add	x4, x0, x4
	ldrh	w8, [x4, 2]
	cmp	w3, w8
	beq	.L112
	bcc	.L113
	tbz	x5, 2, .L248
	ldrh	w5, [x4, 4]
	cmp	w3, w5
	beq	.L112
	bcc	.L113
	cmp	w6, 4
	beq	.L249
	ldrh	w5, [x4, 6]
	cmp	w3, w5
	beq	.L112
	bcc	.L113
	cmp	w6, 5
	beq	.L250
	ldrh	w5, [x4, 8]
	cmp	w3, w5
	beq	.L112
	bcc	.L113
	cmp	w6, 7
	bne	.L251
	ldrh	w4, [x4, 10]
	cmp	w3, w4
	beq	.L112
	bcc	.L113
	add	w1, w1, 7
.L131:
	add	w4, w6, w12, lsl 5
	sub	w7, w7, w6
	dup	v29.8h, w3
	lsr	w8, w7, 3
	mov	w5, 0
	add	x4, x0, x4, lsl 1
	add	x6, x4, w8, uxtw 4
	b	.L139
	.p2align 2,,3
.L253:
	fmov	x9, d31
	cbnz	x9, .L137
	add	w5, w5, 8
	cmp	x6, x4
	beq	.L252
.L139:
	ldr	q31, [x4]
	add	x4, x4, 16
	cmeq	v30.8h, v31.8h, v29.8h
	cmhi	v31.8h, v31.8h, v29.8h
	umaxp	v30.4s, v30.4s, v30.4s
	umaxp	v31.4s, v31.4s, v31.4s
	fmov	x9, d30
	cbz	x9, .L253
.L137:
	add	w1, w1, w5
.L130:
	sxtw	x1, w1
	b	.L141
	.p2align 2,,3
.L232:
	bcc	.L113
	cmp	w2, w1
	ble	.L113
.L141:
	ldrh	w4, [x0, x1, lsl 1]
	add	x1, x1, 1
	cmp	w3, w4
	bne	.L232
	mov	w0, 1
	b	.L231
	.p2align 2,,3
.L121:
	dup	v21.8h, w3
	ldr	q20, [x0]
	cmeq	v20.8h, v21.8h, v20.8h
	umaxv	h20, v20.8h
	umov	w1, v20.h[0]
	tst	w1, 65535
	bne	.L112
	cmp	w2, 8
	beq	.L113
	ldrh	w1, [x0, 16]
	cmp	w3, w1
	beq	.L112
	bcc	.L113
	cmp	w2, 9
	beq	.L113
	ldrh	w1, [x0, 18]
	cmp	w3, w1
	beq	.L112
	bcc	.L113
	cmp	w2, 10
	beq	.L113
	ldrh	w1, [x0, 20]
	cmp	w3, w1
	beq	.L112
	bcc	.L113
	cmp	w2, 11
	beq	.L113
	ldrh	w1, [x0, 22]
	cmp	w3, w1
	beq	.L112
	bcc	.L113
	cmp	w2, 12
	beq	.L113
	ldrh	w1, [x0, 24]
	cmp	w3, w1
	beq	.L112
	bcc	.L113
	cmp	w2, 13
	beq	.L113
	ldrh	w1, [x0, 26]
	cmp	w3, w1
	beq	.L112
	bcc	.L113
	cmp	w2, 15
	bne	.L113
	ldrh	w0, [x0, 28]
	cmp	w0, w3
	cset	w0, eq
	ret
	.p2align 2,,3
.L113:
	mov	w0, 0
	ret
.L125:
	ldrh	w1, [x0, 62]
	cmp	w1, w3
	bcc	.L129
	mov	w1, 0
.L163:
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
	.p2align 2,,3
.L245:
	cmp	w7, w6
	beq	.L113
	add	w1, w1, w6
	b	.L149
.L165:
	mov	w1, 16
	b	.L115
.L164:
	mov	w1, 16
	b	.L114
.L252:
	lsl	w8, w8, 3
	cmp	w8, w7
	beq	.L113
	add	w1, w1, w8
	b	.L130
.L166:
	mov	w1, 17
	b	.L115
.L175:
	mov	w1, w4
	b	.L150
.L240:
	add	w1, w1, 2
	b	.L150
.L167:
	mov	w1, 18
	b	.L115
.L241:
	add	w1, w1, 3
	b	.L150
.L168:
	mov	w1, 19
	b	.L115
.L242:
	add	w1, w1, 4
	b	.L150
.L169:
	mov	w1, 20
	b	.L115
.L170:
	mov	w1, 21
	b	.L115
.L243:
	add	w1, w1, 5
	b	.L150
.L171:
	mov	w1, 22
	b	.L115
.L244:
	add	w1, w1, 6
	b	.L150
.L248:
	add	w1, w1, 3
	b	.L131
.L247:
	add	w1, w1, 2
	b	.L131
.L173:
	mov	w1, w4
	b	.L131
.L249:
	add	w1, w1, 4
	b	.L131
.L251:
	add	w1, w1, 6
	b	.L131
.L250:
	add	w1, w1, 5
	b	.L131
	.cfi_endproc
.LFE3140:
	.size	_ZN5ab_cr19simd_quad_pi5_spineEPKtS1_it, .-_ZN5ab_cr19simd_quad_pi5_spineEPKtS1_it
	.align	2
	.p2align 5,,15
	.global	_ZN5ab_cr25simd_quad_pi5_build_spineEPKtiPt
	.type	_ZN5ab_cr25simd_quad_pi5_build_spineEPKtiPt, %function
_ZN5ab_cr25simd_quad_pi5_build_spineEPKtiPt:
.LFB3141:
	.cfi_startproc
	cmp	w1, 31
	ble	.L254
	mov	w3, 0
	asr	w1, w1, 5
	add	x0, x0, 62
	.p2align 5,,15
.L256:
	ubfiz	x4, x3, 6, 32
	ldrh	w4, [x0, x4]
	strh	w4, [x2, x3, lsl 1]
	add	x3, x3, 1
	cmp	w1, w3
	bgt	.L256
.L254:
	ret
	.cfi_endproc
.LFE3141:
	.size	_ZN5ab_cr25simd_quad_pi5_build_spineEPKtiPt, .-_ZN5ab_cr25simd_quad_pi5_build_spineEPKtiPt
	.align	2
	.p2align 5,,15
	.global	_ZN5ab_cr23simd_quad_pi5_spine_256EPKtS1_t
	.type	_ZN5ab_cr23simd_quad_pi5_spine_256EPKtS1_t, %function
_ZN5ab_cr23simd_quad_pi5_spine_256EPKtS1_t:
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
	beq	.L260
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
.L260:
	mov	w0, 0
	ret
	.cfi_endproc
.LFE3142:
	.size	_ZN5ab_cr23simd_quad_pi5_spine_256EPKtS1_t, .-_ZN5ab_cr23simd_quad_pi5_spine_256EPKtS1_t
	.align	2
	.p2align 5,,15
	.global	_ZN5ab_cr23simd_quad_pi5_spine_512EPKtS1_t
	.type	_ZN5ab_cr23simd_quad_pi5_spine_512EPKtS1_t, %function
_ZN5ab_cr23simd_quad_pi5_spine_512EPKtS1_t:
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
	bcs	.L262
	add	w3, w3, 1
	mov	w1, 0
	cmp	w3, 16
	beq	.L263
.L262:
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
.L263:
	mov	w0, w1
	ret
	.cfi_endproc
.LFE3143:
	.size	_ZN5ab_cr23simd_quad_pi5_spine_512EPKtS1_t, .-_ZN5ab_cr23simd_quad_pi5_spine_512EPKtS1_t
	.align	2
	.p2align 5,,15
	.global	_ZN5ab_cr24simd_quad_pi5_spine_1024EPKtS1_t
	.type	_ZN5ab_cr24simd_quad_pi5_spine_1024EPKtS1_t, %function
_ZN5ab_cr24simd_quad_pi5_spine_1024EPKtS1_t:
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
	beq	.L268
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
.L268:
	mov	w0, 0
	ret
	.cfi_endproc
.LFE3144:
	.size	_ZN5ab_cr24simd_quad_pi5_spine_1024EPKtS1_t, .-_ZN5ab_cr24simd_quad_pi5_spine_1024EPKtS1_t
	.align	2
	.p2align 5,,15
	.global	_ZN5ab_cr24simd_quad_pi5_spine_2048EPKtS1_t
	.type	_ZN5ab_cr24simd_quad_pi5_spine_2048EPKtS1_t, %function
_ZN5ab_cr24simd_quad_pi5_spine_2048EPKtS1_t:
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
	bcs	.L270
	add	w3, w3, 1
	mov	w1, 0
	cmp	w3, 64
	beq	.L271
.L270:
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
.L271:
	mov	w0, w1
	ret
	.cfi_endproc
.LFE3145:
	.size	_ZN5ab_cr24simd_quad_pi5_spine_2048EPKtS1_t, .-_ZN5ab_cr24simd_quad_pi5_spine_2048EPKtS1_t
	.align	2
	.p2align 5,,15
	.global	_ZN5ab_cr24simd_quad_pi5_spine_4096EPKtS1_t
	.type	_ZN5ab_cr24simd_quad_pi5_spine_4096EPKtS1_t, %function
_ZN5ab_cr24simd_quad_pi5_spine_4096EPKtS1_t:
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
	beq	.L276
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
.L276:
	mov	w0, 0
	ret
	.cfi_endproc
.LFE3146:
	.size	_ZN5ab_cr24simd_quad_pi5_spine_4096EPKtS1_t, .-_ZN5ab_cr24simd_quad_pi5_spine_4096EPKtS1_t
	.ident	"GCC: (GNU) 17.0.0 20260704 (experimental)"
	.section	.note.GNU-stack,"",@progbits
