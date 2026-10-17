0000000000407ad0 <ab_base::simd_quad_intel_spine(unsigned short const*, unsigned short const*, int, unsigned short)>:
  407ad0:	vmovd  %ecx,%xmm0
  407ad4:	mov    %rdi,%r9
  407ad7:	mov    %edx,%r11d
  407ada:	vpbroadcastw %xmm0,%ymm0
  407adf:	cmp    $0x1f,%edx
  407ae2:	jg     407d90 <ab_base::simd_quad_intel_spine(unsigned short const*, unsigned short const*, int, unsigned short)+0x2c0>
  407ae8:	cmp    $0xf,%edx
  407aeb:	jle    408050 <ab_base::simd_quad_intel_spine(unsigned short const*, unsigned short const*, int, unsigned short)+0x580>
  407af1:	vpcmpeqw (%rdi),%ymm0,%ymm1
  407af5:	vpmovmskb %ymm1,%eax
  407af9:	test   %eax,%eax
  407afb:	jne    408518 <ab_base::simd_quad_intel_spine(unsigned short const*, unsigned short const*, int, unsigned short)+0xa48>
  407b01:	cmp    $0x10,%edx
  407b04:	je     407d80 <ab_base::simd_quad_intel_spine(unsigned short const*, unsigned short const*, int, unsigned short)+0x2b0>
  407b0a:	lea    0x20(%rdi),%r8
  407b0e:	mov    $0xb,%edi
  407b13:	mov    %r8,%rdx
  407b16:	shr    $1,%rdx
  407b19:	neg    %rdx
  407b1c:	mov    %edx,%esi
  407b1e:	and    $0x7,%esi
  407b21:	lea    0x8(%rsi),%eax
  407b24:	cmp    %edi,%eax
  407b26:	cmovb  %edi,%eax
  407b29:	lea    -0x11(%r11),%edi
  407b2d:	cmp    %eax,%edi
  407b2f:	jb     4085ae <ab_base::simd_quad_intel_spine(unsigned short const*, unsigned short const*, int, unsigned short)+0xade>
  407b35:	test   %esi,%esi
  407b37:	je     4085a4 <ab_base::simd_quad_intel_spine(unsigned short const*, unsigned short const*, int, unsigned short)+0xad4>
  407b3d:	movzwl 0x20(%r9),%eax
  407b42:	cmp    %cx,%ax
  407b45:	jae    4080d9 <ab_base::simd_quad_intel_spine(unsigned short const*, unsigned short const*, int, unsigned short)+0x609>
  407b4b:	test   $0x6,%dl
  407b4e:	je     4085cb <ab_base::simd_quad_intel_spine(unsigned short const*, unsigned short const*, int, unsigned short)+0xafb>
  407b54:	movzwl 0x22(%r9),%eax
  407b59:	cmp    %cx,%ax
  407b5c:	jae    4080d9 <ab_base::simd_quad_intel_spine(unsigned short const*, unsigned short const*, int, unsigned short)+0x609>
  407b62:	cmp    $0x2,%esi
  407b65:	jbe    4085dd <ab_base::simd_quad_intel_spine(unsigned short const*, unsigned short const*, int, unsigned short)+0xb0d>
  407b6b:	movzwl 0x24(%r9),%eax
  407b70:	cmp    %cx,%ax
  407b73:	jae    4080d9 <ab_base::simd_quad_intel_spine(unsigned short const*, unsigned short const*, int, unsigned short)+0x609>
  407b79:	and    $0x4,%edx
  407b7c:	je     4085ef <ab_base::simd_quad_intel_spine(unsigned short const*, unsigned short const*, int, unsigned short)+0xb1f>
  407b82:	movzwl 0x26(%r9),%eax
  407b87:	cmp    %cx,%ax
  407b8a:	jae    4080d9 <ab_base::simd_quad_intel_spine(unsigned short const*, unsigned short const*, int, unsigned short)+0x609>
  407b90:	cmp    $0x4,%esi
  407b93:	je     408601 <ab_base::simd_quad_intel_spine(unsigned short const*, unsigned short const*, int, unsigned short)+0xb31>
  407b99:	movzwl 0x28(%r9),%eax
  407b9e:	cmp    %cx,%ax
  407ba1:	jae    4080d9 <ab_base::simd_quad_intel_spine(unsigned short const*, unsigned short const*, int, unsigned short)+0x609>
  407ba7:	cmp    $0x5,%esi
  407baa:	je     40861b <ab_base::simd_quad_intel_spine(unsigned short const*, unsigned short const*, int, unsigned short)+0xb4b>
  407bb0:	movzwl 0x2a(%r9),%eax
  407bb5:	cmp    %cx,%ax
  407bb8:	jae    4080d9 <ab_base::simd_quad_intel_spine(unsigned short const*, unsigned short const*, int, unsigned short)+0x609>
  407bbe:	cmp    $0x7,%esi
  407bc1:	jne    408625 <ab_base::simd_quad_intel_spine(unsigned short const*, unsigned short const*, int, unsigned short)+0xb55>
  407bc7:	movzwl 0x2c(%r9),%eax
  407bcc:	cmp    %cx,%ax
  407bcf:	jae    4080d9 <ab_base::simd_quad_intel_spine(unsigned short const*, unsigned short const*, int, unsigned short)+0x609>
  407bd5:	mov    $0x17,%edx
  407bda:	mov    %esi,%eax
  407bdc:	vpminuw (%r8,%rax,2),%xmm0,%xmm1
  407be2:	vpcmpeqw %xmm1,%xmm0,%xmm0
  407be6:	vptest %xmm0,%xmm0
  407beb:	jne    408537 <ab_base::simd_quad_intel_spine(unsigned short const*, unsigned short const*, int, unsigned short)+0xa67>
  407bf1:	lea    -0x18(%r11),%eax
  407bf5:	cmp    %esi,%eax
  407bf7:	je     407d80 <ab_base::simd_quad_intel_spine(unsigned short const*, unsigned short const*, int, unsigned short)+0x2b0>
  407bfd:	add    $0x8,%edx
  407c00:	mov    %edx,%edi
  407c02:	movzwl (%r9,%rdi,2),%eax
  407c07:	cmp    %cx,%ax
  407c0a:	jae    4080d9 <ab_base::simd_quad_intel_spine(unsigned short const*, unsigned short const*, int, unsigned short)+0x609>
  407c10:	lea    0x1(%rdx),%eax
  407c13:	cmp    %eax,%r11d
  407c16:	jle    407d80 <ab_base::simd_quad_intel_spine(unsigned short const*, unsigned short const*, int, unsigned short)+0x2b0>
  407c1c:	movzwl 0x2(%r9,%rdi,2),%eax
  407c22:	lea    0x2(%rdi,%rdi,1),%rsi
  407c27:	cmp    %cx,%ax
  407c2a:	jae    4080d9 <ab_base::simd_quad_intel_spine(unsigned short const*, unsigned short const*, int, unsigned short)+0x609>
  407c30:	lea    0x2(%rdx),%eax
  407c33:	cmp    %eax,%r11d
  407c36:	jle    407d80 <ab_base::simd_quad_intel_spine(unsigned short const*, unsigned short const*, int, unsigned short)+0x2b0>
  407c3c:	movzwl 0x2(%r9,%rsi,1),%eax
  407c42:	cmp    %cx,%ax
  407c45:	jae    4080d9 <ab_base::simd_quad_intel_spine(unsigned short const*, unsigned short const*, int, unsigned short)+0x609>
  407c4b:	lea    0x3(%rdx),%eax
  407c4e:	cmp    %eax,%r11d
  407c51:	jle    407d80 <ab_base::simd_quad_intel_spine(unsigned short const*, unsigned short const*, int, unsigned short)+0x2b0>
  407c57:	movzwl 0x4(%r9,%rsi,1),%eax
  407c5d:	cmp    %cx,%ax
  407c60:	jae    4080d9 <ab_base::simd_quad_intel_spine(unsigned short const*, unsigned short const*, int, unsigned short)+0x609>
  407c66:	lea    0x4(%rdx),%eax
  407c69:	cmp    %eax,%r11d
  407c6c:	jle    407d80 <ab_base::simd_quad_intel_spine(unsigned short const*, unsigned short const*, int, unsigned short)+0x2b0>
  407c72:	movzwl 0x6(%r9,%rsi,1),%eax
  407c78:	cmp    %cx,%ax
  407c7b:	jae    4080d9 <ab_base::simd_quad_intel_spine(unsigned short const*, unsigned short const*, int, unsigned short)+0x609>
  407c81:	lea    0x5(%rdx),%eax
  407c84:	cmp    %eax,%r11d
  407c87:	jle    407d80 <ab_base::simd_quad_intel_spine(unsigned short const*, unsigned short const*, int, unsigned short)+0x2b0>
  407c8d:	movzwl 0x8(%r9,%rsi,1),%eax
  407c93:	cmp    %cx,%ax
  407c96:	jae    4080d9 <ab_base::simd_quad_intel_spine(unsigned short const*, unsigned short const*, int, unsigned short)+0x609>
  407c9c:	lea    0x6(%rdx),%eax
  407c9f:	cmp    %r11d,%eax
  407ca2:	jge    407d80 <ab_base::simd_quad_intel_spine(unsigned short const*, unsigned short const*, int, unsigned short)+0x2b0>
  407ca8:	movzwl 0xa(%r9,%rsi,1),%eax
  407cae:	cmp    %cx,%ax
  407cb1:	jae    4080d9 <ab_base::simd_quad_intel_spine(unsigned short const*, unsigned short const*, int, unsigned short)+0x609>
  407cb7:	lea    0x7(%rdx),%eax
  407cba:	cmp    %r11d,%eax
  407cbd:	jge    407d80 <ab_base::simd_quad_intel_spine(unsigned short const*, unsigned short const*, int, unsigned short)+0x2b0>
  407cc3:	movzwl 0xc(%r9,%rsi,1),%eax
  407cc9:	cmp    %cx,%ax
  407ccc:	jae    4080d9 <ab_base::simd_quad_intel_spine(unsigned short const*, unsigned short const*, int, unsigned short)+0x609>
  407cd2:	lea    0x8(%rdx),%eax
  407cd5:	cmp    %eax,%r11d
  407cd8:	jle    407d80 <ab_base::simd_quad_intel_spine(unsigned short const*, unsigned short const*, int, unsigned short)+0x2b0>
  407cde:	movzwl 0xe(%r9,%rsi,1),%eax
  407ce4:	cmp    %cx,%ax
  407ce7:	jae    4080d9 <ab_base::simd_quad_intel_spine(unsigned short const*, unsigned short const*, int, unsigned short)+0x609>
  407ced:	lea    0x9(%rdx),%eax
  407cf0:	cmp    %eax,%r11d
  407cf3:	jle    407d80 <ab_base::simd_quad_intel_spine(unsigned short const*, unsigned short const*, int, unsigned short)+0x2b0>
  407cf9:	movzwl 0x10(%r9,%rsi,1),%eax
  407cff:	cmp    %cx,%ax
  407d02:	jae    4080d9 <ab_base::simd_quad_intel_spine(unsigned short const*, unsigned short const*, int, unsigned short)+0x609>
  407d08:	lea    0xa(%rdx),%eax
  407d0b:	cmp    %eax,%r11d
  407d0e:	jle    407d80 <ab_base::simd_quad_intel_spine(unsigned short const*, unsigned short const*, int, unsigned short)+0x2b0>
  407d10:	movzwl 0x12(%r9,%rsi,1),%eax
  407d16:	cmp    %cx,%ax
  407d19:	jae    4080d9 <ab_base::simd_quad_intel_spine(unsigned short const*, unsigned short const*, int, unsigned short)+0x609>
  407d1f:	lea    0xb(%rdx),%eax
  407d22:	cmp    %eax,%r11d
  407d25:	jle    407d80 <ab_base::simd_quad_intel_spine(unsigned short const*, unsigned short const*, int, unsigned short)+0x2b0>
  407d27:	movzwl 0x14(%r9,%rsi,1),%eax
  407d2d:	cmp    %cx,%ax
  407d30:	jae    4080d9 <ab_base::simd_quad_intel_spine(unsigned short const*, unsigned short const*, int, unsigned short)+0x609>
  407d36:	lea    0xc(%rdx),%eax
  407d39:	cmp    %eax,%r11d
  407d3c:	jle    407d80 <ab_base::simd_quad_intel_spine(unsigned short const*, unsigned short const*, int, unsigned short)+0x2b0>
  407d3e:	movzwl 0x16(%r9,%rsi,1),%eax
  407d44:	cmp    %cx,%ax
  407d47:	jae    4080d9 <ab_base::simd_quad_intel_spine(unsigned short const*, unsigned short const*, int, unsigned short)+0x609>
  407d4d:	lea    0xd(%rdx),%eax
  407d50:	cmp    %eax,%r11d
  407d53:	jle    407d80 <ab_base::simd_quad_intel_spine(unsigned short const*, unsigned short const*, int, unsigned short)+0x2b0>
  407d55:	movzwl 0x18(%r9,%rsi,1),%eax
  407d5b:	cmp    %cx,%ax
  407d5e:	jae    4080d9 <ab_base::simd_quad_intel_spine(unsigned short const*, unsigned short const*, int, unsigned short)+0x609>
  407d64:	add    $0xe,%edx
  407d67:	cmp    %edx,%r11d
  407d6a:	jle    407d80 <ab_base::simd_quad_intel_spine(unsigned short const*, unsigned short const*, int, unsigned short)+0x2b0>
  407d6c:	movzwl 0x3c(%r9),%eax
  407d71:	cmp    %cx,%ax
  407d74:	jae    4080d9 <ab_base::simd_quad_intel_spine(unsigned short const*, unsigned short const*, int, unsigned short)+0x609>
  407d7a:	nopw   0x0(%rax,%rax,1)
  407d80:	xor    %eax,%eax
  407d82:	vzeroupper
  407d85:	ret
  407d86:	cs nopw 0x0(%rax,%rax,1)
  407d90:	push   %rbp
  407d91:	mov    %rsp,%rbp
  407d94:	sub    $0x10,%rsp
  407d98:	mov    %rbx,-0x10(%rbp)
  407d9c:	mov    %edx,%ebx
  407d9e:	sar    $0x5,%ebx
  407da1:	cmp    $0x7f,%edx
  407da4:	jle    408160 <ab_base::simd_quad_intel_spine(unsigned short const*, unsigned short const*, int, unsigned short)+0x690>
  407daa:	mov    %r12,-0x8(%rbp)
  407dae:	mov    %rsi,%r10
  407db1:	mov    %ebx,%eax
  407db3:	xor    %r8d,%r8d
  407db6:	prefetcht0 (%rsi)
  407db9:	nopl   0x0(%rax)
  407dc0:	mov    %eax,%esi
  407dc2:	sar    $0x2,%esi
  407dc5:	lea    (%rsi,%r8,1),%edx
  407dc9:	lea    (%rdx,%rsi,1),%edi
  407dcc:	movslq %edx,%rdx
  407dcf:	cmp    %cx,(%r10,%rdx,2)
  407dd4:	movslq %edi,%r12
  407dd7:	setb   %dl
  407dda:	cmp    %cx,(%r10,%r12,2)
  407ddf:	movzbl %dl,%edx
  407de2:	adc    $0x0,%edx
  407de5:	add    %esi,%edi
  407de7:	movslq %edi,%rdi
  407dea:	cmp    %cx,(%r10,%rdi,2)
  407def:	adc    $0x0,%edx
  407df2:	imul   %esi,%edx
  407df5:	add    %edx,%r8d
  407df8:	lea    (%rsi,%rsi,2),%edx
  407dfb:	sub    %edx,%eax
  407dfd:	cmp    $0x3,%eax
  407e00:	jg     407dc0 <ab_base::simd_quad_intel_spine(unsigned short const*, unsigned short const*, int, unsigned short)+0x2f0>
  407e02:	cmp    $0x1,%eax
  407e05:	jle    407e3b <ab_base::simd_quad_intel_spine(unsigned short const*, unsigned short const*, int, unsigned short)+0x36b>
  407e07:	nopl   (%rax)
  407e0a:	data16 cs nopw 0x0(%rax,%rax,1)
  407e15:	data16 cs nopw 0x0(%rax,%rax,1)
  407e20:	mov    %eax,%edx
  407e22:	sar    $1,%edx
  407e24:	lea    (%rdx,%r8,1),%esi
  407e28:	movslq %esi,%rdi
  407e2b:	cmp    %cx,(%r10,%rdi,2)
  407e30:	cmovb  %esi,%r8d
  407e34:	sub    %edx,%eax
  407e36:	cmp    $0x1,%eax
  407e39:	jg     407e20 <ab_base::simd_quad_intel_spine(unsigned short const*, unsigned short const*, int, unsigned short)+0x350>
  407e3b:	movslq %r8d,%rax
  407e3e:	cmp    %cx,(%r10,%rax,2)
  407e43:	adc    $0x0,%r8d
  407e47:	cmp    %ebx,%r8d
  407e4a:	jl     408130 <ab_base::simd_quad_intel_spine(unsigned short const*, unsigned short const*, int, unsigned short)+0x660>
  407e50:	mov    %ebx,%eax
  407e52:	shl    $0x5,%eax
  407e55:	cmp    %eax,%r11d
  407e58:	jle    408528 <ab_base::simd_quad_intel_spine(unsigned short const*, unsigned short const*, int, unsigned short)+0xa58>
  407e5e:	mov    %ebx,%ebx
  407e60:	mov    $0x17,%r8d
  407e66:	mov    %r11d,%r12d
  407e69:	shl    $0x6,%rbx
  407e6d:	sub    %eax,%r12d
  407e70:	lea    (%r9,%rbx,1),%rdi
  407e74:	lea    -0x1(%r12),%ebx
  407e79:	mov    %rdi,%r10
  407e7c:	shr    $1,%r10
  407e7f:	neg    %r10
  407e82:	mov    %r10d,%esi
  407e85:	and    $0xf,%esi
  407e88:	lea    0x10(%rsi),%edx
  407e8b:	cmp    %r8d,%edx
  407e8e:	cmovb  %r8d,%edx
  407e92:	cmp    %edx,%ebx
  407e94:	jb     40810c <ab_base::simd_quad_intel_spine(unsigned short const*, unsigned short const*, int, unsigned short)+0x63c>
  407e9a:	test   %esi,%esi
  407e9c:	je     408007 <ab_base::simd_quad_intel_spine(unsigned short const*, unsigned short const*, int, unsigned short)+0x537>
  407ea2:	movzwl (%rdi),%edx
  407ea5:	cmp    %cx,%dx
  407ea8:	jae    408116 <ab_base::simd_quad_intel_spine(unsigned short const*, unsigned short const*, int, unsigned short)+0x646>
  407eae:	test   $0xe,%r10b
  407eb2:	je     4085c4 <ab_base::simd_quad_intel_spine(unsigned short const*, unsigned short const*, int, unsigned short)+0xaf4>
  407eb8:	lea    0x1(%rax),%r8d
  407ebc:	movzwl (%r9,%r8,2),%edx
  407ec1:	cmp    %cx,%dx
  407ec4:	jae    408116 <ab_base::simd_quad_intel_spine(unsigned short const*, unsigned short const*, int, unsigned short)+0x646>
  407eca:	cmp    $0x2,%esi
  407ecd:	jbe    4085d5 <ab_base::simd_quad_intel_spine(unsigned short const*, unsigned short const*, int, unsigned short)+0xb05>
  407ed3:	movzwl 0x2(%r9,%r8,2),%edx
  407ed9:	cmp    %cx,%dx
  407edc:	jae    408116 <ab_base::simd_quad_intel_spine(unsigned short const*, unsigned short const*, int, unsigned short)+0x646>
  407ee2:	test   $0xc,%r10b
  407ee6:	je     4085e7 <ab_base::simd_quad_intel_spine(unsigned short const*, unsigned short const*, int, unsigned short)+0xb17>
  407eec:	movzwl 0x4(%r9,%r8,2),%edx
  407ef2:	cmp    %cx,%dx
  407ef5:	jae    408116 <ab_base::simd_quad_intel_spine(unsigned short const*, unsigned short const*, int, unsigned short)+0x646>
  407efb:	cmp    $0x4,%esi
  407efe:	jbe    4085f9 <ab_base::simd_quad_intel_spine(unsigned short const*, unsigned short const*, int, unsigned short)+0xb29>
  407f04:	movzwl 0x6(%r9,%r8,2),%edx
  407f0a:	cmp    %cx,%dx
  407f0d:	jae    408116 <ab_base::simd_quad_intel_spine(unsigned short const*, unsigned short const*, int, unsigned short)+0x646>
  407f13:	cmp    $0x5,%esi
  407f16:	je     40860b <ab_base::simd_quad_intel_spine(unsigned short const*, unsigned short const*, int, unsigned short)+0xb3b>
  407f1c:	movzwl 0x8(%r9,%r8,2),%edx
  407f22:	cmp    %cx,%dx
  407f25:	jae    408116 <ab_base::simd_quad_intel_spine(unsigned short const*, unsigned short const*, int, unsigned short)+0x646>
  407f2b:	cmp    $0x6,%esi
  407f2e:	je     408613 <ab_base::simd_quad_intel_spine(unsigned short const*, unsigned short const*, int, unsigned short)+0xb43>
  407f34:	movzwl 0xa(%r9,%r8,2),%edx
  407f3a:	cmp    %cx,%dx
  407f3d:	jae    408116 <ab_base::simd_quad_intel_spine(unsigned short const*, unsigned short const*, int, unsigned short)+0x646>
  407f43:	and    $0x8,%r10d
  407f47:	je     40862f <ab_base::simd_quad_intel_spine(unsigned short const*, unsigned short const*, int, unsigned short)+0xb5f>
  407f4d:	movzwl 0xc(%r9,%r8,2),%edx
  407f53:	cmp    %cx,%dx
  407f56:	jae    408116 <ab_base::simd_quad_intel_spine(unsigned short const*, unsigned short const*, int, unsigned short)+0x646>
  407f5c:	cmp    $0x8,%esi
  407f5f:	je     408637 <ab_base::simd_quad_intel_spine(unsigned short const*, unsigned short const*, int, unsigned short)+0xb67>
  407f65:	movzwl 0xe(%r9,%r8,2),%edx
  407f6b:	cmp    %cx,%dx
  407f6e:	jae    408116 <ab_base::simd_quad_intel_spine(unsigned short const*, unsigned short const*, int, unsigned short)+0x646>
  407f74:	cmp    $0x9,%esi
  407f77:	je     40859c <ab_base::simd_quad_intel_spine(unsigned short const*, unsigned short const*, int, unsigned short)+0xacc>
  407f7d:	movzwl 0x10(%r9,%r8,2),%edx
  407f83:	cmp    %cx,%dx
  407f86:	jae    408116 <ab_base::simd_quad_intel_spine(unsigned short const*, unsigned short const*, int, unsigned short)+0x646>
  407f8c:	cmp    $0xa,%esi
  407f8f:	je     40863f <ab_base::simd_quad_intel_spine(unsigned short const*, unsigned short const*, int, unsigned short)+0xb6f>
  407f95:	movzwl 0x12(%r9,%r8,2),%edx
  407f9b:	cmp    %cx,%dx
  407f9e:	jae    408116 <ab_base::simd_quad_intel_spine(unsigned short const*, unsigned short const*, int, unsigned short)+0x646>
  407fa4:	cmp    $0xb,%esi
  407fa7:	je     408647 <ab_base::simd_quad_intel_spine(unsigned short const*, unsigned short const*, int, unsigned short)+0xb77>
  407fad:	movzwl 0x14(%r9,%r8,2),%edx
  407fb3:	cmp    %cx,%dx
  407fb6:	jae    408116 <ab_base::simd_quad_intel_spine(unsigned short const*, unsigned short const*, int, unsigned short)+0x646>
  407fbc:	cmp    $0xc,%esi
  407fbf:	je     40864f <ab_base::simd_quad_intel_spine(unsigned short const*, unsigned short const*, int, unsigned short)+0xb7f>
  407fc5:	movzwl 0x16(%r9,%r8,2),%edx
  407fcb:	cmp    %cx,%dx
  407fce:	jae    408116 <ab_base::simd_quad_intel_spine(unsigned short const*, unsigned short const*, int, unsigned short)+0x646>
  407fd4:	cmp    $0xd,%esi
  407fd7:	je     408657 <ab_base::simd_quad_intel_spine(unsigned short const*, unsigned short const*, int, unsigned short)+0xb87>
  407fdd:	movzwl 0x18(%r9,%r8,2),%edx
  407fe3:	cmp    %cx,%dx
  407fe6:	jae    408116 <ab_base::simd_quad_intel_spine(unsigned short const*, unsigned short const*, int, unsigned short)+0x646>
  407fec:	cmp    $0xf,%esi
  407fef:	jne    408683 <ab_base::simd_quad_intel_spine(unsigned short const*, unsigned short const*, int, unsigned short)+0xbb3>
  407ff5:	movzwl 0x1a(%r9,%r8,2),%edx
  407ffb:	cmp    %cx,%dx
  407ffe:	jae    408116 <ab_base::simd_quad_intel_spine(unsigned short const*, unsigned short const*, int, unsigned short)+0x646>
  408004:	add    $0xf,%eax
  408007:	mov    %r12d,%r8d
  40800a:	xor    %edx,%edx
  40800c:	sub    %esi,%r8d
  40800f:	lea    (%rdi,%rsi,2),%rsi
  408013:	mov    %r8d,%edi
  408016:	and    $0xfffffff0,%edi
  408019:	jmp    40802f <ab_base::simd_quad_intel_spine(unsigned short const*, unsigned short const*, int, unsigned short)+0x55f>
  40801b:	nopl   0x0(%rax,%rax,1)
  408020:	add    $0x10,%edx
  408023:	add    $0x20,%rsi
  408027:	cmp    %edx,%edi
  408029:	je     408560 <ab_base::simd_quad_intel_spine(unsigned short const*, unsigned short const*, int, unsigned short)+0xa90>
  40802f:	vpminuw (%rsi),%ymm0,%ymm1
  408034:	vpcmpeqw %ymm1,%ymm0,%ymm1
  408038:	vptest %ymm1,%ymm1
  40803d:	je     408020 <ab_base::simd_quad_intel_spine(unsigned short const*, unsigned short const*, int, unsigned short)+0x550>
  40803f:	add    %edx,%eax
  408041:	jmp    40810c <ab_base::simd_quad_intel_spine(unsigned short const*, unsigned short const*, int, unsigned short)+0x63c>
  408046:	cs nopw 0x0(%rax,%rax,1)
  408050:	cmp    $0x7,%edx
  408053:	jg     408460 <ab_base::simd_quad_intel_spine(unsigned short const*, unsigned short const*, int, unsigned short)+0x990>
  408059:	test   %edx,%edx
  40805b:	jle    407d80 <ab_base::simd_quad_intel_spine(unsigned short const*, unsigned short const*, int, unsigned short)+0x2b0>
  408061:	movzwl (%rdi),%eax
  408064:	cmp    %cx,%ax
  408067:	jae    4080d9 <ab_base::simd_quad_intel_spine(unsigned short const*, unsigned short const*, int, unsigned short)+0x609>
  408069:	cmp    $0x1,%edx
  40806c:	je     407d80 <ab_base::simd_quad_intel_spine(unsigned short const*, unsigned short const*, int, unsigned short)+0x2b0>
  408072:	movzwl 0x2(%rdi),%eax
  408076:	cmp    %cx,%ax
  408079:	jae    4080d9 <ab_base::simd_quad_intel_spine(unsigned short const*, unsigned short const*, int, unsigned short)+0x609>
  40807b:	cmp    $0x2,%edx
  40807e:	je     407d80 <ab_base::simd_quad_intel_spine(unsigned short const*, unsigned short const*, int, unsigned short)+0x2b0>
  408084:	movzwl 0x4(%rdi),%eax
  408088:	cmp    %cx,%ax
  40808b:	jae    4080d9 <ab_base::simd_quad_intel_spine(unsigned short const*, unsigned short const*, int, unsigned short)+0x609>
  40808d:	cmp    $0x3,%edx
  408090:	je     407d80 <ab_base::simd_quad_intel_spine(unsigned short const*, unsigned short const*, int, unsigned short)+0x2b0>
  408096:	movzwl 0x6(%rdi),%eax
  40809a:	cmp    %cx,%ax
  40809d:	jae    4080d9 <ab_base::simd_quad_intel_spine(unsigned short const*, unsigned short const*, int, unsigned short)+0x609>
  40809f:	cmp    $0x4,%edx
  4080a2:	je     407d80 <ab_base::simd_quad_intel_spine(unsigned short const*, unsigned short const*, int, unsigned short)+0x2b0>
  4080a8:	movzwl 0x8(%rdi),%eax
  4080ac:	cmp    %cx,%ax
  4080af:	jae    4080d9 <ab_base::simd_quad_intel_spine(unsigned short const*, unsigned short const*, int, unsigned short)+0x609>
  4080b1:	cmp    $0x5,%edx
  4080b4:	je     407d80 <ab_base::simd_quad_intel_spine(unsigned short const*, unsigned short const*, int, unsigned short)+0x2b0>
  4080ba:	movzwl 0xa(%rdi),%eax
  4080be:	cmp    %cx,%ax
  4080c1:	jae    4080d9 <ab_base::simd_quad_intel_spine(unsigned short const*, unsigned short const*, int, unsigned short)+0x609>
  4080c3:	cmp    $0x7,%edx
  4080c6:	jne    407d80 <ab_base::simd_quad_intel_spine(unsigned short const*, unsigned short const*, int, unsigned short)+0x2b0>
  4080cc:	movzwl 0xc(%rdi),%eax
  4080d0:	cmp    %cx,%ax
  4080d3:	jb     407d80 <ab_base::simd_quad_intel_spine(unsigned short const*, unsigned short const*, int, unsigned short)+0x2b0>
  4080d9:	cmp    %ax,%cx
  4080dc:	sete   %al
  4080df:	vzeroupper
  4080e2:	ret
  4080e3:	nopl   0x0(%rax)
  4080ea:	data16 cs nopw 0x0(%rax,%rax,1)
  4080f5:	data16 cs nopw 0x0(%rax,%rax,1)
  408100:	inc    %rax
  408103:	cmp    %eax,%r11d
  408106:	jle    408528 <ab_base::simd_quad_intel_spine(unsigned short const*, unsigned short const*, int, unsigned short)+0xa58>
  40810c:	movzwl (%r9,%rax,2),%edx
  408111:	cmp    %cx,%dx
  408114:	jb     408100 <ab_base::simd_quad_intel_spine(unsigned short const*, unsigned short const*, int, unsigned short)+0x630>
  408116:	cmp    %dx,%cx
  408119:	mov    -0x8(%rbp),%r12
  40811d:	sete   %al
  408120:	vzeroupper
  408123:	mov    -0x10(%rbp),%rbx
  408127:	leave
  408128:	ret
  408129:	nopl   0x0(%rax)
  408130:	shl    $0x5,%r8d
  408134:	mov    -0x8(%rbp),%r12
  408138:	movslq %r8d,%r8
  40813b:	lea    (%r9,%r8,2),%rax
  40813f:	vpcmpeqw (%rax),%ymm0,%ymm1
  408143:	vpcmpeqw 0x20(%rax),%ymm0,%ymm0
  408148:	vpor   %ymm0,%ymm1,%ymm0
  40814c:	vpmovmskb %ymm0,%eax
  408150:	test   %eax,%eax
  408152:	setne  %al
  408155:	vzeroupper
  408158:	mov    -0x10(%rbp),%rbx
  40815c:	leave
  40815d:	ret
  40815e:	xchg   %ax,%ax
  408160:	cmp    $0x1,%ebx
  408163:	je     40856c <ab_base::simd_quad_intel_spine(unsigned short const*, unsigned short const*, int, unsigned short)+0xa9c>
  408169:	mov    %ebx,%edx
  40816b:	xor    %esi,%esi
  40816d:	nopl   0x0(%rax,%rax,1)
  408175:	data16 cs nopw 0x0(%rax,%rax,1)
  408180:	mov    %edx,%edi
  408182:	sar    $1,%edi
  408184:	lea    (%rdi,%rsi,1),%r8d
  408188:	lea    0x1(%r8),%eax
  40818c:	shl    $0x5,%eax
  40818f:	cltq
  408191:	cmp    %cx,-0x2(%r9,%rax,2)
  408197:	cmovb  %r8d,%esi
  40819b:	sub    %edi,%edx
  40819d:	cmp    $0x1,%edx
  4081a0:	jg     408180 <ab_base::simd_quad_intel_spine(unsigned short const*, unsigned short const*, int, unsigned short)+0x6b0>
  4081a2:	lea    0x1(%rsi),%eax
  4081a5:	mov    %eax,%edx
  4081a7:	shl    $0x5,%edx
  4081aa:	movslq %edx,%rdx
  4081ad:	cmp    %cx,-0x2(%r9,%rdx,2)
  4081b3:	cmovae %esi,%eax
  4081b6:	cmp    %eax,%ebx
  4081b8:	jg     408578 <ab_base::simd_quad_intel_spine(unsigned short const*, unsigned short const*, int, unsigned short)+0xaa8>
  4081be:	mov    %ebx,%eax
  4081c0:	shl    $0x5,%eax
  4081c3:	cmp    %eax,%r11d
  4081c6:	jle    40852c <ab_base::simd_quad_intel_spine(unsigned short const*, unsigned short const*, int, unsigned short)+0xa5c>
  4081cc:	mov    %ebx,%ebx
  4081ce:	mov    $0x17,%r8d
  4081d4:	mov    %r12,-0x8(%rbp)
  4081d8:	mov    %r11d,%r12d
  4081db:	shl    $0x6,%rbx
  4081df:	sub    %eax,%r12d
  4081e2:	lea    (%r9,%rbx,1),%rdi
  4081e6:	mov    %rdi,%r10
  4081e9:	shr    $1,%r10
  4081ec:	neg    %r10
  4081ef:	mov    %r10d,%esi
  4081f2:	and    $0xf,%esi
  4081f5:	lea    0x10(%rsi),%edx
  4081f8:	cmp    %r8d,%edx
  4081fb:	cmovb  %r8d,%edx
  4081ff:	lea    -0x1(%r12),%r8d
  408204:	cmp    %edx,%r8d
  408207:	jb     408437 <ab_base::simd_quad_intel_spine(unsigned short const*, unsigned short const*, int, unsigned short)+0x967>
  40820d:	test   %esi,%esi
  40820f:	je     40837a <ab_base::simd_quad_intel_spine(unsigned short const*, unsigned short const*, int, unsigned short)+0x8aa>
  408215:	movzwl (%rdi),%edx
  408218:	cmp    %cx,%dx
  40821b:	jae    408116 <ab_base::simd_quad_intel_spine(unsigned short const*, unsigned short const*, int, unsigned short)+0x646>
  408221:	test   $0xe,%r10b
  408225:	je     408674 <ab_base::simd_quad_intel_spine(unsigned short const*, unsigned short const*, int, unsigned short)+0xba4>
  40822b:	lea    0x1(%rax),%r8d
  40822f:	movzwl (%r9,%r8,2),%edx
  408234:	cmp    %cx,%dx
  408237:	jae    408116 <ab_base::simd_quad_intel_spine(unsigned short const*, unsigned short const*, int, unsigned short)+0x646>
  40823d:	cmp    $0x2,%esi
  408240:	jbe    40867b <ab_base::simd_quad_intel_spine(unsigned short const*, unsigned short const*, int, unsigned short)+0xbab>
  408246:	movzwl 0x2(%r9,%r8,2),%edx
  40824c:	cmp    %cx,%dx
  40824f:	jae    408116 <ab_base::simd_quad_intel_spine(unsigned short const*, unsigned short const*, int, unsigned short)+0x646>
  408255:	test   $0xc,%r10b
  408259:	je     4086bf <ab_base::simd_quad_intel_spine(unsigned short const*, unsigned short const*, int, unsigned short)+0xbef>
  40825f:	movzwl 0x4(%r9,%r8,2),%edx
  408265:	cmp    %cx,%dx
  408268:	jae    408116 <ab_base::simd_quad_intel_spine(unsigned short const*, unsigned short const*, int, unsigned short)+0x646>
  40826e:	cmp    $0x4,%esi
  408271:	jbe    4086b7 <ab_base::simd_quad_intel_spine(unsigned short const*, unsigned short const*, int, unsigned short)+0xbe7>
  408277:	movzwl 0x6(%r9,%r8,2),%edx
  40827d:	cmp    %cx,%dx
  408280:	jae    408116 <ab_base::simd_quad_intel_spine(unsigned short const*, unsigned short const*, int, unsigned short)+0x646>
  408286:	cmp    $0x5,%esi
  408289:	je     4086af <ab_base::simd_quad_intel_spine(unsigned short const*, unsigned short const*, int, unsigned short)+0xbdf>
  40828f:	movzwl 0x8(%r9,%r8,2),%edx
  408295:	cmp    %cx,%dx
  408298:	jae    408116 <ab_base::simd_quad_intel_spine(unsigned short const*, unsigned short const*, int, unsigned short)+0x646>
  40829e:	cmp    $0x6,%esi
  4082a1:	je     4086c7 <ab_base::simd_quad_intel_spine(unsigned short const*, unsigned short const*, int, unsigned short)+0xbf7>
  4082a7:	movzwl 0xa(%r9,%r8,2),%edx
  4082ad:	cmp    %cx,%dx
  4082b0:	jae    408116 <ab_base::simd_quad_intel_spine(unsigned short const*, unsigned short const*, int, unsigned short)+0x646>
  4082b6:	and    $0x8,%r10d
  4082ba:	je     4086d7 <ab_base::simd_quad_intel_spine(unsigned short const*, unsigned short const*, int, unsigned short)+0xc07>
  4082c0:	movzwl 0xc(%r9,%r8,2),%edx
  4082c6:	cmp    %cx,%dx
  4082c9:	jae    408116 <ab_base::simd_quad_intel_spine(unsigned short const*, unsigned short const*, int, unsigned short)+0x646>
  4082cf:	cmp    $0x8,%esi
  4082d2:	je     4086cf <ab_base::simd_quad_intel_spine(unsigned short const*, unsigned short const*, int, unsigned short)+0xbff>
  4082d8:	movzwl 0xe(%r9,%r8,2),%edx
  4082de:	cmp    %cx,%dx
  4082e1:	jae    408116 <ab_base::simd_quad_intel_spine(unsigned short const*, unsigned short const*, int, unsigned short)+0x646>
  4082e7:	cmp    $0x9,%esi
  4082ea:	je     4086f7 <ab_base::simd_quad_intel_spine(unsigned short const*, unsigned short const*, int, unsigned short)+0xc27>
  4082f0:	movzwl 0x10(%r9,%r8,2),%edx
  4082f6:	cmp    %cx,%dx
  4082f9:	jae    408116 <ab_base::simd_quad_intel_spine(unsigned short const*, unsigned short const*, int, unsigned short)+0x646>
  4082ff:	cmp    $0xa,%esi
  408302:	je     4086ef <ab_base::simd_quad_intel_spine(unsigned short const*, unsigned short const*, int, unsigned short)+0xc1f>
  408308:	movzwl 0x12(%r9,%r8,2),%edx
  40830e:	cmp    %cx,%dx
  408311:	jae    408116 <ab_base::simd_quad_intel_spine(unsigned short const*, unsigned short const*, int, unsigned short)+0x646>
  408317:	cmp    $0xb,%esi
  40831a:	je     4086e7 <ab_base::simd_quad_intel_spine(unsigned short const*, unsigned short const*, int, unsigned short)+0xc17>
  408320:	movzwl 0x14(%r9,%r8,2),%edx
  408326:	cmp    %cx,%dx
  408329:	jae    408116 <ab_base::simd_quad_intel_spine(unsigned short const*, unsigned short const*, int, unsigned short)+0x646>
  40832f:	cmp    $0xc,%esi
  408332:	je     4086df <ab_base::simd_quad_intel_spine(unsigned short const*, unsigned short const*, int, unsigned short)+0xc0f>
  408338:	movzwl 0x16(%r9,%r8,2),%edx
  40833e:	cmp    %cx,%dx
  408341:	jae    408116 <ab_base::simd_quad_intel_spine(unsigned short const*, unsigned short const*, int, unsigned short)+0x646>
  408347:	cmp    $0xd,%esi
  40834a:	je     408707 <ab_base::simd_quad_intel_spine(unsigned short const*, unsigned short const*, int, unsigned short)+0xc37>
  408350:	movzwl 0x18(%r9,%r8,2),%edx
  408356:	cmp    %cx,%dx
  408359:	jae    408116 <ab_base::simd_quad_intel_spine(unsigned short const*, unsigned short const*, int, unsigned short)+0x646>
  40835f:	cmp    $0xf,%esi
  408362:	jne    4086ff <ab_base::simd_quad_intel_spine(unsigned short const*, unsigned short const*, int, unsigned short)+0xc2f>
  408368:	movzwl 0x1a(%r9,%r8,2),%edx
  40836e:	cmp    %cx,%dx
  408371:	jae    408116 <ab_base::simd_quad_intel_spine(unsigned short const*, unsigned short const*, int, unsigned short)+0x646>
  408377:	add    $0xf,%eax
  40837a:	mov    %esi,%edx
  40837c:	lea    (%rdi,%rdx,2),%rdi
  408380:	vpminuw (%rdi),%ymm0,%ymm1
  408385:	vpcmpeqw %ymm1,%ymm0,%ymm1
  408389:	vptest %ymm1,%ymm1
  40838e:	jne    40865f <ab_base::simd_quad_intel_spine(unsigned short const*, unsigned short const*, int, unsigned short)+0xb8f>
  408394:	sub    %esi,%r12d
  408397:	mov    %r12d,%edx
  40839a:	shr    $0x4,%edx
  40839d:	cmp    $0x1,%edx
  4083a0:	je     408429 <ab_base::simd_quad_intel_spine(unsigned short const*, unsigned short const*, int, unsigned short)+0x959>
  4083a6:	vpminuw 0x20(%rdi),%ymm0,%ymm1
  4083ac:	vpcmpeqw %ymm1,%ymm0,%ymm1
  4083b0:	vptest %ymm1,%ymm1
  4083b5:	jne    408668 <ab_base::simd_quad_intel_spine(unsigned short const*, unsigned short const*, int, unsigned short)+0xb98>
  4083bb:	cmp    $0x2,%edx
  4083be:	je     408429 <ab_base::simd_quad_intel_spine(unsigned short const*, unsigned short const*, int, unsigned short)+0x959>
  4083c0:	vpminuw 0x40(%rdi),%ymm0,%ymm1
  4083c6:	vpcmpeqw %ymm1,%ymm0,%ymm1
  4083ca:	vptest %ymm1,%ymm1
  4083cf:	jne    40868b <ab_base::simd_quad_intel_spine(unsigned short const*, unsigned short const*, int, unsigned short)+0xbbb>
  4083d5:	cmp    $0x3,%edx
  4083d8:	je     408429 <ab_base::simd_quad_intel_spine(unsigned short const*, unsigned short const*, int, unsigned short)+0x959>
  4083da:	vpminuw 0x60(%rdi),%ymm0,%ymm1
  4083e0:	vpcmpeqw %ymm1,%ymm0,%ymm1
  4083e4:	vptest %ymm1,%ymm1
  4083e9:	jne    408697 <ab_base::simd_quad_intel_spine(unsigned short const*, unsigned short const*, int, unsigned short)+0xbc7>
  4083ef:	cmp    $0x4,%edx
  4083f2:	je     408429 <ab_base::simd_quad_intel_spine(unsigned short const*, unsigned short const*, int, unsigned short)+0x959>
  4083f4:	vpminuw 0x80(%rdi),%ymm0,%ymm1
  4083fd:	vpcmpeqw %ymm1,%ymm0,%ymm1
  408401:	vptest %ymm1,%ymm1
  408406:	jne    4085b8 <ab_base::simd_quad_intel_spine(unsigned short const*, unsigned short const*, int, unsigned short)+0xae8>
  40840c:	cmp    $0x5,%edx
  40840f:	je     408429 <ab_base::simd_quad_intel_spine(unsigned short const*, unsigned short const*, int, unsigned short)+0x959>
  408411:	vpminuw 0xa0(%rdi),%ymm0,%ymm1
  40841a:	vpcmpeqw %ymm1,%ymm0,%ymm0
  40841e:	vptest %ymm0,%ymm0
  408423:	jne    4086a3 <ab_base::simd_quad_intel_spine(unsigned short const*, unsigned short const*, int, unsigned short)+0xbd3>
  408429:	shl    $0x4,%edx
  40842c:	cmp    %r12d,%edx
  40842f:	je     408528 <ab_base::simd_quad_intel_spine(unsigned short const*, unsigned short const*, int, unsigned short)+0xa58>
  408435:	add    %edx,%eax
  408437:	cltq
  408439:	jmp    40844c <ab_base::simd_quad_intel_spine(unsigned short const*, unsigned short const*, int, unsigned short)+0x97c>
  40843b:	nopl   0x0(%rax,%rax,1)
  408440:	inc    %rax
  408443:	cmp    %eax,%r11d
  408446:	jle    408528 <ab_base::simd_quad_intel_spine(unsigned short const*, unsigned short const*, int, unsigned short)+0xa58>
  40844c:	movzwl (%r9,%rax,2),%edx
  408451:	cmp    %cx,%dx
  408454:	jb     408440 <ab_base::simd_quad_intel_spine(unsigned short const*, unsigned short const*, int, unsigned short)+0x970>
  408456:	jmp    408116 <ab_base::simd_quad_intel_spine(unsigned short const*, unsigned short const*, int, unsigned short)+0x646>
  40845b:	nopl   0x0(%rax,%rax,1)
  408460:	vpcmpeqw (%rdi),%xmm0,%xmm0
  408464:	vpmovmskb %xmm0,%eax
  408468:	test   %eax,%eax
  40846a:	jne    408518 <ab_base::simd_quad_intel_spine(unsigned short const*, unsigned short const*, int, unsigned short)+0xa48>
  408470:	cmp    $0x8,%edx
  408473:	je     407d80 <ab_base::simd_quad_intel_spine(unsigned short const*, unsigned short const*, int, unsigned short)+0x2b0>
  408479:	movzwl 0x10(%rdi),%eax
  40847d:	cmp    %cx,%ax
  408480:	jae    4080d9 <ab_base::simd_quad_intel_spine(unsigned short const*, unsigned short const*, int, unsigned short)+0x609>
  408486:	cmp    $0x9,%edx
  408489:	je     407d80 <ab_base::simd_quad_intel_spine(unsigned short const*, unsigned short const*, int, unsigned short)+0x2b0>
  40848f:	movzwl 0x12(%rdi),%eax
  408493:	cmp    %cx,%ax
  408496:	jae    4080d9 <ab_base::simd_quad_intel_spine(unsigned short const*, unsigned short const*, int, unsigned short)+0x609>
  40849c:	cmp    $0xa,%edx
  40849f:	je     407d80 <ab_base::simd_quad_intel_spine(unsigned short const*, unsigned short const*, int, unsigned short)+0x2b0>
  4084a5:	movzwl 0x14(%rdi),%eax
  4084a9:	cmp    %cx,%ax
  4084ac:	jae    4080d9 <ab_base::simd_quad_intel_spine(unsigned short const*, unsigned short const*, int, unsigned short)+0x609>
  4084b2:	cmp    $0xb,%edx
  4084b5:	je     407d80 <ab_base::simd_quad_intel_spine(unsigned short const*, unsigned short const*, int, unsigned short)+0x2b0>
  4084bb:	movzwl 0x16(%rdi),%eax
  4084bf:	cmp    %cx,%ax
  4084c2:	jae    4080d9 <ab_base::simd_quad_intel_spine(unsigned short const*, unsigned short const*, int, unsigned short)+0x609>
  4084c8:	cmp    $0xc,%edx
  4084cb:	je     407d80 <ab_base::simd_quad_intel_spine(unsigned short const*, unsigned short const*, int, unsigned short)+0x2b0>
  4084d1:	movzwl 0x18(%rdi),%eax
  4084d5:	cmp    %cx,%ax
  4084d8:	jae    4080d9 <ab_base::simd_quad_intel_spine(unsigned short const*, unsigned short const*, int, unsigned short)+0x609>
  4084de:	cmp    $0xd,%edx
  4084e1:	je     407d80 <ab_base::simd_quad_intel_spine(unsigned short const*, unsigned short const*, int, unsigned short)+0x2b0>
  4084e7:	movzwl 0x1a(%rdi),%eax
  4084eb:	cmp    %cx,%ax
  4084ee:	jae    4080d9 <ab_base::simd_quad_intel_spine(unsigned short const*, unsigned short const*, int, unsigned short)+0x609>
  4084f4:	cmp    $0xf,%edx
  4084f7:	jne    407d80 <ab_base::simd_quad_intel_spine(unsigned short const*, unsigned short const*, int, unsigned short)+0x2b0>
  4084fd:	movzwl 0x1c(%rdi),%eax
  408501:	cmp    %cx,%ax
  408504:	jae    4080d9 <ab_base::simd_quad_intel_spine(unsigned short const*, unsigned short const*, int, unsigned short)+0x609>
  40850a:	xor    %eax,%eax
  40850c:	jmp    407d82 <ab_base::simd_quad_intel_spine(unsigned short const*, unsigned short const*, int, unsigned short)+0x2b2>
  408511:	nopl   0x0(%rax)
  408518:	mov    $0x1,%eax
  40851d:	vzeroupper
  408520:	ret
  408521:	nopl   0x0(%rax)
  408528:	mov    -0x8(%rbp),%r12
  40852c:	xor    %eax,%eax
  40852e:	vzeroupper
  408531:	mov    -0x10(%rbp),%rbx
  408535:	leave
  408536:	ret
  408537:	mov    %edx,%edi
  408539:	movzwl (%r9,%rdi,2),%eax
  40853e:	cmp    %cx,%ax
  408541:	jae    4080d9 <ab_base::simd_quad_intel_spine(unsigned short const*, unsigned short const*, int, unsigned short)+0x609>
  408547:	movzwl 0x2(%r9,%rdi,2),%eax
  40854d:	lea    0x2(%rdi,%rdi,1),%rsi
  408552:	cmp    %cx,%ax
  408555:	jb     407c3c <ab_base::simd_quad_intel_spine(unsigned short const*, unsigned short const*, int, unsigned short)+0x16c>
  40855b:	jmp    4080d9 <ab_base::simd_quad_intel_spine(unsigned short const*, unsigned short const*, int, unsigned short)+0x609>
  408560:	cmp    %edi,%r8d
  408563:	je     408528 <ab_base::simd_quad_intel_spine(unsigned short const*, unsigned short const*, int, unsigned short)+0xa58>
  408565:	add    %edi,%eax
  408567:	jmp    40810c <ab_base::simd_quad_intel_spine(unsigned short const*, unsigned short const*, int, unsigned short)+0x63c>
  40856c:	xor    %eax,%eax
  40856e:	cmp    %cx,0x3e(%rdi)
  408572:	jb     4081be <ab_base::simd_quad_intel_spine(unsigned short const*, unsigned short const*, int, unsigned short)+0x6ee>
  408578:	shl    $0x5,%eax
  40857b:	cltq
  40857d:	lea    (%r9,%rax,2),%rax
  408581:	vpcmpeqw (%rax),%ymm0,%ymm1
  408585:	vpcmpeqw 0x20(%rax),%ymm0,%ymm0
  40858a:	vpor   %ymm0,%ymm1,%ymm0
  40858e:	vpmovmskb %ymm0,%eax
  408592:	test   %eax,%eax
  408594:	setne  %al
  408597:	jmp    408155 <ab_base::simd_quad_intel_spine(unsigned short const*, unsigned short const*, int, unsigned short)+0x685>
  40859c:	add    $0x9,%eax
  40859f:	jmp    408007 <ab_base::simd_quad_intel_spine(unsigned short const*, unsigned short const*, int, unsigned short)+0x537>
  4085a4:	mov    $0x10,%edx
  4085a9:	jmp    407bda <ab_base::simd_quad_intel_spine(unsigned short const*, unsigned short const*, int, unsigned short)+0x10a>
  4085ae:	mov    $0x10,%edx
  4085b3:	jmp    407c00 <ab_base::simd_quad_intel_spine(unsigned short const*, unsigned short const*, int, unsigned short)+0x130>
  4085b8:	mov    $0x40,%edx
  4085bd:	add    %edx,%eax
  4085bf:	jmp    408437 <ab_base::simd_quad_intel_spine(unsigned short const*, unsigned short const*, int, unsigned short)+0x967>
  4085c4:	inc    %eax
  4085c6:	jmp    408007 <ab_base::simd_quad_intel_spine(unsigned short const*, unsigned short const*, int, unsigned short)+0x537>
  4085cb:	mov    $0x11,%edx
  4085d0:	jmp    407bda <ab_base::simd_quad_intel_spine(unsigned short const*, unsigned short const*, int, unsigned short)+0x10a>
  4085d5:	add    $0x2,%eax
  4085d8:	jmp    408007 <ab_base::simd_quad_intel_spine(unsigned short const*, unsigned short const*, int, unsigned short)+0x537>
  4085dd:	mov    $0x12,%edx
  4085e2:	jmp    407bda <ab_base::simd_quad_intel_spine(unsigned short const*, unsigned short const*, int, unsigned short)+0x10a>
  4085e7:	add    $0x3,%eax
  4085ea:	jmp    408007 <ab_base::simd_quad_intel_spine(unsigned short const*, unsigned short const*, int, unsigned short)+0x537>
  4085ef:	mov    $0x13,%edx
  4085f4:	jmp    407bda <ab_base::simd_quad_intel_spine(unsigned short const*, unsigned short const*, int, unsigned short)+0x10a>
  4085f9:	add    $0x4,%eax
  4085fc:	jmp    408007 <ab_base::simd_quad_intel_spine(unsigned short const*, unsigned short const*, int, unsigned short)+0x537>
  408601:	mov    $0x14,%edx
  408606:	jmp    407bda <ab_base::simd_quad_intel_spine(unsigned short const*, unsigned short const*, int, unsigned short)+0x10a>
  40860b:	add    $0x5,%eax
  40860e:	jmp    408007 <ab_base::simd_quad_intel_spine(unsigned short const*, unsigned short const*, int, unsigned short)+0x537>
  408613:	add    $0x6,%eax
  408616:	jmp    408007 <ab_base::simd_quad_intel_spine(unsigned short const*, unsigned short const*, int, unsigned short)+0x537>
  40861b:	mov    $0x15,%edx
  408620:	jmp    407bda <ab_base::simd_quad_intel_spine(unsigned short const*, unsigned short const*, int, unsigned short)+0x10a>
  408625:	mov    $0x16,%edx
  40862a:	jmp    407bda <ab_base::simd_quad_intel_spine(unsigned short const*, unsigned short const*, int, unsigned short)+0x10a>
  40862f:	add    $0x7,%eax
  408632:	jmp    408007 <ab_base::simd_quad_intel_spine(unsigned short const*, unsigned short const*, int, unsigned short)+0x537>
  408637:	add    $0x8,%eax
  40863a:	jmp    408007 <ab_base::simd_quad_intel_spine(unsigned short const*, unsigned short const*, int, unsigned short)+0x537>
  40863f:	add    $0xa,%eax
  408642:	jmp    408007 <ab_base::simd_quad_intel_spine(unsigned short const*, unsigned short const*, int, unsigned short)+0x537>
  408647:	add    $0xb,%eax
  40864a:	jmp    408007 <ab_base::simd_quad_intel_spine(unsigned short const*, unsigned short const*, int, unsigned short)+0x537>
  40864f:	add    $0xc,%eax
  408652:	jmp    408007 <ab_base::simd_quad_intel_spine(unsigned short const*, unsigned short const*, int, unsigned short)+0x537>
  408657:	add    $0xd,%eax
  40865a:	jmp    408007 <ab_base::simd_quad_intel_spine(unsigned short const*, unsigned short const*, int, unsigned short)+0x537>
  40865f:	xor    %edx,%edx
  408661:	add    %edx,%eax
  408663:	jmp    408437 <ab_base::simd_quad_intel_spine(unsigned short const*, unsigned short const*, int, unsigned short)+0x967>
  408668:	mov    $0x10,%edx
  40866d:	add    %edx,%eax
  40866f:	jmp    408437 <ab_base::simd_quad_intel_spine(unsigned short const*, unsigned short const*, int, unsigned short)+0x967>
  408674:	inc    %eax
  408676:	jmp    40837a <ab_base::simd_quad_intel_spine(unsigned short const*, unsigned short const*, int, unsigned short)+0x8aa>
  40867b:	add    $0x2,%eax
  40867e:	jmp    40837a <ab_base::simd_quad_intel_spine(unsigned short const*, unsigned short const*, int, unsigned short)+0x8aa>
  408683:	add    $0xe,%eax
  408686:	jmp    408007 <ab_base::simd_quad_intel_spine(unsigned short const*, unsigned short const*, int, unsigned short)+0x537>
  40868b:	mov    $0x20,%edx
  408690:	add    %edx,%eax
  408692:	jmp    408437 <ab_base::simd_quad_intel_spine(unsigned short const*, unsigned short const*, int, unsigned short)+0x967>
  408697:	mov    $0x30,%edx
  40869c:	add    %edx,%eax
  40869e:	jmp    408437 <ab_base::simd_quad_intel_spine(unsigned short const*, unsigned short const*, int, unsigned short)+0x967>
  4086a3:	mov    $0x50,%edx
  4086a8:	add    %edx,%eax
  4086aa:	jmp    408437 <ab_base::simd_quad_intel_spine(unsigned short const*, unsigned short const*, int, unsigned short)+0x967>
  4086af:	add    $0x5,%eax
  4086b2:	jmp    40837a <ab_base::simd_quad_intel_spine(unsigned short const*, unsigned short const*, int, unsigned short)+0x8aa>
  4086b7:	add    $0x4,%eax
  4086ba:	jmp    40837a <ab_base::simd_quad_intel_spine(unsigned short const*, unsigned short const*, int, unsigned short)+0x8aa>
  4086bf:	add    $0x3,%eax
  4086c2:	jmp    40837a <ab_base::simd_quad_intel_spine(unsigned short const*, unsigned short const*, int, unsigned short)+0x8aa>
  4086c7:	add    $0x6,%eax
  4086ca:	jmp    40837a <ab_base::simd_quad_intel_spine(unsigned short const*, unsigned short const*, int, unsigned short)+0x8aa>
  4086cf:	add    $0x8,%eax
  4086d2:	jmp    40837a <ab_base::simd_quad_intel_spine(unsigned short const*, unsigned short const*, int, unsigned short)+0x8aa>
  4086d7:	add    $0x7,%eax
  4086da:	jmp    40837a <ab_base::simd_quad_intel_spine(unsigned short const*, unsigned short const*, int, unsigned short)+0x8aa>
  4086df:	add    $0xc,%eax
  4086e2:	jmp    40837a <ab_base::simd_quad_intel_spine(unsigned short const*, unsigned short const*, int, unsigned short)+0x8aa>
  4086e7:	add    $0xb,%eax
  4086ea:	jmp    40837a <ab_base::simd_quad_intel_spine(unsigned short const*, unsigned short const*, int, unsigned short)+0x8aa>
  4086ef:	add    $0xa,%eax
  4086f2:	jmp    40837a <ab_base::simd_quad_intel_spine(unsigned short const*, unsigned short const*, int, unsigned short)+0x8aa>
  4086f7:	add    $0x9,%eax
  4086fa:	jmp    40837a <ab_base::simd_quad_intel_spine(unsigned short const*, unsigned short const*, int, unsigned short)+0x8aa>
  4086ff:	add    $0xe,%eax
  408702:	jmp    40837a <ab_base::simd_quad_intel_spine(unsigned short const*, unsigned short const*, int, unsigned short)+0x8aa>
  408707:	add    $0xd,%eax
  40870a:	jmp    40837a <ab_base::simd_quad_intel_spine(unsigned short const*, unsigned short const*, int, unsigned short)+0x8aa>
  40870f:	nop
