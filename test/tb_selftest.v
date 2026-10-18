`timescale 1ns/1ps
// Full raster checks use real timing. Only the explicitly labelled counter tests
// force frame_tick to avoid scanning 256 frames merely to test 8-bit wrap.
module tb_selftest;
 reg clk=0; always #5 clk=~clk;
 reg rst_n=0,ena=1; reg[7:0] ui_in=0,uio_in=0;
 wire[7:0] uo_out,uio_out,uio_oe;
 tt_um_emre_vga_selftest dut(.*);
 integer xx,yy,k,fd,hs,vs,visible,ticks;
 reg[7:0] expected_count;reg expected_heartbeat;
 integer r,g,b;
 task check(input reg ok,input string why);if(!ok)$fatal(1,"%s x=%0d y=%0d",why,dut.x,dut.y);endtask
 task clock_step;begin @(posedge clk);#1;end endtask
 task scan_frame(input string filename);
 begin
  fd=$fopen(filename,"w");check(fd!=0,"cannot open frame output");
  $fdisplay(fd,"P3\n640 480\n255");
  hs=0;vs=0;visible=0;ticks=0;
  expected_count=dut.frame_count;expected_heartbeat=dut.heartbeat;
  for(yy=0;yy<525;yy=yy+1)begin
   for(xx=0;xx<800;xx=xx+1)begin
    #1;
    check(dut.x==xx && dut.y==yy,"raster sequence");
    check(uo_out[7] == !(xx>=656 && xx<752),"HSYNC polarity/window");
    check(uo_out[3] == !(yy>=490 && yy<492),"VSYNC polarity/window");
    check(dut.active == (xx<640 && yy<480),"active window");
    check(dut.frame_tick == (xx==0 && yy==480),"frame tick position/width");
    check(uio_out==0 && uio_oe==0,"bidirectional pins must be inputs");
    if(!uo_out[7])hs=hs+1;if(!uo_out[3])vs=vs+1;
    if(dut.frame_tick)ticks=ticks+1;
    if(xx<640 && yy<480)begin
     visible=visible+1;
     check(dut.frame_count==expected_count && dut.heartbeat==expected_heartbeat,"animation changed in visible scan");
     r={uo_out[0],uo_out[4]};g={uo_out[1],uo_out[5]};b={uo_out[2],uo_out[6]};
     $fdisplay(fd,"%0d %0d %0d",r*85,g*85,b*85);
     if(xx<4 || xx>=636 || yy<4 || yy>=476)check(r==3 && g==3 && b==3,"white border");
     else if(yy==200)check(r==0 && g==0 && b==1,"background");
     else if(yy==250)begin
      if(xx>=32+(expected_count%128)*4 && xx<96+(expected_count%128)*4)check(r==3 && g==3 && b==3,"moving block");
      else check(r==0 && g==0 && b==1,"moving block background");
     end
     if(yy==360 && xx>=16 && xx<208 && ((xx-16)%24)<20)begin
      k=(xx-16)/24;check(r==0 && g==(expected_count[k]?3:1) && b==g,"binary frame counter");
     end
     if(yy==420 && xx>=16 && xx<96)check(r==0 && g==(expected_heartbeat?3:0) && b==0,"heartbeat pixel");
     if(yy==80 && xx%80==40)begin
      case(xx/80)
       0:check(r==3 && g==0 && b==0,"red bar");
       1:check(r==3 && g==3 && b==0,"yellow bar");
       2:check(r==0 && g==3 && b==0,"green bar");
       3:check(r==0 && g==3 && b==3,"cyan bar");
       4:check(r==0 && g==0 && b==3,"blue bar");
       5:check(r==3 && g==0 && b==3,"magenta bar");
       6:check(r==1 && g==1 && b==1,"gray bar");
       7:check(r==3 && g==3 && b==3,"white bar");
      endcase
     end
    end else check((uo_out & 8'h77)==0,"RGB must be black throughout blanking");
    clock_step();
   end
   // Neither UART/fire levels nor any other input participates in this design.
   ui_in=ui_in+8'h37;uio_in=~uio_in;
  end
  check(hs==96*525 && vs==2*800 && visible==640*480 && ticks==1,"full-frame totals");
  check(dut.frame_count==expected_count+8'd1,"one real frame increment");
  $fclose(fd);
 end endtask
 task accelerated_ticks(input integer n);
 integer j;begin
  // Test-only enable injection. Real frame tick timing is checked above.
  force dut.frame_tick=1'b1;
  for(j=0;j<n;j=j+1)clock_step();
  release dut.frame_tick;
  // Reposition raster counters for a COMPLETE scan, without changing animation.
  @(negedge clk);dut.video.x=0;dut.video.y=0;#1;
 end endtask
 initial begin
  repeat(4)clock_step();check(uo_out==8'h88,"reset output");
  @(negedge clk);rst_n=1;
  scan_frame("test/output/frame_000.ppm");
  check(dut.frame_count==1 && dut.blink_div==1 && !dut.heartbeat,"real vertical-blank animation");
  accelerated_ticks(28);check(dut.frame_count==29 && !dut.heartbeat && dut.blink_div==29,"heartbeat before threshold");
  accelerated_ticks(1);check(dut.frame_count==30 && dut.heartbeat && dut.blink_div==0,"heartbeat threshold");
  scan_frame("test/output/frame_030.ppm");
  accelerated_ticks(97);check(dut.frame_count==128 && dut.block_x==32,"moving block wraps at128");
  accelerated_ticks(127);check(dut.frame_count==255,"counter maximum");
  accelerated_ticks(1);check(dut.frame_count==0 && dut.block_x==32,"counter wraps at256");
  ena=0;#1;check(uo_out==8'h88 && uio_oe==0,"disabled output");clock_step();
  check(dut.frame_count==0 && dut.blink_div==0 && !dut.heartbeat,"disable resets animation");
  ena=1;clock_step();rst_n=0;#1;check(uo_out==8'h88,"reset assertion immediate black/sync");clock_step();
  check(dut.x==0 && dut.y==0 && dut.frame_count==0,"restart deterministic");
  $display("PASS: two complete real VGA frames, sync/blanking/pins/colors/animation, accelerated heartbeat/wrap/reset checks");$finish;
 end
 initial begin #20000000;$fatal(1,"test timeout");end
endmodule
