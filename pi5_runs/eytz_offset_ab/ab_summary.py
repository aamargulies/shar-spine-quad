import re, statistics
rx = re.compile(r"^(I2|I3|I4|I5|I|H|F|D|C)\s+\S.*?\s+(\d+\.\d+)\s+(\d+\.\d+)\s+(\d+\.\d+)\s+(\d+\.\d+)\s*$")
runs = []
for r in (1,2,3):
    d = {}
    for line in open(f"ab_run{r}.txt"):
        m = rx.match(line)
        if m: d[m.group(1)] = [float(m.group(i)) for i in (2,3,4,5)]
    runs.append(d)
modes = ["hot_bat","hot_ser","cold_bat","cold_ser"]
print("paired deltas vs F per run (3 runs, 100 sets x 200 reps, Pi 5 CPU 2), and median:")
for v in ["I","I2","I3","I4","I5","H","D"]:
    out = []
    for mi, m in enumerate(modes):
        ds = [(run[v][mi]/run["F"][mi]-1)*100 for run in runs]
        out.append(f"{m}: " + "/".join(f"{x:+.1f}" for x in ds) + f" med {statistics.median(ds):+.1f}%")
    print(f"  {v:3s} " + " | ".join(out))
print("\npaired deltas of I (as-is) vs I2 (no prefetch): effect of the shipped prefetch itself")
for mi, m in enumerate(modes):
    ds = [(run["I"][mi]/run["I2"][mi]-1)*100 for run in runs]
    print(f"  {m}: " + "/".join(f"{x:+.1f}" for x in ds) + f" med {statistics.median(ds):+.1f}%")
print("\npaired deltas of I3 (fixed, gated) vs I2 (no prefetch): benefit of a correct prefetch")
for mi, m in enumerate(modes):
    ds = [(run["I3"][mi]/run["I2"][mi]-1)*100 for run in runs]
    print(f"  {m}: " + "/".join(f"{x:+.1f}" for x in ds) + f" med {statistics.median(ds):+.1f}%")
print("\npaired deltas of I4 (fixed, masked) vs I2 (no prefetch)")
for mi, m in enumerate(modes):
    ds = [(run["I4"][mi]/run["I2"][mi]-1)*100 for run in runs]
    print(f"  {m}: " + "/".join(f"{x:+.1f}" for x in ds) + f" med {statistics.median(ds):+.1f}%")
print("\nabsolute medians (ns/q):")
for v in ["F","I","I2","I3","I4","I5","H","D","C"]:
    print(f"  {v:3s} " + "  ".join(f"{statistics.median([run[v][mi] for run in runs]):8.1f}" for mi in range(4)))
