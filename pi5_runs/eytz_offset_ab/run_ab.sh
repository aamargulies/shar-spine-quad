#!/bin/bash
cd /tmp/claude-1001/-Shared-QuadSearch/fb54694c-3101-4172-8fa4-b312e6a251c3/scratchpad/km-eytzinger
for r in 1 2 3; do
  s=$(date +%s)
  taskset -c 2 ./bt_ab 100 200 all > ab_run$r.txt 2>&1
  e=$(date +%s)
  echo "run $r wall=$((e-s)) s" >> ab_timing.txt
done
echo done > ab_done.flag
