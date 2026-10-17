000000000040bb80 <ab_tail::simd_quad_intel(unsigned short const*, int, unsigned short)>:
  40bb80:	mov    %esi,%r8d
  40bb83:	mov    %edx,%esi
  40bb85:	vmovd  %esi,%xmm0
  40bb89:	vpbroadcastw %xmm0,%ymm0
  40bb8e:	cmp    $0x1f,%r8d
  40bb92:	jg     40be30 <ab_tail::simd_quad_intel(unsigned short const*, int, unsigned short)+0x2b0>
  40bb98:	cmp    $0xf,%r8d
  40bb9c:	jle    40bf50 <ab_tail::simd_quad_intel(unsigned short const*, int, unsigned short)+0x3d0>
  40bba2:	vpcmpeqw (%rdi),%ymm0,%ymm1
  40bba6:	vpmovmskb %ymm1,%eax
  40bbaa:	test   %eax,%eax
  40bbac:	jne    40c098 <ab_tail::simd_quad_intel(unsigned short const*, int, unsigned short)+0x518>
  40bbb2:	cmp    $0x10,%r8d
  40bbb6:	je     40be20 <ab_tail::simd_quad_intel(unsigned short const*, int, unsigned short)+0x2a0>
  40bbbc:	lea    0x20(%rdi),%r10
  40bbc0:	mov    $0xb,%r9d
  40bbc6:	mov    %r10,%rdx
  40bbc9:	shr    $1,%rdx
  40bbcc:	neg    %rdx
  40bbcf:	mov    %edx,%ecx
  40bbd1:	and    $0x7,%ecx
  40bbd4:	lea    0x8(%rcx),%eax
  40bbd7:	cmp    %r9d,%eax
  40bbda:	cmovb  %r9d,%eax
  40bbde:	lea    -0x11(%r8),%r9d
  40bbe2:	cmp    %eax,%r9d
  40bbe5:	jb     40c0d5 <ab_tail::simd_quad_intel(unsigned short const*, int, unsigned short)+0x555>
  40bbeb:	test   %ecx,%ecx
  40bbed:	je     40c0cb <ab_tail::simd_quad_intel(unsigned short const*, int, unsigned short)+0x54b>
  40bbf3:	movzwl 0x20(%rdi),%eax
  40bbf7:	cmp    %si,%ax
  40bbfa:	jae    40bfe1 <ab_tail::simd_quad_intel(unsigned short const*, int, unsigned short)+0x461>
  40bc00:	test   $0x6,%dl
  40bc03:	je     40c0df <ab_tail::simd_quad_intel(unsigned short const*, int, unsigned short)+0x55f>
  40bc09:	movzwl 0x22(%rdi),%eax
  40bc0d:	cmp    %si,%ax
  40bc10:	jae    40bfe1 <ab_tail::simd_quad_intel(unsigned short const*, int, unsigned short)+0x461>
  40bc16:	cmp    $0x2,%ecx
  40bc19:	jbe    40c0e9 <ab_tail::simd_quad_intel(unsigned short const*, int, unsigned short)+0x569>
  40bc1f:	movzwl 0x24(%rdi),%eax
  40bc23:	cmp    %si,%ax
  40bc26:	jae    40bfe1 <ab_tail::simd_quad_intel(unsigned short const*, int, unsigned short)+0x461>
  40bc2c:	and    $0x4,%edx
  40bc2f:	je     40c0f3 <ab_tail::simd_quad_intel(unsigned short const*, int, unsigned short)+0x573>
  40bc35:	movzwl 0x26(%rdi),%eax
  40bc39:	cmp    %si,%ax
  40bc3c:	jae    40bfe1 <ab_tail::simd_quad_intel(unsigned short const*, int, unsigned short)+0x461>
  40bc42:	cmp    $0x4,%ecx
  40bc45:	je     40c0fd <ab_tail::simd_quad_intel(unsigned short const*, int, unsigned short)+0x57d>
  40bc4b:	movzwl 0x28(%rdi),%eax
  40bc4f:	cmp    %si,%ax
  40bc52:	jae    40bfe1 <ab_tail::simd_quad_intel(unsigned short const*, int, unsigned short)+0x461>
  40bc58:	cmp    $0x5,%ecx
  40bc5b:	je     40c107 <ab_tail::simd_quad_intel(unsigned short const*, int, unsigned short)+0x587>
  40bc61:	movzwl 0x2a(%rdi),%eax
  40bc65:	cmp    %si,%ax
  40bc68:	jae    40bfe1 <ab_tail::simd_quad_intel(unsigned short const*, int, unsigned short)+0x461>
  40bc6e:	cmp    $0x7,%ecx
  40bc71:	jne    40c111 <ab_tail::simd_quad_intel(unsigned short const*, int, unsigned short)+0x591>
  40bc77:	movzwl 0x2c(%rdi),%eax
  40bc7b:	cmp    %si,%ax
  40bc7e:	jae    40bfe1 <ab_tail::simd_quad_intel(unsigned short const*, int, unsigned short)+0x461>
  40bc84:	mov    $0x17,%edx
  40bc89:	mov    %ecx,%eax
  40bc8b:	vpminuw (%r10,%rax,2),%xmm0,%xmm1
  40bc91:	vpcmpeqw %xmm1,%xmm0,%xmm0
  40bc95:	vptest %xmm0,%xmm0
  40bc9a:	jne    40c0a1 <ab_tail::simd_quad_intel(unsigned short const*, int, unsigned short)+0x521>
  40bca0:	lea    -0x18(%r8),%eax
  40bca4:	cmp    %ecx,%eax
  40bca6:	je     40be20 <ab_tail::simd_quad_intel(unsigned short const*, int, unsigned short)+0x2a0>
  40bcac:	add    $0x8,%edx
  40bcaf:	mov    %edx,%r9d
  40bcb2:	movzwl (%rdi,%r9,2),%eax
  40bcb7:	cmp    %si,%ax
  40bcba:	jae    40bfe1 <ab_tail::simd_quad_intel(unsigned short const*, int, unsigned short)+0x461>
  40bcc0:	lea    0x1(%rdx),%eax
  40bcc3:	cmp    %eax,%r8d
  40bcc6:	jle    40be20 <ab_tail::simd_quad_intel(unsigned short const*, int, unsigned short)+0x2a0>
  40bccc:	movzwl 0x2(%rdi,%r9,2),%eax
  40bcd2:	lea    0x2(%r9,%r9,1),%rcx
  40bcd7:	cmp    %si,%ax
  40bcda:	jae    40bfe1 <ab_tail::simd_quad_intel(unsigned short const*, int, unsigned short)+0x461>
  40bce0:	lea    0x2(%rdx),%eax
  40bce3:	cmp    %eax,%r8d
  40bce6:	jle    40be20 <ab_tail::simd_quad_intel(unsigned short const*, int, unsigned short)+0x2a0>
  40bcec:	movzwl 0x2(%rdi,%rcx,1),%eax
  40bcf1:	cmp    %si,%ax
  40bcf4:	jae    40bfe1 <ab_tail::simd_quad_intel(unsigned short const*, int, unsigned short)+0x461>
  40bcfa:	lea    0x3(%rdx),%eax
  40bcfd:	cmp    %r8d,%eax
  40bd00:	jge    40be20 <ab_tail::simd_quad_intel(unsigned short const*, int, unsigned short)+0x2a0>
  40bd06:	movzwl 0x4(%rdi,%rcx,1),%eax
  40bd0b:	cmp    %si,%ax
  40bd0e:	jae    40bfe1 <ab_tail::simd_quad_intel(unsigned short const*, int, unsigned short)+0x461>
  40bd14:	lea    0x4(%rdx),%eax
  40bd17:	cmp    %r8d,%eax
  40bd1a:	jge    40be20 <ab_tail::simd_quad_intel(unsigned short const*, int, unsigned short)+0x2a0>
  40bd20:	movzwl 0x6(%rdi,%rcx,1),%eax
  40bd25:	cmp    %si,%ax
  40bd28:	jae    40bfe1 <ab_tail::simd_quad_intel(unsigned short const*, int, unsigned short)+0x461>
  40bd2e:	lea    0x5(%rdx),%eax
  40bd31:	cmp    %eax,%r8d
  40bd34:	jle    40be20 <ab_tail::simd_quad_intel(unsigned short const*, int, unsigned short)+0x2a0>
  40bd3a:	movzwl 0x8(%rdi,%rcx,1),%eax
  40bd3f:	cmp    %si,%ax
  40bd42:	jae    40bfe1 <ab_tail::simd_quad_intel(unsigned short const*, int, unsigned short)+0x461>
  40bd48:	lea    0x6(%rdx),%eax
  40bd4b:	cmp    %eax,%r8d
  40bd4e:	jle    40be20 <ab_tail::simd_quad_intel(unsigned short const*, int, unsigned short)+0x2a0>
  40bd54:	movzwl 0xa(%rdi,%rcx,1),%eax
  40bd59:	cmp    %si,%ax
  40bd5c:	jae    40bfe1 <ab_tail::simd_quad_intel(unsigned short const*, int, unsigned short)+0x461>
  40bd62:	lea    0x7(%rdx),%eax
  40bd65:	cmp    %eax,%r8d
  40bd68:	jle    40be20 <ab_tail::simd_quad_intel(unsigned short const*, int, unsigned short)+0x2a0>
  40bd6e:	movzwl 0xc(%rdi,%rcx,1),%eax
  40bd73:	cmp    %si,%ax
  40bd76:	jae    40bfe1 <ab_tail::simd_quad_intel(unsigned short const*, int, unsigned short)+0x461>
  40bd7c:	lea    0x8(%rdx),%eax
  40bd7f:	cmp    %eax,%r8d
  40bd82:	jle    40be20 <ab_tail::simd_quad_intel(unsigned short const*, int, unsigned short)+0x2a0>
  40bd88:	movzwl 0xe(%rdi,%rcx,1),%eax
  40bd8d:	cmp    %si,%ax
  40bd90:	jae    40bfe1 <ab_tail::simd_quad_intel(unsigned short const*, int, unsigned short)+0x461>
  40bd96:	lea    0x9(%rdx),%eax
  40bd99:	cmp    %eax,%r8d
  40bd9c:	jle    40be20 <ab_tail::simd_quad_intel(unsigned short const*, int, unsigned short)+0x2a0>
  40bda2:	movzwl 0x10(%rdi,%rcx,1),%eax
  40bda7:	cmp    %si,%ax
  40bdaa:	jae    40bfe1 <ab_tail::simd_quad_intel(unsigned short const*, int, unsigned short)+0x461>
  40bdb0:	lea    0xa(%rdx),%eax
  40bdb3:	cmp    %eax,%r8d
  40bdb6:	jle    40be20 <ab_tail::simd_quad_intel(unsigned short const*, int, unsigned short)+0x2a0>
  40bdb8:	movzwl 0x12(%rdi,%rcx,1),%eax
  40bdbd:	cmp    %si,%ax
  40bdc0:	jae    40bfe1 <ab_tail::simd_quad_intel(unsigned short const*, int, unsigned short)+0x461>
  40bdc6:	lea    0xb(%rdx),%eax
  40bdc9:	cmp    %eax,%r8d
  40bdcc:	jle    40be20 <ab_tail::simd_quad_intel(unsigned short const*, int, unsigned short)+0x2a0>
  40bdce:	movzwl 0x14(%rdi,%rcx,1),%eax
  40bdd3:	cmp    %si,%ax
  40bdd6:	jae    40bfe1 <ab_tail::simd_quad_intel(unsigned short const*, int, unsigned short)+0x461>
  40bddc:	lea    0xc(%rdx),%eax
  40bddf:	cmp    %eax,%r8d
  40bde2:	jle    40be20 <ab_tail::simd_quad_intel(unsigned short const*, int, unsigned short)+0x2a0>
  40bde4:	movzwl 0x16(%rdi,%rcx,1),%eax
  40bde9:	cmp    %si,%ax
  40bdec:	jae    40bfe1 <ab_tail::simd_quad_intel(unsigned short const*, int, unsigned short)+0x461>
  40bdf2:	lea    0xd(%rdx),%eax
  40bdf5:	cmp    %eax,%r8d
  40bdf8:	jle    40be20 <ab_tail::simd_quad_intel(unsigned short const*, int, unsigned short)+0x2a0>
  40bdfa:	movzwl 0x18(%rdi,%rcx,1),%eax
  40bdff:	cmp    %si,%ax
  40be02:	jae    40bfe1 <ab_tail::simd_quad_intel(unsigned short const*, int, unsigned short)+0x461>
  40be08:	add    $0xe,%edx
  40be0b:	cmp    %edx,%r8d
  40be0e:	jle    40be20 <ab_tail::simd_quad_intel(unsigned short const*, int, unsigned short)+0x2a0>
  40be10:	movzwl 0x3c(%rdi),%eax
  40be14:	cmp    %si,%ax
  40be17:	jae    40bfe1 <ab_tail::simd_quad_intel(unsigned short const*, int, unsigned short)+0x461>
  40be1d:	nopl   (%rax)
  40be20:	xor    %eax,%eax
  40be22:	vzeroupper
  40be25:	ret
  40be26:	cs nopw 0x0(%rax,%rax,1)
  40be30:	push   %rbp
  40be31:	mov    %r8d,%r9d
  40be34:	xor    %ecx,%ecx
  40be36:	sar    $0x5,%r9d
  40be3a:	mov    %r9d,%eax
  40be3d:	mov    %rsp,%rbp
  40be40:	push   %rbx
  40be41:	cmp    $0x7f,%r8d
  40be45:	jle    40bee0 <ab_tail::simd_quad_intel(unsigned short const*, int, unsigned short)+0x360>
  40be4b:	nopl   0x0(%rax,%rax,1)
  40be50:	mov    %eax,%r10d
  40be53:	sar    $0x2,%r10d
  40be57:	lea    (%r10,%rcx,1),%edx
  40be5b:	lea    (%rdx,%r10,1),%r11d
  40be5f:	inc    %edx
  40be61:	shl    $0x5,%edx
  40be64:	lea    0x1(%r11),%ebx
  40be68:	lea    0x1(%r10,%r11,1),%r11d
  40be6d:	movslq %edx,%rdx
  40be70:	cmp    %si,-0x2(%rdi,%rdx,2)
  40be75:	setb   %dl
  40be78:	shl    $0x5,%ebx
  40be7b:	movslq %ebx,%rbx
  40be7e:	movzbl %dl,%edx
  40be81:	cmp    %si,-0x2(%rdi,%rbx,2)
  40be86:	adc    $0x0,%edx
  40be89:	shl    $0x5,%r11d
  40be8d:	movslq %r11d,%r11
  40be90:	cmp    %si,-0x2(%rdi,%r11,2)
  40be96:	adc    $0x0,%edx
  40be99:	imul   %r10d,%edx
  40be9d:	add    %edx,%ecx
  40be9f:	lea    (%r10,%r10,2),%edx
  40bea3:	sub    %edx,%eax
  40bea5:	mov    %eax,%edx
  40bea7:	sar    $1,%edx
  40bea9:	add    %ecx,%edx
  40beab:	shl    $0x5,%edx
  40beae:	movslq %edx,%rdx
  40beb1:	prefetcht0 (%rdi,%rdx,2)
  40beb5:	cmp    $0x3,%eax
  40beb8:	jg     40be50 <ab_tail::simd_quad_intel(unsigned short const*, int, unsigned short)+0x2d0>
  40beba:	jmp    40bee0 <ab_tail::simd_quad_intel(unsigned short const*, int, unsigned short)+0x360>
  40bebc:	nopl   0x0(%rax)
  40bec0:	mov    %eax,%r10d
  40bec3:	sar    $1,%r10d
  40bec6:	lea    (%rcx,%r10,1),%r11d
  40beca:	lea    0x1(%r11),%edx
  40bece:	shl    $0x5,%edx
  40bed1:	movslq %edx,%rdx
  40bed4:	cmp    %si,-0x2(%rdi,%rdx,2)
  40bed9:	cmovb  %r11d,%ecx
  40bedd:	sub    %r10d,%eax
  40bee0:	cmp    $0x1,%eax
  40bee3:	jg     40bec0 <ab_tail::simd_quad_intel(unsigned short const*, int, unsigned short)+0x340>
  40bee5:	lea    0x1(%rcx),%eax
  40bee8:	mov    %eax,%edx
  40beea:	shl    $0x5,%edx
  40beed:	movslq %edx,%rdx
  40bef0:	cmp    %si,-0x2(%rdi,%rdx,2)
  40bef5:	cmovae %ecx,%eax
  40bef8:	cmp    %r9d,%eax
  40befb:	jl     40bf28 <ab_tail::simd_quad_intel(unsigned short const*, int, unsigned short)+0x3a8>
  40befd:	mov    %r8d,%r8d
  40bf00:	vpcmpeqw -0x40(%rdi,%r8,2),%ymm0,%ymm1
  40bf07:	vpcmpeqw -0x20(%rdi,%r8,2),%ymm0,%ymm0
  40bf0e:	vpor   %ymm0,%ymm1,%ymm0
  40bf12:	vpmovmskb %ymm0,%eax
  40bf16:	test   %eax,%eax
  40bf18:	vzeroupper
  40bf1b:	setne  %al
  40bf1e:	mov    -0x8(%rbp),%rbx
  40bf22:	leave
  40bf23:	ret
  40bf24:	nopl   0x0(%rax)
  40bf28:	shl    $0x5,%eax
  40bf2b:	cltq
  40bf2d:	lea    (%rdi,%rax,2),%rax
  40bf31:	vpcmpeqw (%rax),%ymm0,%ymm1
  40bf35:	vpcmpeqw 0x20(%rax),%ymm0,%ymm0
  40bf3a:	vpor   %ymm0,%ymm1,%ymm0
  40bf3e:	vpmovmskb %ymm0,%eax
  40bf42:	test   %eax,%eax
  40bf44:	vzeroupper
  40bf47:	setne  %al
  40bf4a:	mov    -0x8(%rbp),%rbx
  40bf4e:	leave
  40bf4f:	ret
  40bf50:	cmp    $0x7,%r8d
  40bf54:	jg     40bff0 <ab_tail::simd_quad_intel(unsigned short const*, int, unsigned short)+0x470>
  40bf5a:	test   %r8d,%r8d
  40bf5d:	jle    40be20 <ab_tail::simd_quad_intel(unsigned short const*, int, unsigned short)+0x2a0>
  40bf63:	movzwl (%rdi),%eax
  40bf66:	cmp    %dx,%ax
  40bf69:	jae    40bfe1 <ab_tail::simd_quad_intel(unsigned short const*, int, unsigned short)+0x461>
  40bf6b:	cmp    $0x1,%r8d
  40bf6f:	je     40be20 <ab_tail::simd_quad_intel(unsigned short const*, int, unsigned short)+0x2a0>
  40bf75:	movzwl 0x2(%rdi),%eax
  40bf79:	cmp    %dx,%ax
  40bf7c:	jae    40bfe1 <ab_tail::simd_quad_intel(unsigned short const*, int, unsigned short)+0x461>
  40bf7e:	cmp    $0x2,%r8d
  40bf82:	je     40be20 <ab_tail::simd_quad_intel(unsigned short const*, int, unsigned short)+0x2a0>
  40bf88:	movzwl 0x4(%rdi),%eax
  40bf8c:	cmp    %dx,%ax
  40bf8f:	jae    40bfe1 <ab_tail::simd_quad_intel(unsigned short const*, int, unsigned short)+0x461>
  40bf91:	cmp    $0x3,%r8d
  40bf95:	je     40be20 <ab_tail::simd_quad_intel(unsigned short const*, int, unsigned short)+0x2a0>
  40bf9b:	movzwl 0x6(%rdi),%eax
  40bf9f:	cmp    %dx,%ax
  40bfa2:	jae    40bfe1 <ab_tail::simd_quad_intel(unsigned short const*, int, unsigned short)+0x461>
  40bfa4:	cmp    $0x4,%r8d
  40bfa8:	je     40be20 <ab_tail::simd_quad_intel(unsigned short const*, int, unsigned short)+0x2a0>
  40bfae:	movzwl 0x8(%rdi),%eax
  40bfb2:	cmp    %dx,%ax
  40bfb5:	jae    40bfe1 <ab_tail::simd_quad_intel(unsigned short const*, int, unsigned short)+0x461>
  40bfb7:	cmp    $0x5,%r8d
  40bfbb:	je     40be20 <ab_tail::simd_quad_intel(unsigned short const*, int, unsigned short)+0x2a0>
  40bfc1:	movzwl 0xa(%rdi),%eax
  40bfc5:	cmp    %dx,%ax
  40bfc8:	jae    40bfe1 <ab_tail::simd_quad_intel(unsigned short const*, int, unsigned short)+0x461>
  40bfca:	cmp    $0x7,%r8d
  40bfce:	jne    40be20 <ab_tail::simd_quad_intel(unsigned short const*, int, unsigned short)+0x2a0>
  40bfd4:	movzwl 0xc(%rdi),%eax
  40bfd8:	cmp    %dx,%ax
  40bfdb:	jb     40be20 <ab_tail::simd_quad_intel(unsigned short const*, int, unsigned short)+0x2a0>
  40bfe1:	cmp    %ax,%si
  40bfe4:	sete   %al
  40bfe7:	vzeroupper
  40bfea:	ret
  40bfeb:	nopl   0x0(%rax,%rax,1)
  40bff0:	vpcmpeqw (%rdi),%xmm0,%xmm0
  40bff4:	vpmovmskb %xmm0,%eax
  40bff8:	test   %eax,%eax
  40bffa:	jne    40c098 <ab_tail::simd_quad_intel(unsigned short const*, int, unsigned short)+0x518>
  40c000:	cmp    $0x8,%r8d
  40c004:	je     40be20 <ab_tail::simd_quad_intel(unsigned short const*, int, unsigned short)+0x2a0>
  40c00a:	movzwl 0x10(%rdi),%eax
  40c00e:	cmp    %dx,%ax
  40c011:	jae    40bfe1 <ab_tail::simd_quad_intel(unsigned short const*, int, unsigned short)+0x461>
  40c013:	cmp    $0x9,%r8d
  40c017:	je     40be20 <ab_tail::simd_quad_intel(unsigned short const*, int, unsigned short)+0x2a0>
  40c01d:	movzwl 0x12(%rdi),%eax
  40c021:	cmp    %dx,%ax
  40c024:	jae    40bfe1 <ab_tail::simd_quad_intel(unsigned short const*, int, unsigned short)+0x461>
  40c026:	cmp    $0xa,%r8d
  40c02a:	je     40be20 <ab_tail::simd_quad_intel(unsigned short const*, int, unsigned short)+0x2a0>
  40c030:	movzwl 0x14(%rdi),%eax
  40c034:	cmp    %dx,%ax
  40c037:	jae    40bfe1 <ab_tail::simd_quad_intel(unsigned short const*, int, unsigned short)+0x461>
  40c039:	cmp    $0xb,%r8d
  40c03d:	je     40be20 <ab_tail::simd_quad_intel(unsigned short const*, int, unsigned short)+0x2a0>
  40c043:	movzwl 0x16(%rdi),%eax
  40c047:	cmp    %dx,%ax
  40c04a:	jae    40bfe1 <ab_tail::simd_quad_intel(unsigned short const*, int, unsigned short)+0x461>
  40c04c:	cmp    $0xc,%r8d
  40c050:	je     40be20 <ab_tail::simd_quad_intel(unsigned short const*, int, unsigned short)+0x2a0>
  40c056:	movzwl 0x18(%rdi),%eax
  40c05a:	cmp    %dx,%ax
  40c05d:	jae    40bfe1 <ab_tail::simd_quad_intel(unsigned short const*, int, unsigned short)+0x461>
  40c05f:	cmp    $0xd,%r8d
  40c063:	je     40be20 <ab_tail::simd_quad_intel(unsigned short const*, int, unsigned short)+0x2a0>
  40c069:	movzwl 0x1a(%rdi),%eax
  40c06d:	cmp    %dx,%ax
  40c070:	jae    40bfe1 <ab_tail::simd_quad_intel(unsigned short const*, int, unsigned short)+0x461>
  40c076:	cmp    $0xf,%r8d
  40c07a:	jne    40be20 <ab_tail::simd_quad_intel(unsigned short const*, int, unsigned short)+0x2a0>
  40c080:	movzwl 0x1c(%rdi),%eax
  40c084:	cmp    %dx,%ax
  40c087:	jae    40bfe1 <ab_tail::simd_quad_intel(unsigned short const*, int, unsigned short)+0x461>
  40c08d:	xor    %eax,%eax
  40c08f:	jmp    40be22 <ab_tail::simd_quad_intel(unsigned short const*, int, unsigned short)+0x2a2>
  40c094:	nopl   0x0(%rax)
  40c098:	mov    $0x1,%eax
  40c09d:	vzeroupper
  40c0a0:	ret
  40c0a1:	mov    %edx,%r9d
  40c0a4:	movzwl (%rdi,%r9,2),%eax
  40c0a9:	cmp    %si,%ax
  40c0ac:	jae    40bfe1 <ab_tail::simd_quad_intel(unsigned short const*, int, unsigned short)+0x461>
  40c0b2:	movzwl 0x2(%rdi,%r9,2),%eax
  40c0b8:	lea    0x2(%r9,%r9,1),%rcx
  40c0bd:	cmp    %si,%ax
  40c0c0:	jb     40bcec <ab_tail::simd_quad_intel(unsigned short const*, int, unsigned short)+0x16c>
  40c0c6:	jmp    40bfe1 <ab_tail::simd_quad_intel(unsigned short const*, int, unsigned short)+0x461>
  40c0cb:	mov    $0x10,%edx
  40c0d0:	jmp    40bc89 <ab_tail::simd_quad_intel(unsigned short const*, int, unsigned short)+0x109>
  40c0d5:	mov    $0x10,%edx
  40c0da:	jmp    40bcaf <ab_tail::simd_quad_intel(unsigned short const*, int, unsigned short)+0x12f>
  40c0df:	mov    $0x11,%edx
  40c0e4:	jmp    40bc89 <ab_tail::simd_quad_intel(unsigned short const*, int, unsigned short)+0x109>
  40c0e9:	mov    $0x12,%edx
  40c0ee:	jmp    40bc89 <ab_tail::simd_quad_intel(unsigned short const*, int, unsigned short)+0x109>
  40c0f3:	mov    $0x13,%edx
  40c0f8:	jmp    40bc89 <ab_tail::simd_quad_intel(unsigned short const*, int, unsigned short)+0x109>
  40c0fd:	mov    $0x14,%edx
  40c102:	jmp    40bc89 <ab_tail::simd_quad_intel(unsigned short const*, int, unsigned short)+0x109>
  40c107:	mov    $0x15,%edx
  40c10c:	jmp    40bc89 <ab_tail::simd_quad_intel(unsigned short const*, int, unsigned short)+0x109>
  40c111:	mov    $0x16,%edx
  40c116:	jmp    40bc89 <ab_tail::simd_quad_intel(unsigned short const*, int, unsigned short)+0x109>
  40c11b:	nopl   0x0(%rax,%rax,1)
