<!---

This file is used to generate your project datasheet. Please fill in the information below and delete any unused
sections.

You can also include images in this folder and reference them in the markdown. Each image must be less than
512 kb in size, and the combined size of all images must be less than 1 MB.
-->

## What it does

This is a watchdog timer with a 32-bit counter and optional window feature.

WINDOW_CLOSE is how many cycles until the watchdog timer pulls the output interrupt high either low or high respectively. WINDOW_OPEN < WINDOW_CLOSE. WINDOW_OPEN can be 0.

Remember to ENABLE the timer after setting WINDOW_CLOSE if you want the watchdog to start working.

out[0] is an interrupt line pulled high 
out[1] is an interrupt line pulled low
out[2] is a line pulled high for 1 cycle when PAT is set 1

## Register map

The following registers are used to interact with the watchdog

| Address | Name    | Access | Description                                                         |
|---------|---------|--------|---------------------------------------------------------------------|
| 0x00    | ENABLE  | R/W    | 1 = Enable, 0 = Disable.
| 0x01    | WINDOW_OPEN | R/W    | 32-bit value for how many cycles after reset the watchdog window should open                    |
| 0x02    | WINDOW_CLOSE    | R/W      | 32-bit value for how many cycles after reset the watchdog window should close |
| 0x03    | PAT | R/W   | 1=Pat. 0=Undefined "Patting" the watchdog timer causes it to reset the timer.


## How to test

Set `WINDOW_CLOSE` to 100
Set `ENABLE` to 1
Wait 101 cycles
`out[0]` should be high until reset
`out[1]` should be low until reset

Set WINDOW_CLOSE to 100
Set ENABLE to 1
Wait 50 cycles
Set ENABLE to 0
Wait 51 more cycles
The watchdog should not have triggered so check `out[0]` and `out[1]`
`out[0]` should still be low
`out[1]` should still be high

Notes:

* You can't configure the window open and close while the watchdog is enabled.

## External hardware

None required.
