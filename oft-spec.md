# Open FPV Timer (OFT) — draft spec v0.3

**Status:** idea draft, 2026-11-08. Nothing here is built or final.

**Changes from v0.2 (was "Open Timer Node", OTN):**

- Renamed to **OFT**. Terms changed to match: the C5 receiver is now a **Node** (was "radio"),
  the box with compute is now a **Timer** (was "node" / "host"). `otn-core` → `oft-core`,
  `otnd` → `oftd`, `otn-hub` → `oft-hub`.
- Added **prior art** (§2): RotorHazard and LapRF, checked against source.
- The service now announces **capabilities** in `/info` and the WebSocket `hello`.
  Conformance levels L1–L3 are named bundles of capabilities.
- Message type key is `type` (was `t`). Live signal is `samples`, passes are `crossing`.
- Added `fw.update`: the Timer finds and flashes its Nodes over USB or UART.
- Added **RF silence** rule: no Wi-Fi or other transmitting at the gate.
- **Pilots per Node** is spelled out in §4.1 with a `seats_per_node` config knob.
- Reference code exists: the `oft` repo (Rust workspace: `oft-nodelink`, `oft-core`,
  `oft-sim`, `oftd`) implements §5, §8 and §6 and is tested against synthetic passes.
- B3 (Raspberry Pi Timer) now covers 8 Nodes: USB for data, shared SYNC wire for time.
- Added **B5: carrier board** (8 C5s, one USB link) with a **Pi HAT variant** (§9.2), and
  RotorHazard / NuclearHazard multi-node hardware as prior art.

## 1. What this is

OFT is an open, cheap, easy-to-build **timer** for FPV racing.

- A Timer has **1 to n Nodes** behind one network endpoint, usually one Ethernet cable.
- It runs a **small network service** (the OFT Protocol) that any timing software can use to
  configure it and read data back: Grid, a RotorHazard plugin, a browser, or `curl`.
- The Timer detects and timestamps crossings, and makes the raw signal available.
- Race logic (pilots, heats, laps, results) stays in the Race Manager.

### Design principle: many builds, one firmware, one core

```
  NODE FIRMWARE (one)           OFT CORE (one library)            TIMER HOSTS (many)
  ESP32-C5, ESP-IDF, C          Rust, no_std (+alloc)             ┌ oftd     — Linux / Pi / laptop
  tune, sample, timestamp  ──►  clock mapping, seat scheduling,   ├ oft-hub  — RP2350 + W5500
  stream raw power              detection, ring buffers,          ├ in-process inside Grid
  (no detection, no network)    OFT protocol types                └ (future hosts)
```

- **Nodes are simple.** They tune, sample, timestamp and stream. Keeping them small keeps
  the GPL fork of esp-sdr / widscan58 small, and keeps the undocumented PHY code in one place.
- **Every decision lives in `oft-core`:** detection, thresholds, `t_mid`, seat scheduling and
  buffers. One implementation, tested once by replaying recorded sample streams.
- **Timer hosts are thin.** Each is `oft-core` plus that platform's I/O (serial ports, network
  stack, HTTP). Builds differ only in host and transport.

### Goals

- **Flexible:** the same Nodes and core support a bench dongle, a single-pilot PoE gate box,
  an 8-pilot box, or a Linux timer.
- **Easy to build:** every reference build uses off-the-shelf boards.
- **Open:** the spec is published (suggested licence: CC BY 4.0). Node firmware is GPL-3.0
  (esp-sdr base). `oft-core` and the hosts are GPL-3.0 or AGPL-3.0, compatible with Grid's
  AGPL-3.0.
- **Receiver-agnostic:** the ESP32-C5 is the reference Node, but anything that speaks the
  Node link (§5) is a Node. That includes an AD8318 sampled by the Timer's ADC, or an RX5808
  adaptor.
- **Wired:** Ethernet for the OFT Protocol. Nodes connect to the Timer over USB or UART.

### Non-goals (v1)

- Wi-Fi or any other RF link for timer comms (see §4.3).
- Race logic.
- Clock sync tighter than about 1 ms across separate Timers.

## 2. Prior art

Checked against source on 2026-11-08.

### RotorHazard (`src/node/commands.{h,cpp}`, `src/node/RssiNode.cpp`, `src/interface/RHInterface.py`, NODE_API_LEVEL 36)

- Node (Arduino or STM32 per RX5808) talks to the Pi over I2C or serial. **The Pi polls every
  100 ms** (`RH_UPDATE_INTERVAL`).
- **The node detects passes** with EnterAt/ExitAt thresholds (hysteresis).
- Pass time = **midpoint of the peak-RSSI plateau** (`passPeak.firstTime + duration/2`).
- `READ_LAP_PASS_STATS`: lap count (u8), **ms since last pass** (u16), current RSSI, peak RSSI,
  pass peak RSSI, loop time. The Pi converts "ms since" to absolute time, so polling delay
  does not affect accuracy.
- `READ_LAP_EXTREMUMS`: one queued peak or nadir per poll (rssi, ms ago, duration). This
  compressed history drives the RSSI graph and **marshaling recalculation** on the Pi.

### RotorHazard multi-node hardware (8 receivers on one Pi)

- **Classic Arduino build:** one Arduino Nano per RX5808, all on the Pi's single I2C bus.
  Each picks an address `0x08`–`0x16` (even) from hardware-select pins on its PCB slot
  (`rhnode.cpp`). The Pi polls each address in turn.
- **S32_BPill / NuclearHazard:** **one STM32** (Blue Pill chip) drives up to 8 RX5808s. Shared
  SPI data and clock, one select pin each (`PB6–PB9, PB12–PB15`), one analog RSSI pin each.
  Detection runs on the STM32 for every receiver. `MULTI_RHNODE_MAX 8` (`config.h`).
- **Link:** **one GPIO UART** to the Pi, `/dev/ttyAMA0` (falls back to `/dev/serial0`), 921600
  baud (`serial_node.py`). The Pi addresses 8 logical nodes over it with `WRITE_CURNODE_INDEX`.
- **Flashing from the web UI:** the Pi drives **GPIO17 → STM32 reset** and **GPIO27 → BOOT0**,
  enters the STM32 ROM bootloader, and flashes over the same UART (`stm32loader.py`). OFT's
  UART Node flashing (§5.1) uses the same pattern.
- **NuclearHazard Core** (`resources/NuclearHazardCore/`): the STM32 is soldered on the main
  board, RX5808s sit on plug-in dual carrier cards, and the Pi mounts on the 40-pin header.
  Board takes 2–5S input and powers the Pi. RH senses filled slots at boot.
- **Extras:** USB nodes add serial ports on top of the PCB nodes (`doc/USB Nodes.md`).
  Secondary timers join over the network, usually Wi-Fi (`doc/Cluster.md`).

Why OFT can't copy this directly: an RX5808 is a bare SPI-tuned chip with an analog output,
so one MCU can share 8 of them. A C5 is a full MCU with its own firmware and clock, so OFT
needs one link per C5 (or a hub that aggregates them) plus clock mapping (§4.2).

### ImmersionRC LapRF (from `@fpvcult/laprf` 1.1.1; protocol spec v1.2, Aug 2017)

- USB / Ethernet / BT. Binary records framed with SOR `0x5A`, EOR `0x5B`, escape `0x5C`, CRC.
- **The device detects passes** and pushes `passing` records (`0xDA09`): slot, `rtcTime`
  (u64 device RTC), decoder id, **monotonic passing number**, peak height, flags.
- `status` (`0xDA0A`) pushed periodically: per-slot RSSI, gate state, battery voltage.
- `rfSetup` (`0xDA02`): per-slot band/channel, frequency, threshold, gain. `time` (`0xDA0C`):
  RTC request for host clock alignment.
- Not verified: `rtcTime` units (commonly described as µs).

### What OFT takes from them

1. **Timestamp at the source.** Both report device-timestamped passes; neither relies on
   arrival time.
2. **Monotonic `seq`** on crossings (LapRF), so the client can detect gaps.
3. **Plateau midpoint** as the lap time (RH), refined in §8 to an edge-level midpoint.
4. **Signal history for marshaling** (RH), but full rate instead of peaks and nadirs only.
5. Improvement on both: devices **announce capabilities**, so clients need not know the
   hardware in advance.

## 3. Terms

| Term | Meaning |
|---|---|
| **OFT** | Open FPV Timer: the project and ecosystem. |
| **Node** (OFTN) | One receiver that speaks the Node link (reference: ESP32-C5). Samples and timestamps; no detection. |
| **Timer** | One OFT network endpoint with **one timer clock**: compute running `oft-core`, plus its Nodes. |
| **Seat** | One watched frequency, usually one pilot. |
| **Adapter** | Bridge from the OFT Protocol to a Race Manager (RH plugin, LiveTime, Trackside, Grid). |
| **Race Manager** | The timing software: RotorHazard, LiveTime, FPVTrackside, GridFPV. |
| **OFT Protocol** | The Timer's network service (§6). |
| **Node link** | The binary link between a Node and its Timer (§5). |

## 4. Layers

| Layer | Runs on | Does | Talks |
|---|---|---|---|
| Node firmware | Each C5 | Tunes to its assigned frequency plan. Measures band power and noise per seat at about 1 kHz from I/Q samples. Timestamps on its own µs clock. Latches SYNC edges if wired. | Node link (§5) over USB-CDC or UART |
| `oft-core` | Timer | Maps Node clocks onto the timer clock. Assigns seats to Nodes. Runs detection (§8). Keeps crossing and sample ring buffers. Builds OFT messages. | In-memory API |
| Host shell | Timer | Serial and USB I/O, network stack, HTTP/WS, mDNS, config storage, Node flashing. | OFT Protocol (§6) |

### 4.1 Seat scheduling (in `oft-core`)

- If seats ≤ Nodes: **one seat per Node**, continuous dwell, no hopping. Most accurate.
- If seats > Nodes: seats are spread across Nodes, and each Node hops. Priority goes to even
  spacing and to keeping a seat on the same Node between heats.
- `/info` reports each seat's actual sample rate and Node assignment.
- With one shared gate antenna and a splitter, any Node can take any seat, so physical port
  order does not matter. Nodes are identified by chip id from their `Hello`.

**Pilots per Node (multi-pilot on one C5).** A single Node can watch several seats by
hopping, the way FPVGateC5MK does. This is a first-class feature, not a fallback:

- A Node's `Hello` reports `max_seats` (the C5 reference: 8). The `Plan` message carries up
  to 8 `{seat, freq}` pairs per Node.
- `/config` has `seats_per_node` (default: the Node's `max_seats`). The scheduler never puts
  more seats on a Node than that. For a single-Node Timer, the number of **enabled seats**
  is therefore the number of pilots on that Node.
- The cost is sample rate and settling: a Node sampling at 1 kHz split 4 ways gives each
  seat 250 Hz, and every hop costs a settling window flagged `post_hop`. Timing accuracy
  degrades roughly with the number of seats. Guidance: **1 seat for the best timing, up to
  4 for racing, up to 8 for practice or open flying.** `/info` reports each seat's actual
  `rate_hz` so clients can show this.
- The B1 single-pilot timer is the one-seat case of the same firmware; nothing changes in
  the protocol when a second pilot is added.

### 4.2 Clocks

- `oft-core` owns the **timer clock**: µs since the Timer booted, unsigned 64-bit.
- Each Node stamps in its own clock. The core maps every Node clock onto the timer clock:
  - **SYNC wire (preferred):** the Timer pulses one GPIO at 10–100 Hz, wired to every Node.
    Each Node reports the Node timestamp of every edge; the core fits offset and drift.
    Expect well under 0.1 ms (to verify). SYNC is independent of the data link, so it works
    with USB Nodes too.
  - **Ping fit (no SYNC wire):** periodic pings, keep lowest round trips, linear fit. Expect
    roughly 0.1–0.5 ms over USB (to verify). Fine for millisecond timing.
- **Lap intervals:** when one seat stays on one Node, intervals can come straight from that
  Node's clock with no mapping error. The core keeps Node timestamps internally and reports
  timer-clock times outward.

### 4.3 RF silence

The race band (5.645–5.945 GHz) overlaps 5 GHz Wi-Fi channels 149–165 (5.745–5.825 GHz).
Anything transmitting at the gate raises the noise floor the Nodes are measuring.

- Node firmware MUST be **receive-only**: no Wi-Fi association, scans, beacons or BLE.
- Timer images MUST ship with Wi-Fi and Bluetooth **off**. A setup hotspot, if offered, is
  2.4 GHz only and off during races.

## 5. Node link (Node ↔ Timer)

- Point-to-point: **one link per Node** over USB-CDC or UART (921600 baud–2 Mbaud).
- **COBS-framed binary with CRC-16.** Little-endian. Versioned.
- Bandwidth: one seat at 1 kHz × 2 bytes is about 2 kB/s. A Node hopping across 8 seats is
  about 16 kB/s. Both are small next to 921600 baud or USB full speed.

| Direction | Message | Contents |
|---|---|---|
| Node → Timer | `Hello` | chip id, firmware version, link protocol version, tunable range, max seats, features (`sync`, `iq_dump`) |
| Timer → Node | `Plan` | list of `{seat, freq_mhz}`, dwell and hop order, filter bandwidth, gain or attenuation |
| Node → Timer | `Samples` | seat, t0 (Node µs), dt, `int16[]` power in 0.1 dB, noise floor, flags (`clipped`, `post_hop`) |
| Node → Timer | `SyncEdge` | Node µs timestamp of a SYNC edge |
| Timer ↔ Node | `Ping` / `Pong` | Timer time, then Node time, for ping-fit clock mapping |
| Node → Timer | `Status` | temperature, hop errors, overruns, gain state |
| Timer → Node | `Reset`, `Identify` (blink LED), `Dfu` | maintenance |

Any receiver that speaks this link is a valid Node. Examples:

- **AD8318 front end:** the Timer reads its own ADC and presents an internal virtual Node
  with one seat, `freq: any`.
- **RX5808 adaptor:** a small MCU drives SPI tuning, reads the analog RSSI pin, and speaks
  the Node link.

### 5.1 Finding and flashing Nodes

- **USB Nodes:** the C5's built-in USB serial enumerates as `/dev/ttyACM*` with Espressif
  VID `0x303A`. A udev rule (Linux) or the host shell spots new ports, reads `Hello`, and
  compares firmware versions. The Timer resets the C5 into its ROM bootloader over USB and
  flashes with `esptool`. No extra wires.
- **UART Nodes:** ports are fixed by wiring. The Timer needs two extra GPIOs per Node, to
  **EN** and the **BOOT** strap pin (check the C5 datasheet for the pin), to enter the ROM
  bootloader, then runs `esptool --before no_reset`.
- `Dfu` on the Node link (reboot into the ROM bootloader from firmware) is reserved, so a
  UART Node could later be flashed without the BOOT wire.

## 6. OFT Protocol (Timer ↔ Adapter)

LAN only. HTTP/1.1 with JSON for control and catch-up, plus one WebSocket for live data.
JSON is the mandatory encoding; other encodings may be offered in `encodings` later.

### 6.1 Discovery

- mDNS service `_oft._tcp`. TXT: `id`, `fw`, `proto=1`, `seats`, `nodes`, `level`.
- DHCP by default. A static IP can be set via `/config`.
- Timers must support at least 2 simultaneous clients (4 recommended).

### 6.2 Capabilities

`/info` and the WebSocket `hello` carry the same `capabilities` object. A present key means
supported; an absent key means not supported. Unknown keys MUST be ignored. Vendor keys use
an `x-<vendor>-` prefix.

| Capability | Meaning | Fields |
|---|---|---|
| `crossings` | Timer detects crossings and emits `crossing` events; `/crossings?since=` works | `algorithms`, `replay` (crossings kept for catch-up), `fields` (optional crossing fields supported) |
| `samples.stream` | Live signal over the WebSocket | `rate_hz` (max per seat), `decimate` (supported factors) |
| `samples.history` | `/samples` returns past signal for a time window | `full_rate_s` (seconds kept at full rate), `reduced_rate_s`, `reduced_hz` |
| `config` | `/config` accepts writes | `persist`, `threshold_modes` (`auto`, `manual`), `min_lap_ms` |
| `time` | `/time` and clock info | `sync` (`ping`, `ptp`), `err_us` (current estimate) |
| `fw.update` | Timer can update its Nodes (and optionally itself) | `nodes` (`usb`, `uart`), `self` (bool) |
| `direction` | Crossings include direction | reserved |

**Conformance levels** are bundles of capabilities:

| Level | Requires | Grid features |
|---|---|---|
| **L1** | `crossings`, `config`, `time` | LivePasses, FrequencyMgmt, Calibration |
| **L2** | L1 + `samples.stream` | + SignalContext |
| **L3** | L2 + `samples.history` | + SignalRecovery (marshaling) |

Adapters only need L1. All reference builds aim for L3.

### 6.3 HTTP endpoints (prefix `/oft/v1`)

| Method | Path | Purpose |
|---|---|---|
| GET | `/info` | Timer id, `boot_id`, host type, protocol version, level, `capabilities`, firmware versions (Timer and each Node), Nodes (`[{id, chip, range_mhz, link}]`), seats (`[{seat, node, rate_hz}]`), `calibrated` |
| GET / PUT | `/config` | seats (`[{seat, freq_mhz, enabled}]`), `seats_per_node`, attenuation, threshold mode and values, `min_lap_ms`, network settings |
| GET | `/status` | uptime, temperature, link, per-Node state, clock-fit quality (residual µs), dropped samples, clients |
| GET | `/time` | timer clock now, in µs |
| GET | `/crossings?since=<seq>` | crossings after `seq`, for catching up after a reconnect |
| GET | `/samples?seat=&from=&to=` | signal history, for re-deriving a missed lap |
| POST | `/fw/nodes` | start a Node update (body: which Nodes, or `all`); progress in `/status` |
| GET | `/stream` | WebSocket upgrade for live data |

### 6.4 WebSocket stream

One JSON object per text frame. On connect the Timer sends `hello`:

```json
{
  "type": "hello",
  "proto": 1,
  "timer": "oft-3fa2",
  "boot_id": "9c1e",
  "time_us": 81234567,
  "level": "L3",
  "encodings": ["json"],
  "capabilities": {
    "crossings": { "algorithms": ["edge_mid"], "replay": 256, "fields": ["t_enter", "t_exit", "peak", "snr"] },
    "samples.stream": { "rate_hz": 1000, "decimate": [1, 2, 5, 10, 20] },
    "samples.history": { "full_rate_s": 3600, "reduced_rate_s": 0, "reduced_hz": 0 },
    "config": { "persist": true, "threshold_modes": ["auto", "manual"], "min_lap_ms": true },
    "time": { "sync": ["ping"], "err_us": 0 },
    "fw.update": { "nodes": ["usb"], "self": false }
  }
}
```

The client subscribes. Each `sub` replaces the previous one:

```json
{"type":"sub","crossings":{"since":41},"samples":{"seats":"all","decimate":1},"status":true}
```

Subscribing to a capability the Timer did not announce returns
`{"type":"error","code":"unsupported","msg":"..."}`.

The Timer then sends:

```json
{"type":"samples","seat":0,"t0":81234000,"dt_us":1000,"p":[-912,-910,-640,-235],"nf":-920}

{"type":"crossing","seq":42,"seat":0,"t_enter":81230120,"t_exit":81262480,
 "t_mid":81246300,"peak":-235,"snr":685,"flags":[]}

{"type":"status","uptime_s":3600,"temp_c":41,"dropped":0,"clock_err_us":40}
```

- Power values (`p`, `nf`, `peak`) are **tenths of a dB** as integers: relative dB unless
  `/info` says `"calibrated":true`, then tenths of a dBm. `snr` is tenths of a dB.
- Samples are batched every 20–50 ms. `decimate` lowers the rate.
- `crossings.since` replays buffered crossings after that `seq` (reconnect catch-up).
- A binary sample frame is reserved for v2 (offered via `encodings`).

### 6.5 Reliability and security

- Crossings carry a monotonic `seq` per `boot_id`. A `boot_id` change means the Timer
  rebooted; clients reset their `seq` tracking.
- v1 has no authentication and assumes a trusted race LAN. An optional bearer token is
  reserved.

## 7. Time across Timers

- Race Managers should compute laps from Timer timestamps only. Arrival time affects only
  how fast a crossing shows up (target: on screen within ~500 ms of the crossing, dominated
  by waiting for the signal to fall after the peak).
- For ordering and multi-gate splits, the client aligns each Timer via `/time` (NTP-style,
  keeping the lowest round trip). Expect about 1 ms or better on a quiet wired LAN.
- **Grid in-process host:** Node clocks map onto Grid's own clock directly. No network hop.

## 8. Detection (normative, implemented once in `oft-core`)

Algorithm id: `edge_mid`.

- The core keeps a smoothed power trace per seat. It drops or interpolates samples flagged
  `post_hop`, and tracks the **noise floor**.
- **Threshold modes:**
  - `auto`: enter at floor + `snr_enter` dB (default 15), exit at enter − `hysteresis` dB
    (default 5).
  - `manual`: absolute enter and exit levels (RotorHazard-style EnterAt/ExitAt).
- A **crossing** spans enter to exit. Timers MUST report `t_enter`, `t_exit` and `t_mid`.
- **`t_mid` is the lap timestamp.** It is the midpoint of the times the smoothed trace
  crosses the **edge level** on the rise and on the fall. The edge level defaults to halfway
  in dB between the noise floor and the peak. This is robust to the dip in the middle of the
  pulse caused by the quad antenna's axial null (RotorHazard's plateau midpoint is not).
- `min_lap_ms` suppresses a second crossing within that window.
- Optional `flags`: `clipped`, `low_snr`, `hop_artifact`, `truncated`.
- Implementation notes from `oft-core` (verified against synthetic passes, see the `oft`
  repo): keep ~128 samples of pre-trigger history so the rising edge is found even when the
  edge level is below the enter level; clamp the edge level to no lower than the exit level;
  subtract the smoothing filter's group delay (2^shift − 1 samples for the EMA) from `t_mid`;
  track the noise floor in fixed point, only while the signal is well below the enter level,
  and faster downwards than upwards. With these, `t_mid` lands within ~2 ms of the true pulse
  centre on clean, dipped and clipped synthetic passes at 1 kHz.

## 9. Reference builds

All builds use the same Node firmware and `oft-core`.

| Build | Timer host | Nodes and link | Network | ~USD | Use |
|---|---|---|---|---|---|
| **B0: bench dongle** | Grid in-process, or `oftd` on a laptop | 1–2 XIAO ESP32-C5 on USB | none, or localhost | 7–14 | Development, testing, a laptop parked by the gate |
| **B1: single-pilot gate box** | `oft-hub` on a **Waveshare RP2350-POE-ETH** (RP2350A + W6300 + PoE module, one board). Alt: W5500-EVB-Pico2 + 802.3af splitter | 1 XIAO ESP32-C5 on a hardware UART, with SYNC | Ethernet + PoE | 38 (actual) | **First OFT test (RaceGOW).** Parts in [hbom-b1-single-pilot.md](hbom-b1-single-pilot.md) |
| **B2: multi-pilot gate box (MCU)** | `oft-hub` on a Pico 2 + W5500 | 2–8 C5s: 2 on hardware UARTs, up to 6 more on PIO UARTs, shared SYNC | Ethernet + PoE | 30 + ~8 per Node | 8-pilot gate, low power, instant boot |
| **B3: Raspberry Pi Timer** | `oftd` on a Pi 4/5 + PoE HAT | Up to 8 C5s on USB (powered hub), shared SYNC from one Pi GPIO | Ethernet + PoE | 80–120 | **First target.** Easiest to develop on; full-session history; can also run Grid or RH as a standalone timer |
| **B4: AD8318 node** | `oft-hub` on a Pico 2 | AD8318 on the Pico ADC as a virtual Node, one seat, any frequency | Ethernet + PoE | 35–45 | Channel-agnostic single pilot (fallback) |
| **B5: carrier board** | `oftd` on a Pi (separate, or mounted as a HAT) | 8 C5 modules + on-board USB hub chip, **one USB link** to the Pi, SYNC routed on the board | Ethernet + PoE (via the Pi) | TBD | **Clean end product** for B3. See §9.2 |

### 9.1 B3 detail: 8 Nodes on a Pi

**Pi UARTs** (PL011-class; usable after enabling overlays):

| Model | UARTs on the 40-pin header | Notes |
|---|---|---|
| Pi 4 | UART0 (GPIO14/15), UART2 (0/1), UART3 (4/5), UART4 (8/9), UART5 (12/13), plus mini-UART1 | UART0 is used by Bluetooth unless `disable-bt`. GPIO0/1 are the HAT ID EEPROM pins, which can clash with a PoE HAT. Mini-UART baud follows the core clock. Realistic: **4**. |
| Pi 5 | UART0–4 via RP1 (GPIO14/15, 0/1, 4/5, 8/9, 12/13), plus a separate debug UART connector | Same GPIO0/1 HAT caveat. Realistic: **4–5**. |

So UART alone does not reach 8. **Use USB for Node data:**

- 8 C5s on a **powered USB hub** (or two 4-port hubs). Each Node is a `ttyACM` port. Total
  data is under 150 kB/s even with every Node hopping.
- Gives auto-discovery and flashing for free (§5.1).
- Add **one SYNC wire** from a Pi GPIO to every Node (buffered fan-out if needed) for
  sub-0.1 ms clock mapping. Without it, ping fit over USB is still fine for ms timing.
- A loose USB hub is fine on the bench but bulky in a gate box. The **carrier board** (B5,
  §9.2) replaces it.
- UART stays the transport for the MCU builds (B1, B2), where it is the natural fit.

**Power:** a Pi 4 (~3–6 W) plus 8 C5s (est. 0.5–1 W each, to be measured) may exceed
802.3af (12.95 W at the device). Plan for **802.3at** on 8-Node B3 builds, or power the
USB hub locally.

**SD card:** use a read-only root filesystem with a separate writable data partition, so
pulling power at the field does not corrupt the card. Boot takes about 20–30 s.

### 9.2 B5 detail: carrier board and Pi HAT

One board holds up to 8 C5 modules and presents them to the Pi as **one USB connection**.
Software sees the same 8 `ttyACM` Nodes as B3, so nothing above the Node link changes.

**On the board:**

- Up to 8 C5 modules (a variant with an antenna connector, e.g. a "-U" module; check
  availability). Slots may be populated partly; the Timer finds whatever enumerates.
- **USB hub chip(s)** with 8 downstream ports (e.g. two 4-port hub ICs, or a 7-port plus one;
  part TBD). One upstream port to the Pi.
- **SYNC** routed from one input pin to every C5, buffered.
- Flashing uses the C5's USB reset into the ROM bootloader, so no EN/BOOT wires are needed
  (§5.1). Per-module status LEDs for `Identify`.
- **RF:** either one SMA input into an on-board 8-way splitter (every seat on the same gate
  antenna, splitter loss doubles as attenuation), or one connector per module.
- Power for all C5s from the board, not through the Pi's USB ports.

**Two form factors, same circuit:**

| Variant | How it connects | Pros | Cons |
|---|---|---|---|
| **Standalone carrier** | USB cable to any Pi or laptop | Works with any host, including a laptop for B0-style development | One more box and cable |
| **Pi HAT** (NuclearHazard style) | Mounts on the 40-pin header. SYNC on a GPIO pin. USB upstream via a short right-angle jumper to a Pi USB port, or **pogo pins onto the USB test pads** of a Pi Zero 2 | One compact unit; the board can take 2–5S or PoE input and power the Pi through the header | The 40-pin header carries no USB, so the USB path needs the jumper or pogo pins |

A third HAT option skips USB: an RP2350 on the HAT collects the 8 C5 UARTs (as in B2) and
passes everything to the Pi over **one UART**, with RH-style GPIO reset/BOOT for flashing.
It is the closest copy of NuclearHazard, but adds an MCU and a firmware layer between the
Nodes and the Pi. Keep it as a fallback if the USB path proves awkward.

### 9.3 Shared details

- **Antenna:** a stubby in a foil-lined cup, or a PCB patch, on the top bar looking down.
  With several Nodes, one gate antenna into an N-way splitter keeps every seat on the same
  beam, and the splitter loss doubles as attenuation.
- **Box:** 3D-printed, with a PVC clamp (21.3 / 26.7 mm OD).

**Max n:** the protocol allows up to 255 seats and Nodes. B2 tops out at 8 Nodes (UART
count). B3 is limited by USB. The practical limit is about 8 simultaneous analog pilots per
gate (spectrum), so **8 is the design target**.

### 9.4 History on MCU Timers

Full-rate history for 8 seats is 16 kB/s (8 × 1000 × 2 bytes), so the Pico 2's 520 KB RAM
could hold only about 15 s alongside everything else. MCU Timers keep **full rate around
each crossing, plus a 100 Hz trace**: 8 seats × 100 Hz × 2 bytes is 1.6 kB/s, so about
2 minutes fits in 200 KB. Linux Timers keep full rate for the whole session. Each Timer
reports what it keeps in `samples.history`.

## 10. Code layout (proposal)

```
oft/
  spec/                 this document, Node-link + OFT Protocol schemas
  node-c5/              ESP-IDF C firmware (GPL-3.0, esp-sdr base)
  core/                 oft-core: Rust no_std (+alloc) — clocks, scheduler, detection, buffers, protocol types
  host-linux/           oftd: tokio + axum, serial/USB Nodes, mDNS, Node flashing
  host-rp2350/          oft-hub: embassy-rp + embassy-net-wiznet, PIO UARTs
  tools/                recorder/replayer (capture Node-link streams, replay into core for tests)
```

- Grid depends on `core/` directly (in-process host for B0) and gets an `oft` adapter in
  `crates/adapters` for networked Timers.
- The recorder and replayer make detection testable without flying, matching Grid's adapter
  philosophy ("pure translators, replay-testable").

## 11. Open questions

1. ESP-IDF/C on the Node plus Rust everywhere else, or Rust on the C5 (esp-idf-sys) for one
   language end to end?
2. How accurate is ping fit over USB in practice? Is a SYNC wire required for B3?
3. Should a Node offer optional on-Node detection, for hosts too small to run the core?
   Current answer: no, keep one implementation.
4. Is JSON fast enough on the RP2350 for 8 seats × 1 kHz, or does v1 need binary sample
   frames?
5. Is power calibration (dBm) worth defining, or should values stay relative?
6. Is an ESP32-P4 (built-in Ethernet MAC) worth a Timer host target?
7. Should OFT live in its own repo, separate from Grid?
8. Will other Race Managers (RotorHazard plugin, FPVTrackside, LiveTime) adopt it? If so,
   keep L1 tiny.
9. Does a Timer need race start/stop, or does it always emit and let the Race Manager
   filter? Leaning: always emit.
10. Verify LapRF `rtcTime` units and the C5 BOOT strap pin before relying on either.
11. B5 carrier: which hub IC(s), which C5 module, on-board splitter or one connector per
    module, and total power for 8 C5s plus a Pi (802.3af vs 802.3at)?
12. B5 HAT: right-angle USB jumper vs Zero 2 pogo pins vs the RP2350-over-UART option.
