# Third-party notices

This repository's own code and write-ups are under the MIT licence in `LICENSE`.
The items below are, or were, third-party material. None of them is covered by
that licence. Everything here was checked on 2026-10-11; quotations are verbatim
from the pages named.

## 1. Daniel Lemire, "You can beat the binary search" (post text and code)

**In the repository.** `Text/article.text` is a plain-text copy of the post as
published on 2026-04-27 (copied on or about 2026-04-30; in the repository since
commit f0a9538, 2026-05-11; attribution header prepended 2026-10-11, which also
lists the differences from the live page). `simd_quad.c` is the post's
reference kernel, as published on 2026-04-27, `#include`d by the harnesses as
the "simd" / "Lem" baseline; it is not relicensed under MIT and its copyright
stays with its author.

**The post.** <https://lemire.me/blog/2026/04/27/you-can-beat-the-binary-search/>,
published 2026-04-27 (page metadata `2026-04-27T17:32:13+00:00`), updated
2026-10-02 (`2026-10-02T23:16:55+00:00`). The page carries no copyright,
licence or Creative Commons statement of its own; its footer and sidebar link to
"Terms of use" (<https://lemire.me/blog/terms-of-use/>). It says "My source code
is available", linking to
<https://github.com/lemire/Code-used-on-Daniel-Lemire-s-blog/tree/master/2026/04/26/benchmark>,
and ends with a suggested citation ("Daniel Lemire, "You can beat the binary
search," in *Daniel Lemire's blog*, ..."). The blog's home page
(<https://lemire.me/blog/>) and about page (<https://lemire.me/blog/about-me/>)
state no licence either; both link to the same terms page.

**Licence of the text.** The terms-of-use page says, under "General Policies":

> All of the content except for the comments is made available under a Creative
> Commons license to facilitate free reuse: you can share and adapt this content,
> even for commercial use, as long as you credit the blog posts to me. It is ok
> if you make money from my blog posts.

In that paragraph the clause "you can share and adapt this content, even for
commercial use, as long as you credit the blog posts to me" links to
<https://creativecommons.org/licenses/by/3.0/> (Creative Commons Attribution 3.0),
as do the words "Creative Commons license" in the FAQ answer quoted next.
The same page's FAQ adds: "Can I translate one of your blog post? Yes. You can
translate any blog post and publish it elsewhere, under a Creative Commons
license. It implies that you must credit me, but it is ok if you make money."
On that basis `Text/article.text` is kept, with attribution, under CC BY 3.0,
and is excluded from this repository's MIT licence.

**Licence of the code.** No licence specific to the code is stated anywhere we
looked. The post states none. The terms-of-use page's only code-specific
sentence is a disclaimer, not a licence:

> Blogging is literature, not engineering. Code taken from a blog post should not
> be expected to work, it is meant to illustrate an idea. Don't build production
> systems by copying and pasting random code from the Internet. It will not end
> well.

Lemire's code repository, `lemire/Code-used-on-Daniel-Lemire-s-blog`, has no
`LICENSE` file at its root (fetching `.../master/LICENSE` returns 404) and the
GitHub API reports its `license` field as null; the two source files in
`2026/04/26/benchmark/benchmarks/` (`benchmark.cpp`, `simple.cpp`) carry no
licence or copyright header. The blanket CC BY 3.0 statement for "all of the
content except for the comments" is therefore the only licence text that could
cover the code shown in the post's appendix; we record that as a fact about the
pages, not as a legal conclusion.

**Version note.** The post and its code were revised on 2026-10-02 (the commit
in Lemire's repository is dated 2026-10-02 and titled "Search arrays under 16
elements with overlapping SIMD loads in the beat-binary-search post."). The
copies here are the 2026-04-27 version, whose "Initial Check" step is a linear
scan below 16 elements; the live version compares against two overlapping SIMD
loads instead. Every comparison in this repository against "Lemire's reference"
is against the April version.

## 2. Khuong & Morin, "Array Layouts for Comparison-Based Searching"

Paul-Virak Khuong and Pat Morin, "Array Layouts for Comparison-Based
Searching", *ACM Journal of Experimental Algorithmics* 22 (2017), pp. 1–39,
<https://doi.org/10.1145/3053370> (Crossref: published online 2017-05-10, in
print 2017-12-15). Preprint: arXiv:1509.05053, <https://arxiv.org/abs/1509.05053>
(v1 16 Sep 2015; v2 15 Mar 2017, "46 pages; 24 figures; updated after reviewing
by ACM JEA"). The arXiv record's "Rights to this article" link is arXiv's
non-exclusive distribution licence
(<http://arxiv.org/licenses/nonexclusive-distrib/1.0/>: "I grant arXiv.org a
perpetual, non-exclusive license to distribute this article."), which is a grant
to arXiv, not a redistribution licence for third parties.

Until 2026-10-11 the repository root carried
`ArrayLayoutsForComparisonBasedSearching.pdf` (471,091 bytes, 49 pages; first
page "ARRAY LAYOUTS FOR COMPARISON-BASED SEARCHING", "Paul-Virak Khuong and Pat
Morin", "March 14, 2017"; no arXiv stamp; added in commit 5fdbb0a, 2026-07-03).
The file was removed from the repository on 2026-10-11, and the published
history was rewritten the same day to purge it. The paper is cited,
not redistributed: `KhuongMorin.md` and `KMtrick.md` open with the citation, and
their section, listing and "PDF p." references are to that 49-page version.

## 3. Knuth, *The Art of Computer Programming*, Vol. 3, page scans

Until 2026-10-11 the repository carried `Images/Knuth_V3_p416.png`,
`Images/Knuth_V3_p423.png` and `Images/Knuth_V3_p706.png` (added in commit
5fdbb0a, 2026-07-03): scans of pages 416, 423 and 706 of Donald E. Knuth, *The
Art of Computer Programming, Volume 3: Sorting and Searching*, 2nd ed.,
Addison-Wesley, 1998. The book is copyrighted and the scans were not licensed
for redistribution; they were removed on 2026-10-11 and purged from the published
history the same day. No tracked file referenced them. The write-ups cite the pages
by number instead: p. 416 for the inline attribution "Another modification of
binary search, suggested in 1971 by L. E. Shar", p. 423 for the exercises and
p. 706 for their answers (`Text/journey.text`, bibliography and "Notes on
citations"; `Text/shar.text`).

## History

On 2026-10-11 the published `main` branch was rewritten with `git filter-repo`
to remove the Khuong & Morin PDF, the three Knuth page scans and four compiled
benchmark binaries from every commit (they had entered the history in the
pre-migration snapshot of 2026-07-03). Commit hashes from that snapshot onward
changed. Copies may persist in forks made before the rewrite and in GitHub's
caches until those are purged.
