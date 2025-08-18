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

    # Test enabling watchdog timer by writing to interrupt.
    await tqv.write_word_reg(0, 0x1)
    assert await tqv.read_byte_reg(0) == 0x1
    assert await tqv.read_hword_reg(0) == 0x1
    assert await tqv.read_word_reg(0) == 0x1

    # Set an input value, in the example this will be added to the register value
    dut.ui_in.value = 30

    # Wait for two clock cycles to see the output values, because ui_in is synchronized over two clocks,
    # and a further clock is required for the output to propagate.
    await ClockCycles(dut.clk, 3)

    assert dut.uo_out.value == 0b1001_0000

    # Input value of 0 should be read back from register 1 as it was never set.
    assert await tqv.read_byte_reg(1) == 0

    # Test the interrupt, generated when ui_in[6] goes high
    dut.ui_in[6].value = 1
    await ClockCycles(dut.clk, 1)
    dut.ui_in[6].value = 0

    # Interrupt asserted
    await ClockCycles(dut.clk, 3)
    assert dut.uio_out[0].value == 1

    # Interrupt doesn't clear
    await ClockCycles(dut.clk, 10)
    assert dut.uio_out[0].value == 1


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
    await tqv.write_word_reg(1, 0xA)

    # Test enabling watchdog timer by writing to interrupt.
    await tqv.write_word_reg(0, 0x1)

    await ClockCycles(dut.clk, 5)
    # watchdog has been enabled, no pat seen, timer not expired
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
    await tqv.write_word_reg(1, 0xA)

    # Test enabling watchdog timer by writing to interrupt.
    await tqv.write_word_reg(0, 0x1)

    await ClockCycles(dut.clk, 10)
    # watchdog has been enabled, no pat seen, timer expired
    assert dut.uo_out.value == 0b10010000


  # Test that enabling the watchdog timer with a WINDOW_OPEN of 5 and a WINDOW_CLOSE of 10 doesn't 
  # trigger outside the window but does trigger inside the window.
