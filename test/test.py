# SPDX-FileCopyrightText: © 2025 Tiny Tapeout
# SPDX-License-Identifier: Apache-2.0

import cocotb
from cocotb.clock import Clock
from cocotb.triggers import ClockCycles

from tqv import TinyQV

@cocotb.test()
async def test_enabled_without_window(dut):
    dut._log.info("Start")

    # Set the clock period to 100 ns (10 MHz)
    clock = Clock(dut.clk, 100, units="ns")
    cocotb.start_soon(clock.start())

    # Interact with your design's registers through this TinyQV class.
    # This will allow the same test to be run when your design is integrated
    # with TinyQV - the implementation of this class will be replaces with a
    # different version that uses Risc-V instructions instead of the SPI 
    # interface to read and write the registers.
    tqv = TinyQV(dut)

    # Reset
    await tqv.reset()

    dut._log.info("Test project behavior")

    await tqv.write_word_reg(0, 0x1)
    assert await tqv.read_byte_reg(0) == 0x1
    assert await tqv.read_hword_reg(0) == 0x1
    assert await tqv.read_word_reg(0) == 0x1

    await ClockCycles(dut.clk, 3)

    # assign uo_out = {interrupt_high, interrupt_low, saw_pat, watchdog_enabled, after_window_start, after_window_close, 2'b00};
    assert dut.uo_out.value == 0b1001_1100


# Test that enabling the watchdog timer with a WINDOW_CLOSE of results in a set watchdog
@cocotb.test()
async def test_enabled_with_window_close(dut):
    dut._log.info("Start")

    # Set the clock period to 100 ns (10 MHz)
    clock = Clock(dut.clk, 100, units="ns")
    cocotb.start_soon(clock.start())

    # Interact with your design's registers through this TinyQV class.
    # This will allow the same test to be run when your design is integrated
    # with TinyQV - the implementation of this class will be replaces with a
    # different version that uses Risc-V instructions instead of the SPI 
    # interface to read and write the registers.
    tqv = TinyQV(dut)
    # Reset
    await tqv.reset()

    dut._log.info("Test project behavior")
    # Test writing 10 to WATCHDOG_CLOSE register
    await tqv.write_word_reg(2, 0xA)

    # Test enabling watchdog timer by writing to interrupt.
    await tqv.write_word_reg(0, 0x1)

    await ClockCycles(dut.clk, 5)
    # no interrupts, no pat seen, watchdog has been enabled, timer not expired
    assert dut.uo_out.value == 0b01010000

# Test that enabling the watchdog timer with a WINDOW_CLOSE of 10 results in an expired timer in 10 cycles.
@cocotb.test()
async def test_enabled_with_window_close(dut):
    dut._log.info("Start")

    # Set the clock period to 100 ns (10 MHz)
    clock = Clock(dut.clk, 100, units="ns")
    cocotb.start_soon(clock.start())

    # Interact with your design's registers through this TinyQV class.
    # This will allow the same test to be run when your design is integrated
    # with TinyQV - the implementation of this class will be replaces with a
    # different version that uses Risc-V instructions instead of the SPI 
    # interface to read and write the registers.
    tqv = TinyQV(dut)
    # Reset
    await tqv.reset()

    dut._log.info("Test project behavior")
    # Test writing 10 to WATCHDOG_CLOSE register
    await tqv.write_word_reg(2, 0xAAA)

    # Test enabling watchdog timer by writing to interrupt.
    await tqv.write_word_reg(0, 0x1)

    await ClockCycles(dut.clk, 1)
    # watchdog has been enabled, no pat seen, timer expired
    # no interrupt, no pat seen, watchdog enabled, after_window_start, window has not closed.
    assert dut.uo_out.value == 0b01011000 # this is actually 0b10011100 so the timer has expired after 1 clock cycle.
    
    await ClockCycles(dut.clk, 0xAAA)
    # interrupt, watchdog enabled, after_window_start, after_window_close
    assert dut.uo_out.value == 0b1001_1100

    # interrupts, no pat seen, watchdog enabled, after_window_start, 
    # After enough clock cycles, this should be 0b10011000
    timer_elapsed = 0
    for _ in range(100):
        if dut.uo_out.value != 0b01011000:
            assert dut.uo_out.value == 0b10011100
        if dut.uo_out.value == 0b10011100:
            timer_elapsed = 1
    assert timer_elapsed


  # Test that enabling the watchdog timer with a WINDOW_OPEN of 5 and a WINDOW_CLOSE of 10 doesn't 
  # trigger outside the window but does trigger inside the window.
# Test that enabling the watchdog timer with a WINDOW_CLOSE of 10 results in an expired timer in 10 cycles.
@cocotb.test()
async def test_enabled_with_window_start_and_close(dut):
    dut._log.info("Start")

    # Set the clock period to 100 ns (10 MHz)
    clock = Clock(dut.clk, 100, units="ns")
    cocotb.start_soon(clock.start())

    # Interact with your design's registers through this TinyQV class.
    # This will allow the same test to be run when your design is integrated
    # with TinyQV - the implementation of this class will be replaces with a
    # different version that uses Risc-V instructions instead of the SPI 
    # interface to read and write the registers.
    tqv = TinyQV(dut)
    # Reset
    await tqv.reset()

    dut._log.info("Test project behavior")
    # Writing 5 to WATCHDOG_START register
    await tqv.write_word_reg(1, 0x5)
    # Writing 10 to WATCHDOG_CLOSE register
    await tqv.write_word_reg(2, 0xA)
    # Enabling watchdog timer
    await tqv.write_word_reg(0, 0x1)

    await ClockCycles(dut.clk, 0xA)

    assert dut.uo_out.value == 0b10011100
