#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")/.."
mkdir -p test/output
iverilog -g2012 -Wall -s tb_selftest -o test/output/selftest.vvp src/project.v src/vga_timing.v test/tb_selftest.v
vvp test/output/selftest.vvp
python3 test/render_frames.py
