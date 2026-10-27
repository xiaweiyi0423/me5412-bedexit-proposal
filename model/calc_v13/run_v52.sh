#!/bin/bash
# v5.2 chain after the slider synthesis and the handrail choice (seat_1dof/handrail.json):
# 81-user check on the slider -> fair vertical baseline -> cushions (uniform table, zoned grid/effort/consistency track)
# -> structure checks -> page data. Logs go to /tmp/claude-0/v52_*.log
set -e
cd "$(dirname "$0")"
L=/tmp/claude-0
python3 seat_1dof_slider.py eval > $L/v52_slider.log 2>&1; tail -2 $L/v52_slider.log
python3 seat_1dof_vertical_v52.py > $L/v52_vertical.log 2>&1; tail -1 $L/v52_vertical.log
CUSH_MECH=slider python3 seat_cushion.py > $L/v52_cushion.log 2>&1; tail -1 $L/v52_cushion.log
rm -f seat_1dof/cushion_zoned.json
python3 seat_cushion_zoned.py grid > $L/v52_zgrid.log 2>&1; tail -1 $L/v52_zgrid.log
python3 seat_cushion_zoned.py effort "均匀 6/6，5 cm（现推荐）" "后 10 / 前 3，分界 -2 cm" "后 15 / 前 2，分界 -2 cm" "后 30 / 前 1，分界 -2 cm" \
  "后 15 / 前 2，分界 0 cm" "后 15 / 前 2，分界 -2 cm，前区顶面低 1 cm" "后 15 / 前 2，分界 -2 cm，前区顶面低 2 cm" "后 15 / 前 2，分界 -2 cm，前区顶面低 3 cm" > $L/v52_zeff.log 2>&1
tail -1 $L/v52_zeff.log
python3 seat_cushion_zoned.py track "后 10 / 前 3，分界 -2 cm" "均匀 6/6，5 cm（现推荐）" > $L/v52_ztrack.log 2>&1; tail -3 $L/v52_ztrack.log
python3 seat_1dof_v5_checks.py > $L/v52_checks.log 2>&1; tail -6 $L/v52_checks.log
python3 seat_1dof_page_data_v5.py > $L/v52_page.log 2>&1; tail -4 $L/v52_page.log
echo CHAIN-DONE
