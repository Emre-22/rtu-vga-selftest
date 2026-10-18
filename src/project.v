// SPDX-License-Identifier: Apache-2.0
`default_nettype none
module tt_um_emre_vga_selftest(
 input wire [7:0] ui_in, output wire [7:0] uo_out,
 input wire [7:0] uio_in, output wire [7:0] uio_out,
 output wire [7:0] uio_oe, input wire ena, clk, rst_n
);
 wire running = rst_n && ena;
 wire [9:0] x,y;
 wire active,hsync,vsync,frame_tick;
 vga_timing video(.clk(clk),.rst_n(running),.x(x),.y(y),
  .active(active),.hsync(hsync),.vsync(vsync),.frame_tick(frame_tick));
 reg [7:0] frame_count;
 reg [4:0] blink_div;
 reg heartbeat;
 always @(posedge clk) begin
  if(!running) begin frame_count<=0;blink_div<=0;heartbeat<=0;end
  else if(frame_tick) begin
   frame_count<=frame_count+8'd1;
   if(blink_div==5'd29) begin blink_div<=0;heartbeat<=!heartbeat;end
   else blink_div<=blink_div+5'd1;
  end
 end
 wire [9:0] block_x = 10'd32 + {1'b0,frame_count[6:0],2'b00};
 wire [2:0] bar = x<10'd80 ? 3'd0 : x<10'd160 ? 3'd1 :
   x<10'd240 ? 3'd2 : x<10'd320 ? 3'd3 : x<10'd400 ? 3'd4 :
   x<10'd480 ? 3'd5 : x<10'd560 ? 3'd6 : 3'd7;
 reg [1:0] red,green,blue;
 integer i;
 always @* begin
  i=0;red=0;green=0;blue=0;
  if(running && active) begin
   blue=1;
   if(y<10'd160) begin
    case(bar)
     0:begin red=3;green=0;blue=0;end
     1:begin red=3;green=3;blue=0;end
     2:begin red=0;green=3;blue=0;end
     3:begin red=0;green=3;blue=3;end
     4:begin red=0;green=0;blue=3;end
     5:begin red=3;green=0;blue=3;end
     6:begin red=1;green=1;blue=1;end
     default:begin red=3;green=3;blue=3;end
    endcase
   end
   if(y>=10'd230 && y<10'd278 && x>=block_x && x<block_x+10'd64)
    begin red=3;green=3;blue=3;end
   for(i=0;i<8;i=i+1) begin
    if(y>=10'd350 && y<10'd370 && x>=10'd16+10'(i*24) && x<10'd36+10'(i*24)) begin
     red=0;green=frame_count[i]?2'd3:2'd1;blue=frame_count[i]?2'd3:2'd1;
    end
   end
   if(y>=10'd400 && y<10'd440 && x>=10'd16 && x<10'd96)
    begin red=0;green=heartbeat?2'd3:2'd0;blue=0;end
   if(x<10'd4 || x>=10'd636 || y<10'd4 || y>=10'd476)
    begin red=3;green=3;blue=3;end
  end
 end
 assign uo_out=running ? {hsync,blue[0],green[0],red[0],vsync,blue[1],green[1],red[1]} : 8'h88;
 assign uio_out=8'h00;
 assign uio_oe=8'h00;
 wire _unused=&{ui_in,uio_in,1'b0};
endmodule
`default_nettype wire

