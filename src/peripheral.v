/*
 * Copyright (c) 2025 Your Name
 * SPDX-License-Identifier: Apache-2.0
 */

`default_nettype none

// Change the name of this module to something that reflects its functionality and includes your name for uniqueness
// For example tqvp_yourname_spi for an SPI peripheral.
// Then edit tt_wrapper.v line 41 and change tqvp_example to your chosen module name.
module tqvp_stevej_watchdog (
    input         clk,          // Clock - the TinyQV project clock is normally set to 64MHz.
    input         rst_n,        // Reset_n - low to reset.

    input  [7:0]  ui_in,        // The input PMOD, always available.  Note that ui_in[7] is normally used for UART RX.
                                // The inputs are synchronized to the clock, note this will introduce 2 cycles of delay on the inputs.

    output [7:0]  uo_out,       // The output PMOD.  Each wire is only connected if this peripheral is selected.
                                // Note that uo_out[0] is normally used for UART TX.

    input [5:0]   address,      // Address within this peripheral's address space
    input [31:0]  data_in,      // Data in to the peripheral, bottom 8, 16 or all 32 bits are valid on write.

    // Data read and write requests from the TinyQV core.
    input [1:0]   data_write_n, // 11 = no write, 00 = 8-bits, 01 = 16-bits, 10 = 32-bits
    input [1:0]   data_read_n,  // 11 = no read,  00 = 8-bits, 01 = 16-bits, 10 = 32-bits
    
    output [31:0] data_out,     // Data out from the peripheral, bottom 8, 16 or all 32 bits are valid on read when data_ready is high.
    output        data_ready,

    output        user_interrupt  // Dedicated interrupt request for this peripheral
);

    // Implement a 32-bit read/write register at address 0
    reg [31:0] window_start;
    reg [31:0] window_close;
    reg watchdog_enabled; // has the user enabled the design
    reg pat; // has the user patted the watchdog this window?

    always @(posedge clk) begin
        if (!rst_n) begin
            window_start <= 32'b0;
            window_close <= 32'b0;
            watchdog_enabled <= 1'b0;
            pat <= 1'b0;
        end else begin
            if (address == 6'h0) begin // Address 0 is ENABLE
                if (data_write_n != 2'b11) watchdog_enabled <= data_in[0];
            end

            if (!timer_expired) begin
                timer <= timer + 1;
            end else if (data_in[0]) begin
                // the watchdog is being patted so reset the timer.
                timer <= 0;
                // register output that we've seen a pat.
                saw_pat <= 1;
            end else if (!data_in[0]) begin
                saw_pat <= 0;
            end

        end
    end
    reg [31:0] example_data;
    wire timer_expired;
    reg [31:0] timer;

    wire interrupt_high; // destination is an output pin, driving high means the window was missed.
    wire interrupt_low; // destination is an output pin, driving low means the window was missed.
    reg saw_pat; // destination is an output pin, driving high means the watchdog was pat and reset.

    assign timer_expired = watchdog_enabled && (timer > window_close && timer > window_start);
    assign interrupt_high = timer_expired;
    assign interrupt_low = !timer_expired;
    assign user_interrupt = interrupt_high;
    assign uo_out = {interrupt_high, interrupt_low, saw_pat, 5'b0_0000};

    // Unused
    assign data_out = 32'h0;

    // All reads complete in 1 clock
    assign data_ready = 1;
    
    // User interrupt is generated on rising edge of ui_in[6], and cleared by writing a 1 to the low bit of address 8.
    //reg example_interrupt;
    reg last_ui_in_6;

`ifdef FORMAL
    logic f_past_valid;

    initial begin
      f_past_valid = 1'b0;
    end

    always @(posedge clk) begin
        if (!f_past_valid) begin
            assume (!rst_n);
        end

        f_past_valid <= 1'b1;
    end


    always @(posedge clk) begin
        if (f_past_valid) begin
            // the timer can only expire if the watchdog is enabled
            if (timer_expired) begin
                assert (watchdog_enabled);
            end

            // the interrupt can only be pulled high by the timer expiring
            if (interrupt_high) begin
                assert (timer_expired);
                assert (watchdog_enabled);
            end
        end
     end
`endif // FORMAL


    // List all unused inputs to prevent warnings
    // data_read_n is unused as none of our behaviour depends on whether
    // registers are being read.
    wire _unused = &{data_read_n, 1'b0};

endmodule
