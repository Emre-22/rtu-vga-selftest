# VGA Selftest

Independent bench diagnostic for the ETR FabricFoxv2 FPGA ASIC simulator. It must animate without a phone, UART, buttons or any input value. It does not modify or submit a shared Tiny Tapeout shuttle project.

Nominal25.2MHz external pixel clock. VGA640x480@60Hz,800clocks/line,525lines/frame, negative HSYNC96clocks atx656..751, negative VSYNC2lines aty490..491. RGB is black outside active video. Animation changes only atx0,y480(verticalblank).

Visuals: white4pixel border, eight upper colour bars, a64x48white block moving4pixels perframe across the lower-middle area,8binary frame-counter squares and a green heartbeat toggling every30frames(0.5seconds). There is no waiting-for-input or game-over state.

Standard Tiny VGA mapping: uo0R1,uo1G1,uo2B1,uo3VSYNC,uo4R0,uo5G0,uo6B0,uo7HSYNC. Allui/uio inputs unused;uio_out/uio_oe=0. ena must be high;rst_n is active-low. Reset/disabled output is0x88.

Use the temporary startup helper to explicitly select this design, set the external clock and pulse reset. See README.md for upload verification, startup conflicts and hardware limits.
