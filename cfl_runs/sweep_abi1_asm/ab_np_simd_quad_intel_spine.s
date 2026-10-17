0000000000409f60 <ab_np::simd_quad_intel_spine(unsigned short const*, unsigned short const*, int, unsigned short)>:
  409f60:	vmovd  %ecx,%xmm0
  409f64:	mov    %rdi,%r9
  409f67:	mov    %edx,%r11d
  409f6a:	vpbroadcastw %xmm0,%ymm0
  409f6f:	cmp    $0x1f,%edx
  409f72:	jg     40a220 <ab_np::simd_quad_intel_spine(unsigned short const*, unsigned short const*, int, unsigned short)+0x2c0>
  409f78:	cmp    $0xf,%edx
  409f7b:	jle    40a810 <ab_np::simd_quad_intel_spine(unsigned short const*, unsigned short const*, int, unsigned short)+0x8b0>
  409f81:	vpcmpeqw (%rdi),%ymm0,%ymm1
  409f85:	vpmovmskb %ymm1,%eax
  409f89:	test   %eax,%eax
  409f8b:	jne    40a9b0 <ab_np::simd_quad_intel_spine(unsigned short const*, unsigned short const*, int, unsigned short)+0xa50>
  409f91:	cmp    $0x10,%edx
  409f94:	je     40a210 <ab_np::simd_quad_intel_spine(unsigned short const*, unsigned short const*, int, unsigned short)+0x2b0>
  409f9a:	lea    0x20(%rdi),%r8
  409f9e:	mov    $0xb,%edi
  409fa3:	mov    %r8,%rdx
  409fa6:	shr    $1,%rdx
  409fa9:	neg    %rdx
  409fac:	mov    %edx,%esi
  409fae:	and    $0x7,%esi
  409fb1:	lea    0x8(%rsi),%eax
  409fb4:	cmp    %edi,%eax
  409fb6:	cmovb  %edi,%eax
  409fb9:	lea    -0x11(%r11),%edi
  409fbd:	cmp    %eax,%edi
  409fbf:	jb     40aa41 <ab_np::simd_quad_intel_spine(unsigned short const*, unsigned short const*, int, unsigned short)+0xae1>
  409fc5:	test   %esi,%esi
  409fc7:	je     40aa37 <ab_np::simd_quad_intel_spine(unsigned short const*, unsigned short const*, int, unsigned short)+0xad7>
  409fcd:	movzwl 0x20(%r9),%eax
  409fd2:	cmp    %cx,%ax
  409fd5:	jae    40a899 <ab_np::simd_quad_intel_spine(unsigned short const*, unsigned short const*, int, unsigned short)+0x939>
  409fdb:	test   $0x6,%dl
  409fde:	je     40aa57 <ab_np::simd_quad_intel_spine(unsigned short const*, unsigned short const*, int, unsigned short)+0xaf7>
  409fe4:	movzwl 0x22(%r9),%eax
  409fe9:	cmp    %cx,%ax
  409fec:	jae    40a899 <ab_np::simd_quad_intel_spine(unsigned short const*, unsigned short const*, int, unsigned short)+0x939>
  409ff2:	cmp    $0x2,%esi
  409ff5:	jbe    40aa61 <ab_np::simd_quad_intel_spine(unsigned short const*, unsigned short const*, int, unsigned short)+0xb01>
  409ffb:	movzwl 0x24(%r9),%eax
  40a000:	cmp    %cx,%ax
  40a003:	jae    40a899 <ab_np::simd_quad_intel_spine(unsigned short const*, unsigned short const*, int, unsigned short)+0x939>
  40a009:	and    $0x4,%edx
  40a00c:	je     40aa72 <ab_np::simd_quad_intel_spine(unsigned short const*, unsigned short const*, int, unsigned short)+0xb12>
  40a012:	movzwl 0x26(%r9),%eax
  40a017:	cmp    %cx,%ax
  40a01a:	jae    40a899 <ab_np::simd_quad_intel_spine(unsigned short const*, unsigned short const*, int, unsigned short)+0x939>
  40a020:	cmp    $0x4,%esi
  40a023:	je     40aa84 <ab_np::simd_quad_intel_spine(unsigned short const*, unsigned short const*, int, unsigned short)+0xb24>
  40a029:	movzwl 0x28(%r9),%eax
  40a02e:	cmp    %cx,%ax
  40a031:	jae    40a899 <ab_np::simd_quad_intel_spine(unsigned short const*, unsigned short const*, int, unsigned short)+0x939>
  40a037:	cmp    $0x5,%esi
  40a03a:	je     40aa8e <ab_np::simd_quad_intel_spine(unsigned short const*, unsigned short const*, int, unsigned short)+0xb2e>
  40a040:	movzwl 0x2a(%r9),%eax
  40a045:	cmp    %cx,%ax
  40a048:	jae    40a899 <ab_np::simd_quad_intel_spine(unsigned short const*, unsigned short const*, int, unsigned short)+0x939>
  40a04e:	cmp    $0x7,%esi
  40a051:	jne    40aaa8 <ab_np::simd_quad_intel_spine(unsigned short const*, unsigned short const*, int, unsigned short)+0xb48>
  40a057:	movzwl 0x2c(%r9),%eax
  40a05c:	cmp    %cx,%ax
  40a05f:	jae    40a899 <ab_np::simd_quad_intel_spine(unsigned short const*, unsigned short const*, int, unsigned short)+0x939>
  40a065:	mov    $0x17,%edx
  40a06a:	mov    %esi,%eax
  40a06c:	vpminuw (%r8,%rax,2),%xmm0,%xmm1
  40a072:	vpcmpeqw %xmm1,%xmm0,%xmm0
  40a076:	vptest %xmm0,%xmm0
  40a07b:	jne    40aa07 <ab_np::simd_quad_intel_spine(unsigned short const*, unsigned short const*, int, unsigned short)+0xaa7>
  40a081:	lea    -0x18(%r11),%eax
  40a085:	cmp    %esi,%eax
  40a087:	je     40a210 <ab_np::simd_quad_intel_spine(unsigned short const*, unsigned short const*, int, unsigned short)+0x2b0>
  40a08d:	add    $0x8,%edx
  40a090:	mov    %edx,%edi
  40a092:	movzwl (%r9,%rdi,2),%eax
  40a097:	cmp    %cx,%ax
  40a09a:	jae    40a899 <ab_np::simd_quad_intel_spine(unsigned short const*, unsigned short const*, int, unsigned short)+0x939>
  40a0a0:	lea    0x1(%rdx),%eax
  40a0a3:	cmp    %eax,%r11d
  40a0a6:	jle    40a210 <ab_np::simd_quad_intel_spine(unsigned short const*, unsigned short const*, int, unsigned short)+0x2b0>
  40a0ac:	movzwl 0x2(%r9,%rdi,2),%eax
  40a0b2:	lea    0x2(%rdi,%rdi,1),%rsi
  40a0b7:	cmp    %cx,%ax
  40a0ba:	jae    40a899 <ab_np::simd_quad_intel_spine(unsigned short const*, unsigned short const*, int, unsigned short)+0x939>
  40a0c0:	lea    0x2(%rdx),%eax
  40a0c3:	cmp    %eax,%r11d
  40a0c6:	jle    40a210 <ab_np::simd_quad_intel_spine(unsigned short const*, unsigned short const*, int, unsigned short)+0x2b0>
  40a0cc:	movzwl 0x2(%r9,%rsi,1),%eax
  40a0d2:	cmp    %cx,%ax
  40a0d5:	jae    40a899 <ab_np::simd_quad_intel_spine(unsigned short const*, unsigned short const*, int, unsigned short)+0x939>
  40a0db:	lea    0x3(%rdx),%eax
  40a0de:	cmp    %eax,%r11d
  40a0e1:	jle    40a210 <ab_np::simd_quad_intel_spine(unsigned short const*, unsigned short const*, int, unsigned short)+0x2b0>
  40a0e7:	movzwl 0x4(%r9,%rsi,1),%eax
  40a0ed:	cmp    %cx,%ax
  40a0f0:	jae    40a899 <ab_np::simd_quad_intel_spine(unsigned short const*, unsigned short const*, int, unsigned short)+0x939>
  40a0f6:	lea    0x4(%rdx),%eax
  40a0f9:	cmp    %eax,%r11d
  40a0fc:	jle    40a210 <ab_np::simd_quad_intel_spine(unsigned short const*, unsigned short const*, int, unsigned short)+0x2b0>
  40a102:	movzwl 0x6(%r9,%rsi,1),%eax
  40a108:	cmp    %cx,%ax
  40a10b:	jae    40a899 <ab_np::simd_quad_intel_spine(unsigned short const*, unsigned short const*, int, unsigned short)+0x939>
  40a111:	lea    0x5(%rdx),%eax
  40a114:	cmp    %eax,%r11d
  40a117:	jle    40a210 <ab_np::simd_quad_intel_spine(unsigned short const*, unsigned short const*, int, unsigned short)+0x2b0>
  40a11d:	movzwl 0x8(%r9,%rsi,1),%eax
  40a123:	cmp    %cx,%ax
  40a126:	jae    40a899 <ab_np::simd_quad_intel_spine(unsigned short const*, unsigned short const*, int, unsigned short)+0x939>
  40a12c:	lea    0x6(%rdx),%eax
  40a12f:	cmp    %r11d,%eax
  40a132:	jge    40a210 <ab_np::simd_quad_intel_spine(unsigned short const*, unsigned short const*, int, unsigned short)+0x2b0>
  40a138:	movzwl 0xa(%r9,%rsi,1),%eax
  40a13e:	cmp    %cx,%ax
  40a141:	jae    40a899 <ab_np::simd_quad_intel_spine(unsigned short const*, unsigned short const*, int, unsigned short)+0x939>
  40a147:	lea    0x7(%rdx),%eax
  40a14a:	cmp    %r11d,%eax
  40a14d:	jge    40a210 <ab_np::simd_quad_intel_spine(unsigned short const*, unsigned short const*, int, unsigned short)+0x2b0>
  40a153:	movzwl 0xc(%r9,%rsi,1),%eax
  40a159:	cmp    %cx,%ax
  40a15c:	jae    40a899 <ab_np::simd_quad_intel_spine(unsigned short const*, unsigned short const*, int, unsigned short)+0x939>
  40a162:	lea    0x8(%rdx),%eax
  40a165:	cmp    %eax,%r11d
  40a168:	jle    40a210 <ab_np::simd_quad_intel_spine(unsigned short const*, unsigned short const*, int, unsigned short)+0x2b0>
  40a16e:	movzwl 0xe(%r9,%rsi,1),%eax
  40a174:	cmp    %cx,%ax
  40a177:	jae    40a899 <ab_np::simd_quad_intel_spine(unsigned short const*, unsigned short const*, int, unsigned short)+0x939>
  40a17d:	lea    0x9(%rdx),%eax
  40a180:	cmp    %eax,%r11d
  40a183:	jle    40a210 <ab_np::simd_quad_intel_spine(unsigned short const*, unsigned short const*, int, unsigned short)+0x2b0>
  40a189:	movzwl 0x10(%r9,%rsi,1),%eax
  40a18f:	cmp    %cx,%ax
  40a192:	jae    40a899 <ab_np::simd_quad_intel_spine(unsigned short const*, unsigned short const*, int, unsigned short)+0x939>
  40a198:	lea    0xa(%rdx),%eax
  40a19b:	cmp    %eax,%r11d
  40a19e:	jle    40a210 <ab_np::simd_quad_intel_spine(unsigned short const*, unsigned short const*, int, unsigned short)+0x2b0>
  40a1a0:	movzwl 0x12(%r9,%rsi,1),%eax
  40a1a6:	cmp    %cx,%ax
  40a1a9:	jae    40a899 <ab_np::simd_quad_intel_spine(unsigned short const*, unsigned short const*, int, unsigned short)+0x939>
  40a1af:	lea    0xb(%rdx),%eax
  40a1b2:	cmp    %eax,%r11d
  40a1b5:	jle    40a210 <ab_np::simd_quad_intel_spine(unsigned short const*, unsigned short const*, int, unsigned short)+0x2b0>
  40a1b7:	movzwl 0x14(%r9,%rsi,1),%eax
  40a1bd:	cmp    %cx,%ax
  40a1c0:	jae    40a899 <ab_np::simd_quad_intel_spine(unsigned short const*, unsigned short const*, int, unsigned short)+0x939>
  40a1c6:	lea    0xc(%rdx),%eax
  40a1c9:	cmp    %eax,%r11d
  40a1cc:	jle    40a210 <ab_np::simd_quad_intel_spine(unsigned short const*, unsigned short const*, int, unsigned short)+0x2b0>
  40a1ce:	movzwl 0x16(%r9,%rsi,1),%eax
  40a1d4:	cmp    %cx,%ax
  40a1d7:	jae    40a899 <ab_np::simd_quad_intel_spine(unsigned short const*, unsigned short const*, int, unsigned short)+0x939>
  40a1dd:	lea    0xd(%rdx),%eax
  40a1e0:	cmp    %eax,%r11d
  40a1e3:	jle    40a210 <ab_np::simd_quad_intel_spine(unsigned short const*, unsigned short const*, int, unsigned short)+0x2b0>
  40a1e5:	movzwl 0x18(%r9,%rsi,1),%eax
  40a1eb:	cmp    %cx,%ax
  40a1ee:	jae    40a899 <ab_np::simd_quad_intel_spine(unsigned short const*, unsigned short const*, int, unsigned short)+0x939>
  40a1f4:	add    $0xe,%edx
  40a1f7:	cmp    %edx,%r11d
  40a1fa:	jle    40a210 <ab_np::simd_quad_intel_spine(unsigned short const*, unsigned short const*, int, unsigned short)+0x2b0>
  40a1fc:	movzwl 0x3c(%r9),%eax
  40a201:	cmp    %cx,%ax
  40a204:	jae    40a899 <ab_np::simd_quad_intel_spine(unsigned short const*, unsigned short const*, int, unsigned short)+0x939>
  40a20a:	nopw   0x0(%rax,%rax,1)
  40a210:	xor    %eax,%eax
  40a212:	vzeroupper
  40a215:	ret
  40a216:	cs nopw 0x0(%rax,%rax,1)
  40a220:	push   %rbp
  40a221:	mov    %rsp,%rbp
  40a224:	sub    $0x10,%rsp
  40a228:	mov    %rbx,-0x10(%rbp)
  40a22c:	mov    %edx,%ebx
  40a22e:	sar    $0x5,%ebx
  40a231:	cmp    $0x7f,%edx
  40a234:	jg     40a570 <ab_np::simd_quad_intel_spine(unsigned short const*, unsigned short const*, int, unsigned short)+0x610>
  40a23a:	cmp    $0x1,%ebx
  40a23d:	je     40a9c0 <ab_np::simd_quad_intel_spine(unsigned short const*, unsigned short const*, int, unsigned short)+0xa60>
  40a243:	mov    %ebx,%edx
  40a245:	xor    %esi,%esi
  40a247:	xchg   %ax,%ax
  40a249:	data16 cs nopw 0x0(%rax,%rax,1)
  40a254:	data16 cs nopw 0x0(%rax,%rax,1)
  40a25f:	data16 cs nopw 0x0(%rax,%rax,1)
  40a26a:	data16 cs nopw 0x0(%rax,%rax,1)
  40a275:	data16 cs nopw 0x0(%rax,%rax,1)
  40a280:	mov    %edx,%edi
  40a282:	sar    $1,%edi
  40a284:	lea    (%rdi,%rsi,1),%r8d
  40a288:	lea    0x1(%r8),%eax
  40a28c:	shl    $0x5,%eax
  40a28f:	cltq
  40a291:	cmp    %cx,-0x2(%r9,%rax,2)
  40a297:	cmovb  %r8d,%esi
  40a29b:	sub    %edi,%edx
  40a29d:	cmp    $0x1,%edx
  40a2a0:	jg     40a280 <ab_np::simd_quad_intel_spine(unsigned short const*, unsigned short const*, int, unsigned short)+0x320>
  40a2a2:	lea    0x1(%rsi),%eax
  40a2a5:	mov    %eax,%edx
  40a2a7:	shl    $0x5,%edx
  40a2aa:	movslq %edx,%rdx
  40a2ad:	cmp    %cx,-0x2(%r9,%rdx,2)
  40a2b3:	cmovae %esi,%eax
  40a2b6:	cmp    %eax,%ebx
  40a2b8:	jg     40a9cc <ab_np::simd_quad_intel_spine(unsigned short const*, unsigned short const*, int, unsigned short)+0xa6c>
  40a2be:	mov    %ebx,%eax
  40a2c0:	shl    $0x5,%eax
  40a2c3:	cmp    %eax,%r11d
  40a2c6:	jle    40a9fc <ab_np::simd_quad_intel_spine(unsigned short const*, unsigned short const*, int, unsigned short)+0xa9c>
  40a2cc:	mov    %ebx,%ebx
  40a2ce:	mov    $0x17,%r8d
  40a2d4:	mov    %r12,-0x8(%rbp)
  40a2d8:	mov    %r11d,%r12d
  40a2db:	shl    $0x6,%rbx
  40a2df:	sub    %eax,%r12d
  40a2e2:	lea    (%r9,%rbx,1),%rdi
  40a2e6:	mov    %rdi,%r10
  40a2e9:	shr    $1,%r10
  40a2ec:	neg    %r10
  40a2ef:	mov    %r10d,%esi
  40a2f2:	and    $0xf,%esi
  40a2f5:	lea    0x10(%rsi),%edx
  40a2f8:	cmp    %r8d,%edx
  40a2fb:	cmovb  %r8d,%edx
  40a2ff:	lea    -0x1(%r12),%r8d
  40a304:	cmp    %edx,%r8d
  40a307:	jb     40a537 <ab_np::simd_quad_intel_spine(unsigned short const*, unsigned short const*, int, unsigned short)+0x5d7>
  40a30d:	test   %esi,%esi
  40a30f:	je     40a47a <ab_np::simd_quad_intel_spine(unsigned short const*, unsigned short const*, int, unsigned short)+0x51a>
  40a315:	movzwl (%rdi),%edx
  40a318:	cmp    %cx,%dx
  40a31b:	jae    40a560 <ab_np::simd_quad_intel_spine(unsigned short const*, unsigned short const*, int, unsigned short)+0x600>
  40a321:	test   $0xe,%r10b
  40a325:	je     40aadf <ab_np::simd_quad_intel_spine(unsigned short const*, unsigned short const*, int, unsigned short)+0xb7f>
  40a32b:	lea    0x1(%rax),%r8d
  40a32f:	movzwl (%r9,%r8,2),%edx
  40a334:	cmp    %cx,%dx
  40a337:	jae    40a560 <ab_np::simd_quad_intel_spine(unsigned short const*, unsigned short const*, int, unsigned short)+0x600>
  40a33d:	cmp    $0x2,%esi
  40a340:	jbe    40aae6 <ab_np::simd_quad_intel_spine(unsigned short const*, unsigned short const*, int, unsigned short)+0xb86>
  40a346:	movzwl 0x2(%r9,%r8,2),%edx
  40a34c:	cmp    %cx,%dx
  40a34f:	jae    40a560 <ab_np::simd_quad_intel_spine(unsigned short const*, unsigned short const*, int, unsigned short)+0x600>
  40a355:	test   $0xc,%r10b
  40a359:	je     40ab02 <ab_np::simd_quad_intel_spine(unsigned short const*, unsigned short const*, int, unsigned short)+0xba2>
  40a35f:	movzwl 0x4(%r9,%r8,2),%edx
  40a365:	cmp    %cx,%dx
  40a368:	jae    40a560 <ab_np::simd_quad_intel_spine(unsigned short const*, unsigned short const*, int, unsigned short)+0x600>
  40a36e:	cmp    $0x4,%esi
  40a371:	jbe    40ab26 <ab_np::simd_quad_intel_spine(unsigned short const*, unsigned short const*, int, unsigned short)+0xbc6>
  40a377:	movzwl 0x6(%r9,%r8,2),%edx
  40a37d:	cmp    %cx,%dx
  40a380:	jae    40a560 <ab_np::simd_quad_intel_spine(unsigned short const*, unsigned short const*, int, unsigned short)+0x600>
  40a386:	cmp    $0x5,%esi
  40a389:	je     40ab4a <ab_np::simd_quad_intel_spine(unsigned short const*, unsigned short const*, int, unsigned short)+0xbea>
  40a38f:	movzwl 0x8(%r9,%r8,2),%edx
  40a395:	cmp    %cx,%dx
  40a398:	jae    40a560 <ab_np::simd_quad_intel_spine(unsigned short const*, unsigned short const*, int, unsigned short)+0x600>
  40a39e:	cmp    $0x6,%esi
  40a3a1:	je     40ab52 <ab_np::simd_quad_intel_spine(unsigned short const*, unsigned short const*, int, unsigned short)+0xbf2>
  40a3a7:	movzwl 0xa(%r9,%r8,2),%edx
  40a3ad:	cmp    %cx,%dx
  40a3b0:	jae    40a560 <ab_np::simd_quad_intel_spine(unsigned short const*, unsigned short const*, int, unsigned short)+0x600>
  40a3b6:	and    $0x8,%r10d
  40a3ba:	je     40ab5a <ab_np::simd_quad_intel_spine(unsigned short const*, unsigned short const*, int, unsigned short)+0xbfa>
  40a3c0:	movzwl 0xc(%r9,%r8,2),%edx
  40a3c6:	cmp    %cx,%dx
  40a3c9:	jae    40a560 <ab_np::simd_quad_intel_spine(unsigned short const*, unsigned short const*, int, unsigned short)+0x600>
  40a3cf:	cmp    $0x8,%esi
  40a3d2:	je     40ab6a <ab_np::simd_quad_intel_spine(unsigned short const*, unsigned short const*, int, unsigned short)+0xc0a>
  40a3d8:	movzwl 0xe(%r9,%r8,2),%edx
  40a3de:	cmp    %cx,%dx
  40a3e1:	jae    40a560 <ab_np::simd_quad_intel_spine(unsigned short const*, unsigned short const*, int, unsigned short)+0x600>
  40a3e7:	cmp    $0x9,%esi
  40a3ea:	je     40ab7a <ab_np::simd_quad_intel_spine(unsigned short const*, unsigned short const*, int, unsigned short)+0xc1a>
  40a3f0:	movzwl 0x10(%r9,%r8,2),%edx
  40a3f6:	cmp    %cx,%dx
  40a3f9:	jae    40a560 <ab_np::simd_quad_intel_spine(unsigned short const*, unsigned short const*, int, unsigned short)+0x600>
  40a3ff:	cmp    $0xa,%esi
  40a402:	je     40ab82 <ab_np::simd_quad_intel_spine(unsigned short const*, unsigned short const*, int, unsigned short)+0xc22>
  40a408:	movzwl 0x12(%r9,%r8,2),%edx
  40a40e:	cmp    %cx,%dx
  40a411:	jae    40a560 <ab_np::simd_quad_intel_spine(unsigned short const*, unsigned short const*, int, unsigned short)+0x600>
  40a417:	cmp    $0xb,%esi
  40a41a:	je     40ab8a <ab_np::simd_quad_intel_spine(unsigned short const*, unsigned short const*, int, unsigned short)+0xc2a>
  40a420:	movzwl 0x14(%r9,%r8,2),%edx
  40a426:	cmp    %cx,%dx
  40a429:	jae    40a560 <ab_np::simd_quad_intel_spine(unsigned short const*, unsigned short const*, int, unsigned short)+0x600>
  40a42f:	cmp    $0xc,%esi
  40a432:	je     40ab92 <ab_np::simd_quad_intel_spine(unsigned short const*, unsigned short const*, int, unsigned short)+0xc32>
  40a438:	movzwl 0x16(%r9,%r8,2),%edx
  40a43e:	cmp    %cx,%dx
  40a441:	jae    40a560 <ab_np::simd_quad_intel_spine(unsigned short const*, unsigned short const*, int, unsigned short)+0x600>
  40a447:	cmp    $0xd,%esi
  40a44a:	je     40aba2 <ab_np::simd_quad_intel_spine(unsigned short const*, unsigned short const*, int, unsigned short)+0xc42>
  40a450:	movzwl 0x18(%r9,%r8,2),%edx
  40a456:	cmp    %cx,%dx
  40a459:	jae    40a560 <ab_np::simd_quad_intel_spine(unsigned short const*, unsigned short const*, int, unsigned short)+0x600>
  40a45f:	cmp    $0xf,%esi
  40a462:	jne    40ab9a <ab_np::simd_quad_intel_spine(unsigned short const*, unsigned short const*, int, unsigned short)+0xc3a>
  40a468:	movzwl 0x1a(%r9,%r8,2),%edx
  40a46e:	cmp    %cx,%dx
  40a471:	jae    40a560 <ab_np::simd_quad_intel_spine(unsigned short const*, unsigned short const*, int, unsigned short)+0x600>
  40a477:	add    $0xf,%eax
  40a47a:	mov    %esi,%edx
  40a47c:	lea    (%rdi,%rdx,2),%rdi
  40a480:	vpminuw (%rdi),%ymm0,%ymm1
  40a485:	vpcmpeqw %ymm1,%ymm0,%ymm1
  40a489:	vptest %ymm1,%ymm1
  40a48e:	jne    40aac2 <ab_np::simd_quad_intel_spine(unsigned short const*, unsigned short const*, int, unsigned short)+0xb62>
  40a494:	sub    %esi,%r12d
  40a497:	mov    %r12d,%edx
  40a49a:	shr    $0x4,%edx
  40a49d:	cmp    $0x1,%edx
  40a4a0:	je     40a529 <ab_np::simd_quad_intel_spine(unsigned short const*, unsigned short const*, int, unsigned short)+0x5c9>
  40a4a6:	vpminuw 0x20(%rdi),%ymm0,%ymm1
  40a4ac:	vpcmpeqw %ymm1,%ymm0,%ymm1
  40a4b0:	vptest %ymm1,%ymm1
  40a4b5:	jne    40aad3 <ab_np::simd_quad_intel_spine(unsigned short const*, unsigned short const*, int, unsigned short)+0xb73>
  40a4bb:	cmp    $0x2,%edx
  40a4be:	je     40a529 <ab_np::simd_quad_intel_spine(unsigned short const*, unsigned short const*, int, unsigned short)+0x5c9>
  40a4c0:	vpminuw 0x40(%rdi),%ymm0,%ymm1
  40a4c6:	vpcmpeqw %ymm1,%ymm0,%ymm1
  40a4ca:	vptest %ymm1,%ymm1
  40a4cf:	jne    40aaf6 <ab_np::simd_quad_intel_spine(unsigned short const*, unsigned short const*, int, unsigned short)+0xb96>
  40a4d5:	cmp    $0x3,%edx
  40a4d8:	je     40a529 <ab_np::simd_quad_intel_spine(unsigned short const*, unsigned short const*, int, unsigned short)+0x5c9>
  40a4da:	vpminuw 0x60(%rdi),%ymm0,%ymm1
  40a4e0:	vpcmpeqw %ymm1,%ymm0,%ymm1
  40a4e4:	vptest %ymm1,%ymm1
  40a4e9:	jne    40ab0a <ab_np::simd_quad_intel_spine(unsigned short const*, unsigned short const*, int, unsigned short)+0xbaa>
  40a4ef:	cmp    $0x4,%edx
  40a4f2:	je     40a529 <ab_np::simd_quad_intel_spine(unsigned short const*, unsigned short const*, int, unsigned short)+0x5c9>
  40a4f4:	vpminuw 0x80(%rdi),%ymm0,%ymm1
  40a4fd:	vpcmpeqw %ymm1,%ymm0,%ymm1
  40a501:	vptest %ymm1,%ymm1
  40a506:	jne    40aa4b <ab_np::simd_quad_intel_spine(unsigned short const*, unsigned short const*, int, unsigned short)+0xaeb>
  40a50c:	cmp    $0x5,%edx
  40a50f:	je     40a529 <ab_np::simd_quad_intel_spine(unsigned short const*, unsigned short const*, int, unsigned short)+0x5c9>
  40a511:	vpminuw 0xa0(%rdi),%ymm0,%ymm1
  40a51a:	vpcmpeqw %ymm1,%ymm0,%ymm0
  40a51e:	vptest %ymm0,%ymm0
  40a523:	jne    40ab2e <ab_np::simd_quad_intel_spine(unsigned short const*, unsigned short const*, int, unsigned short)+0xbce>
  40a529:	shl    $0x4,%edx
  40a52c:	cmp    %r12d,%edx
  40a52f:	je     40a9f8 <ab_np::simd_quad_intel_spine(unsigned short const*, unsigned short const*, int, unsigned short)+0xa98>
  40a535:	add    %edx,%eax
  40a537:	cltq
  40a539:	jmp    40a54c <ab_np::simd_quad_intel_spine(unsigned short const*, unsigned short const*, int, unsigned short)+0x5ec>
  40a53b:	nopl   0x0(%rax,%rax,1)
  40a540:	inc    %rax
  40a543:	cmp    %eax,%r11d
  40a546:	jle    40a9f8 <ab_np::simd_quad_intel_spine(unsigned short const*, unsigned short const*, int, unsigned short)+0xa98>
  40a54c:	movzwl (%r9,%rax,2),%edx
  40a551:	cmp    %cx,%dx
  40a554:	jb     40a540 <ab_np::simd_quad_intel_spine(unsigned short const*, unsigned short const*, int, unsigned short)+0x5e0>
  40a556:	cs nopw 0x0(%rax,%rax,1)
  40a560:	cmp    %dx,%cx
  40a563:	mov    -0x8(%rbp),%r12
  40a567:	sete   %al
  40a56a:	jmp    40a9a5 <ab_np::simd_quad_intel_spine(unsigned short const*, unsigned short const*, int, unsigned short)+0xa45>
  40a56f:	nop
  40a570:	mov    %r12,-0x8(%rbp)
  40a574:	mov    %rsi,%r10
  40a577:	mov    %ebx,%eax
  40a579:	xor    %r8d,%r8d
  40a57c:	prefetcht0 (%rsi)
  40a57f:	nop
  40a580:	mov    %eax,%esi
  40a582:	sar    $0x2,%esi
  40a585:	lea    (%rsi,%r8,1),%edx
  40a589:	lea    (%rdx,%rsi,1),%edi
  40a58c:	movslq %edx,%rdx
  40a58f:	cmp    %cx,(%r10,%rdx,2)
  40a594:	movslq %edi,%r12
  40a597:	setb   %dl
  40a59a:	cmp    %cx,(%r10,%r12,2)
  40a59f:	movzbl %dl,%edx
  40a5a2:	adc    $0x0,%edx
  40a5a5:	add    %esi,%edi
  40a5a7:	movslq %edi,%rdi
  40a5aa:	cmp    %cx,(%r10,%rdi,2)
  40a5af:	adc    $0x0,%edx
  40a5b2:	imul   %esi,%edx
  40a5b5:	add    %edx,%r8d
  40a5b8:	lea    (%rsi,%rsi,2),%edx
  40a5bb:	sub    %edx,%eax
  40a5bd:	cmp    $0x3,%eax
  40a5c0:	jg     40a580 <ab_np::simd_quad_intel_spine(unsigned short const*, unsigned short const*, int, unsigned short)+0x620>
  40a5c2:	cmp    $0x1,%eax
  40a5c5:	jle    40a5fb <ab_np::simd_quad_intel_spine(unsigned short const*, unsigned short const*, int, unsigned short)+0x69b>
  40a5c7:	nopl   (%rax)
  40a5ca:	data16 cs nopw 0x0(%rax,%rax,1)
  40a5d5:	data16 cs nopw 0x0(%rax,%rax,1)
  40a5e0:	mov    %eax,%edx
  40a5e2:	sar    $1,%edx
  40a5e4:	lea    (%rdx,%r8,1),%esi
  40a5e8:	movslq %esi,%rdi
  40a5eb:	cmp    %cx,(%r10,%rdi,2)
  40a5f0:	cmovb  %esi,%r8d
  40a5f4:	sub    %edx,%eax
  40a5f6:	cmp    $0x1,%eax
  40a5f9:	jg     40a5e0 <ab_np::simd_quad_intel_spine(unsigned short const*, unsigned short const*, int, unsigned short)+0x680>
  40a5fb:	movslq %r8d,%rax
  40a5fe:	cmp    %cx,(%r10,%rax,2)
  40a603:	adc    $0x0,%r8d
  40a607:	cmp    %ebx,%r8d
  40a60a:	jl     40a980 <ab_np::simd_quad_intel_spine(unsigned short const*, unsigned short const*, int, unsigned short)+0xa20>
  40a610:	mov    %ebx,%eax
  40a612:	shl    $0x5,%eax
  40a615:	cmp    %eax,%r11d
  40a618:	jle    40a9f8 <ab_np::simd_quad_intel_spine(unsigned short const*, unsigned short const*, int, unsigned short)+0xa98>
  40a61e:	mov    %ebx,%ebx
  40a620:	mov    $0x17,%r8d
  40a626:	mov    %r11d,%r12d
  40a629:	shl    $0x6,%rbx
  40a62d:	sub    %eax,%r12d
  40a630:	lea    (%r9,%rbx,1),%rdi
  40a634:	lea    -0x1(%r12),%ebx
  40a639:	mov    %rdi,%r10
  40a63c:	shr    $1,%r10
  40a63f:	neg    %r10
  40a642:	mov    %r10d,%esi
  40a645:	and    $0xf,%esi
  40a648:	lea    0x10(%rsi),%edx
  40a64b:	cmp    %r8d,%edx
  40a64e:	cmovb  %r8d,%edx
  40a652:	cmp    %edx,%ebx
  40a654:	jb     40a96c <ab_np::simd_quad_intel_spine(unsigned short const*, unsigned short const*, int, unsigned short)+0xa0c>
  40a65a:	test   %esi,%esi
  40a65c:	je     40a7c7 <ab_np::simd_quad_intel_spine(unsigned short const*, unsigned short const*, int, unsigned short)+0x867>
  40a662:	movzwl (%rdi),%edx
  40a665:	cmp    %cx,%dx
  40a668:	jae    40a560 <ab_np::simd_quad_intel_spine(unsigned short const*, unsigned short const*, int, unsigned short)+0x600>
  40a66e:	test   $0xe,%r10b
  40a672:	je     40aa6b <ab_np::simd_quad_intel_spine(unsigned short const*, unsigned short const*, int, unsigned short)+0xb0b>
  40a678:	lea    0x1(%rax),%r8d
  40a67c:	movzwl (%r9,%r8,2),%edx
  40a681:	cmp    %cx,%dx
  40a684:	jae    40a560 <ab_np::simd_quad_intel_spine(unsigned short const*, unsigned short const*, int, unsigned short)+0x600>
  40a68a:	cmp    $0x2,%esi
  40a68d:	jbe    40aa7c <ab_np::simd_quad_intel_spine(unsigned short const*, unsigned short const*, int, unsigned short)+0xb1c>
  40a693:	movzwl 0x2(%r9,%r8,2),%edx
  40a699:	cmp    %cx,%dx
  40a69c:	jae    40a560 <ab_np::simd_quad_intel_spine(unsigned short const*, unsigned short const*, int, unsigned short)+0x600>
  40a6a2:	test   $0xc,%r10b
  40a6a6:	je     40aa98 <ab_np::simd_quad_intel_spine(unsigned short const*, unsigned short const*, int, unsigned short)+0xb38>
  40a6ac:	movzwl 0x4(%r9,%r8,2),%edx
  40a6b2:	cmp    %cx,%dx
  40a6b5:	jae    40a560 <ab_np::simd_quad_intel_spine(unsigned short const*, unsigned short const*, int, unsigned short)+0x600>
  40a6bb:	cmp    $0x4,%esi
  40a6be:	jbe    40aaa0 <ab_np::simd_quad_intel_spine(unsigned short const*, unsigned short const*, int, unsigned short)+0xb40>
  40a6c4:	movzwl 0x6(%r9,%r8,2),%edx
  40a6ca:	cmp    %cx,%dx
  40a6cd:	jae    40a560 <ab_np::simd_quad_intel_spine(unsigned short const*, unsigned short const*, int, unsigned short)+0x600>
  40a6d3:	cmp    $0x5,%esi
  40a6d6:	je     40aab2 <ab_np::simd_quad_intel_spine(unsigned short const*, unsigned short const*, int, unsigned short)+0xb52>
  40a6dc:	movzwl 0x8(%r9,%r8,2),%edx
  40a6e2:	cmp    %cx,%dx
  40a6e5:	jae    40a560 <ab_np::simd_quad_intel_spine(unsigned short const*, unsigned short const*, int, unsigned short)+0x600>
  40a6eb:	cmp    $0x6,%esi
  40a6ee:	je     40aaba <ab_np::simd_quad_intel_spine(unsigned short const*, unsigned short const*, int, unsigned short)+0xb5a>
  40a6f4:	movzwl 0xa(%r9,%r8,2),%edx
  40a6fa:	cmp    %cx,%dx
  40a6fd:	jae    40a560 <ab_np::simd_quad_intel_spine(unsigned short const*, unsigned short const*, int, unsigned short)+0x600>
  40a703:	and    $0x8,%r10d
  40a707:	je     40aacb <ab_np::simd_quad_intel_spine(unsigned short const*, unsigned short const*, int, unsigned short)+0xb6b>
  40a70d:	movzwl 0xc(%r9,%r8,2),%edx
  40a713:	cmp    %cx,%dx
  40a716:	jae    40a560 <ab_np::simd_quad_intel_spine(unsigned short const*, unsigned short const*, int, unsigned short)+0x600>
  40a71c:	cmp    $0x8,%esi
  40a71f:	je     40aaee <ab_np::simd_quad_intel_spine(unsigned short const*, unsigned short const*, int, unsigned short)+0xb8e>
  40a725:	movzwl 0xe(%r9,%r8,2),%edx
  40a72b:	cmp    %cx,%dx
  40a72e:	jae    40a560 <ab_np::simd_quad_intel_spine(unsigned short const*, unsigned short const*, int, unsigned short)+0x600>
  40a734:	cmp    $0x9,%esi
  40a737:	je     40ab16 <ab_np::simd_quad_intel_spine(unsigned short const*, unsigned short const*, int, unsigned short)+0xbb6>
  40a73d:	movzwl 0x10(%r9,%r8,2),%edx
  40a743:	cmp    %cx,%dx
  40a746:	jae    40a560 <ab_np::simd_quad_intel_spine(unsigned short const*, unsigned short const*, int, unsigned short)+0x600>
  40a74c:	cmp    $0xa,%esi
  40a74f:	je     40ab1e <ab_np::simd_quad_intel_spine(unsigned short const*, unsigned short const*, int, unsigned short)+0xbbe>
  40a755:	movzwl 0x12(%r9,%r8,2),%edx
  40a75b:	cmp    %cx,%dx
  40a75e:	jae    40a560 <ab_np::simd_quad_intel_spine(unsigned short const*, unsigned short const*, int, unsigned short)+0x600>
  40a764:	cmp    $0xb,%esi
  40a767:	je     40ab42 <ab_np::simd_quad_intel_spine(unsigned short const*, unsigned short const*, int, unsigned short)+0xbe2>
  40a76d:	movzwl 0x14(%r9,%r8,2),%edx
  40a773:	cmp    %cx,%dx
  40a776:	jae    40a560 <ab_np::simd_quad_intel_spine(unsigned short const*, unsigned short const*, int, unsigned short)+0x600>
  40a77c:	cmp    $0xc,%esi
  40a77f:	je     40ab3a <ab_np::simd_quad_intel_spine(unsigned short const*, unsigned short const*, int, unsigned short)+0xbda>
  40a785:	movzwl 0x16(%r9,%r8,2),%edx
  40a78b:	cmp    %cx,%dx
  40a78e:	jae    40a560 <ab_np::simd_quad_intel_spine(unsigned short const*, unsigned short const*, int, unsigned short)+0x600>
  40a794:	cmp    $0xd,%esi
  40a797:	je     40ab62 <ab_np::simd_quad_intel_spine(unsigned short const*, unsigned short const*, int, unsigned short)+0xc02>
  40a79d:	movzwl 0x18(%r9,%r8,2),%edx
  40a7a3:	cmp    %cx,%dx
  40a7a6:	jae    40a560 <ab_np::simd_quad_intel_spine(unsigned short const*, unsigned short const*, int, unsigned short)+0x600>
  40a7ac:	cmp    $0xf,%esi
  40a7af:	jne    40ab72 <ab_np::simd_quad_intel_spine(unsigned short const*, unsigned short const*, int, unsigned short)+0xc12>
  40a7b5:	movzwl 0x1a(%r9,%r8,2),%edx
  40a7bb:	cmp    %cx,%dx
  40a7be:	jae    40a560 <ab_np::simd_quad_intel_spine(unsigned short const*, unsigned short const*, int, unsigned short)+0x600>
  40a7c4:	add    $0xf,%eax
  40a7c7:	mov    %r12d,%r8d
  40a7ca:	xor    %edx,%edx
  40a7cc:	sub    %esi,%r8d
  40a7cf:	lea    (%rdi,%rsi,2),%rsi
  40a7d3:	mov    %r8d,%edi
  40a7d6:	and    $0xfffffff0,%edi
  40a7d9:	jmp    40a7ef <ab_np::simd_quad_intel_spine(unsigned short const*, unsigned short const*, int, unsigned short)+0x88f>
  40a7db:	nopl   0x0(%rax,%rax,1)
  40a7e0:	add    $0x10,%edx
  40a7e3:	add    $0x20,%rsi
  40a7e7:	cmp    %edx,%edi
  40a7e9:	je     40a9f0 <ab_np::simd_quad_intel_spine(unsigned short const*, unsigned short const*, int, unsigned short)+0xa90>
  40a7ef:	vpminuw (%rsi),%ymm0,%ymm1
  40a7f4:	vpcmpeqw %ymm1,%ymm0,%ymm1
  40a7f8:	vptest %ymm1,%ymm1
  40a7fd:	je     40a7e0 <ab_np::simd_quad_intel_spine(unsigned short const*, unsigned short const*, int, unsigned short)+0x880>
  40a7ff:	add    %edx,%eax
  40a801:	jmp    40a96c <ab_np::simd_quad_intel_spine(unsigned short const*, unsigned short const*, int, unsigned short)+0xa0c>
  40a806:	cs nopw 0x0(%rax,%rax,1)
  40a810:	cmp    $0x7,%edx
  40a813:	jg     40a8a8 <ab_np::simd_quad_intel_spine(unsigned short const*, unsigned short const*, int, unsigned short)+0x948>
  40a819:	test   %edx,%edx
  40a81b:	jle    40a210 <ab_np::simd_quad_intel_spine(unsigned short const*, unsigned short const*, int, unsigned short)+0x2b0>
  40a821:	movzwl (%rdi),%eax
  40a824:	cmp    %cx,%ax
  40a827:	jae    40a899 <ab_np::simd_quad_intel_spine(unsigned short const*, unsigned short const*, int, unsigned short)+0x939>
  40a829:	cmp    $0x1,%edx
  40a82c:	je     40a210 <ab_np::simd_quad_intel_spine(unsigned short const*, unsigned short const*, int, unsigned short)+0x2b0>
  40a832:	movzwl 0x2(%rdi),%eax
  40a836:	cmp    %cx,%ax
  40a839:	jae    40a899 <ab_np::simd_quad_intel_spine(unsigned short const*, unsigned short const*, int, unsigned short)+0x939>
  40a83b:	cmp    $0x2,%edx
  40a83e:	je     40a210 <ab_np::simd_quad_intel_spine(unsigned short const*, unsigned short const*, int, unsigned short)+0x2b0>
  40a844:	movzwl 0x4(%rdi),%eax
  40a848:	cmp    %cx,%ax
  40a84b:	jae    40a899 <ab_np::simd_quad_intel_spine(unsigned short const*, unsigned short const*, int, unsigned short)+0x939>
  40a84d:	cmp    $0x3,%edx
  40a850:	je     40a210 <ab_np::simd_quad_intel_spine(unsigned short const*, unsigned short const*, int, unsigned short)+0x2b0>
  40a856:	movzwl 0x6(%rdi),%eax
  40a85a:	cmp    %cx,%ax
  40a85d:	jae    40a899 <ab_np::simd_quad_intel_spine(unsigned short const*, unsigned short const*, int, unsigned short)+0x939>
  40a85f:	cmp    $0x4,%edx
  40a862:	je     40a210 <ab_np::simd_quad_intel_spine(unsigned short const*, unsigned short const*, int, unsigned short)+0x2b0>
  40a868:	movzwl 0x8(%rdi),%eax
  40a86c:	cmp    %cx,%ax
  40a86f:	jae    40a899 <ab_np::simd_quad_intel_spine(unsigned short const*, unsigned short const*, int, unsigned short)+0x939>
  40a871:	cmp    $0x5,%edx
  40a874:	je     40a210 <ab_np::simd_quad_intel_spine(unsigned short const*, unsigned short const*, int, unsigned short)+0x2b0>
  40a87a:	movzwl 0xa(%rdi),%eax
  40a87e:	cmp    %cx,%ax
  40a881:	jae    40a899 <ab_np::simd_quad_intel_spine(unsigned short const*, unsigned short const*, int, unsigned short)+0x939>
  40a883:	cmp    $0x7,%edx
  40a886:	jne    40a210 <ab_np::simd_quad_intel_spine(unsigned short const*, unsigned short const*, int, unsigned short)+0x2b0>
  40a88c:	movzwl 0xc(%rdi),%eax
  40a890:	cmp    %cx,%ax
  40a893:	jb     40a210 <ab_np::simd_quad_intel_spine(unsigned short const*, unsigned short const*, int, unsigned short)+0x2b0>
  40a899:	cmp    %ax,%cx
  40a89c:	sete   %al
  40a89f:	vzeroupper
  40a8a2:	ret
  40a8a3:	nopl   0x0(%rax,%rax,1)
  40a8a8:	vpcmpeqw (%rdi),%xmm0,%xmm0
  40a8ac:	vpmovmskb %xmm0,%eax
  40a8b0:	test   %eax,%eax
  40a8b2:	jne    40a9b0 <ab_np::simd_quad_intel_spine(unsigned short const*, unsigned short const*, int, unsigned short)+0xa50>
  40a8b8:	cmp    $0x8,%edx
  40a8bb:	je     40a210 <ab_np::simd_quad_intel_spine(unsigned short const*, unsigned short const*, int, unsigned short)+0x2b0>
  40a8c1:	movzwl 0x10(%rdi),%eax
  40a8c5:	cmp    %cx,%ax
  40a8c8:	jae    40a899 <ab_np::simd_quad_intel_spine(unsigned short const*, unsigned short const*, int, unsigned short)+0x939>
  40a8ca:	cmp    $0x9,%edx
  40a8cd:	je     40a210 <ab_np::simd_quad_intel_spine(unsigned short const*, unsigned short const*, int, unsigned short)+0x2b0>
  40a8d3:	movzwl 0x12(%rdi),%eax
  40a8d7:	cmp    %cx,%ax
  40a8da:	jae    40a899 <ab_np::simd_quad_intel_spine(unsigned short const*, unsigned short const*, int, unsigned short)+0x939>
  40a8dc:	cmp    $0xa,%edx
  40a8df:	je     40a210 <ab_np::simd_quad_intel_spine(unsigned short const*, unsigned short const*, int, unsigned short)+0x2b0>
  40a8e5:	movzwl 0x14(%rdi),%eax
  40a8e9:	cmp    %cx,%ax
  40a8ec:	jae    40a899 <ab_np::simd_quad_intel_spine(unsigned short const*, unsigned short const*, int, unsigned short)+0x939>
  40a8ee:	cmp    $0xb,%edx
  40a8f1:	je     40a210 <ab_np::simd_quad_intel_spine(unsigned short const*, unsigned short const*, int, unsigned short)+0x2b0>
  40a8f7:	movzwl 0x16(%rdi),%eax
  40a8fb:	cmp    %cx,%ax
  40a8fe:	jae    40a899 <ab_np::simd_quad_intel_spine(unsigned short const*, unsigned short const*, int, unsigned short)+0x939>
  40a900:	cmp    $0xc,%edx
  40a903:	je     40a210 <ab_np::simd_quad_intel_spine(unsigned short const*, unsigned short const*, int, unsigned short)+0x2b0>
  40a909:	movzwl 0x18(%rdi),%eax
  40a90d:	cmp    %cx,%ax
  40a910:	jae    40a899 <ab_np::simd_quad_intel_spine(unsigned short const*, unsigned short const*, int, unsigned short)+0x939>
  40a912:	cmp    $0xd,%edx
  40a915:	je     40a210 <ab_np::simd_quad_intel_spine(unsigned short const*, unsigned short const*, int, unsigned short)+0x2b0>
  40a91b:	movzwl 0x1a(%rdi),%eax
  40a91f:	cmp    %cx,%ax
  40a922:	jae    40a899 <ab_np::simd_quad_intel_spine(unsigned short const*, unsigned short const*, int, unsigned short)+0x939>
  40a928:	cmp    $0xf,%edx
  40a92b:	jne    40a210 <ab_np::simd_quad_intel_spine(unsigned short const*, unsigned short const*, int, unsigned short)+0x2b0>
  40a931:	movzwl 0x1c(%rdi),%eax
  40a935:	cmp    %cx,%ax
  40a938:	jae    40a899 <ab_np::simd_quad_intel_spine(unsigned short const*, unsigned short const*, int, unsigned short)+0x939>
  40a93e:	xor    %eax,%eax
  40a940:	jmp    40a212 <ab_np::simd_quad_intel_spine(unsigned short const*, unsigned short const*, int, unsigned short)+0x2b2>
  40a945:	nopl   0x0(%rax,%rax,1)
  40a94a:	data16 cs nopw 0x0(%rax,%rax,1)
  40a955:	data16 cs nopw 0x0(%rax,%rax,1)
  40a960:	inc    %rax
  40a963:	cmp    %eax,%r11d
  40a966:	jle    40a9f8 <ab_np::simd_quad_intel_spine(unsigned short const*, unsigned short const*, int, unsigned short)+0xa98>
  40a96c:	movzwl (%r9,%rax,2),%edx
  40a971:	cmp    %cx,%dx
  40a974:	jb     40a960 <ab_np::simd_quad_intel_spine(unsigned short const*, unsigned short const*, int, unsigned short)+0xa00>
  40a976:	jmp    40a560 <ab_np::simd_quad_intel_spine(unsigned short const*, unsigned short const*, int, unsigned short)+0x600>
  40a97b:	nopl   0x0(%rax,%rax,1)
  40a980:	shl    $0x5,%r8d
  40a984:	mov    -0x8(%rbp),%r12
  40a988:	movslq %r8d,%r8
  40a98b:	lea    (%r9,%r8,2),%rax
  40a98f:	vpcmpeqw (%rax),%ymm0,%ymm1
  40a993:	vpcmpeqw 0x20(%rax),%ymm0,%ymm0
  40a998:	vpor   %ymm0,%ymm1,%ymm0
  40a99c:	vpmovmskb %ymm0,%eax
  40a9a0:	test   %eax,%eax
  40a9a2:	setne  %al
  40a9a5:	vzeroupper
  40a9a8:	mov    -0x10(%rbp),%rbx
  40a9ac:	leave
  40a9ad:	ret
  40a9ae:	xchg   %ax,%ax
  40a9b0:	mov    $0x1,%eax
  40a9b5:	vzeroupper
  40a9b8:	ret
  40a9b9:	nopl   0x0(%rax)
  40a9c0:	xor    %eax,%eax
  40a9c2:	cmp    %cx,0x3e(%rdi)
  40a9c6:	jb     40a2be <ab_np::simd_quad_intel_spine(unsigned short const*, unsigned short const*, int, unsigned short)+0x35e>
  40a9cc:	shl    $0x5,%eax
  40a9cf:	cltq
  40a9d1:	lea    (%r9,%rax,2),%rax
  40a9d5:	vpcmpeqw (%rax),%ymm0,%ymm1
  40a9d9:	vpcmpeqw 0x20(%rax),%ymm0,%ymm0
  40a9de:	vpor   %ymm0,%ymm1,%ymm0
  40a9e2:	vpmovmskb %ymm0,%eax
  40a9e6:	test   %eax,%eax
  40a9e8:	setne  %al
  40a9eb:	jmp    40a9a5 <ab_np::simd_quad_intel_spine(unsigned short const*, unsigned short const*, int, unsigned short)+0xa45>
  40a9ed:	nopl   (%rax)
  40a9f0:	cmp    %edi,%r8d
  40a9f3:	jne    40aa30 <ab_np::simd_quad_intel_spine(unsigned short const*, unsigned short const*, int, unsigned short)+0xad0>
  40a9f5:	nopl   (%rax)
  40a9f8:	mov    -0x8(%rbp),%r12
  40a9fc:	xor    %eax,%eax
  40a9fe:	vzeroupper
  40aa01:	mov    -0x10(%rbp),%rbx
  40aa05:	leave
  40aa06:	ret
  40aa07:	mov    %edx,%edi
  40aa09:	movzwl (%r9,%rdi,2),%eax
  40aa0e:	cmp    %cx,%ax
  40aa11:	jae    40a899 <ab_np::simd_quad_intel_spine(unsigned short const*, unsigned short const*, int, unsigned short)+0x939>
  40aa17:	movzwl 0x2(%r9,%rdi,2),%eax
  40aa1d:	lea    0x2(%rdi,%rdi,1),%rsi
  40aa22:	cmp    %cx,%ax
  40aa25:	jb     40a0cc <ab_np::simd_quad_intel_spine(unsigned short const*, unsigned short const*, int, unsigned short)+0x16c>
  40aa2b:	jmp    40a899 <ab_np::simd_quad_intel_spine(unsigned short const*, unsigned short const*, int, unsigned short)+0x939>
  40aa30:	add    %edi,%eax
  40aa32:	jmp    40a96c <ab_np::simd_quad_intel_spine(unsigned short const*, unsigned short const*, int, unsigned short)+0xa0c>
  40aa37:	mov    $0x10,%edx
  40aa3c:	jmp    40a06a <ab_np::simd_quad_intel_spine(unsigned short const*, unsigned short const*, int, unsigned short)+0x10a>
  40aa41:	mov    $0x10,%edx
  40aa46:	jmp    40a090 <ab_np::simd_quad_intel_spine(unsigned short const*, unsigned short const*, int, unsigned short)+0x130>
  40aa4b:	mov    $0x40,%edx
  40aa50:	add    %edx,%eax
  40aa52:	jmp    40a537 <ab_np::simd_quad_intel_spine(unsigned short const*, unsigned short const*, int, unsigned short)+0x5d7>
  40aa57:	mov    $0x11,%edx
  40aa5c:	jmp    40a06a <ab_np::simd_quad_intel_spine(unsigned short const*, unsigned short const*, int, unsigned short)+0x10a>
  40aa61:	mov    $0x12,%edx
  40aa66:	jmp    40a06a <ab_np::simd_quad_intel_spine(unsigned short const*, unsigned short const*, int, unsigned short)+0x10a>
  40aa6b:	inc    %eax
  40aa6d:	jmp    40a7c7 <ab_np::simd_quad_intel_spine(unsigned short const*, unsigned short const*, int, unsigned short)+0x867>
  40aa72:	mov    $0x13,%edx
  40aa77:	jmp    40a06a <ab_np::simd_quad_intel_spine(unsigned short const*, unsigned short const*, int, unsigned short)+0x10a>
  40aa7c:	add    $0x2,%eax
  40aa7f:	jmp    40a7c7 <ab_np::simd_quad_intel_spine(unsigned short const*, unsigned short const*, int, unsigned short)+0x867>
  40aa84:	mov    $0x14,%edx
  40aa89:	jmp    40a06a <ab_np::simd_quad_intel_spine(unsigned short const*, unsigned short const*, int, unsigned short)+0x10a>
  40aa8e:	mov    $0x15,%edx
  40aa93:	jmp    40a06a <ab_np::simd_quad_intel_spine(unsigned short const*, unsigned short const*, int, unsigned short)+0x10a>
  40aa98:	add    $0x3,%eax
  40aa9b:	jmp    40a7c7 <ab_np::simd_quad_intel_spine(unsigned short const*, unsigned short const*, int, unsigned short)+0x867>
  40aaa0:	add    $0x4,%eax
  40aaa3:	jmp    40a7c7 <ab_np::simd_quad_intel_spine(unsigned short const*, unsigned short const*, int, unsigned short)+0x867>
  40aaa8:	mov    $0x16,%edx
  40aaad:	jmp    40a06a <ab_np::simd_quad_intel_spine(unsigned short const*, unsigned short const*, int, unsigned short)+0x10a>
  40aab2:	add    $0x5,%eax
  40aab5:	jmp    40a7c7 <ab_np::simd_quad_intel_spine(unsigned short const*, unsigned short const*, int, unsigned short)+0x867>
  40aaba:	add    $0x6,%eax
  40aabd:	jmp    40a7c7 <ab_np::simd_quad_intel_spine(unsigned short const*, unsigned short const*, int, unsigned short)+0x867>
  40aac2:	xor    %edx,%edx
  40aac4:	add    %edx,%eax
  40aac6:	jmp    40a537 <ab_np::simd_quad_intel_spine(unsigned short const*, unsigned short const*, int, unsigned short)+0x5d7>
  40aacb:	add    $0x7,%eax
  40aace:	jmp    40a7c7 <ab_np::simd_quad_intel_spine(unsigned short const*, unsigned short const*, int, unsigned short)+0x867>
  40aad3:	mov    $0x10,%edx
  40aad8:	add    %edx,%eax
  40aada:	jmp    40a537 <ab_np::simd_quad_intel_spine(unsigned short const*, unsigned short const*, int, unsigned short)+0x5d7>
  40aadf:	inc    %eax
  40aae1:	jmp    40a47a <ab_np::simd_quad_intel_spine(unsigned short const*, unsigned short const*, int, unsigned short)+0x51a>
  40aae6:	add    $0x2,%eax
  40aae9:	jmp    40a47a <ab_np::simd_quad_intel_spine(unsigned short const*, unsigned short const*, int, unsigned short)+0x51a>
  40aaee:	add    $0x8,%eax
  40aaf1:	jmp    40a7c7 <ab_np::simd_quad_intel_spine(unsigned short const*, unsigned short const*, int, unsigned short)+0x867>
  40aaf6:	mov    $0x20,%edx
  40aafb:	add    %edx,%eax
  40aafd:	jmp    40a537 <ab_np::simd_quad_intel_spine(unsigned short const*, unsigned short const*, int, unsigned short)+0x5d7>
  40ab02:	add    $0x3,%eax
  40ab05:	jmp    40a47a <ab_np::simd_quad_intel_spine(unsigned short const*, unsigned short const*, int, unsigned short)+0x51a>
  40ab0a:	mov    $0x30,%edx
  40ab0f:	add    %edx,%eax
  40ab11:	jmp    40a537 <ab_np::simd_quad_intel_spine(unsigned short const*, unsigned short const*, int, unsigned short)+0x5d7>
  40ab16:	add    $0x9,%eax
  40ab19:	jmp    40a7c7 <ab_np::simd_quad_intel_spine(unsigned short const*, unsigned short const*, int, unsigned short)+0x867>
  40ab1e:	add    $0xa,%eax
  40ab21:	jmp    40a7c7 <ab_np::simd_quad_intel_spine(unsigned short const*, unsigned short const*, int, unsigned short)+0x867>
  40ab26:	add    $0x4,%eax
  40ab29:	jmp    40a47a <ab_np::simd_quad_intel_spine(unsigned short const*, unsigned short const*, int, unsigned short)+0x51a>
  40ab2e:	mov    $0x50,%edx
  40ab33:	add    %edx,%eax
  40ab35:	jmp    40a537 <ab_np::simd_quad_intel_spine(unsigned short const*, unsigned short const*, int, unsigned short)+0x5d7>
  40ab3a:	add    $0xc,%eax
  40ab3d:	jmp    40a7c7 <ab_np::simd_quad_intel_spine(unsigned short const*, unsigned short const*, int, unsigned short)+0x867>
  40ab42:	add    $0xb,%eax
  40ab45:	jmp    40a7c7 <ab_np::simd_quad_intel_spine(unsigned short const*, unsigned short const*, int, unsigned short)+0x867>
  40ab4a:	add    $0x5,%eax
  40ab4d:	jmp    40a47a <ab_np::simd_quad_intel_spine(unsigned short const*, unsigned short const*, int, unsigned short)+0x51a>
  40ab52:	add    $0x6,%eax
  40ab55:	jmp    40a47a <ab_np::simd_quad_intel_spine(unsigned short const*, unsigned short const*, int, unsigned short)+0x51a>
  40ab5a:	add    $0x7,%eax
  40ab5d:	jmp    40a47a <ab_np::simd_quad_intel_spine(unsigned short const*, unsigned short const*, int, unsigned short)+0x51a>
  40ab62:	add    $0xd,%eax
  40ab65:	jmp    40a7c7 <ab_np::simd_quad_intel_spine(unsigned short const*, unsigned short const*, int, unsigned short)+0x867>
  40ab6a:	add    $0x8,%eax
  40ab6d:	jmp    40a47a <ab_np::simd_quad_intel_spine(unsigned short const*, unsigned short const*, int, unsigned short)+0x51a>
  40ab72:	add    $0xe,%eax
  40ab75:	jmp    40a7c7 <ab_np::simd_quad_intel_spine(unsigned short const*, unsigned short const*, int, unsigned short)+0x867>
  40ab7a:	add    $0x9,%eax
  40ab7d:	jmp    40a47a <ab_np::simd_quad_intel_spine(unsigned short const*, unsigned short const*, int, unsigned short)+0x51a>
  40ab82:	add    $0xa,%eax
  40ab85:	jmp    40a47a <ab_np::simd_quad_intel_spine(unsigned short const*, unsigned short const*, int, unsigned short)+0x51a>
  40ab8a:	add    $0xb,%eax
  40ab8d:	jmp    40a47a <ab_np::simd_quad_intel_spine(unsigned short const*, unsigned short const*, int, unsigned short)+0x51a>
  40ab92:	add    $0xc,%eax
  40ab95:	jmp    40a47a <ab_np::simd_quad_intel_spine(unsigned short const*, unsigned short const*, int, unsigned short)+0x51a>
  40ab9a:	add    $0xe,%eax
  40ab9d:	jmp    40a47a <ab_np::simd_quad_intel_spine(unsigned short const*, unsigned short const*, int, unsigned short)+0x51a>
  40aba2:	add    $0xd,%eax
  40aba5:	jmp    40a47a <ab_np::simd_quad_intel_spine(unsigned short const*, unsigned short const*, int, unsigned short)+0x51a>
  40abaa:	nopw   0x0(%rax,%rax,1)
