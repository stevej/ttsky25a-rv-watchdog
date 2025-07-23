<!---

This file is used to generate your project datasheet. Please fill in the information below and delete any unused
sections.

You can also include images in this folder and reference them in the markdown. Each image must be less than
512 kb in size, and the combined size of all images must be less than 1 MB.
-->

## What it does

This is a watchdog timer with a 32-bit resolution window.

## Register map

Document the registers that are used to interact with your peripheral

| Address | Name  | Access | Description                                                         |
|---------|-------|--------|---------------------------------------------------------------------|
| 0x00    | ENABLE  | R/W    | 1=Enable, 0=Disable. Enables or disables the watchdog             |
| 0x01    | WINDOW_START | R/W | How many cycles until the window opens                          |
| 0x02    | WINDOW_CLOSE | R/W | How many cycles until the window closes                         |
| 0x03    | WATCHDOG_PAT | W  | "Pat" the watchdog, restarting the watch window                 

## How to test

Positive test: Set a window, then pat it within the window. No interrupt lines should be high or low.
Negative test: Set a window, allow it to expire. The two interrupt lines should be driven high and low respectively.


## External hardware

None required.