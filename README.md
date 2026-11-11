# OFT spec and research

Notes from 2026-11-08 on building better and cheaper FPV timer hardware for Grid.

- [research-notes-2026-11.md](research-notes-2026-11.md): what the RX5808 really does, gate
  link budget, antenna options, receivers (AD8318, RX5808 with coax, ESP32-C5 software
  radio, LapRF), Ethernet topologies, Grid adapter fit, step plan, sources.
- [oft-spec.md](oft-spec.md): draft v0.4 of the Open FPV Timer (OFT, formerly OTN). One
  Node firmware (C5), one Rust core library (`oft-core`), many Timer hosts: Grid in-process,
  a Pico 2 + W5500 hub, or Linux `oftd` on a Raspberry Pi (first target). The Timer serves
  the OFT Protocol (HTTP + WebSocket, capabilities, levels L1–L3). Includes RotorHazard and
  LapRF prior art.
- [hbom-b1-single-pilot.md](hbom-b1-single-pilot.md): parts bought and still needed for the
  first single-pilot gate timer (B1), plus wiring.

**Code:** sibling repos `oft` (Rust workspace: core, sim, oftd), `oft-timer-rp2350` (B1 Timer firmware), `oft-node-c5` (C5 Node firmware, widscan58 fork) and `rh-oft` (RotorHazard plugin).

**Current lean:** ESP32-C5 receivers, wired Ethernet with PoE. Reference firmware on the GPL
esp-sdr / widscan58 base, which can be combined with Grid's AGPL. The node detects and
timestamps crossings; race logic stays in the timing system.

**Next experiments:**

1. Test a gate antenna with an RX5808 node fed by coax.
2. Flash FPVGateC5MK and widscan58 on XIAO C5 boards and run them in gridfpv-rh beside the
   RX5808 node.
3. Bring up a C5 + W5500 serving `/oft/v1/info`.

## Acknowledgements

OFT started from reading other people's open work. These projects shaped it:

- **[FPVGateC5MK](https://github.com/LouisHitchcock/FPVGateC5MK)**,
  **[FPVGateC5RX](https://github.com/LouisHitchcock/FPVGateC5RX)** and
  **[FPVGate](https://github.com/LouisHitchcock/FPVGate)** by Louis Hitchcock. The main
  inspiration for this project. FPVGate showed that an ESP32-C5 can replace the
  hard-to-buy RX5808 as a lap-timing receiver, and FPVGateC5MK showed that one C5 can hop
  across a full heat of pilots fast enough to time them all. OFT's Node is built on that
  idea. FPVGate is licensed CC BY-NC-SA 4.0, so OFT takes the idea and its published
  measurements, not its code.
- **[widscan58](https://github.com/CapnBry/widscan58)** by CapnBry (GPL-3.0-or-later). The
  OFT Node firmware ([oft-node-c5](https://github.com/Open-FPV-Timer/oft-node-c5)) is a fork
  of it: the scanner, tuning, level measurement and web flasher are widscan58's, and OFT
  adds a mode that streams levels to a Timer.
- **[esp-sdr](https://github.com/ESPARGOS/esp-sdr)** and
  **[C5VRX](https://github.com/Twotoz/C5VRX)**, which widscan58 builds on. They found and
  published the way to capture raw radio samples on the ESP32-C5 that all of the above
  depend on.
- **[RotorHazard](https://github.com/RotorHazard/RotorHazard)**. The enter/exit threshold
  model, the manual calibration mode and much of what we know about RX5808 timing come
  from reading its node firmware and server. OFT's RotorHazard plugin
  ([rh-oft](https://github.com/Open-FPV-Timer/rh-oft)) runs inside it.

The [research notes](research-notes-2026-11.md)
record what we learned from each. If you like OFT, go and look at theirs.
