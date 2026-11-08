# OFT spec and research

Notes from 2026-11-08 on building better and cheaper FPV timer hardware for Grid.

- [research-notes-2026-11.md](research-notes-2026-11.md): what the RX5808 really does, gate
  link budget, antenna options, receivers (AD8318, RX5808 with coax, ESP32-C5 software
  radio, LapRF), Ethernet topologies, Grid adapter fit, step plan, sources.
- [oft-spec.md](oft-spec.md): draft v0.3 of the Open FPV Timer (OFT, formerly OTN). One
  Node firmware (C5), one Rust core library (`oft-core`), many Timer hosts: Grid in-process,
  a Pico 2 + W5500 hub, or Linux `oftd` on a Raspberry Pi (first target). The Timer serves
  the OFT Protocol (HTTP + WebSocket, capabilities, levels L1–L3). Includes RotorHazard and
  LapRF prior art.
- [hbom-b1-single-pilot.md](hbom-b1-single-pilot.md): parts bought and still needed for the
  first single-pilot gate timer (B1), plus wiring.

**Current lean:** ESP32-C5 receivers, wired Ethernet with PoE. Reference firmware on the GPL
esp-sdr / widscan58 base, which can be combined with Grid's AGPL. The node detects and
timestamps crossings; race logic stays in the timing system.

**Next experiments:**

1. Test a gate antenna with an RX5808 node fed by coax.
2. Flash FPVGateC5MK and widscan58 on XIAO C5 boards and run them in gridfpv-rh beside the
   RX5808 node.
3. Bring up a C5 + W5500 serving `/oft/v1/info`.
