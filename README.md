# RTU VGA self-test

An independent ETR/FabricFoxv2 FPGA diagnostic that **animates immediately without a phone or buttons**. This separates VGA/frame-update bring-up from the Phone Flight game's control-link requirements. No existing game repository, shared shuttle assembly or manufacturing submission is changed.

## Expected screen

- Eight colour bars across the top, with a white border.
- A white block slides horizontally below the bars, wrapping about every 2.13 seconds.
- Eight small cyan/grey squares show a binary counter that changes every video frame.
- A green rectangle at bottom left flashes every 0.5 seconds.

If those three animated elements remain static after verified loading/clock/reset, this diagnostic is failing. It never waits for a phone, UART packet, fire or restart input. Input switches have no effect.

## Board and artifact

Target: **ETR with FabricFoxv2 ICE40UP5K simulator**, not the white board's fixed TT.RUN.09 ASIC or a classic simulator with different pin constraints. Tiny VGA goes to OUTPUT PMOD and the monitor uses its own power. The laptop's data USB connection can power/control the board for this test; the phone stays disconnected.

Nominal external clock 25.2 MHz, standard 640x480/60 Hz VGA timing. The helper checks reported clock error within 0.5%; physical frequency/monitor lock still needs checking. All bidirectional pins remain inputs. This repository runs RTL and real FPGA synthesis/routing checks, not ASIC GDS/manufacturing verification. info.yaml uses a minimal 1x1 template footprint only; no extra event tiles are allocated.

Download the verified `tt_um_emre_vga_selftest.bin` and SHA256SUMS from the [verified release](https://github.com/Emre-22/rtu-vga-selftest/releases/tag/vga-selftest-v1). GitHub Actions builds the programming file; uploading/selecting it is separate. A synthesis PASS does not prove upload success. The existing Phone Flight `.bin` is a different project and intentionally waits for phone controls.

## Upload and run from a Windows laptop

Clone this repository, enter its folder, and place the release `.bin` under `build/`. Replace COM3 with the board's port. Close other programs using that port.

```powershell
python -m pip install mpremote==1.27.0
mpremote connect list
mpremote connect COM3 df
mpremote connect COM3 fs ls :/bitstreams
```

The ICE40 image is normally 104,090 bytes regardless of how small the RTL is. Allow extra space for filesystem overhead; the upload helper refuses inadequate free space. If space is low, back up existing bitstreams and agree with the mentor which obsolete file can be removed. No helper formats flash or deletes other projects.

```powershell
mpremote connect COM3 fs cp -r :/bitstreams board-backup
```

If our earlier `standalone.install()` phone-game hook exists, it will otherwise select Phone Flight again at startup. Enter maintenance mode using its documented startup bypass, then temporarily disable that hook with this marker:

```powershell
mpremote connect COM3 fs touch :rtu-standalone.disabled
```

The marker changes no SDK/configuration files. Restore phone-game autostart later with `mpremote connect COM3 fs rm :rtu-standalone.disabled`. A running phone relay disables Ctrl-C, so mpremote may require the management reset/startup FIRE bypass described in the [phone-game recovery guide](https://github.com/z10565/tt-zarina-first-project/blob/feat/standalone-usb/docs/STANDALONE.md). Do not reflash firmware to solve a busy serial console.

Upload, read back/verify, and temporarily start the self-test:

```powershell
python fpga/upload.py --port COM3 --bin build/tt_um_emre_vga_selftest.bin --start
```

The helper stores a content-addressed name under `/bitstreams`, verifies remote size/SHA256, and prints the exact selected project. It never overwrites another project's image. The temporary startup helper explicitly selects that image, sets manual input mode, requests the clock, checks its reported rate and pulses reset. It changes no main.py/config.ini and installs no autostart. Keep board USB connected during the test. After a power-cycle, rerun the command to start this diagnostic again.

If using the mentor's existing builder instead, its command is:

```powershell
python ttfpga.py https://github.com/Emre-22/rtu-vga-selftest
```

That tool is external to this repo; check its full upload log and hash. A canonical upload can be started with `mpremote connect COM3 run fpga/start_test.py`. Merely listing `/bitstreams` or copying config.ini to the laptop does not load/select a design.

## Verification and reporting

Run locally in Linux/WSL with Icarus, Verilator and Python:

```sh
verilator --lint-only -Wall -Wno-DECLFILENAME --top-module tt_um_emre_vga_selftest src/project.v src/vga_timing.v
bash test/run_checks.sh
python -m unittest discover -s fpga -p 'test*.py' -v
```

Tests must verify exact sync/blanking, real frame ticks, movement/heartbeat/counting, ignored inputs, deterministic reset/enable and bidirectional enables. Rendered preview frames are produced by Verilog simulation, not a replacement software animation. Final release notes record actual CI SHA, FPGA utilization/timing and tests; physical hardware success is reported only after observation.

For a failure, capture: helper stdout, verified bitstream SHA256, selected project name, actual clock reported, whether bars/border are visible, whether white block/counter/heartbeat change, and a short monitor video if possible. This identifies a failed animation without relying on the phone.

Original template/tool attribution is retained in [NOTICE](NOTICE) and [LICENSE](LICENSE).

