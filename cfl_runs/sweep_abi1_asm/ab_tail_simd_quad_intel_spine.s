000000000040c120 <ab_tail::simd_quad_intel_spine(unsigned short const*, unsigned short const*, int, unsigned short)>:
  40c120:	mov    %ecx,%r8d
  40c123:	mov    %rdi,%r9
  40c126:	mov    %edx,%r11d
  40c129:	vmovd  %r8d,%xmm0
  40c12e:	vpbroadcastw %xmm0,%ymm0
  40c133:	cmp    $0x1f,%edx
  40c136:	jg     40c3f0 <ab_tail::simd_quad_intel_spine(unsigned short const*, unsigned short const*, int, unsigned short)+0x2d0>
  40c13c:	cmp    $0xf,%edx
  40c13f:	jle    40c500 <ab_tail::simd_quad_intel_spine(unsigned short const*, unsigned short const*, int, unsigned short)+0x3e0>
  40c145:	vpcmpeqw (%rdi),%ymm0,%ymm1
  40c149:	vpmovmskb %ymm1,%eax
  40c14d:	test   %eax,%eax
  40c14f:	jne    40c6d8 <ab_tail::simd_quad_intel_spine(unsigned short const*, unsigned short const*, int, unsigned short)+0x5b8>
  40c155:	cmp    $0x10,%edx
  40c158:	je     40c3e8 <ab_tail::simd_quad_intel_spine(unsigned short const*, unsigned short const*, int, unsigned short)+0x2c8>
  40c15e:	lea    0x20(%rdi),%rdi
  40c162:	mov    $0xb,%esi
  40c167:	mov    %rdi,%rdx
  40c16a:	shr    $1,%rdx
  40c16d:	neg    %rdx
  40c170:	mov    %edx,%ecx
  40c172:	and    $0x7,%ecx
  40c175:	lea    0x8(%rcx),%eax
  40c178:	cmp    %esi,%eax
  40c17a:	cmovb  %esi,%eax
  40c17d:	lea    -0x11(%r11),%esi
  40c181:	cmp    %eax,%esi
  40c183:	jb     40c746 <ab_tail::simd_quad_intel_spine(unsigned short const*, unsigned short const*, int, unsigned short)+0x626>
  40c189:	test   %ecx,%ecx
  40c18b:	je     40c73c <ab_tail::simd_quad_intel_spine(unsigned short const*, unsigned short const*, int, unsigned short)+0x61c>
  40c191:	movzwl 0x20(%r9),%eax
  40c196:	cmp    %r8w,%ax
  40c19a:	jae    40c589 <ab_tail::simd_quad_intel_spine(unsigned short const*, unsigned short const*, int, unsigned short)+0x469>
  40c1a0:	test   $0x6,%dl
  40c1a3:	je     40c750 <ab_tail::simd_quad_intel_spine(unsigned short const*, unsigned short const*, int, unsigned short)+0x630>
  40c1a9:	movzwl 0x22(%r9),%eax
  40c1ae:	cmp    %r8w,%ax
  40c1b2:	jae    40c589 <ab_tail::simd_quad_intel_spine(unsigned short const*, unsigned short const*, int, unsigned short)+0x469>
  40c1b8:	cmp    $0x2,%ecx
  40c1bb:	jbe    40c75a <ab_tail::simd_quad_intel_spine(unsigned short const*, unsigned short const*, int, unsigned short)+0x63a>
  40c1c1:	movzwl 0x24(%r9),%eax
  40c1c6:	cmp    %r8w,%ax
  40c1ca:	jae    40c589 <ab_tail::simd_quad_intel_spine(unsigned short const*, unsigned short const*, int, unsigned short)+0x469>
  40c1d0:	and    $0x4,%edx
  40c1d3:	je     40c764 <ab_tail::simd_quad_intel_spine(unsigned short const*, unsigned short const*, int, unsigned short)+0x644>
  40c1d9:	movzwl 0x26(%r9),%eax
  40c1de:	cmp    %r8w,%ax
  40c1e2:	jae    40c589 <ab_tail::simd_quad_intel_spine(unsigned short const*, unsigned short const*, int, unsigned short)+0x469>
  40c1e8:	cmp    $0x4,%ecx
  40c1eb:	je     40c76e <ab_tail::simd_quad_intel_spine(unsigned short const*, unsigned short const*, int, unsigned short)+0x64e>
  40c1f1:	movzwl 0x28(%r9),%eax
  40c1f6:	cmp    %r8w,%ax
  40c1fa:	jae    40c589 <ab_tail::simd_quad_intel_spine(unsigned short const*, unsigned short const*, int, unsigned short)+0x469>
  40c200:	cmp    $0x5,%ecx
  40c203:	je     40c778 <ab_tail::simd_quad_intel_spine(unsigned short const*, unsigned short const*, int, unsigned short)+0x658>
  40c209:	movzwl 0x2a(%r9),%eax
  40c20e:	cmp    %r8w,%ax
  40c212:	jae    40c589 <ab_tail::simd_quad_intel_spine(unsigned short const*, unsigned short const*, int, unsigned short)+0x469>
  40c218:	cmp    $0x7,%ecx
  40c21b:	jne    40c782 <ab_tail::simd_quad_intel_spine(unsigned short const*, unsigned short const*, int, unsigned short)+0x662>
  40c221:	movzwl 0x2c(%r9),%eax
  40c226:	cmp    %r8w,%ax
  40c22a:	jae    40c589 <ab_tail::simd_quad_intel_spine(unsigned short const*, unsigned short const*, int, unsigned short)+0x469>
  40c230:	mov    $0x17,%edx
  40c235:	mov    %ecx,%eax
  40c237:	vpminuw (%rdi,%rax,2),%xmm0,%xmm1
  40c23d:	vpcmpeqw %xmm1,%xmm0,%xmm0
  40c241:	vptest %xmm0,%xmm0
  40c246:	jne    40c6e1 <ab_tail::simd_quad_intel_spine(unsigned short const*, unsigned short const*, int, unsigned short)+0x5c1>
  40c24c:	lea    -0x18(%r11),%eax
  40c250:	cmp    %ecx,%eax
  40c252:	je     40c3e8 <ab_tail::simd_quad_intel_spine(unsigned short const*, unsigned short const*, int, unsigned short)+0x2c8>
  40c258:	add    $0x8,%edx
  40c25b:	mov    %edx,%esi
  40c25d:	movzwl (%r9,%rsi,2),%eax
  40c262:	cmp    %r8w,%ax
  40c266:	jae    40c589 <ab_tail::simd_quad_intel_spine(unsigned short const*, unsigned short const*, int, unsigned short)+0x469>
  40c26c:	lea    0x1(%rdx),%eax
  40c26f:	cmp    %r11d,%eax
  40c272:	jge    40c3e8 <ab_tail::simd_quad_intel_spine(unsigned short const*, unsigned short const*, int, unsigned short)+0x2c8>
  40c278:	movzwl 0x2(%r9,%rsi,2),%eax
  40c27e:	lea    0x2(%rsi,%rsi,1),%rcx
  40c283:	cmp    %r8w,%ax
  40c287:	jae    40c589 <ab_tail::simd_quad_intel_spine(unsigned short const*, unsigned short const*, int, unsigned short)+0x469>
  40c28d:	lea    0x2(%rdx),%eax
  40c290:	cmp    %eax,%r11d
  40c293:	jle    40c3e8 <ab_tail::simd_quad_intel_spine(unsigned short const*, unsigned short const*, int, unsigned short)+0x2c8>
  40c299:	movzwl 0x2(%r9,%rcx,1),%eax
  40c29f:	cmp    %r8w,%ax
  40c2a3:	jae    40c589 <ab_tail::simd_quad_intel_spine(unsigned short const*, unsigned short const*, int, unsigned short)+0x469>
  40c2a9:	lea    0x3(%rdx),%eax
  40c2ac:	cmp    %r11d,%eax
  40c2af:	jge    40c3e8 <ab_tail::simd_quad_intel_spine(unsigned short const*, unsigned short const*, int, unsigned short)+0x2c8>
  40c2b5:	movzwl 0x4(%r9,%rcx,1),%eax
  40c2bb:	cmp    %r8w,%ax
  40c2bf:	jae    40c589 <ab_tail::simd_quad_intel_spine(unsigned short const*, unsigned short const*, int, unsigned short)+0x469>
  40c2c5:	lea    0x4(%rdx),%eax
  40c2c8:	cmp    %eax,%r11d
  40c2cb:	jle    40c3e8 <ab_tail::simd_quad_intel_spine(unsigned short const*, unsigned short const*, int, unsigned short)+0x2c8>
  40c2d1:	movzwl 0x6(%r9,%rcx,1),%eax
  40c2d7:	cmp    %r8w,%ax
  40c2db:	jae    40c589 <ab_tail::simd_quad_intel_spine(unsigned short const*, unsigned short const*, int, unsigned short)+0x469>
  40c2e1:	lea    0x5(%rdx),%eax
  40c2e4:	cmp    %eax,%r11d
  40c2e7:	jle    40c3e8 <ab_tail::simd_quad_intel_spine(unsigned short const*, unsigned short const*, int, unsigned short)+0x2c8>
  40c2ed:	movzwl 0x8(%r9,%rcx,1),%eax
  40c2f3:	cmp    %r8w,%ax
  40c2f7:	jae    40c589 <ab_tail::simd_quad_intel_spine(unsigned short const*, unsigned short const*, int, unsigned short)+0x469>
  40c2fd:	lea    0x6(%rdx),%eax
  40c300:	cmp    %eax,%r11d
  40c303:	jle    40c3e8 <ab_tail::simd_quad_intel_spine(unsigned short const*, unsigned short const*, int, unsigned short)+0x2c8>
  40c309:	movzwl 0xa(%r9,%rcx,1),%eax
  40c30f:	cmp    %r8w,%ax
  40c313:	jae    40c589 <ab_tail::simd_quad_intel_spine(unsigned short const*, unsigned short const*, int, unsigned short)+0x469>
  40c319:	lea    0x7(%rdx),%eax
  40c31c:	cmp    %eax,%r11d
  40c31f:	jle    40c3e8 <ab_tail::simd_quad_intel_spine(unsigned short const*, unsigned short const*, int, unsigned short)+0x2c8>
  40c325:	movzwl 0xc(%r9,%rcx,1),%eax
  40c32b:	cmp    %r8w,%ax
  40c32f:	jae    40c589 <ab_tail::simd_quad_intel_spine(unsigned short const*, unsigned short const*, int, unsigned short)+0x469>
  40c335:	lea    0x8(%rdx),%eax
  40c338:	cmp    %eax,%r11d
  40c33b:	jle    40c3e8 <ab_tail::simd_quad_intel_spine(unsigned short const*, unsigned short const*, int, unsigned short)+0x2c8>
  40c341:	movzwl 0xe(%r9,%rcx,1),%eax
  40c347:	cmp    %r8w,%ax
  40c34b:	jae    40c589 <ab_tail::simd_quad_intel_spine(unsigned short const*, unsigned short const*, int, unsigned short)+0x469>
  40c351:	lea    0x9(%rdx),%eax
  40c354:	cmp    %eax,%r11d
  40c357:	jle    40c3e8 <ab_tail::simd_quad_intel_spine(unsigned short const*, unsigned short const*, int, unsigned short)+0x2c8>
  40c35d:	movzwl 0x10(%r9,%rcx,1),%eax
  40c363:	cmp    %r8w,%ax
  40c367:	jae    40c589 <ab_tail::simd_quad_intel_spine(unsigned short const*, unsigned short const*, int, unsigned short)+0x469>
  40c36d:	lea    0xa(%rdx),%eax
  40c370:	cmp    %eax,%r11d
  40c373:	jle    40c3e8 <ab_tail::simd_quad_intel_spine(unsigned short const*, unsigned short const*, int, unsigned short)+0x2c8>
  40c375:	movzwl 0x12(%r9,%rcx,1),%eax
  40c37b:	cmp    %r8w,%ax
  40c37f:	jae    40c589 <ab_tail::simd_quad_intel_spine(unsigned short const*, unsigned short const*, int, unsigned short)+0x469>
  40c385:	lea    0xb(%rdx),%eax
  40c388:	cmp    %eax,%r11d
  40c38b:	jle    40c3e8 <ab_tail::simd_quad_intel_spine(unsigned short const*, unsigned short const*, int, unsigned short)+0x2c8>
  40c38d:	movzwl 0x14(%r9,%rcx,1),%eax
  40c393:	cmp    %r8w,%ax
  40c397:	jae    40c589 <ab_tail::simd_quad_intel_spine(unsigned short const*, unsigned short const*, int, unsigned short)+0x469>
  40c39d:	lea    0xc(%rdx),%eax
  40c3a0:	cmp    %eax,%r11d
  40c3a3:	jle    40c3e8 <ab_tail::simd_quad_intel_spine(unsigned short const*, unsigned short const*, int, unsigned short)+0x2c8>
  40c3a5:	movzwl 0x16(%r9,%rcx,1),%eax
  40c3ab:	cmp    %r8w,%ax
  40c3af:	jae    40c589 <ab_tail::simd_quad_intel_spine(unsigned short const*, unsigned short const*, int, unsigned short)+0x469>
  40c3b5:	lea    0xd(%rdx),%eax
  40c3b8:	cmp    %eax,%r11d
  40c3bb:	jle    40c3e8 <ab_tail::simd_quad_intel_spine(unsigned short const*, unsigned short const*, int, unsigned short)+0x2c8>
  40c3bd:	movzwl 0x18(%r9,%rcx,1),%eax
  40c3c3:	cmp    %r8w,%ax
  40c3c7:	jae    40c589 <ab_tail::simd_quad_intel_spine(unsigned short const*, unsigned short const*, int, unsigned short)+0x469>
  40c3cd:	add    $0xe,%edx
  40c3d0:	cmp    %edx,%r11d
  40c3d3:	jle    40c3e8 <ab_tail::simd_quad_intel_spine(unsigned short const*, unsigned short const*, int, unsigned short)+0x2c8>
  40c3d5:	movzwl 0x3c(%r9),%eax
  40c3da:	cmp    %r8w,%ax
  40c3de:	jae    40c589 <ab_tail::simd_quad_intel_spine(unsigned short const*, unsigned short const*, int, unsigned short)+0x469>
  40c3e4:	nopl   0x0(%rax)
  40c3e8:	xor    %eax,%eax
  40c3ea:	vzeroupper
  40c3ed:	ret
  40c3ee:	xchg   %ax,%ax
  40c3f0:	push   %rbp
  40c3f1:	mov    %rsp,%rbp
  40c3f4:	sub    $0x10,%rsp
  40c3f8:	mov    %rbx,-0x10(%rbp)
  40c3fc:	mov    %edx,%ebx
  40c3fe:	sar    $0x5,%ebx
  40c401:	cmp    $0x7f,%edx
  40c404:	jle    40c5b0 <ab_tail::simd_quad_intel_spine(unsigned short const*, unsigned short const*, int, unsigned short)+0x490>
  40c40a:	mov    %r12,-0x8(%rbp)
  40c40e:	mov    %rsi,%r10
  40c411:	mov    %ebx,%eax
  40c413:	xor    %edi,%edi
  40c415:	prefetcht0 (%rsi)
  40c418:	nopl   0x0(%rax)
  40c41f:	data16 cs nopw 0x0(%rax,%rax,1)
  40c42a:	data16 cs nopw 0x0(%rax,%rax,1)
  40c435:	data16 cs nopw 0x0(%rax,%rax,1)
  40c440:	mov    %eax,%ecx
  40c442:	sar    $0x2,%ecx
  40c445:	lea    (%rcx,%rdi,1),%edx
  40c448:	lea    (%rdx,%rcx,1),%esi
  40c44b:	movslq %edx,%rdx
  40c44e:	cmp    %r8w,(%r10,%rdx,2)
  40c453:	movslq %esi,%r12
  40c456:	setb   %dl
  40c459:	cmp    %r8w,(%r10,%r12,2)
  40c45e:	movzbl %dl,%edx
  40c461:	adc    $0x0,%edx
  40c464:	add    %ecx,%esi
  40c466:	movslq %esi,%rsi
  40c469:	cmp    %r8w,(%r10,%rsi,2)
  40c46e:	adc    $0x0,%edx
  40c471:	imul   %ecx,%edx
  40c474:	add    %edx,%edi
  40c476:	lea    (%rcx,%rcx,2),%edx
  40c479:	sub    %edx,%eax
  40c47b:	cmp    $0x3,%eax
  40c47e:	jg     40c440 <ab_tail::simd_quad_intel_spine(unsigned short const*, unsigned short const*, int, unsigned short)+0x320>
  40c480:	cmp    $0x1,%eax
  40c483:	jle    40c4b9 <ab_tail::simd_quad_intel_spine(unsigned short const*, unsigned short const*, int, unsigned short)+0x399>
  40c485:	nopl   0x0(%rax,%rax,1)
  40c48a:	data16 cs nopw 0x0(%rax,%rax,1)
  40c495:	data16 cs nopw 0x0(%rax,%rax,1)
  40c4a0:	mov    %eax,%edx
  40c4a2:	sar    $1,%edx
  40c4a4:	lea    (%rdx,%rdi,1),%ecx
  40c4a7:	movslq %ecx,%rsi
  40c4aa:	cmp    %r8w,(%r10,%rsi,2)
  40c4af:	cmovb  %ecx,%edi
  40c4b2:	sub    %edx,%eax
  40c4b4:	cmp    $0x1,%eax
  40c4b7:	jg     40c4a0 <ab_tail::simd_quad_intel_spine(unsigned short const*, unsigned short const*, int, unsigned short)+0x380>
  40c4b9:	movslq %edi,%rax
  40c4bc:	cmp    %r8w,(%r10,%rax,2)
  40c4c1:	adc    $0x0,%edi
  40c4c4:	cmp    %ebx,%edi
  40c4c6:	jl     40c598 <ab_tail::simd_quad_intel_spine(unsigned short const*, unsigned short const*, int, unsigned short)+0x478>
  40c4cc:	mov    %r11d,%r11d
  40c4cf:	vpcmpeqw -0x40(%r9,%r11,2),%ymm0,%ymm1
  40c4d6:	vpcmpeqw -0x20(%r9,%r11,2),%ymm0,%ymm0
  40c4dd:	vpor   %ymm0,%ymm1,%ymm0
  40c4e1:	mov    -0x8(%rbp),%r12
  40c4e5:	vpmovmskb %ymm0,%eax
  40c4e9:	test   %eax,%eax
  40c4eb:	setne  %al
  40c4ee:	vzeroupper
  40c4f1:	mov    -0x10(%rbp),%rbx
  40c4f5:	leave
  40c4f6:	ret
  40c4f7:	nopw   0x0(%rax,%rax,1)
  40c500:	cmp    $0x7,%edx
  40c503:	jg     40c620 <ab_tail::simd_quad_intel_spine(unsigned short const*, unsigned short const*, int, unsigned short)+0x500>
  40c509:	test   %edx,%edx
  40c50b:	jle    40c3e8 <ab_tail::simd_quad_intel_spine(unsigned short const*, unsigned short const*, int, unsigned short)+0x2c8>
  40c511:	movzwl (%rdi),%eax
  40c514:	cmp    %cx,%ax
  40c517:	jae    40c589 <ab_tail::simd_quad_intel_spine(unsigned short const*, unsigned short const*, int, unsigned short)+0x469>
  40c519:	cmp    $0x1,%edx
  40c51c:	je     40c3e8 <ab_tail::simd_quad_intel_spine(unsigned short const*, unsigned short const*, int, unsigned short)+0x2c8>
  40c522:	movzwl 0x2(%rdi),%eax
  40c526:	cmp    %cx,%ax
  40c529:	jae    40c589 <ab_tail::simd_quad_intel_spine(unsigned short const*, unsigned short const*, int, unsigned short)+0x469>
  40c52b:	cmp    $0x2,%edx
  40c52e:	je     40c3e8 <ab_tail::simd_quad_intel_spine(unsigned short const*, unsigned short const*, int, unsigned short)+0x2c8>
  40c534:	movzwl 0x4(%rdi),%eax
  40c538:	cmp    %cx,%ax
  40c53b:	jae    40c589 <ab_tail::simd_quad_intel_spine(unsigned short const*, unsigned short const*, int, unsigned short)+0x469>
  40c53d:	cmp    $0x3,%edx
  40c540:	je     40c3e8 <ab_tail::simd_quad_intel_spine(unsigned short const*, unsigned short const*, int, unsigned short)+0x2c8>
  40c546:	movzwl 0x6(%rdi),%eax
  40c54a:	cmp    %cx,%ax
  40c54d:	jae    40c589 <ab_tail::simd_quad_intel_spine(unsigned short const*, unsigned short const*, int, unsigned short)+0x469>
  40c54f:	cmp    $0x4,%edx
  40c552:	je     40c3e8 <ab_tail::simd_quad_intel_spine(unsigned short const*, unsigned short const*, int, unsigned short)+0x2c8>
  40c558:	movzwl 0x8(%rdi),%eax
  40c55c:	cmp    %cx,%ax
  40c55f:	jae    40c589 <ab_tail::simd_quad_intel_spine(unsigned short const*, unsigned short const*, int, unsigned short)+0x469>
  40c561:	cmp    $0x5,%edx
  40c564:	je     40c3e8 <ab_tail::simd_quad_intel_spine(unsigned short const*, unsigned short const*, int, unsigned short)+0x2c8>
  40c56a:	movzwl 0xa(%rdi),%eax
  40c56e:	cmp    %cx,%ax
  40c571:	jae    40c589 <ab_tail::simd_quad_intel_spine(unsigned short const*, unsigned short const*, int, unsigned short)+0x469>
  40c573:	cmp    $0x7,%edx
  40c576:	jne    40c3e8 <ab_tail::simd_quad_intel_spine(unsigned short const*, unsigned short const*, int, unsigned short)+0x2c8>
  40c57c:	movzwl 0xc(%rdi),%eax
  40c580:	cmp    %cx,%ax
  40c583:	jb     40c3e8 <ab_tail::simd_quad_intel_spine(unsigned short const*, unsigned short const*, int, unsigned short)+0x2c8>
  40c589:	cmp    %ax,%r8w
  40c58d:	sete   %al
  40c590:	vzeroupper
  40c593:	ret
  40c594:	nopl   0x0(%rax)
  40c598:	shl    $0x5,%edi
  40c59b:	movslq %edi,%rdi
  40c59e:	lea    (%r9,%rdi,2),%rax
  40c5a2:	vpcmpeqw (%rax),%ymm0,%ymm1
  40c5a6:	vpcmpeqw 0x20(%rax),%ymm0,%ymm0
  40c5ab:	jmp    40c4dd <ab_tail::simd_quad_intel_spine(unsigned short const*, unsigned short const*, int, unsigned short)+0x3bd>
  40c5b0:	cmp    $0x1,%ebx
  40c5b3:	je     40c70c <ab_tail::simd_quad_intel_spine(unsigned short const*, unsigned short const*, int, unsigned short)+0x5ec>
  40c5b9:	mov    %ebx,%edx
  40c5bb:	xor    %ecx,%ecx
  40c5bd:	nopl   (%rax)
  40c5c0:	mov    %edx,%esi
  40c5c2:	sar    $1,%esi
  40c5c4:	lea    (%rsi,%rcx,1),%edi
  40c5c7:	lea    0x1(%rdi),%eax
  40c5ca:	shl    $0x5,%eax
  40c5cd:	cltq
  40c5cf:	cmp    %r8w,-0x2(%r9,%rax,2)
  40c5d5:	cmovb  %edi,%ecx
  40c5d8:	sub    %esi,%edx
  40c5da:	cmp    $0x1,%edx
  40c5dd:	jg     40c5c0 <ab_tail::simd_quad_intel_spine(unsigned short const*, unsigned short const*, int, unsigned short)+0x4a0>
  40c5df:	lea    0x1(%rcx),%eax
  40c5e2:	mov    %eax,%edx
  40c5e4:	shl    $0x5,%edx
  40c5e7:	movslq %edx,%rdx
  40c5ea:	cmp    %r8w,-0x2(%r9,%rdx,2)
  40c5f0:	cmovae %ecx,%eax
  40c5f3:	cmp    %eax,%ebx
  40c5f5:	jg     40c718 <ab_tail::simd_quad_intel_spine(unsigned short const*, unsigned short const*, int, unsigned short)+0x5f8>
  40c5fb:	mov    %r11d,%r11d
  40c5fe:	vpcmpeqw -0x40(%r9,%r11,2),%ymm0,%ymm1
  40c605:	vpcmpeqw -0x20(%r9,%r11,2),%ymm0,%ymm0
  40c60c:	vpor   %ymm0,%ymm1,%ymm0
  40c610:	vpmovmskb %ymm0,%eax
  40c614:	test   %eax,%eax
  40c616:	setne  %al
  40c619:	jmp    40c4ee <ab_tail::simd_quad_intel_spine(unsigned short const*, unsigned short const*, int, unsigned short)+0x3ce>
  40c61e:	xchg   %ax,%ax
  40c620:	vpcmpeqw (%rdi),%xmm0,%xmm0
  40c624:	vpmovmskb %xmm0,%eax
  40c628:	test   %eax,%eax
  40c62a:	jne    40c6d8 <ab_tail::simd_quad_intel_spine(unsigned short const*, unsigned short const*, int, unsigned short)+0x5b8>
  40c630:	cmp    $0x8,%edx
  40c633:	je     40c3e8 <ab_tail::simd_quad_intel_spine(unsigned short const*, unsigned short const*, int, unsigned short)+0x2c8>
  40c639:	movzwl 0x10(%rdi),%eax
  40c63d:	cmp    %cx,%ax
  40c640:	jae    40c589 <ab_tail::simd_quad_intel_spine(unsigned short const*, unsigned short const*, int, unsigned short)+0x469>
  40c646:	cmp    $0x9,%edx
  40c649:	je     40c3e8 <ab_tail::simd_quad_intel_spine(unsigned short const*, unsigned short const*, int, unsigned short)+0x2c8>
  40c64f:	movzwl 0x12(%rdi),%eax
  40c653:	cmp    %cx,%ax
  40c656:	jae    40c589 <ab_tail::simd_quad_intel_spine(unsigned short const*, unsigned short const*, int, unsigned short)+0x469>
  40c65c:	cmp    $0xa,%edx
  40c65f:	je     40c3e8 <ab_tail::simd_quad_intel_spine(unsigned short const*, unsigned short const*, int, unsigned short)+0x2c8>
  40c665:	movzwl 0x14(%rdi),%eax
  40c669:	cmp    %cx,%ax
  40c66c:	jae    40c589 <ab_tail::simd_quad_intel_spine(unsigned short const*, unsigned short const*, int, unsigned short)+0x469>
  40c672:	cmp    $0xb,%edx
  40c675:	je     40c3e8 <ab_tail::simd_quad_intel_spine(unsigned short const*, unsigned short const*, int, unsigned short)+0x2c8>
  40c67b:	movzwl 0x16(%rdi),%eax
  40c67f:	cmp    %cx,%ax
  40c682:	jae    40c589 <ab_tail::simd_quad_intel_spine(unsigned short const*, unsigned short const*, int, unsigned short)+0x469>
  40c688:	cmp    $0xc,%edx
  40c68b:	je     40c3e8 <ab_tail::simd_quad_intel_spine(unsigned short const*, unsigned short const*, int, unsigned short)+0x2c8>
  40c691:	movzwl 0x18(%rdi),%eax
  40c695:	cmp    %cx,%ax
  40c698:	jae    40c589 <ab_tail::simd_quad_intel_spine(unsigned short const*, unsigned short const*, int, unsigned short)+0x469>
  40c69e:	cmp    $0xd,%edx
  40c6a1:	je     40c3e8 <ab_tail::simd_quad_intel_spine(unsigned short const*, unsigned short const*, int, unsigned short)+0x2c8>
  40c6a7:	movzwl 0x1a(%rdi),%eax
  40c6ab:	cmp    %cx,%ax
  40c6ae:	jae    40c589 <ab_tail::simd_quad_intel_spine(unsigned short const*, unsigned short const*, int, unsigned short)+0x469>
  40c6b4:	cmp    $0xf,%edx
  40c6b7:	jne    40c3e8 <ab_tail::simd_quad_intel_spine(unsigned short const*, unsigned short const*, int, unsigned short)+0x2c8>
  40c6bd:	movzwl 0x1c(%rdi),%eax
  40c6c1:	cmp    %cx,%ax
  40c6c4:	jae    40c589 <ab_tail::simd_quad_intel_spine(unsigned short const*, unsigned short const*, int, unsigned short)+0x469>
  40c6ca:	xor    %eax,%eax
  40c6cc:	jmp    40c3ea <ab_tail::simd_quad_intel_spine(unsigned short const*, unsigned short const*, int, unsigned short)+0x2ca>
  40c6d1:	nopl   0x0(%rax)
  40c6d8:	mov    $0x1,%eax
  40c6dd:	vzeroupper
  40c6e0:	ret
  40c6e1:	mov    %edx,%esi
  40c6e3:	movzwl (%r9,%rsi,2),%eax
  40c6e8:	cmp    %r8w,%ax
  40c6ec:	jae    40c589 <ab_tail::simd_quad_intel_spine(unsigned short const*, unsigned short const*, int, unsigned short)+0x469>
  40c6f2:	movzwl 0x2(%r9,%rsi,2),%eax
  40c6f8:	lea    0x2(%rsi,%rsi,1),%rcx
  40c6fd:	cmp    %r8w,%ax
  40c701:	jb     40c299 <ab_tail::simd_quad_intel_spine(unsigned short const*, unsigned short const*, int, unsigned short)+0x179>
  40c707:	jmp    40c589 <ab_tail::simd_quad_intel_spine(unsigned short const*, unsigned short const*, int, unsigned short)+0x469>
  40c70c:	xor    %eax,%eax
  40c70e:	cmp    %cx,0x3e(%rdi)
  40c712:	jb     40c5fb <ab_tail::simd_quad_intel_spine(unsigned short const*, unsigned short const*, int, unsigned short)+0x4db>
  40c718:	shl    $0x5,%eax
  40c71b:	cltq
  40c71d:	lea    (%r9,%rax,2),%rax
  40c721:	vpcmpeqw (%rax),%ymm0,%ymm1
  40c725:	vpcmpeqw 0x20(%rax),%ymm0,%ymm0
  40c72a:	vpor   %ymm0,%ymm1,%ymm0
  40c72e:	vpmovmskb %ymm0,%eax
  40c732:	test   %eax,%eax
  40c734:	setne  %al
  40c737:	jmp    40c4ee <ab_tail::simd_quad_intel_spine(unsigned short const*, unsigned short const*, int, unsigned short)+0x3ce>
  40c73c:	mov    $0x10,%edx
  40c741:	jmp    40c235 <ab_tail::simd_quad_intel_spine(unsigned short const*, unsigned short const*, int, unsigned short)+0x115>
  40c746:	mov    $0x10,%edx
  40c74b:	jmp    40c25b <ab_tail::simd_quad_intel_spine(unsigned short const*, unsigned short const*, int, unsigned short)+0x13b>
  40c750:	mov    $0x11,%edx
  40c755:	jmp    40c235 <ab_tail::simd_quad_intel_spine(unsigned short const*, unsigned short const*, int, unsigned short)+0x115>
  40c75a:	mov    $0x12,%edx
  40c75f:	jmp    40c235 <ab_tail::simd_quad_intel_spine(unsigned short const*, unsigned short const*, int, unsigned short)+0x115>
  40c764:	mov    $0x13,%edx
  40c769:	jmp    40c235 <ab_tail::simd_quad_intel_spine(unsigned short const*, unsigned short const*, int, unsigned short)+0x115>
  40c76e:	mov    $0x14,%edx
  40c773:	jmp    40c235 <ab_tail::simd_quad_intel_spine(unsigned short const*, unsigned short const*, int, unsigned short)+0x115>
  40c778:	mov    $0x15,%edx
  40c77d:	jmp    40c235 <ab_tail::simd_quad_intel_spine(unsigned short const*, unsigned short const*, int, unsigned short)+0x115>
  40c782:	mov    $0x16,%edx
  40c787:	jmp    40c235 <ab_tail::simd_quad_intel_spine(unsigned short const*, unsigned short const*, int, unsigned short)+0x115>
  40c78c:	nopl   0x0(%rax)
