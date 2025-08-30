# SPDX-FileCopyrightText: © 2025 Tiny Tapeout
# SPDX-License-Identifier: Apache-2.0

import cocotb
from cocotb.clock import Clock
from cocotb.triggers import ClockCycles

from tqv import TinyQV

# Tests cover the following scenario.
# 1) Enabling the watchdog without a timer should result in immediately tripping.
# 2) Enabling the watchdog with a timer should trigger after the timer.
# 3) Enabling the watchdog with a timer that is reset should not trigger after the first timer expires.
# 4) Enabling the watchdog and then disabling the watchdog disables the timer from expiring.
# 5) TODO: Enabling the watchdog with a WINDOW_START and WINDOW_CLOSE should expire if the pat happens before the window.

# Reminder: assign uo_out = {interrupt_high, interrupt_low, saw_pat, watchdog_enabled, after_window_start, after_window_close, 2'b00};

@cocotb.test()
async def test_enabled_without_window(dut):
    "Enabling the watchdog without a timer should result in immediately tripping."
    dut._log.info("Start")

    # Set the clock period to 100 ns (10 MHz)
    clock = Clock(dut.clk, 100, units="ns")
    cocotb.start_soon(clock.start())

    tqv = TinyQV(dut)
    await tqv.reset()

    await tqv.write_word_reg(0, 0x1)
    await ClockCycles(dut.clk, 1)

    assert dut.uo_out.value == 0b1001_1100

@cocotb.test()
async def test_enabled_with_window_close_trigger_after_expiration(dut):
    "Enabling with WINDOW_CLOSE should cause a trigger only after the timer expires."
    dut._log.info("Start")

    # Set the clock period to 100 ns (10 MHz)
    clock = Clock(dut.clk, 100, units="ns")
    cocotb.start_soon(clock.start())

    tqv = TinyQV(dut)
    await tqv.reset()

    dut._log.info("Testing a watchdog with a WINDOW_CLOSE but no WINDOW_START")

    # WINDOW_CLOSE is set to 25 cycles, the minimum number of cycles a window can be due to timing.
    # Any shorter than 25 and this test will fail.
    await tqv.write_word_reg(2, 25)
    # ENABLE watchdog
    await tqv.write_word_reg(0, 0x1)
    await ClockCycles(dut.clk, 1)

    # After one cycle, no interrupt
    assert dut.uo_out.value == 0b0101_1000

    # Next clock cycle we see the interrupt.
    await ClockCycles(dut.clk, 1)
    assert dut.uo_out.value == 0b1001_1100

@cocotb.test()
async def test_enabled_with_window_close_and_then_disable_no_trigger(dut):
    "Enabling with WINDOW_CLOSE and then disabling should cause no trigger."
    dut._log.info("Start")

    # Set the clock period to 100 ns (10 MHz)
    clock = Clock(dut.clk, 100, units="ns")
    cocotb.start_soon(clock.start())

    tqv = TinyQV(dut)
    await tqv.reset()
    dut._log.info("Enabling with WINDOW_CLOSE and then disabling should cause no trigger.")

    # Set a window large enough to last two spi writes.
    await tqv.write_word_reg(2, 0x50)
    # ENABLE watchdog
    await tqv.write_word_reg(0, 0x1)
    await ClockCycles(dut.clk, 1)

    # assign uo_out = {interrupt_high, interrupt_low, saw_pat, watchdog_enabled, after_window_start, after_window_close, 2'b00};
    assert dut.uo_out.value != 0b1001_1100

    # DISABLE watchdog
    await tqv.write_word_reg(0, 0x0)
    await ClockCycles(dut.clk, 1)

    # The interrupt does not trigger, no matter how long we wait
    await ClockCycles(dut.clk, 1000)
    assert dut.uo_out.value != 0b1001_1100

@cocotb.test()
async def test_enabled_with_window_close_and_then_pat_no_trigger(dut):
    "Enabling with WINDOW_CLOSE and then patting should cause no trigger."
    dut._log.info("Start")

    # Set the clock period to 100 ns (10 MHz)
    clock = Clock(dut.clk, 100, units="ns")
    cocotb.start_soon(clock.start())

    tqv = TinyQV(dut)
    await tqv.reset()
    dut._log.info("Enabling with WINDOW_CLOSE and then patting should cause no trigger.")

    # Set a window large enough to survive two spi writes.
    await tqv.write_word_reg(2, 75)
    # ENABLE watchdog
    await tqv.write_word_reg(0, 1)
    await ClockCycles(dut.clk, 1)

    # assign uo_out = {interrupt_high, interrupt_low, saw_pat, watchdog_enabled, after_window_start, after_window_close, 2'b00};
    assert dut.uo_out.value != 0b1001_1100

    # Send a pat to the watch watchdog
    await tqv.write_word_reg(3, 1)
    await ClockCycles(dut.clk, 1)

    # The watchdog should not trigger
    await ClockCycles(dut.clk, 50)
    assert dut.uo_out.value != 0b1001_1100
    assert dut.uo_out.value == 0b0111_1000


@cocotb.test()
async def test_enabled_with_window_close_no_start_with_pat_twice_then_expire(dut):
    "Enabling with only WINDOW_CLOSE and patting twice causes the timer to reset."
    dut._log.info("Start")

    # Set the clock period to 100 ns (10 MHz)
    clock = Clock(dut.clk, 100, units="ns")
    cocotb.start_soon(clock.start())

    tqv = TinyQV(dut)
    await tqv.reset()
    dut._log.info("Enabling with only WINDOW_CLOSE and patting twice causes the timer to reset.")

    # WINDOW_CLOSE is 25 cycles. This is the minimum number of cycles a window can be due to timing.
    await tqv.write_word_reg(2, 25)
    # ENABLE watchdog
    await tqv.write_word_reg(0, 0x1)
    await ClockCycles(dut.clk, 1)

    # assign uo_out = {interrupt_high, interrupt_low, saw_pat, watchdog_enabled, after_window_start, after_window_close, 2'b00};
    assert dut.uo_out.value != 0b1001_1100

    # Send Pat to reset watchdog, check that the timer hasn't expired.
    await tqv.write_word_reg(3, 1) # how many cycles does this take?
    await ClockCycles(dut.clk, 1)
    assert dut.uo_out.value == 0b0111_1000

    # Send Pat again to reset watchdog, check that timer hasn't expired.
    await tqv.write_word_reg(3, 1) # how many cycles does this take?
    await ClockCycles(dut.clk, 1)
    assert dut.uo_out.value == 0b0111_1000

    # Don't send pat, let the timer expire.
    await ClockCycles(dut.clk, 1)
    assert dut.uo_out.value == 0b1011_1100

@cocotb.test()
async def test_enabled_with_window_close_and_open_not_enabled_no_trigger(dut):
    "Setting WINDOW_OPEN and WINDOW_CLOSE and not enabling it should result in no trigger."
    dut._log.info("Start")

    # Set the clock period to 100 ns (10 MHz)
    clock = Clock(dut.clk, 100, units="ns")
    cocotb.start_soon(clock.start())

    tqv = TinyQV(dut)
    await tqv.reset()
    dut._log.info("Setting WINDOW_OPEN and WINDOW_CLOSE and not enabling it should result in no trigger.")

    # WINDOW_START
    await tqv.write_word_reg(1, 25)
    # WINDOW_CLOSE
    await tqv.write_word_reg(2, 50)

    # wait longer than the watchdog is set for to see if it triggers.
    await ClockCycles(dut.clk, 35)
    # assign uo_out = {interrupt_high, interrupt_low, saw_pat, watchdog_enabled, after_window_start, after_window_close, 2'b00};
    assert dut.uo_out.value != 0b1001_1100
    assert dut.uo_out.value == 0b0100_0000


# Test that enabling the watchdog timer with a WINDOW_CLOSE of 10 results in an expired timer in 10 cycles.
@cocotb.test()
async def test_enabled_with_window_close_and_immediate_pat(dut):
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
    # Set WINDOW_CLOSE
    await tqv.write_word_reg(2, 0xAAA) # 2730 cycles
    assert await tqv.read_word_reg(2) == 0xAAA

    # Test enabling watchdog timer by writing to interrupt.
    await tqv.write_word_reg(0, 0x1)

    # Send pat immediately
    await tqv.write_word_reg(3, 0x1)
    assert await tqv.read_word_reg(3) == 0x1

    await ClockCycles(dut.clk, 1)
    # watchdog has been enabled, no pat seen, timer expired
    # no interrupt, no pat seen, watchdog enabled, after_window_start, window has not closed.
    assert dut.uo_out.value != 0b10011100 # we should not have triggered.
    assert dut.uo_out.value == 0b01111000

    # Check that the watchdog is enabled but not triggered for 10 cycles.
    for _ in range(10):
      await ClockCycles(dut.clk, 1)
      # watchdog has been enabled, no pat seen, timer expired
      # no interrupt, no pat seen, watchdog enabled, after_window_start, window has not closed.
      assert dut.uo_out.value == 0b01111000

    # TODO: Mystery! For some unknown reason we only need 101, and not (2730 - already used) cycles, for the watchdog to trigger.
    await ClockCycles(dut.clk, 0xAAA)
    # interrupt, watchdog enabled, after_window_start, after_window_close
    assert dut.uo_out.value == 0b1011_1100

    # interrupts, no pat seen, watchdog enabled, after_window_start
    # After enough clock cycles, this should be 0b10011000 which indicates the watchdog has been triggered.
    timer_elapsed = 0
    for _ in range(10):
        if dut.uo_out.value != 0b0111_1000:
            assert dut.uo_out.value == 0b1011_1100
        if dut.uo_out.value == 0b1011_1100:
            timer_elapsed = 1
    assert timer_elapsed


  # Test that enabling the watchdog timer with a WINDOW_OPEN of 5 and a WINDOW_CLOSE of 10 doesn't 
  # trigger outside the window but does trigger inside the window.


# Test that enabling the watchdog timer with a WINDOW_CLOSE of 10 results in an expired timer in 10 cycles.
@cocotb.test()
async def test_enabled_with_window_start_and_close_early_pat(dut):
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
    await tqv.write_word_reg(2, 0xBBB)
    # Enabling watchdog timer
    await tqv.write_word_reg(0, 0x1)

    # Wait and then pat.
    await ClockCycles(dut.clk, 10)
    # patting to reset the timer.
    await tqv.write_word_reg(3, 0x1)
    assert await tqv.read_word_reg(3) == 0x1


    await ClockCycles(dut.clk, 1)
    # watchdog should not have tripped after 1 cycle when configured for 0xBBB cycles
    assert dut.uo_out.value != 0b10011100
    assert dut.uo_out.value == 0b01111000


    # The watchdog should not trigger in less cycles than configured.
    await ClockCycles(dut.clk, 0xAA)
    # If this assertion fails, the watchdog triggered too quickly from our perspective.
    assert dut.uo_out.value != 0b10011100

    await ClockCycles(dut.clk, 1)
    assert dut.uo_out.value == 0b01111000

    await ClockCycles(dut.clk, 0xBBB)
    assert dut.uo_out.value == 0b10111100


# Test that enabling the watchdog timer with a WINDOW_CLOSE of 10 results in an expired timer in 10 cycles.
@cocotb.test()
async def test_enabled_with_window_start_and_close_no_pat(dut):
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
    await tqv.write_word_reg(1, 25)
    # Writing 10 to WATCHDOG_CLOSE register
    await tqv.write_word_reg(2, 250)
    # Enabling watchdog timer
    await tqv.write_word_reg(0, 0x1)

    await ClockCycles(dut.clk, 1)
    # watchdog should not have tripped after 1 cycle when configured for 0xBBB cycles
    assert dut.uo_out.value != 0b10011100
    assert dut.uo_out.value == 0b01010000

    # The watchdog should not trigger in less cycles than configured.
    await ClockCycles(dut.clk, 0x10)
    # If this assertion fails, the watchdog triggered too quickly from our perspective.
    assert dut.uo_out.value != 0b10011100

    await ClockCycles(dut.clk, 0x11)
    assert dut.uo_out.value == 0b01011000

    await ClockCycles(dut.clk, 0xAAA)
    assert dut.uo_out.value == 0b10011100

