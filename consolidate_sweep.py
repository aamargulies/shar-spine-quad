#!/usr/bin/env python3
"""Fold the per-cell outputs of a sweep campaign into one raw file.

The sweep drivers (m4_runs/run_sweep.sh, m4_runs/run_sweep_f_vs_lem.sh,
pi5_runs/run_sweep.sh) write one two-line file per (N, mode, run) cell:

    DIR/PREFIX_n<N>_<mode>_run<R>.txt

Thousands of such files are slow to list, copy and diff, so after a campaign
they are folded into a single lossless archive, DIR/PREFIX_raw.txt:

    ### sweep_n64_hb_run1.txt
    # bench_sweep inner_n=64 mode=hb num_sets=200 hot_reps=200
    RESULT inner_n=64 mode=hb F=10.3456 Fstar=8.5812
    ### sweep_n64_hb_run2.txt
    # bench_sweep inner_n=64 mode=hb num_sets=200 hot_reps=200
    RESULT inner_n=64 mode=hb F=10.4012 Fstar=8.6103
    ...

Format: for each source file, one header line '### <basename>' followed by
that file's lines verbatim (byte for byte, line endings included). Entries
are sorted by (N numeric, mode in the order hb, hs, cb, cs, R numeric). The
format is lossless provided no source line starts with '### ' and every
non-empty source file ends with a newline; the tool refuses to write
otherwise, so nothing is ever archived in a form it cannot reproduce.

The aggregators m4_runs/compute_sweep.py, m4_runs/compute_sweep_f_vs_lem.py
and pi5_runs/compute_sweep.py read the per-cell file when it exists and fall
back to the matching entry of the raw file when it does not, so a fresh
campaign works before consolidation and the archived campaigns work after it.

Usage (from the repo root):

    python3 consolidate_sweep.py DIR PREFIX [--delete]

    python3 consolidate_sweep.py m4_runs  sweep      -> m4_runs/sweep_raw.txt
    python3 consolidate_sweep.py m4_runs  sweep_fvl  -> m4_runs/sweep_fvl_raw.txt
    python3 consolidate_sweep.py pi5_runs sweep      -> pi5_runs/sweep_raw.txt

The file pattern is anchored (PREFIX, then '_n', then digits), so PREFIX
'sweep' does not pick up the 'sweep_fvl_n*' files or sweep_n_list.txt.

If DIR/PREFIX_raw.txt already exists it is merged: existing entries are
kept and entries whose basename matches a newly gathered file are replaced.
The result is written to a temporary file in DIR and renamed into place.

With --delete, the raw file is read back after writing, every source file's
content is checked verbatim against its entry, and only then are the source
files removed (one unlink per file, no subprocesses). Any mismatch aborts
before anything is deleted.
"""
import argparse
import io
import os
import re
import sys
import tempfile

MODES = ("hb", "hs", "cb", "cs")
HEADER = b"### "


def cell_regex(prefix):
    """Match PREFIX_n<N>_<mode>_run<R>.txt and nothing else."""
    return re.compile(r"^" + re.escape(prefix) + r"_n(\d+)_([a-z]+)_run(\d+)\.txt$")


def sort_key(rx, basename):
    """(N numeric, mode in MODES order, R numeric); names outside the pattern sort last."""
    m = rx.match(basename)
    if not m:
        return (1, 0, len(MODES), "", 0, basename)
    n, mode, r = int(m.group(1)), m.group(2), int(m.group(3))
    mode_idx = MODES.index(mode) if mode in MODES else len(MODES)
    return (0, n, mode_idx, mode, r, basename)


def check_archivable(basename, content):
    """Refuse content the line-oriented format could not reproduce verbatim."""
    if content and not content.endswith(b"\n"):
        raise SystemExit(f"error: {basename} does not end with a newline; "
                         "the raw format cannot store it verbatim")
    for line in io.BytesIO(content):
        if line.startswith(HEADER):
            raise SystemExit(f"error: {basename} has a line starting with '### ', "
                             "which the raw format uses as its entry header")


def read_raw(path):
    """Parse a raw file into {basename: bytes}; {} if it does not exist."""
    if not os.path.exists(path):
        return {}
    with open(path, "rb") as f:
        data = f.read()
    chunks = {}
    cur = None
    for line in io.BytesIO(data):          # splits on b"\n" only, keeps the ends
        if line.startswith(HEADER):
            cur = line[len(HEADER):].rstrip(b"\r\n").decode()
            if cur in chunks:
                raise SystemExit(f"error: {path}: duplicate entry '{cur}'")
            chunks[cur] = []
        elif cur is None:
            raise SystemExit(f"error: {path}: content before the first '### ' header")
        else:
            chunks[cur].append(line)
    return {name: b"".join(lines) for name, lines in chunks.items()}


def write_raw(path, entries, rx):
    """Write entries in sort order via a temp file in the same directory, then rename."""
    order = sorted(entries, key=lambda name: sort_key(rx, name))
    directory = os.path.dirname(path) or "."
    fd, tmp = tempfile.mkstemp(dir=directory, prefix=os.path.basename(path) + ".", suffix=".tmp")
    try:
        with os.fdopen(fd, "wb") as f:
            for name in order:
                f.write(HEADER + name.encode() + b"\n")
                f.write(entries[name])
            f.flush()
            os.fsync(f.fileno())
        os.replace(tmp, path)
    except BaseException:
        try:
            os.unlink(tmp)
        except OSError:
            pass
        raise
    return order


def main(argv=None):
    ap = argparse.ArgumentParser(
        description="Fold DIR/PREFIX_n<N>_<mode>_run<R>.txt files into DIR/PREFIX_raw.txt "
                    "(lossless; see the module docstring for the format).")
    ap.add_argument("dir", help="directory holding the per-cell files, e.g. m4_runs")
    ap.add_argument("prefix", help="per-cell file prefix, e.g. sweep or sweep_fvl")
    ap.add_argument("--delete", action="store_true",
                    help="after writing and re-reading the raw file, delete the per-cell files")
    args = ap.parse_args(argv)

    directory = os.path.normpath(args.dir)
    if not os.path.isdir(directory):
        raise SystemExit(f"error: {directory} is not a directory")
    rx = cell_regex(args.prefix)
    pattern = os.path.join(directory, f"{args.prefix}_n<N>_<mode>_run<R>.txt")
    raw_path = os.path.join(directory, f"{args.prefix}_raw.txt")

    names = sorted(n for n in os.listdir(directory) if rx.match(n))
    existing = read_raw(raw_path)
    if not names and not existing:
        raise SystemExit(f"error: no files match {pattern} and {raw_path} does not exist")

    gathered = {}
    for name in names:
        with open(os.path.join(directory, name), "rb") as f:
            content = f.read()
        check_archivable(name, content)
        gathered[name] = content

    for name, content in existing.items():
        check_archivable(name, content)
    replaced = sum(1 for name in gathered if name in existing)
    unknown = [name for name in existing if not rx.match(name)]
    merged = dict(existing)
    merged.update(gathered)

    order = write_raw(raw_path, merged, rx)

    print(f"gathered {len(gathered)} file(s) matching {pattern}")
    if existing:
        print(f"merged with existing {raw_path}: {len(existing)} entries, {replaced} replaced")
    for name in unknown:
        print(f"warning: kept entry '{name}' from {raw_path}, which does not match the pattern",
              file=sys.stderr)
    print(f"wrote {raw_path}: {len(order)} entries, {os.path.getsize(raw_path)} bytes")

    if args.delete:
        if not gathered:
            print("nothing to delete")
            return 0
        back = read_raw(raw_path)
        bad = [name for name in gathered if back.get(name) != gathered[name]]
        if bad:
            raise SystemExit(f"error: {len(bad)} file(s) not reproduced verbatim from {raw_path} "
                             f"(first: {bad[0]}); nothing deleted")
        print(f"verified {len(gathered)} file(s) verbatim against {raw_path}")
        for name in gathered:
            os.unlink(os.path.join(directory, name))
        print(f"deleted {len(gathered)} file(s)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
