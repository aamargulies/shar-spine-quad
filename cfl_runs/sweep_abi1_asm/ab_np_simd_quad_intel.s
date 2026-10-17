0000000000409700 <ab_np::simd_quad_intel(unsigned short const*, int, unsigned short)>:
  409700:	mov    %rdi,%r8
  409703:	mov    %edx,%edi
  409705:	mov    %esi,%r9d
  409708:	vmovd  %edi,%xmm1
  40970c:	vpbroadcastw %xmm1,%ymm1
  409711:	cmp    $0x1f,%esi
  409714:	jg     4099c0 <ab_np::simd_quad_intel(unsigned short const*, int, unsigned short)+0x2c0>
  40971a:	cmp    $0xf,%esi
  40971d:	jle    409cf0 <ab_np::simd_quad_intel(unsigned short const*, int, unsigned short)+0x5f0>
  409723:	vpcmpeqw (%r8),%ymm1,%ymm0
  409728:	vpmovmskb %ymm0,%eax
  40972c:	test   %eax,%eax
  40972e:	jne    409e38 <ab_np::simd_quad_intel(unsigned short const*, int, unsigned short)+0x738>
  409734:	cmp    $0x10,%esi
  409737:	je     4099b0 <ab_np::simd_quad_intel(unsigned short const*, int, unsigned short)+0x2b0>
  40973d:	lea    0x20(%r8),%r10
  409741:	mov    $0xb,%esi
  409746:	mov    %r10,%rdx
  409749:	shr    $1,%rdx
  40974c:	neg    %rdx
  40974f:	mov    %edx,%ecx
  409751:	and    $0x7,%ecx
  409754:	lea    0x8(%rcx),%eax
  409757:	cmp    %esi,%eax
  409759:	cmovb  %esi,%eax
  40975c:	lea    -0x11(%r9),%esi
  409760:	cmp    %eax,%esi
  409762:	jb     409e9c <ab_np::simd_quad_intel(unsigned short const*, int, unsigned short)+0x79c>
  409768:	test   %ecx,%ecx
  40976a:	je     409e92 <ab_np::simd_quad_intel(unsigned short const*, int, unsigned short)+0x792>
  409770:	movzwl 0x20(%r8),%eax
  409775:	cmp    %di,%ax
  409778:	jae    409d80 <ab_np::simd_quad_intel(unsigned short const*, int, unsigned short)+0x680>
  40977e:	test   $0x6,%dl
  409781:	je     409ecd <ab_np::simd_quad_intel(unsigned short const*, int, unsigned short)+0x7cd>
  409787:	movzwl 0x22(%r8),%eax
  40978c:	cmp    %di,%ax
  40978f:	jae    409d80 <ab_np::simd_quad_intel(unsigned short const*, int, unsigned short)+0x680>
  409795:	cmp    $0x2,%ecx
  409798:	jbe    409ed7 <ab_np::simd_quad_intel(unsigned short const*, int, unsigned short)+0x7d7>
  40979e:	movzwl 0x24(%r8),%eax
  4097a3:	cmp    %di,%ax
  4097a6:	jae    409d80 <ab_np::simd_quad_intel(unsigned short const*, int, unsigned short)+0x680>
  4097ac:	and    $0x4,%edx
  4097af:	je     409ef1 <ab_np::simd_quad_intel(unsigned short const*, int, unsigned short)+0x7f1>
  4097b5:	movzwl 0x26(%r8),%eax
  4097ba:	cmp    %di,%ax
  4097bd:	jae    409d80 <ab_np::simd_quad_intel(unsigned short const*, int, unsigned short)+0x680>
  4097c3:	cmp    $0x4,%ecx
  4097c6:	je     409efb <ab_np::simd_quad_intel(unsigned short const*, int, unsigned short)+0x7fb>
  4097cc:	movzwl 0x28(%r8),%eax
  4097d1:	cmp    %di,%ax
  4097d4:	jae    409d80 <ab_np::simd_quad_intel(unsigned short const*, int, unsigned short)+0x680>
  4097da:	cmp    $0x5,%ecx
  4097dd:	je     409f0d <ab_np::simd_quad_intel(unsigned short const*, int, unsigned short)+0x80d>
  4097e3:	movzwl 0x2a(%r8),%eax
  4097e8:	cmp    %di,%ax
  4097eb:	jae    409d80 <ab_np::simd_quad_intel(unsigned short const*, int, unsigned short)+0x680>
  4097f1:	cmp    $0x7,%ecx
  4097f4:	jne    409f1f <ab_np::simd_quad_intel(unsigned short const*, int, unsigned short)+0x81f>
  4097fa:	movzwl 0x2c(%r8),%eax
  4097ff:	cmp    %di,%ax
  409802:	jae    409d80 <ab_np::simd_quad_intel(unsigned short const*, int, unsigned short)+0x680>
  409808:	mov    $0x17,%edx
  40980d:	mov    %ecx,%eax
  40980f:	vpminuw (%r10,%rax,2),%xmm1,%xmm0
  409815:	vpcmpeqw %xmm0,%xmm1,%xmm1
  409819:	vptest %xmm1,%xmm1
  40981e:	jne    409e69 <ab_np::simd_quad_intel(unsigned short const*, int, unsigned short)+0x769>
  409824:	lea    -0x18(%r9),%eax
  409828:	cmp    %ecx,%eax
  40982a:	je     4099b0 <ab_np::simd_quad_intel(unsigned short const*, int, unsigned short)+0x2b0>
  409830:	add    $0x8,%edx
  409833:	mov    %edx,%esi
  409835:	movzwl (%r8,%rsi,2),%eax
  40983a:	cmp    %di,%ax
  40983d:	jae    409d80 <ab_np::simd_quad_intel(unsigned short const*, int, unsigned short)+0x680>
  409843:	lea    0x1(%rdx),%eax
  409846:	cmp    %eax,%r9d
  409849:	jle    4099b0 <ab_np::simd_quad_intel(unsigned short const*, int, unsigned short)+0x2b0>
  40984f:	movzwl 0x2(%r8,%rsi,2),%eax
  409855:	lea    0x2(%rsi,%rsi,1),%rcx
  40985a:	cmp    %di,%ax
  40985d:	jae    409d80 <ab_np::simd_quad_intel(unsigned short const*, int, unsigned short)+0x680>
  409863:	lea    0x2(%rdx),%eax
  409866:	cmp    %r9d,%eax
  409869:	jge    4099b0 <ab_np::simd_quad_intel(unsigned short const*, int, unsigned short)+0x2b0>
  40986f:	movzwl 0x2(%r8,%rcx,1),%eax
  409875:	cmp    %di,%ax
  409878:	jae    409d80 <ab_np::simd_quad_intel(unsigned short const*, int, unsigned short)+0x680>
  40987e:	lea    0x3(%rdx),%eax
  409881:	cmp    %eax,%r9d
  409884:	jle    4099b0 <ab_np::simd_quad_intel(unsigned short const*, int, unsigned short)+0x2b0>
  40988a:	movzwl 0x4(%r8,%rcx,1),%eax
  409890:	cmp    %di,%ax
  409893:	jae    409d80 <ab_np::simd_quad_intel(unsigned short const*, int, unsigned short)+0x680>
  409899:	lea    0x4(%rdx),%eax
  40989c:	cmp    %eax,%r9d
  40989f:	jle    4099b0 <ab_np::simd_quad_intel(unsigned short const*, int, unsigned short)+0x2b0>
  4098a5:	movzwl 0x6(%r8,%rcx,1),%eax
  4098ab:	cmp    %di,%ax
  4098ae:	jae    409d80 <ab_np::simd_quad_intel(unsigned short const*, int, unsigned short)+0x680>
  4098b4:	lea    0x5(%rdx),%eax
  4098b7:	cmp    %r9d,%eax
  4098ba:	jge    4099b0 <ab_np::simd_quad_intel(unsigned short const*, int, unsigned short)+0x2b0>
  4098c0:	movzwl 0x8(%r8,%rcx,1),%eax
  4098c6:	cmp    %di,%ax
  4098c9:	jae    409d80 <ab_np::simd_quad_intel(unsigned short const*, int, unsigned short)+0x680>
  4098cf:	lea    0x6(%rdx),%eax
  4098d2:	cmp    %eax,%r9d
  4098d5:	jle    4099b0 <ab_np::simd_quad_intel(unsigned short const*, int, unsigned short)+0x2b0>
  4098db:	movzwl 0xa(%r8,%rcx,1),%eax
  4098e1:	cmp    %di,%ax
  4098e4:	jae    409d80 <ab_np::simd_quad_intel(unsigned short const*, int, unsigned short)+0x680>
  4098ea:	lea    0x7(%rdx),%eax
  4098ed:	cmp    %eax,%r9d
  4098f0:	jle    4099b0 <ab_np::simd_quad_intel(unsigned short const*, int, unsigned short)+0x2b0>
  4098f6:	movzwl 0xc(%r8,%rcx,1),%eax
  4098fc:	cmp    %di,%ax
  4098ff:	jae    409d80 <ab_np::simd_quad_intel(unsigned short const*, int, unsigned short)+0x680>
  409905:	lea    0x8(%rdx),%eax
  409908:	cmp    %eax,%r9d
  40990b:	jle    4099b0 <ab_np::simd_quad_intel(unsigned short const*, int, unsigned short)+0x2b0>
  409911:	movzwl 0xe(%r8,%rcx,1),%eax
  409917:	cmp    %di,%ax
  40991a:	jae    409d80 <ab_np::simd_quad_intel(unsigned short const*, int, unsigned short)+0x680>
  409920:	lea    0x9(%rdx),%eax
  409923:	cmp    %eax,%r9d
  409926:	jle    4099b0 <ab_np::simd_quad_intel(unsigned short const*, int, unsigned short)+0x2b0>
  40992c:	movzwl 0x10(%r8,%rcx,1),%eax
  409932:	cmp    %di,%ax
  409935:	jae    409d80 <ab_np::simd_quad_intel(unsigned short const*, int, unsigned short)+0x680>
  40993b:	lea    0xa(%rdx),%eax
  40993e:	cmp    %eax,%r9d
  409941:	jle    4099b0 <ab_np::simd_quad_intel(unsigned short const*, int, unsigned short)+0x2b0>
  409943:	movzwl 0x12(%r8,%rcx,1),%eax
  409949:	cmp    %di,%ax
  40994c:	jae    409d80 <ab_np::simd_quad_intel(unsigned short const*, int, unsigned short)+0x680>
  409952:	lea    0xb(%rdx),%eax
  409955:	cmp    %eax,%r9d
  409958:	jle    4099b0 <ab_np::simd_quad_intel(unsigned short const*, int, unsigned short)+0x2b0>
  40995a:	movzwl 0x14(%r8,%rcx,1),%eax
  409960:	cmp    %di,%ax
  409963:	jae    409d80 <ab_np::simd_quad_intel(unsigned short const*, int, unsigned short)+0x680>
  409969:	lea    0xc(%rdx),%eax
  40996c:	cmp    %eax,%r9d
  40996f:	jle    4099b0 <ab_np::simd_quad_intel(unsigned short const*, int, unsigned short)+0x2b0>
  409971:	movzwl 0x16(%r8,%rcx,1),%eax
  409977:	cmp    %di,%ax
  40997a:	jae    409d80 <ab_np::simd_quad_intel(unsigned short const*, int, unsigned short)+0x680>
  409980:	lea    0xd(%rdx),%eax
  409983:	cmp    %eax,%r9d
  409986:	jle    4099b0 <ab_np::simd_quad_intel(unsigned short const*, int, unsigned short)+0x2b0>
  409988:	movzwl 0x18(%r8,%rcx,1),%eax
  40998e:	cmp    %di,%ax
  409991:	jae    409d80 <ab_np::simd_quad_intel(unsigned short const*, int, unsigned short)+0x680>
  409997:	add    $0xe,%edx
  40999a:	cmp    %edx,%r9d
  40999d:	jle    4099b0 <ab_np::simd_quad_intel(unsigned short const*, int, unsigned short)+0x2b0>
  40999f:	movzwl 0x3c(%r8),%eax
  4099a4:	cmp    %di,%ax
  4099a7:	jae    409d80 <ab_np::simd_quad_intel(unsigned short const*, int, unsigned short)+0x680>
  4099ad:	nopl   (%rax)
  4099b0:	xor    %eax,%eax
  4099b2:	vzeroupper
  4099b5:	ret
  4099b6:	cs nopw 0x0(%rax,%rax,1)
  4099c0:	push   %rbp
  4099c1:	mov    %esi,%r10d
  4099c4:	xor    %esi,%esi
  4099c6:	sar    $0x5,%r10d
  4099ca:	mov    %r10d,%edx
  4099cd:	mov    %rsp,%rbp
  4099d0:	push   %rbx
  4099d1:	cmp    $0x7f,%r9d
  4099d5:	jle    409a5d <ab_np::simd_quad_intel(unsigned short const*, int, unsigned short)+0x35d>
  4099db:	nopl   0x0(%rax,%rax,1)
  4099e0:	mov    %edx,%ecx
  4099e2:	sar    $0x2,%ecx
  4099e5:	lea    (%rcx,%rsi,1),%eax
  4099e8:	lea    (%rax,%rcx,1),%r11d
  4099ec:	inc    %eax
  4099ee:	shl    $0x5,%eax
  4099f1:	lea    0x1(%r11),%ebx
  4099f5:	lea    0x1(%rcx,%r11,1),%r11d
  4099fa:	cltq
  4099fc:	cmp    %di,-0x2(%r8,%rax,2)
  409a02:	setb   %al
  409a05:	shl    $0x5,%ebx
  409a08:	movslq %ebx,%rbx
  409a0b:	movzbl %al,%eax
  409a0e:	cmp    %di,-0x2(%r8,%rbx,2)
  409a14:	adc    $0x0,%eax
  409a17:	shl    $0x5,%r11d
  409a1b:	movslq %r11d,%r11
  409a1e:	cmp    %di,-0x2(%r8,%r11,2)
  409a24:	adc    $0x0,%eax
  409a27:	imul   %ecx,%eax
  409a2a:	add    %eax,%esi
  409a2c:	lea    (%rcx,%rcx,2),%eax
  409a2f:	sub    %eax,%edx
  409a31:	cmp    $0x3,%edx
  409a34:	jg     4099e0 <ab_np::simd_quad_intel(unsigned short const*, int, unsigned short)+0x2e0>
  409a36:	jmp    409a5d <ab_np::simd_quad_intel(unsigned short const*, int, unsigned short)+0x35d>
  409a38:	nopl   0x0(%rax,%rax,1)
  409a40:	mov    %edx,%ecx
  409a42:	sar    $1,%ecx
  409a44:	lea    (%rcx,%rsi,1),%r11d
  409a48:	lea    0x1(%r11),%eax
  409a4c:	shl    $0x5,%eax
  409a4f:	cltq
  409a51:	cmp    %di,-0x2(%r8,%rax,2)
  409a57:	cmovb  %r11d,%esi
  409a5b:	sub    %ecx,%edx
  409a5d:	cmp    $0x1,%edx
  409a60:	jg     409a40 <ab_np::simd_quad_intel(unsigned short const*, int, unsigned short)+0x340>
  409a62:	lea    0x1(%rsi),%eax
  409a65:	mov    %eax,%edx
  409a67:	shl    $0x5,%edx
  409a6a:	movslq %edx,%rdx
  409a6d:	cmp    %di,-0x2(%r8,%rdx,2)
  409a73:	cmovae %esi,%eax
  409a76:	cmp    %r10d,%eax
  409a79:	jl     409cc8 <ab_np::simd_quad_intel(unsigned short const*, int, unsigned short)+0x5c8>
  409a7f:	mov    %r10d,%eax
  409a82:	shl    $0x5,%eax
  409a85:	cmp    %eax,%r9d
  409a88:	jle    409e48 <ab_np::simd_quad_intel(unsigned short const*, int, unsigned short)+0x748>
  409a8e:	mov    %r10d,%r10d
  409a91:	mov    %r9d,%ebx
  409a94:	shl    $0x6,%r10
  409a98:	sub    %eax,%ebx
  409a9a:	lea    (%r8,%r10,1),%rcx
  409a9e:	mov    $0x17,%r10d
  409aa4:	mov    %rcx,%r11
  409aa7:	shr    $1,%r11
  409aaa:	neg    %r11
  409aad:	mov    %r11d,%esi
  409ab0:	and    $0xf,%esi
  409ab3:	lea    0x10(%rsi),%edx
  409ab6:	cmp    %r10d,%edx
  409ab9:	cmovb  %r10d,%edx
  409abd:	lea    -0x1(%rbx),%r10d
  409ac1:	cmp    %edx,%r10d
  409ac4:	jb     409c82 <ab_np::simd_quad_intel(unsigned short const*, int, unsigned short)+0x582>
  409aca:	test   %esi,%esi
  409acc:	je     409c37 <ab_np::simd_quad_intel(unsigned short const*, int, unsigned short)+0x537>
  409ad2:	movzwl (%rcx),%edx
  409ad5:	cmp    %di,%dx
  409ad8:	jae    409cb6 <ab_np::simd_quad_intel(unsigned short const*, int, unsigned short)+0x5b6>
  409ade:	test   $0xe,%r11b
  409ae2:	je     409ea6 <ab_np::simd_quad_intel(unsigned short const*, int, unsigned short)+0x7a6>
  409ae8:	lea    0x1(%rax),%r10d
  409aec:	movzwl (%r8,%r10,2),%edx
  409af1:	cmp    %di,%dx
  409af4:	jae    409cb6 <ab_np::simd_quad_intel(unsigned short const*, int, unsigned short)+0x5b6>
  409afa:	cmp    $0x2,%esi
  409afd:	jbe    409ead <ab_np::simd_quad_intel(unsigned short const*, int, unsigned short)+0x7ad>
  409b03:	movzwl 0x2(%r8,%r10,2),%edx
  409b09:	cmp    %di,%dx
  409b0c:	jae    409cb6 <ab_np::simd_quad_intel(unsigned short const*, int, unsigned short)+0x5b6>
  409b12:	test   $0xc,%r11b
  409b16:	je     409eb5 <ab_np::simd_quad_intel(unsigned short const*, int, unsigned short)+0x7b5>
  409b1c:	movzwl 0x4(%r8,%r10,2),%edx
  409b22:	cmp    %di,%dx
  409b25:	jae    409cb6 <ab_np::simd_quad_intel(unsigned short const*, int, unsigned short)+0x5b6>
  409b2b:	cmp    $0x4,%esi
  409b2e:	jbe    409ebd <ab_np::simd_quad_intel(unsigned short const*, int, unsigned short)+0x7bd>
  409b34:	movzwl 0x6(%r8,%r10,2),%edx
  409b3a:	cmp    %di,%dx
  409b3d:	jae    409cb6 <ab_np::simd_quad_intel(unsigned short const*, int, unsigned short)+0x5b6>
  409b43:	cmp    $0x5,%esi
  409b46:	je     409ec5 <ab_np::simd_quad_intel(unsigned short const*, int, unsigned short)+0x7c5>
  409b4c:	movzwl 0x8(%r8,%r10,2),%edx
  409b52:	cmp    %di,%dx
  409b55:	jae    409cb6 <ab_np::simd_quad_intel(unsigned short const*, int, unsigned short)+0x5b6>
  409b5b:	cmp    $0x6,%esi
  409b5e:	je     409ee1 <ab_np::simd_quad_intel(unsigned short const*, int, unsigned short)+0x7e1>
  409b64:	movzwl 0xa(%r8,%r10,2),%edx
  409b6a:	cmp    %di,%dx
  409b6d:	jae    409cb6 <ab_np::simd_quad_intel(unsigned short const*, int, unsigned short)+0x5b6>
  409b73:	and    $0x8,%r11d
  409b77:	je     409ee9 <ab_np::simd_quad_intel(unsigned short const*, int, unsigned short)+0x7e9>
  409b7d:	movzwl 0xc(%r8,%r10,2),%edx
  409b83:	cmp    %di,%dx
  409b86:	jae    409cb6 <ab_np::simd_quad_intel(unsigned short const*, int, unsigned short)+0x5b6>
  409b8c:	cmp    $0x8,%esi
  409b8f:	je     409f05 <ab_np::simd_quad_intel(unsigned short const*, int, unsigned short)+0x805>
  409b95:	movzwl 0xe(%r8,%r10,2),%edx
  409b9b:	cmp    %di,%dx
  409b9e:	jae    409cb6 <ab_np::simd_quad_intel(unsigned short const*, int, unsigned short)+0x5b6>
  409ba4:	cmp    $0x9,%esi
  409ba7:	je     409f17 <ab_np::simd_quad_intel(unsigned short const*, int, unsigned short)+0x817>
  409bad:	movzwl 0x10(%r8,%r10,2),%edx
  409bb3:	cmp    %di,%dx
  409bb6:	jae    409cb6 <ab_np::simd_quad_intel(unsigned short const*, int, unsigned short)+0x5b6>
  409bbc:	cmp    $0xa,%esi
  409bbf:	je     409f29 <ab_np::simd_quad_intel(unsigned short const*, int, unsigned short)+0x829>
  409bc5:	movzwl 0x12(%r8,%r10,2),%edx
  409bcb:	cmp    %di,%dx
  409bce:	jae    409cb6 <ab_np::simd_quad_intel(unsigned short const*, int, unsigned short)+0x5b6>
  409bd4:	cmp    $0xb,%esi
  409bd7:	je     409f39 <ab_np::simd_quad_intel(unsigned short const*, int, unsigned short)+0x839>
  409bdd:	movzwl 0x14(%r8,%r10,2),%edx
  409be3:	cmp    %di,%dx
  409be6:	jae    409cb6 <ab_np::simd_quad_intel(unsigned short const*, int, unsigned short)+0x5b6>
  409bec:	cmp    $0xc,%esi
  409bef:	je     409f31 <ab_np::simd_quad_intel(unsigned short const*, int, unsigned short)+0x831>
  409bf5:	movzwl 0x16(%r8,%r10,2),%edx
  409bfb:	cmp    %di,%dx
  409bfe:	jae    409cb6 <ab_np::simd_quad_intel(unsigned short const*, int, unsigned short)+0x5b6>
  409c04:	cmp    $0xd,%esi
  409c07:	je     409f41 <ab_np::simd_quad_intel(unsigned short const*, int, unsigned short)+0x841>
  409c0d:	movzwl 0x18(%r8,%r10,2),%edx
  409c13:	cmp    %di,%dx
  409c16:	jae    409cb6 <ab_np::simd_quad_intel(unsigned short const*, int, unsigned short)+0x5b6>
  409c1c:	cmp    $0xf,%esi
  409c1f:	jne    409f49 <ab_np::simd_quad_intel(unsigned short const*, int, unsigned short)+0x849>
  409c25:	movzwl 0x1a(%r8,%r10,2),%edx
  409c2b:	cmp    %di,%dx
  409c2e:	jae    409cb6 <ab_np::simd_quad_intel(unsigned short const*, int, unsigned short)+0x5b6>
  409c34:	add    $0xf,%eax
  409c37:	sub    %esi,%ebx
  409c39:	lea    (%rcx,%rsi,2),%rdx
  409c3d:	xor    %ecx,%ecx
  409c3f:	mov    %ebx,%r10d
  409c42:	shr    $0x4,%r10d
  409c46:	mov    %r10d,%esi
  409c49:	shl    $0x5,%rsi
  409c4d:	add    %rdx,%rsi
  409c50:	jmp    409c70 <ab_np::simd_quad_intel(unsigned short const*, int, unsigned short)+0x570>
  409c52:	nopl   (%rax)
  409c55:	data16 cs nopw 0x0(%rax,%rax,1)
  409c60:	add    $0x20,%rdx
  409c64:	add    $0x10,%ecx
  409c67:	cmp    %rdx,%rsi
  409c6a:	je     409e58 <ab_np::simd_quad_intel(unsigned short const*, int, unsigned short)+0x758>
  409c70:	vpminuw (%rdx),%ymm1,%ymm0
  409c75:	vpcmpeqw %ymm0,%ymm1,%ymm0
  409c79:	vptest %ymm0,%ymm0
  409c7e:	je     409c60 <ab_np::simd_quad_intel(unsigned short const*, int, unsigned short)+0x560>
  409c80:	add    %ecx,%eax
  409c82:	cltq
  409c84:	jmp    409cac <ab_np::simd_quad_intel(unsigned short const*, int, unsigned short)+0x5ac>
  409c86:	nopl   0x0(%rax)
  409c8a:	data16 cs nopw 0x0(%rax,%rax,1)
  409c95:	data16 cs nopw 0x0(%rax,%rax,1)
  409ca0:	inc    %rax
  409ca3:	cmp    %eax,%r9d
  409ca6:	jle    409e48 <ab_np::simd_quad_intel(unsigned short const*, int, unsigned short)+0x748>
  409cac:	movzwl (%r8,%rax,2),%edx
  409cb1:	cmp    %di,%dx
  409cb4:	jb     409ca0 <ab_np::simd_quad_intel(unsigned short const*, int, unsigned short)+0x5a0>
  409cb6:	cmp    %dx,%di
  409cb9:	vzeroupper
  409cbc:	sete   %al
  409cbf:	mov    -0x8(%rbp),%rbx
  409cc3:	leave
  409cc4:	ret
  409cc5:	nopl   (%rax)
  409cc8:	shl    $0x5,%eax
  409ccb:	cltq
  409ccd:	lea    (%r8,%rax,2),%rax
  409cd1:	vpcmpeqw (%rax),%ymm1,%ymm0
  409cd5:	vpcmpeqw 0x20(%rax),%ymm1,%ymm1
  409cda:	vpor   %ymm1,%ymm0,%ymm0
  409cde:	vpmovmskb %ymm0,%eax
  409ce2:	test   %eax,%eax
  409ce4:	vzeroupper
  409ce7:	setne  %al
  409cea:	mov    -0x8(%rbp),%rbx
  409cee:	leave
  409cef:	ret
  409cf0:	cmp    $0x7,%esi
  409cf3:	jg     409d90 <ab_np::simd_quad_intel(unsigned short const*, int, unsigned short)+0x690>
  409cf9:	test   %esi,%esi
  409cfb:	jle    4099b0 <ab_np::simd_quad_intel(unsigned short const*, int, unsigned short)+0x2b0>
  409d01:	movzwl (%r8),%eax
  409d05:	cmp    %dx,%ax
  409d08:	jae    409d80 <ab_np::simd_quad_intel(unsigned short const*, int, unsigned short)+0x680>
  409d0a:	cmp    $0x1,%esi
  409d0d:	je     4099b0 <ab_np::simd_quad_intel(unsigned short const*, int, unsigned short)+0x2b0>
  409d13:	movzwl 0x2(%r8),%eax
  409d18:	cmp    %dx,%ax
  409d1b:	jae    409d80 <ab_np::simd_quad_intel(unsigned short const*, int, unsigned short)+0x680>
  409d1d:	cmp    $0x2,%esi
  409d20:	je     4099b0 <ab_np::simd_quad_intel(unsigned short const*, int, unsigned short)+0x2b0>
  409d26:	movzwl 0x4(%r8),%eax
  409d2b:	cmp    %dx,%ax
  409d2e:	jae    409d80 <ab_np::simd_quad_intel(unsigned short const*, int, unsigned short)+0x680>
  409d30:	cmp    $0x3,%esi
  409d33:	je     4099b0 <ab_np::simd_quad_intel(unsigned short const*, int, unsigned short)+0x2b0>
  409d39:	movzwl 0x6(%r8),%eax
  409d3e:	cmp    %dx,%ax
  409d41:	jae    409d80 <ab_np::simd_quad_intel(unsigned short const*, int, unsigned short)+0x680>
  409d43:	cmp    $0x4,%esi
  409d46:	je     4099b0 <ab_np::simd_quad_intel(unsigned short const*, int, unsigned short)+0x2b0>
  409d4c:	movzwl 0x8(%r8),%eax
  409d51:	cmp    %dx,%ax
  409d54:	jae    409d80 <ab_np::simd_quad_intel(unsigned short const*, int, unsigned short)+0x680>
  409d56:	cmp    $0x5,%esi
  409d59:	je     4099b0 <ab_np::simd_quad_intel(unsigned short const*, int, unsigned short)+0x2b0>
  409d5f:	movzwl 0xa(%r8),%eax
  409d64:	cmp    %dx,%ax
  409d67:	jae    409d80 <ab_np::simd_quad_intel(unsigned short const*, int, unsigned short)+0x680>
  409d69:	cmp    $0x7,%esi
  409d6c:	jne    4099b0 <ab_np::simd_quad_intel(unsigned short const*, int, unsigned short)+0x2b0>
  409d72:	movzwl 0xc(%r8),%eax
  409d77:	cmp    %dx,%ax
  409d7a:	jb     4099b0 <ab_np::simd_quad_intel(unsigned short const*, int, unsigned short)+0x2b0>
  409d80:	cmp    %ax,%di
  409d83:	sete   %al
  409d86:	vzeroupper
  409d89:	ret
  409d8a:	nopw   0x0(%rax,%rax,1)
  409d90:	vpcmpeqw (%r8),%xmm1,%xmm1
  409d95:	vpmovmskb %xmm1,%eax
  409d99:	test   %eax,%eax
  409d9b:	jne    409e38 <ab_np::simd_quad_intel(unsigned short const*, int, unsigned short)+0x738>
  409da1:	cmp    $0x8,%esi
  409da4:	je     4099b0 <ab_np::simd_quad_intel(unsigned short const*, int, unsigned short)+0x2b0>
  409daa:	movzwl 0x10(%r8),%eax
  409daf:	cmp    %dx,%ax
  409db2:	jae    409d80 <ab_np::simd_quad_intel(unsigned short const*, int, unsigned short)+0x680>
  409db4:	cmp    $0x9,%esi
  409db7:	je     4099b0 <ab_np::simd_quad_intel(unsigned short const*, int, unsigned short)+0x2b0>
  409dbd:	movzwl 0x12(%r8),%eax
  409dc2:	cmp    %dx,%ax
  409dc5:	jae    409d80 <ab_np::simd_quad_intel(unsigned short const*, int, unsigned short)+0x680>
  409dc7:	cmp    $0xa,%esi
  409dca:	je     4099b0 <ab_np::simd_quad_intel(unsigned short const*, int, unsigned short)+0x2b0>
  409dd0:	movzwl 0x14(%r8),%eax
  409dd5:	cmp    %dx,%ax
  409dd8:	jae    409d80 <ab_np::simd_quad_intel(unsigned short const*, int, unsigned short)+0x680>
  409dda:	cmp    $0xb,%esi
  409ddd:	je     4099b0 <ab_np::simd_quad_intel(unsigned short const*, int, unsigned short)+0x2b0>
  409de3:	movzwl 0x16(%r8),%eax
  409de8:	cmp    %dx,%ax
  409deb:	jae    409d80 <ab_np::simd_quad_intel(unsigned short const*, int, unsigned short)+0x680>
  409ded:	cmp    $0xc,%esi
  409df0:	je     4099b0 <ab_np::simd_quad_intel(unsigned short const*, int, unsigned short)+0x2b0>
  409df6:	movzwl 0x18(%r8),%eax
  409dfb:	cmp    %dx,%ax
  409dfe:	jae    409d80 <ab_np::simd_quad_intel(unsigned short const*, int, unsigned short)+0x680>
  409e00:	cmp    $0xd,%esi
  409e03:	je     4099b0 <ab_np::simd_quad_intel(unsigned short const*, int, unsigned short)+0x2b0>
  409e09:	movzwl 0x1a(%r8),%eax
  409e0e:	cmp    %dx,%ax
  409e11:	jae    409d80 <ab_np::simd_quad_intel(unsigned short const*, int, unsigned short)+0x680>
  409e17:	cmp    $0xf,%esi
  409e1a:	jne    4099b0 <ab_np::simd_quad_intel(unsigned short const*, int, unsigned short)+0x2b0>
  409e20:	movzwl 0x1c(%r8),%eax
  409e25:	cmp    %dx,%ax
  409e28:	jae    409d80 <ab_np::simd_quad_intel(unsigned short const*, int, unsigned short)+0x680>
  409e2e:	xor    %eax,%eax
  409e30:	jmp    4099b2 <ab_np::simd_quad_intel(unsigned short const*, int, unsigned short)+0x2b2>
  409e35:	nopl   (%rax)
  409e38:	mov    $0x1,%eax
  409e3d:	vzeroupper
  409e40:	ret
  409e41:	nopl   0x0(%rax)
  409e48:	xor    %eax,%eax
  409e4a:	vzeroupper
  409e4d:	mov    -0x8(%rbp),%rbx
  409e51:	leave
  409e52:	ret
  409e53:	nopl   0x0(%rax,%rax,1)
  409e58:	shl    $0x4,%r10d
  409e5c:	cmp    %ebx,%r10d
  409e5f:	je     409e48 <ab_np::simd_quad_intel(unsigned short const*, int, unsigned short)+0x748>
  409e61:	add    %r10d,%eax
  409e64:	jmp    409c82 <ab_np::simd_quad_intel(unsigned short const*, int, unsigned short)+0x582>
  409e69:	mov    %edx,%esi
  409e6b:	movzwl (%r8,%rsi,2),%eax
  409e70:	cmp    %di,%ax
  409e73:	jae    409d80 <ab_np::simd_quad_intel(unsigned short const*, int, unsigned short)+0x680>
  409e79:	movzwl 0x2(%r8,%rsi,2),%eax
  409e7f:	lea    0x2(%rsi,%rsi,1),%rcx
  409e84:	cmp    %di,%ax
  409e87:	jb     40986f <ab_np::simd_quad_intel(unsigned short const*, int, unsigned short)+0x16f>
  409e8d:	jmp    409d80 <ab_np::simd_quad_intel(unsigned short const*, int, unsigned short)+0x680>
  409e92:	mov    $0x10,%edx
  409e97:	jmp    40980d <ab_np::simd_quad_intel(unsigned short const*, int, unsigned short)+0x10d>
  409e9c:	mov    $0x10,%edx
  409ea1:	jmp    409833 <ab_np::simd_quad_intel(unsigned short const*, int, unsigned short)+0x133>
  409ea6:	inc    %eax
  409ea8:	jmp    409c37 <ab_np::simd_quad_intel(unsigned short const*, int, unsigned short)+0x537>
  409ead:	add    $0x2,%eax
  409eb0:	jmp    409c37 <ab_np::simd_quad_intel(unsigned short const*, int, unsigned short)+0x537>
  409eb5:	add    $0x3,%eax
  409eb8:	jmp    409c37 <ab_np::simd_quad_intel(unsigned short const*, int, unsigned short)+0x537>
  409ebd:	add    $0x4,%eax
  409ec0:	jmp    409c37 <ab_np::simd_quad_intel(unsigned short const*, int, unsigned short)+0x537>
  409ec5:	add    $0x5,%eax
  409ec8:	jmp    409c37 <ab_np::simd_quad_intel(unsigned short const*, int, unsigned short)+0x537>
  409ecd:	mov    $0x11,%edx
  409ed2:	jmp    40980d <ab_np::simd_quad_intel(unsigned short const*, int, unsigned short)+0x10d>
  409ed7:	mov    $0x12,%edx
  409edc:	jmp    40980d <ab_np::simd_quad_intel(unsigned short const*, int, unsigned short)+0x10d>
  409ee1:	add    $0x6,%eax
  409ee4:	jmp    409c37 <ab_np::simd_quad_intel(unsigned short const*, int, unsigned short)+0x537>
  409ee9:	add    $0x7,%eax
  409eec:	jmp    409c37 <ab_np::simd_quad_intel(unsigned short const*, int, unsigned short)+0x537>
  409ef1:	mov    $0x13,%edx
  409ef6:	jmp    40980d <ab_np::simd_quad_intel(unsigned short const*, int, unsigned short)+0x10d>
  409efb:	mov    $0x14,%edx
  409f00:	jmp    40980d <ab_np::simd_quad_intel(unsigned short const*, int, unsigned short)+0x10d>
  409f05:	add    $0x8,%eax
  409f08:	jmp    409c37 <ab_np::simd_quad_intel(unsigned short const*, int, unsigned short)+0x537>
  409f0d:	mov    $0x15,%edx
  409f12:	jmp    40980d <ab_np::simd_quad_intel(unsigned short const*, int, unsigned short)+0x10d>
  409f17:	add    $0x9,%eax
  409f1a:	jmp    409c37 <ab_np::simd_quad_intel(unsigned short const*, int, unsigned short)+0x537>
  409f1f:	mov    $0x16,%edx
  409f24:	jmp    40980d <ab_np::simd_quad_intel(unsigned short const*, int, unsigned short)+0x10d>
  409f29:	add    $0xa,%eax
  409f2c:	jmp    409c37 <ab_np::simd_quad_intel(unsigned short const*, int, unsigned short)+0x537>
  409f31:	add    $0xc,%eax
  409f34:	jmp    409c37 <ab_np::simd_quad_intel(unsigned short const*, int, unsigned short)+0x537>
  409f39:	add    $0xb,%eax
  409f3c:	jmp    409c37 <ab_np::simd_quad_intel(unsigned short const*, int, unsigned short)+0x537>
  409f41:	add    $0xd,%eax
  409f44:	jmp    409c37 <ab_np::simd_quad_intel(unsigned short const*, int, unsigned short)+0x537>
  409f49:	add    $0xe,%eax
  409f4c:	jmp    409c37 <ab_np::simd_quad_intel(unsigned short const*, int, unsigned short)+0x537>
  409f51:	nopl   0x0(%rax)
  409f55:	data16 cs nopw 0x0(%rax,%rax,1)
