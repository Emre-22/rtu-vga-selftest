# VGA bring-up diagnostic

Read README.md for expected visual behavior and WORKPLAN.md before editing. The coordinator owns Git and shared documentation. Workers edit only assigned paths.

This independent diagnostic must animate without UART, phone, buttons or input pin levels. Keep the Tiny Tapeout interface and Tiny VGA output map. Use25.2MHz,640x480/60Hz,800x525negative-sync timing; update animation only in vertical blank. Leave all bidirectional pins as inputs.

Target ETR/FabricFoxv2 ICE40UP5K using pinned official support tools. It is an FPGA bench test, not a manufacturing submission. Preserve other projects and board firmware. Verify file size/hash after upload; a successful synthesis log does not prove successful transfer or selection.

Run RTL timing/animation tests and FPGA timing checks. Report physical results separately from simulation. Hardware startup helpers must hold reset on configuration errors and explicitly set clock/reset/project. Any existing phone-game startup hook must be bypassed for this test without deleting its files.
