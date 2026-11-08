# HBOM — B1 single-pilot gate timer (first OFT test, RaceGOW)

Updated: 2026-11-08. Build B1 in [oft-spec.md](oft-spec.md) §9.

## Purchased

| # | Part | Exact item | Role | Qty have | Qty per timer | Unit cost (paid) | Line total | Link |
|---|---|---|---|---|---|---|---|---|
| 1 | Timer MCU + Ethernet + PoE | SMKTelec **RP2350-POE-ETH-Dev-Kit** (appears to be Waveshare RP2350-POE-ETH). RP2350A, 16 MB flash, **WIZnet W6300** Ethernet, 100 Mbps RJ45, USB-C. Kit includes PoE module, 2× 20-pin headers, 2 screws + nuts | Timer host: `oft-core`, OFT Protocol over Ethernet, powered by PoE | **2** | 1 | $25.29 | $50.58 | [Amazon B0HCC1RHL7](https://www.amazon.com/dp/B0HCC1RHL7) |
| 2 | Node | **Seeed Studio XIAO ESP32-C5** (SKU 100010048). ESP32-C5, dual-band radio, USB-C, u.FL antenna connector | Node: tunes, samples, timestamps, streams over UART | **2** | 1 | $12.99 | $25.98 | [Amazon B0GWQ8K461](https://www.amazon.com/dp/B0GWQ8K461) |

**Purchased total:** $76.56 for 2 timers' worth. **Per timer: $38.28** (pre-tax).

## On hand (no purchase needed)

| # | Part | Qty per timer | Notes |
|---|---|---|---|
| 3 | u.FL 5.8 GHz antenna | 1 | Plugs straight into the XIAO's u.FL, so no pigtail needed. Mount looking down from the top bar; a foil-lined cup narrows the beam |
| 4 | Jumper wires | ~5 | See wiring below |
| 5 | Enclosure | 1 | Ryan designs and prints. PVC clamp (21.3 / 26.7 mm OD). Must clear the RJ45, PoE module, both USB-C ports, and the u.FL antenna |
| 6 | Ethernet cable + PoE switch | shared | Already in use at RaceGOW. Confirm the kit's PoE module is 802.3af |

## Antenna and shielding test plan

Goal: a **narrow, unclipped peak well above the noise floor** when a quad passes under the top
bar. Use the C5 itself as the meter: stream its signal, carry a 25 mW VTX (analog, then
HDZero) through the gate, and record each run (also useful as replay data for detection).

### Antennas on hand

| Antenna | Type | Expect |
|---|---|---|
| None (bare u.FL) | Board/trace pickup | Weak, built-in attenuation, but varies with angle and nearby wires. Hard to repeat |
| Whoop whip | Linear dipole, omni | Known, small, receives RHCP and LHCP equally (about 3 dB loss on each). Fair to every pilot |
| Directional u.FL (from bigger quads) | Likely circular (patch/helical), directional | Narrower beam, so sharper peaks. Higher gain, so may clip. **Handedness matters** (below) |

**Polarization:** FPV video is mostly circular. A circular timer antenna of the *opposite*
handedness to a pilot's VTX loses roughly 20 dB or more, so RHCP and LHCP pilots would read very
differently. Check the directional antennas' handedness (RHCP/LHCP). Prefer linear (the whip)
unless every RaceGOW pilot runs the same handedness. Test a directional antenna with both an
RHCP and an LHCP VTX.

### Test matrix

| Run | Antenna | Shield | Notes |
|---|---|---|---|
| A | None | Open air | Baseline for the no-antenna idea |
| B | Whip | Open air | Baseline omni |
| C | None | Foil box, window | Ryan's plan |
| D | Whip | Foil box, window | Likely winner for fairness |
| E | Directional | Open air | Beam only. Watch for clipping |
| F | Directional | Foil box, window | Narrowest. Most likely to need attenuation |

Record per run: peak level, noise floor between passes, peak width (time above floor + half
the peak), any clipping, and RHCP vs LHCP difference.

### Box rules (foil liner)

- **Window at least 3–5 cm** across. 5.8 GHz is about 5.2 cm wavelength; openings under about
  2.5 cm block almost everything.
- **Antenna right at the window.** The window does most of the aiming, not the antenna's
  pointing. Keep the C5 near it, not deep in a foil cavity (reflections smear the peak).
- **Foil wall between the RP2350 board and the C5**, jumpers passing through. Shielding traps
  the RP2350/W6300 noise in with the receiver otherwise.
- **Cables in at the end away from the window**, short inside the box. Every cable carries RF
  through the shield.
- **Removable liner and adjustable window** (tape or slide), so one print tests every run.

## Only if needed

| # | Part | Spec | Est. cost | When |
|---|---|---|---|---|
| 7 | Attenuation | u.FL inline attenuator, or move/shield the antenna | $5–10 | Only if the C5 clips (saturates) at gate distance. Test first |

**Per-timer total: $38.28**, under the $50 target.

## Wiring (RP2350-POE-ETH ↔ XIAO ESP32-C5)

Pin numbers TBD until the board's pinout is checked (avoid the W6300's pins).

| Signal | RP2350 board | XIAO C5 | Notes |
|---|---|---|---|
| Power | 5 V / VSYS out | 5V | Power the C5 from 5 V, not the board's 3.3 V regulator (800 mA max) |
| Ground | GND | GND | |
| Node link TX → RX | UART TX (GPIO TBD) | UART RX (D7) | 921600 baud to start |
| Node link RX ← TX | UART RX (GPIO TBD) | UART TX (D6) | |
| SYNC | GPIO TBD (output) | any free GPIO (input) | Clock sync pulse, 10–100 Hz |
| C5 reset (optional) | GPIO TBD | EN / RST pad | Only needed to flash the C5 from the RP2350. First test: flash over USB-C from the laptop |
| C5 boot (optional) | GPIO TBD | BOOT strap pin | Same as above. Check C5 datasheet for the strap pin |

XIAO D6/D7 as the default UART pins is from the XIAO family layout; confirm on the C5 pinout.

## To check when the boards arrive

1. **RP2350 board pinout:** which GPIOs the W6300 uses, and whether it is wired for single SPI
   or quad SPI (decides Rust `embassy-net-wiznet` git vs C Pico SDK + WIZnet ioLibrary).
2. **PoE module:** standard (802.3af?) and 5 V output current.
3. **XIAO C5:** UART pins, a free pin for SYNC, antenna connector type, and current draw while
   sampling.
4. **Enclosure inputs:** board outlines and the RJ45, USB-C and u.FL positions, from both
   boards' dimension drawings.
