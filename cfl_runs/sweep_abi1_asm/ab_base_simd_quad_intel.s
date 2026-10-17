0000000000407280 <ab_base::simd_quad_intel(unsigned short const*, int, unsigned short)>:
  407280:	mov    %rdi,%rcx
  407283:	mov    %edx,%edi
  407285:	mov    %esi,%r8d
  407288:	vmovd  %edi,%xmm1
  40728c:	vpbroadcastw %xmm1,%ymm1
  407291:	cmp    $0x1f,%esi
  407294:	jg     407530 <ab_base::simd_quad_intel(unsigned short const*, int, unsigned short)+0x2b0>
  40729a:	cmp    $0xf,%esi
  40729d:	jle    407870 <ab_base::simd_quad_intel(unsigned short const*, int, unsigned short)+0x5f0>
  4072a3:	vpcmpeqw (%rcx),%ymm1,%ymm0
  4072a7:	vpmovmskb %ymm0,%eax
  4072ab:	test   %eax,%eax
  4072ad:	jne    4079a8 <ab_base::simd_quad_intel(unsigned short const*, int, unsigned short)+0x728>
  4072b3:	cmp    $0x10,%esi
  4072b6:	je     407520 <ab_base::simd_quad_intel(unsigned short const*, int, unsigned short)+0x2a0>
  4072bc:	lea    0x20(%rcx),%r10
  4072c0:	mov    $0xb,%r9d
  4072c6:	mov    %r10,%rdx
  4072c9:	shr    $1,%rdx
  4072cc:	neg    %rdx
  4072cf:	mov    %edx,%esi
  4072d1:	and    $0x7,%esi
  4072d4:	lea    0x8(%rsi),%eax
  4072d7:	cmp    %r9d,%eax
  4072da:	cmovb  %r9d,%eax
  4072de:	lea    -0x11(%r8),%r9d
  4072e2:	cmp    %eax,%r9d
  4072e5:	jb     407a0d <ab_base::simd_quad_intel(unsigned short const*, int, unsigned short)+0x78d>
  4072eb:	test   %esi,%esi
  4072ed:	je     407a03 <ab_base::simd_quad_intel(unsigned short const*, int, unsigned short)+0x783>
  4072f3:	movzwl 0x20(%rcx),%eax
  4072f7:	cmp    %di,%ax
  4072fa:	jae    4078f9 <ab_base::simd_quad_intel(unsigned short const*, int, unsigned short)+0x679>
  407300:	test   $0x6,%dl
  407303:	je     407a3e <ab_base::simd_quad_intel(unsigned short const*, int, unsigned short)+0x7be>
  407309:	movzwl 0x22(%rcx),%eax
  40730d:	cmp    %di,%ax
  407310:	jae    4078f9 <ab_base::simd_quad_intel(unsigned short const*, int, unsigned short)+0x679>
  407316:	cmp    $0x2,%esi
  407319:	jbe    407a48 <ab_base::simd_quad_intel(unsigned short const*, int, unsigned short)+0x7c8>
  40731f:	movzwl 0x24(%rcx),%eax
  407323:	cmp    %di,%ax
  407326:	jae    4078f9 <ab_base::simd_quad_intel(unsigned short const*, int, unsigned short)+0x679>
  40732c:	and    $0x4,%edx
  40732f:	je     407a62 <ab_base::simd_quad_intel(unsigned short const*, int, unsigned short)+0x7e2>
  407335:	movzwl 0x26(%rcx),%eax
  407339:	cmp    %di,%ax
  40733c:	jae    4078f9 <ab_base::simd_quad_intel(unsigned short const*, int, unsigned short)+0x679>
  407342:	cmp    $0x4,%esi
  407345:	je     407a6c <ab_base::simd_quad_intel(unsigned short const*, int, unsigned short)+0x7ec>
  40734b:	movzwl 0x28(%rcx),%eax
  40734f:	cmp    %di,%ax
  407352:	jae    4078f9 <ab_base::simd_quad_intel(unsigned short const*, int, unsigned short)+0x679>
  407358:	cmp    $0x5,%esi
  40735b:	je     407a7e <ab_base::simd_quad_intel(unsigned short const*, int, unsigned short)+0x7fe>
  407361:	movzwl 0x2a(%rcx),%eax
  407365:	cmp    %di,%ax
  407368:	jae    4078f9 <ab_base::simd_quad_intel(unsigned short const*, int, unsigned short)+0x679>
  40736e:	cmp    $0x7,%esi
  407371:	jne    407a90 <ab_base::simd_quad_intel(unsigned short const*, int, unsigned short)+0x810>
  407377:	movzwl 0x2c(%rcx),%eax
  40737b:	cmp    %di,%ax
  40737e:	jae    4078f9 <ab_base::simd_quad_intel(unsigned short const*, int, unsigned short)+0x679>
  407384:	mov    $0x17,%edx
  407389:	mov    %esi,%eax
  40738b:	vpminuw (%r10,%rax,2),%xmm1,%xmm0
  407391:	vpcmpeqw %xmm0,%xmm1,%xmm1
  407395:	vptest %xmm1,%xmm1
  40739a:	jne    4079d9 <ab_base::simd_quad_intel(unsigned short const*, int, unsigned short)+0x759>
  4073a0:	lea    -0x18(%r8),%eax
  4073a4:	cmp    %esi,%eax
  4073a6:	je     407520 <ab_base::simd_quad_intel(unsigned short const*, int, unsigned short)+0x2a0>
  4073ac:	add    $0x8,%edx
  4073af:	mov    %edx,%r9d
  4073b2:	movzwl (%rcx,%r9,2),%eax
  4073b7:	cmp    %di,%ax
  4073ba:	jae    4078f9 <ab_base::simd_quad_intel(unsigned short const*, int, unsigned short)+0x679>
  4073c0:	lea    0x1(%rdx),%eax
  4073c3:	cmp    %eax,%r8d
  4073c6:	jle    407520 <ab_base::simd_quad_intel(unsigned short const*, int, unsigned short)+0x2a0>
  4073cc:	movzwl 0x2(%rcx,%r9,2),%eax
  4073d2:	lea    0x2(%r9,%r9,1),%rsi
  4073d7:	cmp    %di,%ax
  4073da:	jae    4078f9 <ab_base::simd_quad_intel(unsigned short const*, int, unsigned short)+0x679>
  4073e0:	lea    0x2(%rdx),%eax
  4073e3:	cmp    %r8d,%eax
  4073e6:	jge    407520 <ab_base::simd_quad_intel(unsigned short const*, int, unsigned short)+0x2a0>
  4073ec:	movzwl 0x2(%rcx,%rsi,1),%eax
  4073f1:	cmp    %di,%ax
  4073f4:	jae    4078f9 <ab_base::simd_quad_intel(unsigned short const*, int, unsigned short)+0x679>
  4073fa:	lea    0x3(%rdx),%eax
  4073fd:	cmp    %eax,%r8d
  407400:	jle    407520 <ab_base::simd_quad_intel(unsigned short const*, int, unsigned short)+0x2a0>
  407406:	movzwl 0x4(%rcx,%rsi,1),%eax
  40740b:	cmp    %di,%ax
  40740e:	jae    4078f9 <ab_base::simd_quad_intel(unsigned short const*, int, unsigned short)+0x679>
  407414:	lea    0x4(%rdx),%eax
  407417:	cmp    %eax,%r8d
  40741a:	jle    407520 <ab_base::simd_quad_intel(unsigned short const*, int, unsigned short)+0x2a0>
  407420:	movzwl 0x6(%rcx,%rsi,1),%eax
  407425:	cmp    %di,%ax
  407428:	jae    4078f9 <ab_base::simd_quad_intel(unsigned short const*, int, unsigned short)+0x679>
  40742e:	lea    0x5(%rdx),%eax
  407431:	cmp    %r8d,%eax
  407434:	jge    407520 <ab_base::simd_quad_intel(unsigned short const*, int, unsigned short)+0x2a0>
  40743a:	movzwl 0x8(%rcx,%rsi,1),%eax
  40743f:	cmp    %di,%ax
  407442:	jae    4078f9 <ab_base::simd_quad_intel(unsigned short const*, int, unsigned short)+0x679>
  407448:	lea    0x6(%rdx),%eax
  40744b:	cmp    %eax,%r8d
  40744e:	jle    407520 <ab_base::simd_quad_intel(unsigned short const*, int, unsigned short)+0x2a0>
  407454:	movzwl 0xa(%rcx,%rsi,1),%eax
  407459:	cmp    %di,%ax
  40745c:	jae    4078f9 <ab_base::simd_quad_intel(unsigned short const*, int, unsigned short)+0x679>
  407462:	lea    0x7(%rdx),%eax
  407465:	cmp    %eax,%r8d
  407468:	jle    407520 <ab_base::simd_quad_intel(unsigned short const*, int, unsigned short)+0x2a0>
  40746e:	movzwl 0xc(%rcx,%rsi,1),%eax
  407473:	cmp    %di,%ax
  407476:	jae    4078f9 <ab_base::simd_quad_intel(unsigned short const*, int, unsigned short)+0x679>
  40747c:	lea    0x8(%rdx),%eax
  40747f:	cmp    %eax,%r8d
  407482:	jle    407520 <ab_base::simd_quad_intel(unsigned short const*, int, unsigned short)+0x2a0>
  407488:	movzwl 0xe(%rcx,%rsi,1),%eax
  40748d:	cmp    %di,%ax
  407490:	jae    4078f9 <ab_base::simd_quad_intel(unsigned short const*, int, unsigned short)+0x679>
  407496:	lea    0x9(%rdx),%eax
  407499:	cmp    %eax,%r8d
  40749c:	jle    407520 <ab_base::simd_quad_intel(unsigned short const*, int, unsigned short)+0x2a0>
  4074a2:	movzwl 0x10(%rcx,%rsi,1),%eax
  4074a7:	cmp    %di,%ax
  4074aa:	jae    4078f9 <ab_base::simd_quad_intel(unsigned short const*, int, unsigned short)+0x679>
  4074b0:	lea    0xa(%rdx),%eax
  4074b3:	cmp    %eax,%r8d
  4074b6:	jle    407520 <ab_base::simd_quad_intel(unsigned short const*, int, unsigned short)+0x2a0>
  4074b8:	movzwl 0x12(%rcx,%rsi,1),%eax
  4074bd:	cmp    %di,%ax
  4074c0:	jae    4078f9 <ab_base::simd_quad_intel(unsigned short const*, int, unsigned short)+0x679>
  4074c6:	lea    0xb(%rdx),%eax
  4074c9:	cmp    %eax,%r8d
  4074cc:	jle    407520 <ab_base::simd_quad_intel(unsigned short const*, int, unsigned short)+0x2a0>
  4074ce:	movzwl 0x14(%rcx,%rsi,1),%eax
  4074d3:	cmp    %di,%ax
  4074d6:	jae    4078f9 <ab_base::simd_quad_intel(unsigned short const*, int, unsigned short)+0x679>
  4074dc:	lea    0xc(%rdx),%eax
  4074df:	cmp    %eax,%r8d
  4074e2:	jle    407520 <ab_base::simd_quad_intel(unsigned short const*, int, unsigned short)+0x2a0>
  4074e4:	movzwl 0x16(%rcx,%rsi,1),%eax
  4074e9:	cmp    %di,%ax
  4074ec:	jae    4078f9 <ab_base::simd_quad_intel(unsigned short const*, int, unsigned short)+0x679>
  4074f2:	lea    0xd(%rdx),%eax
  4074f5:	cmp    %eax,%r8d
  4074f8:	jle    407520 <ab_base::simd_quad_intel(unsigned short const*, int, unsigned short)+0x2a0>
  4074fa:	movzwl 0x18(%rcx,%rsi,1),%eax
  4074ff:	cmp    %di,%ax
  407502:	jae    4078f9 <ab_base::simd_quad_intel(unsigned short const*, int, unsigned short)+0x679>
  407508:	add    $0xe,%edx
  40750b:	cmp    %edx,%r8d
  40750e:	jle    407520 <ab_base::simd_quad_intel(unsigned short const*, int, unsigned short)+0x2a0>
  407510:	movzwl 0x3c(%rcx),%eax
  407514:	cmp    %di,%ax
  407517:	jae    4078f9 <ab_base::simd_quad_intel(unsigned short const*, int, unsigned short)+0x679>
  40751d:	nopl   (%rax)
  407520:	xor    %eax,%eax
  407522:	vzeroupper
  407525:	ret
  407526:	cs nopw 0x0(%rax,%rax,1)
  407530:	push   %rbp
  407531:	mov    %esi,%r9d
  407534:	xor    %esi,%esi
  407536:	sar    $0x5,%r9d
  40753a:	mov    %r9d,%eax
  40753d:	mov    %rsp,%rbp
  407540:	push   %rbx
  407541:	cmp    $0x7f,%r8d
  407545:	jle    4075e0 <ab_base::simd_quad_intel(unsigned short const*, int, unsigned short)+0x360>
  40754b:	nopl   0x0(%rax,%rax,1)
  407550:	mov    %eax,%r10d
  407553:	sar    $0x2,%r10d
  407557:	lea    (%r10,%rsi,1),%edx
  40755b:	lea    (%rdx,%r10,1),%r11d
  40755f:	inc    %edx
  407561:	shl    $0x5,%edx
  407564:	lea    0x1(%r11),%ebx
  407568:	lea    0x1(%r10,%r11,1),%r11d
  40756d:	movslq %edx,%rdx
  407570:	cmp    %di,-0x2(%rcx,%rdx,2)
  407575:	setb   %dl
  407578:	shl    $0x5,%ebx
  40757b:	movslq %ebx,%rbx
  40757e:	movzbl %dl,%edx
  407581:	cmp    %di,-0x2(%rcx,%rbx,2)
  407586:	adc    $0x0,%edx
  407589:	shl    $0x5,%r11d
  40758d:	movslq %r11d,%r11
  407590:	cmp    %di,-0x2(%rcx,%r11,2)
  407596:	adc    $0x0,%edx
  407599:	imul   %r10d,%edx
  40759d:	add    %edx,%esi
  40759f:	lea    (%r10,%r10,2),%edx
  4075a3:	sub    %edx,%eax
  4075a5:	mov    %eax,%edx
  4075a7:	sar    $1,%edx
  4075a9:	add    %esi,%edx
  4075ab:	shl    $0x5,%edx
  4075ae:	movslq %edx,%rdx
  4075b1:	prefetcht0 (%rcx,%rdx,2)
  4075b5:	cmp    $0x3,%eax
  4075b8:	jg     407550 <ab_base::simd_quad_intel(unsigned short const*, int, unsigned short)+0x2d0>
  4075ba:	jmp    4075e0 <ab_base::simd_quad_intel(unsigned short const*, int, unsigned short)+0x360>
  4075bc:	nopl   0x0(%rax)
  4075c0:	mov    %eax,%r10d
  4075c3:	sar    $1,%r10d
  4075c6:	lea    (%r10,%rsi,1),%r11d
  4075ca:	lea    0x1(%r11),%edx
  4075ce:	shl    $0x5,%edx
  4075d1:	movslq %edx,%rdx
  4075d4:	cmp    %di,-0x2(%rcx,%rdx,2)
  4075d9:	cmovb  %r11d,%esi
  4075dd:	sub    %r10d,%eax
  4075e0:	cmp    $0x1,%eax
  4075e3:	jg     4075c0 <ab_base::simd_quad_intel(unsigned short const*, int, unsigned short)+0x340>
  4075e5:	lea    0x1(%rsi),%eax
  4075e8:	mov    %eax,%edx
  4075ea:	shl    $0x5,%edx
  4075ed:	movslq %edx,%rdx
  4075f0:	cmp    %di,-0x2(%rcx,%rdx,2)
  4075f5:	cmovae %esi,%eax
  4075f8:	cmp    %r9d,%eax
  4075fb:	jl     407848 <ab_base::simd_quad_intel(unsigned short const*, int, unsigned short)+0x5c8>
  407601:	mov    %r9d,%eax
  407604:	shl    $0x5,%eax
  407607:	cmp    %eax,%r8d
  40760a:	jle    4079b8 <ab_base::simd_quad_intel(unsigned short const*, int, unsigned short)+0x738>
  407610:	mov    %r9d,%r9d
  407613:	mov    $0x17,%r10d
  407619:	mov    %r8d,%ebx
  40761c:	shl    $0x6,%r9
  407620:	sub    %eax,%ebx
  407622:	lea    (%rcx,%r9,1),%rsi
  407626:	mov    %rsi,%r11
  407629:	shr    $1,%r11
  40762c:	neg    %r11
  40762f:	mov    %r11d,%r9d
  407632:	and    $0xf,%r9d
  407636:	lea    0x10(%r9),%edx
  40763a:	cmp    %r10d,%edx
  40763d:	cmovb  %r10d,%edx
  407641:	lea    -0x1(%rbx),%r10d
  407645:	cmp    %edx,%r10d
  407648:	jb     407802 <ab_base::simd_quad_intel(unsigned short const*, int, unsigned short)+0x582>
  40764e:	test   %r9d,%r9d
  407651:	je     4077c3 <ab_base::simd_quad_intel(unsigned short const*, int, unsigned short)+0x543>
  407657:	movzwl (%rsi),%edx
  40765a:	cmp    %di,%dx
  40765d:	jae    407835 <ab_base::simd_quad_intel(unsigned short const*, int, unsigned short)+0x5b5>
  407663:	test   $0xe,%r11b
  407667:	je     407a17 <ab_base::simd_quad_intel(unsigned short const*, int, unsigned short)+0x797>
  40766d:	lea    0x1(%rax),%r10d
  407671:	movzwl (%rcx,%r10,2),%edx
  407676:	cmp    %di,%dx
  407679:	jae    407835 <ab_base::simd_quad_intel(unsigned short const*, int, unsigned short)+0x5b5>
  40767f:	cmp    $0x2,%r9d
  407683:	jbe    407a1e <ab_base::simd_quad_intel(unsigned short const*, int, unsigned short)+0x79e>
  407689:	movzwl 0x2(%rcx,%r10,2),%edx
  40768f:	cmp    %di,%dx
  407692:	jae    407835 <ab_base::simd_quad_intel(unsigned short const*, int, unsigned short)+0x5b5>
  407698:	test   $0xc,%r11b
  40769c:	je     407a26 <ab_base::simd_quad_intel(unsigned short const*, int, unsigned short)+0x7a6>
  4076a2:	movzwl 0x4(%rcx,%r10,2),%edx
  4076a8:	cmp    %di,%dx
  4076ab:	jae    407835 <ab_base::simd_quad_intel(unsigned short const*, int, unsigned short)+0x5b5>
  4076b1:	cmp    $0x4,%r9d
  4076b5:	jbe    407a2e <ab_base::simd_quad_intel(unsigned short const*, int, unsigned short)+0x7ae>
  4076bb:	movzwl 0x6(%rcx,%r10,2),%edx
  4076c1:	cmp    %di,%dx
  4076c4:	jae    407835 <ab_base::simd_quad_intel(unsigned short const*, int, unsigned short)+0x5b5>
  4076ca:	cmp    $0x5,%r9d
  4076ce:	je     407a36 <ab_base::simd_quad_intel(unsigned short const*, int, unsigned short)+0x7b6>
  4076d4:	movzwl 0x8(%rcx,%r10,2),%edx
  4076da:	cmp    %di,%dx
  4076dd:	jae    407835 <ab_base::simd_quad_intel(unsigned short const*, int, unsigned short)+0x5b5>
  4076e3:	cmp    $0x6,%r9d
  4076e7:	je     407a52 <ab_base::simd_quad_intel(unsigned short const*, int, unsigned short)+0x7d2>
  4076ed:	movzwl 0xa(%rcx,%r10,2),%edx
  4076f3:	cmp    %di,%dx
  4076f6:	jae    407835 <ab_base::simd_quad_intel(unsigned short const*, int, unsigned short)+0x5b5>
  4076fc:	and    $0x8,%r11d
  407700:	je     407a5a <ab_base::simd_quad_intel(unsigned short const*, int, unsigned short)+0x7da>
  407706:	movzwl 0xc(%rcx,%r10,2),%edx
  40770c:	cmp    %di,%dx
  40770f:	jae    407835 <ab_base::simd_quad_intel(unsigned short const*, int, unsigned short)+0x5b5>
  407715:	cmp    $0x8,%r9d
  407719:	je     407a76 <ab_base::simd_quad_intel(unsigned short const*, int, unsigned short)+0x7f6>
  40771f:	movzwl 0xe(%rcx,%r10,2),%edx
  407725:	cmp    %di,%dx
  407728:	jae    407835 <ab_base::simd_quad_intel(unsigned short const*, int, unsigned short)+0x5b5>
  40772e:	cmp    $0x9,%r9d
  407732:	je     407a88 <ab_base::simd_quad_intel(unsigned short const*, int, unsigned short)+0x808>
  407738:	movzwl 0x10(%rcx,%r10,2),%edx
  40773e:	cmp    %di,%dx
  407741:	jae    407835 <ab_base::simd_quad_intel(unsigned short const*, int, unsigned short)+0x5b5>
  407747:	cmp    $0xa,%r9d
  40774b:	je     407a9a <ab_base::simd_quad_intel(unsigned short const*, int, unsigned short)+0x81a>
  407751:	movzwl 0x12(%rcx,%r10,2),%edx
  407757:	cmp    %di,%dx
  40775a:	jae    407835 <ab_base::simd_quad_intel(unsigned short const*, int, unsigned short)+0x5b5>
  407760:	cmp    $0xb,%r9d
  407764:	je     407aaa <ab_base::simd_quad_intel(unsigned short const*, int, unsigned short)+0x82a>
  40776a:	movzwl 0x14(%rcx,%r10,2),%edx
  407770:	cmp    %di,%dx
  407773:	jae    407835 <ab_base::simd_quad_intel(unsigned short const*, int, unsigned short)+0x5b5>
  407779:	cmp    $0xc,%r9d
  40777d:	je     407aa2 <ab_base::simd_quad_intel(unsigned short const*, int, unsigned short)+0x822>
  407783:	movzwl 0x16(%rcx,%r10,2),%edx
  407789:	cmp    %di,%dx
  40778c:	jae    407835 <ab_base::simd_quad_intel(unsigned short const*, int, unsigned short)+0x5b5>
  407792:	cmp    $0xd,%r9d
  407796:	je     407ab2 <ab_base::simd_quad_intel(unsigned short const*, int, unsigned short)+0x832>
  40779c:	movzwl 0x18(%rcx,%r10,2),%edx
  4077a2:	cmp    %di,%dx
  4077a5:	jae    407835 <ab_base::simd_quad_intel(unsigned short const*, int, unsigned short)+0x5b5>
  4077ab:	cmp    $0xf,%r9d
  4077af:	jne    407aba <ab_base::simd_quad_intel(unsigned short const*, int, unsigned short)+0x83a>
  4077b5:	movzwl 0x1a(%rcx,%r10,2),%edx
  4077bb:	cmp    %di,%dx
  4077be:	jae    407835 <ab_base::simd_quad_intel(unsigned short const*, int, unsigned short)+0x5b5>
  4077c0:	add    $0xf,%eax
  4077c3:	sub    %r9d,%ebx
  4077c6:	lea    (%rsi,%r9,2),%rdx
  4077ca:	xor    %esi,%esi
  4077cc:	mov    %ebx,%r10d
  4077cf:	shr    $0x4,%r10d
  4077d3:	mov    %r10d,%r9d
  4077d6:	shl    $0x5,%r9
  4077da:	add    %rdx,%r9
  4077dd:	jmp    4077f0 <ab_base::simd_quad_intel(unsigned short const*, int, unsigned short)+0x570>
  4077df:	nop
  4077e0:	add    $0x20,%rdx
  4077e4:	add    $0x10,%esi
  4077e7:	cmp    %rdx,%r9
  4077ea:	je     4079c8 <ab_base::simd_quad_intel(unsigned short const*, int, unsigned short)+0x748>
  4077f0:	vpminuw (%rdx),%ymm1,%ymm0
  4077f5:	vpcmpeqw %ymm0,%ymm1,%ymm0
  4077f9:	vptest %ymm0,%ymm0
  4077fe:	je     4077e0 <ab_base::simd_quad_intel(unsigned short const*, int, unsigned short)+0x560>
  407800:	add    %esi,%eax
  407802:	cltq
  407804:	jmp    40782c <ab_base::simd_quad_intel(unsigned short const*, int, unsigned short)+0x5ac>
  407806:	nopl   0x0(%rax)
  40780a:	data16 cs nopw 0x0(%rax,%rax,1)
  407815:	data16 cs nopw 0x0(%rax,%rax,1)
  407820:	inc    %rax
  407823:	cmp    %eax,%r8d
  407826:	jle    4079b8 <ab_base::simd_quad_intel(unsigned short const*, int, unsigned short)+0x738>
  40782c:	movzwl (%rcx,%rax,2),%edx
  407830:	cmp    %di,%dx
  407833:	jb     407820 <ab_base::simd_quad_intel(unsigned short const*, int, unsigned short)+0x5a0>
  407835:	cmp    %dx,%di
  407838:	vzeroupper
  40783b:	sete   %al
  40783e:	mov    -0x8(%rbp),%rbx
  407842:	leave
  407843:	ret
  407844:	nopl   0x0(%rax)
  407848:	shl    $0x5,%eax
  40784b:	cltq
  40784d:	lea    (%rcx,%rax,2),%rax
  407851:	vpcmpeqw (%rax),%ymm1,%ymm0
  407855:	vpcmpeqw 0x20(%rax),%ymm1,%ymm1
  40785a:	vpor   %ymm1,%ymm0,%ymm0
  40785e:	vpmovmskb %ymm0,%eax
  407862:	test   %eax,%eax
  407864:	vzeroupper
  407867:	setne  %al
  40786a:	mov    -0x8(%rbp),%rbx
  40786e:	leave
  40786f:	ret
  407870:	cmp    $0x7,%esi
  407873:	jg     407908 <ab_base::simd_quad_intel(unsigned short const*, int, unsigned short)+0x688>
  407879:	test   %esi,%esi
  40787b:	jle    407520 <ab_base::simd_quad_intel(unsigned short const*, int, unsigned short)+0x2a0>
  407881:	movzwl (%rcx),%eax
  407884:	cmp    %dx,%ax
  407887:	jae    4078f9 <ab_base::simd_quad_intel(unsigned short const*, int, unsigned short)+0x679>
  407889:	cmp    $0x1,%esi
  40788c:	je     407520 <ab_base::simd_quad_intel(unsigned short const*, int, unsigned short)+0x2a0>
  407892:	movzwl 0x2(%rcx),%eax
  407896:	cmp    %dx,%ax
  407899:	jae    4078f9 <ab_base::simd_quad_intel(unsigned short const*, int, unsigned short)+0x679>
  40789b:	cmp    $0x2,%esi
  40789e:	je     407520 <ab_base::simd_quad_intel(unsigned short const*, int, unsigned short)+0x2a0>
  4078a4:	movzwl 0x4(%rcx),%eax
  4078a8:	cmp    %dx,%ax
  4078ab:	jae    4078f9 <ab_base::simd_quad_intel(unsigned short const*, int, unsigned short)+0x679>
  4078ad:	cmp    $0x3,%esi
  4078b0:	je     407520 <ab_base::simd_quad_intel(unsigned short const*, int, unsigned short)+0x2a0>
  4078b6:	movzwl 0x6(%rcx),%eax
  4078ba:	cmp    %dx,%ax
  4078bd:	jae    4078f9 <ab_base::simd_quad_intel(unsigned short const*, int, unsigned short)+0x679>
  4078bf:	cmp    $0x4,%esi
  4078c2:	je     407520 <ab_base::simd_quad_intel(unsigned short const*, int, unsigned short)+0x2a0>
  4078c8:	movzwl 0x8(%rcx),%eax
  4078cc:	cmp    %dx,%ax
  4078cf:	jae    4078f9 <ab_base::simd_quad_intel(unsigned short const*, int, unsigned short)+0x679>
  4078d1:	cmp    $0x5,%esi
  4078d4:	je     407520 <ab_base::simd_quad_intel(unsigned short const*, int, unsigned short)+0x2a0>
  4078da:	movzwl 0xa(%rcx),%eax
  4078de:	cmp    %dx,%ax
  4078e1:	jae    4078f9 <ab_base::simd_quad_intel(unsigned short const*, int, unsigned short)+0x679>
  4078e3:	cmp    $0x7,%esi
  4078e6:	jne    407520 <ab_base::simd_quad_intel(unsigned short const*, int, unsigned short)+0x2a0>
  4078ec:	movzwl 0xc(%rcx),%eax
  4078f0:	cmp    %dx,%ax
  4078f3:	jb     407520 <ab_base::simd_quad_intel(unsigned short const*, int, unsigned short)+0x2a0>
  4078f9:	cmp    %ax,%di
  4078fc:	sete   %al
  4078ff:	vzeroupper
  407902:	ret
  407903:	nopl   0x0(%rax,%rax,1)
  407908:	vpcmpeqw (%rcx),%xmm1,%xmm1
  40790c:	vpmovmskb %xmm1,%eax
  407910:	test   %eax,%eax
  407912:	jne    4079a8 <ab_base::simd_quad_intel(unsigned short const*, int, unsigned short)+0x728>
  407918:	cmp    $0x8,%esi
  40791b:	je     407520 <ab_base::simd_quad_intel(unsigned short const*, int, unsigned short)+0x2a0>
  407921:	movzwl 0x10(%rcx),%eax
  407925:	cmp    %dx,%ax
  407928:	jae    4078f9 <ab_base::simd_quad_intel(unsigned short const*, int, unsigned short)+0x679>
  40792a:	cmp    $0x9,%esi
  40792d:	je     407520 <ab_base::simd_quad_intel(unsigned short const*, int, unsigned short)+0x2a0>
  407933:	movzwl 0x12(%rcx),%eax
  407937:	cmp    %dx,%ax
  40793a:	jae    4078f9 <ab_base::simd_quad_intel(unsigned short const*, int, unsigned short)+0x679>
  40793c:	cmp    $0xa,%esi
  40793f:	je     407520 <ab_base::simd_quad_intel(unsigned short const*, int, unsigned short)+0x2a0>
  407945:	movzwl 0x14(%rcx),%eax
  407949:	cmp    %dx,%ax
  40794c:	jae    4078f9 <ab_base::simd_quad_intel(unsigned short const*, int, unsigned short)+0x679>
  40794e:	cmp    $0xb,%esi
  407951:	je     407520 <ab_base::simd_quad_intel(unsigned short const*, int, unsigned short)+0x2a0>
  407957:	movzwl 0x16(%rcx),%eax
  40795b:	cmp    %dx,%ax
  40795e:	jae    4078f9 <ab_base::simd_quad_intel(unsigned short const*, int, unsigned short)+0x679>
  407960:	cmp    $0xc,%esi
  407963:	je     407520 <ab_base::simd_quad_intel(unsigned short const*, int, unsigned short)+0x2a0>
  407969:	movzwl 0x18(%rcx),%eax
  40796d:	cmp    %dx,%ax
  407970:	jae    4078f9 <ab_base::simd_quad_intel(unsigned short const*, int, unsigned short)+0x679>
  407972:	cmp    $0xd,%esi
  407975:	je     407520 <ab_base::simd_quad_intel(unsigned short const*, int, unsigned short)+0x2a0>
  40797b:	movzwl 0x1a(%rcx),%eax
  40797f:	cmp    %dx,%ax
  407982:	jae    4078f9 <ab_base::simd_quad_intel(unsigned short const*, int, unsigned short)+0x679>
  407988:	cmp    $0xf,%esi
  40798b:	jne    407520 <ab_base::simd_quad_intel(unsigned short const*, int, unsigned short)+0x2a0>
  407991:	movzwl 0x1c(%rcx),%eax
  407995:	cmp    %dx,%ax
  407998:	jae    4078f9 <ab_base::simd_quad_intel(unsigned short const*, int, unsigned short)+0x679>
  40799e:	xor    %eax,%eax
  4079a0:	jmp    407522 <ab_base::simd_quad_intel(unsigned short const*, int, unsigned short)+0x2a2>
  4079a5:	nopl   (%rax)
  4079a8:	mov    $0x1,%eax
  4079ad:	vzeroupper
  4079b0:	ret
  4079b1:	nopl   0x0(%rax)
  4079b8:	xor    %eax,%eax
  4079ba:	vzeroupper
  4079bd:	mov    -0x8(%rbp),%rbx
  4079c1:	leave
  4079c2:	ret
  4079c3:	nopl   0x0(%rax,%rax,1)
  4079c8:	shl    $0x4,%r10d
  4079cc:	cmp    %ebx,%r10d
  4079cf:	je     4079b8 <ab_base::simd_quad_intel(unsigned short const*, int, unsigned short)+0x738>
  4079d1:	add    %r10d,%eax
  4079d4:	jmp    407802 <ab_base::simd_quad_intel(unsigned short const*, int, unsigned short)+0x582>
  4079d9:	mov    %edx,%r9d
  4079dc:	movzwl (%rcx,%r9,2),%eax
  4079e1:	cmp    %di,%ax
  4079e4:	jae    4078f9 <ab_base::simd_quad_intel(unsigned short const*, int, unsigned short)+0x679>
  4079ea:	movzwl 0x2(%rcx,%r9,2),%eax
  4079f0:	lea    0x2(%r9,%r9,1),%rsi
  4079f5:	cmp    %di,%ax
  4079f8:	jb     4073ec <ab_base::simd_quad_intel(unsigned short const*, int, unsigned short)+0x16c>
  4079fe:	jmp    4078f9 <ab_base::simd_quad_intel(unsigned short const*, int, unsigned short)+0x679>
  407a03:	mov    $0x10,%edx
  407a08:	jmp    407389 <ab_base::simd_quad_intel(unsigned short const*, int, unsigned short)+0x109>
  407a0d:	mov    $0x10,%edx
  407a12:	jmp    4073af <ab_base::simd_quad_intel(unsigned short const*, int, unsigned short)+0x12f>
  407a17:	inc    %eax
  407a19:	jmp    4077c3 <ab_base::simd_quad_intel(unsigned short const*, int, unsigned short)+0x543>
  407a1e:	add    $0x2,%eax
  407a21:	jmp    4077c3 <ab_base::simd_quad_intel(unsigned short const*, int, unsigned short)+0x543>
  407a26:	add    $0x3,%eax
  407a29:	jmp    4077c3 <ab_base::simd_quad_intel(unsigned short const*, int, unsigned short)+0x543>
  407a2e:	add    $0x4,%eax
  407a31:	jmp    4077c3 <ab_base::simd_quad_intel(unsigned short const*, int, unsigned short)+0x543>
  407a36:	add    $0x5,%eax
  407a39:	jmp    4077c3 <ab_base::simd_quad_intel(unsigned short const*, int, unsigned short)+0x543>
  407a3e:	mov    $0x11,%edx
  407a43:	jmp    407389 <ab_base::simd_quad_intel(unsigned short const*, int, unsigned short)+0x109>
  407a48:	mov    $0x12,%edx
  407a4d:	jmp    407389 <ab_base::simd_quad_intel(unsigned short const*, int, unsigned short)+0x109>
  407a52:	add    $0x6,%eax
  407a55:	jmp    4077c3 <ab_base::simd_quad_intel(unsigned short const*, int, unsigned short)+0x543>
  407a5a:	add    $0x7,%eax
  407a5d:	jmp    4077c3 <ab_base::simd_quad_intel(unsigned short const*, int, unsigned short)+0x543>
  407a62:	mov    $0x13,%edx
  407a67:	jmp    407389 <ab_base::simd_quad_intel(unsigned short const*, int, unsigned short)+0x109>
  407a6c:	mov    $0x14,%edx
  407a71:	jmp    407389 <ab_base::simd_quad_intel(unsigned short const*, int, unsigned short)+0x109>
  407a76:	add    $0x8,%eax
  407a79:	jmp    4077c3 <ab_base::simd_quad_intel(unsigned short const*, int, unsigned short)+0x543>
  407a7e:	mov    $0x15,%edx
  407a83:	jmp    407389 <ab_base::simd_quad_intel(unsigned short const*, int, unsigned short)+0x109>
  407a88:	add    $0x9,%eax
  407a8b:	jmp    4077c3 <ab_base::simd_quad_intel(unsigned short const*, int, unsigned short)+0x543>
  407a90:	mov    $0x16,%edx
  407a95:	jmp    407389 <ab_base::simd_quad_intel(unsigned short const*, int, unsigned short)+0x109>
  407a9a:	add    $0xa,%eax
  407a9d:	jmp    4077c3 <ab_base::simd_quad_intel(unsigned short const*, int, unsigned short)+0x543>
  407aa2:	add    $0xc,%eax
  407aa5:	jmp    4077c3 <ab_base::simd_quad_intel(unsigned short const*, int, unsigned short)+0x543>
  407aaa:	add    $0xb,%eax
  407aad:	jmp    4077c3 <ab_base::simd_quad_intel(unsigned short const*, int, unsigned short)+0x543>
  407ab2:	add    $0xd,%eax
  407ab5:	jmp    4077c3 <ab_base::simd_quad_intel(unsigned short const*, int, unsigned short)+0x543>
  407aba:	add    $0xe,%eax
  407abd:	jmp    4077c3 <ab_base::simd_quad_intel(unsigned short const*, int, unsigned short)+0x543>
  407ac2:	nopl   (%rax)
  407ac5:	data16 cs nopw 0x0(%rax,%rax,1)
