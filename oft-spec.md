# Open FPV Timer (OFT) — draft spec v0.10

**Status:** idea draft, 2026-11-22. Nothing here is built or final.

**Changes from v0.9:**

- **Several Nodes on one Timer** (§4.1, §6.3): the first multi-Node Timer exists (the RP2350
  firmware, up to four wired Nodes). Seats are balanced over the Nodes that are answering,
  automatically, as §4.1 always said; switching a Node off and pinning a seat are still to
  come.
- `/status` gains `nodes[]`: each Node's link slot, id, whether it is connected, its
  temperature, clock and link counts. The Node fields `/status` already had stay, and now
  sum the Nodes up: `node_connected` is true only if every wired Node is, the clock fields
  are the worst Node's, `temp_c` the hottest, the `link` counts added together.
- `/info` `nodes[]` gains `slot` and `connected`. `seats[].node` is `null` for a seat no
  Node is serving.
- `/pins` (§6.3) **changed shape**: the links are a list, one per Node,
  `{"nodes":[{"tx":4,"rx":5},{"tx":0,"rx":1}],"sync":6,"en":7,"boot":8}`. How many Nodes the
  Timer drives is how many links are listed. `capabilities.pins.max_nodes` says how many it
  can. SYNC, EN and BOOT are one wire each, shared by every Node.

**Changes from v0.8:**

- **Control** (§6.2, §6.3, §6.6): one client at a time may change a Timer. A client claims
  control on its stream; while a claim holds control, the Timer refuses every write that
  does not carry the holder's key (423). Claims stand for as long as their stream is open,
  the first one holds control and later ones wait. `GET /control` lists them, and the
  Timer's own page, and nothing else, can hand control to any of them with
  `POST /control`. A holder whose stream drops keeps control for 10 s and resumes with its
  key. With no claims, anyone may write, as before.
- Every stream now gets a `control` message straight after `hello`, subscribed or not.
- `/status` carries `config_rev`, which changes whenever the config or its saved state
  does, and `control`, the holder. Clients that show settings re-read `/config` when
  `config_rev` changes.

**Changes from v0.7:**

- **Level units** (§5, §6.3, §6.4, §8): a Node says what its level numbers measure, and
  the Timer passes it on as `nodes[].level` in `/info` (`{"unit":"dB","scale":0.1}` or
  `{"unit":"mV","scale":1}`). Samples, floor, thresholds, `peak` and `snr` are all in that
  unit. Before, every level was called tenths of a dB, which was untrue for a Node that
  reads an RX5808's signal-strength pin. Clients must read the unit instead of assuming
  dB. RotorHazard-style EnterAt / ExitAt levels map onto `/config` as raw levels in the
  Node's unit, set as `manual` thresholds.
- `fw.update.node_image` names the kind of firmware file `/fw/node` takes when it is not
  ESP32 firmware.
- `/status` seats carry `node`, the id of the Node serving the seat.
- **Dropped:** the idea of a RotorHazard plugin that serves an RH timer as an OFT Timer
  (was open question 18). RotorHazard hardware becomes an OFT Timer by running OFT
  firmware on its Node and `oftd` on its Pi, with no RotorHazard involved.
- The rh-oft plugin now sends each seat its own thresholds and reads level units (open
  question 13).

**Changes from v0.6:**

- **Node wiring pins** (§6.3): `GET`/`PUT /pins` choose which of the Timer's pins carry a
  wired Node's signals (`capabilities.pins`), applied at the next start. One firmware then
  covers boards wired differently. The Node's own SYNC pin is a Node setting (§5).
- **Nodes name their chip** (§5): an optional chip name at the end of `Hello`, which the
  Timer shows as the node's `chip` in `/info`. Nodes that send none are ESP32-C5s.
- **Future idea**: a RotorHazard plugin that serves an RH timer as an OFT Timer (dropped
  in v0.8).

**Changes from v0.5:**

- **Pass window** (§8): crossings that start within `pass_window_ms` of the first one are
  one pass, and only the strongest is reported, once the window has closed. For tracks
  that fly close by the gate just before going through it. New `/config` field
  `pass_window_ms` (default 0 = off), announced as `capabilities.config.pass_window_ms`.

**Changes from v0.4:**

- **`seats_per_node` is gone** from `/config` and from `capabilities.config`. How seats are
  spread over Nodes is the Timer's job, not a number the user sets (§4.1). Timers accept
  the field from older clients and ignore it; they do not send it. Clients must not
  require it in a `/config` reply.
- **Planned, not built** (§4.1, open question 16): switching a Node off, and pinning a seat
  to a Node.

**Changes from v0.3:**

- **Per-seat thresholds.** A seat in `/config` may carry its own `threshold`; the top-level
  `threshold` is the default for seats without one (§6.3, §8). Timers that support this
  announce `capabilities.config.seat_thresholds`. A v0.3 `PUT /config` body is still valid.
- **Saved settings and network** (§6.3): `POST`/`DELETE /config/save` keep or forget the
  power-on config (`capabilities.config.persist`); `GET`/`PUT /network` set DHCP or a fixed
  address (`capabilities.network`), applied at the next start; `POST /restart`.
  `/status` gains `timer_temp_c` beside the Node's `temp_c`.
- **Exit hold-off** (§8): a crossing ends only after the signal has stayed below the exit
  level for `exit_hold_ms` (default 100), so a pass with several lobes is one crossing.
  New `/config` field `exit_hold_ms`, announced as `capabilities.config.exit_hold_ms`.
  Found on the first hardware test: hand-carried passes had 10–15 dB dips of 20–40 ms.
- **Holes in the sample stream** are bridged by interpolation in the core (§8), and the
  rising edge is searched from the enter sample, not from the start of the history.
- **Discovery** (§6.1) is spelled out: service type, instance name, TXT keys and their
  values. `oftd` now advertises.

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
- **Pilots per Node** is spelled out in §4.1 with a `seats_per_node` config knob (removed in v0.5).
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
- **Open:** the spec is published under CC BY 4.0 (`LICENSE`). Node firmware is GPL-3.0
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

The Timer decides which Node watches which seat. It is not a user setting: the Timer
knows the Nodes and the channels, and the goal is always the best sample rate for every
pilot.

- If seats ≤ Nodes: **one seat per Node**, continuous dwell, no hopping. Most accurate.
- If seats > Nodes: seats are spread across the Nodes, and each Node hops. What costs
  sample rate is the number of **tuning positions** a Node needs, not its number of seats
  (channels up to 40 MHz apart share one position), so the Timer balances positions:
  neighbouring channels go to the same Node. Second priority: keep a seat on the same Node
  between heats.
- A Node that stops answering gets no seats; the others take them over.
- `/info` reports each seat's actual sample rate and Node assignment.
- With one shared gate antenna and a splitter, any Node can take any seat, so physical port
  order does not matter. Nodes are identified by chip id from their `Hello`.

**Pilots per Node (multi-pilot on one C5).** A single Node can watch several seats by
hopping, the way FPVGateC5MK does. This is a first-class feature, not a fallback:

- A Node's `Hello` reports `max_seats` (the C5 reference: 8). The `Plan` message carries up
  to 8 `{seat, freq}` pairs per Node.
- The scheduler never puts more seats on a Node than its `max_seats`. For a single-Node
  Timer, the number of **enabled seats** is the number of pilots on that Node.
- The cost is sample rate and settling: a Node sampling at 1 kHz split 4 ways gives each
  seat 250 Hz, and every hop costs a settling window flagged `post_hop`. Timing accuracy
  degrades roughly with the number of seats. Guidance: **1 seat for the best timing, up to
  4 for racing, up to 8 for practice or open flying.** `/info` reports each seat's actual
  `rate_hz` so clients can show this.
- The B1 single-pilot timer is the one-seat case of the same firmware; nothing changes in
  the protocol when a second pilot is added.

**Multi-Node Timers.** The RP2350 firmware drives up to four Nodes (`oft-core`'s `sched`
and `Hosts`); `oftd` still drives one and gives it every enabled seat.

- **Balancing is automatic** as described above, and re-run whenever the seats, the
  channels or the set of working Nodes change. A Node counts as working while the Timer
  hears from it; one silent for 3 s loses its seats to the others and takes seats back
  when it returns. A seat that stays on its Node and frequency is not disturbed by a
  re-run: its detector, floor and sample stream carry on. The balance: no Node gets more
  tuning positions than it must, then no Node more seats than it must, then as few seats
  as possible change Node.

Still planned (not built):

- **A Node can be switched off.** `/config` gains `nodes: [{ "id": "<chip id>", "enabled":
  true }]`. A disabled Node gets no seats (for a Node that misbehaves, or to compare
  Nodes). Nodes not listed are enabled. `/info` `nodes[]` shows `enabled` and whether the
  Node is answering.
- **A seat can be pinned.** A seat in `/config` may carry `"node": "<chip id>"`. Pinned
  seats go where they are told; the rest are balanced around them. Pinning every seat is
  fully manual assignment, so there is no separate automatic/manual switch. A pin to a
  Node that is disabled or missing is refused with a reason.
- **Reporting is unchanged:** `/info` `seats[]` already gives each seat's `node` and
  `rate_hz`, which is how race software shows the result of the balancing.
- Announced as `capabilities.config.nodes` (the switch) and `capabilities.config.seat_node`
  (pinning), so clients offer them only where they exist.

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
| Node → Timer | `Hello` | chip id, firmware version, link protocol version, tunable range, max seats, features (`sync`, `iq_dump`, `dfu`, `level_mv`: its levels are millivolts, not tenths of a dB, §6.4), chip name (optional, e.g. `esp32c5`, `stm32f1-rx5808`; shown as the node's `chip` in `/info`) |
| Timer → Node | `Plan` | list of `{seat, freq_mhz}`, dwell and hop order, filter bandwidth, gain or attenuation |
| Node → Timer | `Samples` | seat, t0 (Node µs), dt, `int16[]` power in the Node's level unit, noise floor, flags (`clipped`, `post_hop`) |
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

- A Timer advertises the DNS-SD service `_oft._tcp` over mDNS (`_oft._tcp.local.`), on the
  port that serves the OFT Protocol.
  - **Instance name:** the Timer `id`, e.g. `oft-3fa2._oft._tcp.local.`.
  - **TXT keys:** `id` (same as `/info`), `fw` (Timer firmware version), `proto=1`, `seats`
    (number of enabled seats), `nodes` (number of Nodes that have said hello), `level`
    (`L1`–`L3`). Unknown keys MUST be ignored.
  - The Timer re-announces when `seats` or `nodes` change, and sends a goodbye on a clean
    shutdown. TXT is a hint for listing Timers; `/info` is the source of truth.
  - `oftd` advertises by default; `--no-mdns` turns it off.
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
| `network` | `/network` sets the Timer's address | `static` (bool) |
| `pins` | `/pins` sets which Timer pins the wired Nodes are on | `max_nodes` (how many Node links the Timer has) |
| `config` | `/config` accepts writes | `persist` (`/config/save` works), `threshold_modes` (`auto`, `manual`), `min_lap_ms`, `seat_thresholds` (seats may carry their own `threshold`; absent on v0.3 Timers), `exit_hold_ms` (the field is accepted), `pass_window_ms` (the field is accepted) |
| `time` | `/time` and clock info | `sync` (`ping`, `ptp`), `err_us` (current estimate) |
| `fw.update` | Timer can update its Nodes (and optionally itself) | `nodes` (`usb`, `uart`), `self` (bool), `node_image` (optional: the kind of file `/fw/node` takes when it is not ESP32 firmware, e.g. `stm32f1`) |
| `control` | One client at a time may write (§6.6): `control` messages on the stream, `/control` | none |
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
| GET | `/info` | Timer id, `boot_id`, host type, protocol version, level, `capabilities`, firmware versions (Timer and each Node), Nodes (`[{id, chip, fw, range_mhz, max_seats, level, link}]`; `level` is the unit of that Node's levels, §6.4), seats (`[{seat, node, rate_hz}]`), `calibrated` |
| GET / PUT | `/config` | seats (`[{seat, freq_mhz, enabled, threshold?}]`), attenuation, `threshold` (mode and values; the default for every seat), `min_lap_ms`, `exit_hold_ms`, `pass_window_ms`, network settings |
| GET / POST / DELETE | `/config/save` | With `capabilities.config.persist`. `PUT /config` alone lasts until the next restart. `POST` stores the config in use as the power-on config; `DELETE` forgets it (built-in defaults at the next start). All three answer `{"saved": bool, "current_is_saved": bool}` |
| GET / PUT | `/network` | With `capabilities.network`. Body `{"mode":"dhcp"}` or `{"mode":"static","address":"192.168.1.50","prefix":24,"gateway":"192.168.1.1","dns":"..."}` (gateway and dns optional). Stored at once, used from the next start. `GET` answers `{"saved":{...},"using":"dhcp"|"static"|"dhcp (recovery jumper)","now":{"address","prefix","gateway"},"restart_needed":bool}`. A Timer with a fixed address needs a documented way back to DHCP without the network |
| GET / PUT | `/pins` | With `capabilities.pins`. For Timers whose Nodes are wired to GPIO pins. Body: the pin (GPIO number) for each signal, `{"nodes":[{"tx":4,"rx":5}],"sync":6,"en":7,"boot":8}`. `nodes` has one serial link per Node, first Node first, and its length is how many Nodes the Timer drives (1 to `capabilities.pins.max_nodes`); `tx` is the Timer's transmit (to the Node's RX). `sync`, `en` and `boot` are one wire each, shared by every Node. Stored at once, used from the next start; a body the hardware cannot do is refused with 400 and a reason. `GET` answers `{"saved":{...},"using":{...},"defaults":{...},"choices":{"nodes":[{"tx":[...],"rx":[...]}, ...],"out":[...]},"restart_needed":bool}`; `choices.nodes[k]` lists the pins the k-th link may use (links differ: some are hardware UARTs with fixed pins) and `choices.out` the pins allowed for `sync`, `en` and `boot`. Clients should keep this out of everyday view: it only changes when a board is wired differently |
| GET / POST | `/control` | With `capabilities.control` (§6.6). `GET` lists the claims; `POST` hands control to one of them or frees it |
| POST | `/restart` | Restart the Timer (202, then the connection drops) |
| GET | `/status` | uptime, temperature (`temp_c` Node, `timer_temp_c` Timer), link, clock-fit quality (residual µs), dropped samples, `nodes[]` (per Node: `slot`, `id`, `connected`, `temp_c`, `clock_synced`, `clock_source`, `clock_err_us`, `drift_ppm`, `link`; with several Nodes the top-level Node fields sum these up: the worst clock, the hottest, counts added, `node_connected` only if all are), clients, `config_rev` (a number that changes whenever `/config` or its saved state changes; it restarts with the Timer), `control` (the holder as `{"id", "name"}`, or `null`; §6.6) |
| GET | `/time` | timer clock now, in µs |
| GET | `/crossings?since=<seq>` | crossings after `seq`, for catching up after a reconnect |
| GET | `/samples?seat=&from=&to=` | signal history, for re-deriving a missed lap |
| POST | `/fw/nodes` | start a Node update (body: which Nodes, or `all`); progress in `/status` |
| GET | `/stream` | WebSocket upgrade for live data |

**`/config` thresholds.** The top-level `threshold` applies to every seat that does not
carry its own. A seat's optional `threshold` has the same shape and overrides it for that
seat only:

```json
{
  "seats": [
    { "seat": 0, "freq_mhz": 5658, "enabled": true },
    { "seat": 1, "freq_mhz": 5732, "enabled": true,
      "threshold": { "mode": "manual", "enter": -700, "exit": -760 } }
  ],
  "threshold": { "mode": "auto", "snr_enter": 150, "hysteresis": 50 },
  "min_lap_ms": 2000,
  "exit_hold_ms": 100,
  "pass_window_ms": 0
}
```

- On `PUT`, a seat `threshold` that is absent or `null` means "use the top-level one". `PUT`
  replaces the whole config, so a body without seat thresholds (any v0.3 client) clears them.
- `GET` returns a seat's `threshold` only when that seat has its own.
- `status.seats[].enter` / `exit` report the levels each seat is actually using.
- Threshold values (`snr_enter`, `hysteresis`, `enter`, `exit`) are integers in the level
  unit of the Node serving the seat (§6.4): 150 is 15 dB on a Node that reports dB and
  150 mV on one that reports millivolts. A client that copies a config from one Timer to
  another must check that the units match.
- Clients MUST NOT send seat thresholds unless the Timer announces
  `capabilities.config.seat_thresholds`.

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
    "config": { "persist": true, "threshold_modes": ["auto", "manual"], "min_lap_ms": true, "seat_thresholds": true },
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

{"type":"status","uptime_s":3600,"temp_c":41,"timer_temp_c":38,"dropped":0,"clock_err_us":40}
```

- **Level units.** Every level is an integer in the unit of the Node that measured it:
  samples (`p`, `nf`), `status.seats[]` (`rssi`, `floor`, `enter`, `exit`), crossings
  (`peak`, `snr`) and the thresholds in `/config`. `/info` gives the unit per Node:

  ```json
  "nodes": [{ "id": "10bda3feffc8", "chip": "esp32c5", "level": { "unit": "dB", "scale": 0.1 }, ... }]
  ```

  Multiply a level by `scale` and label it with `unit` to show it. A seat's Node is
  `status.seats[].node` (the Node's `id`; `null` while no Node serves the seat). A Node missing `level`, or a Timer with no Node
  yet, means `dB` at `0.1`.
  - `"dB"`, scale `0.1`: tenths of a dB. Relative to the Node's own full scale unless
    `/info` says `"calibrated":true`, then tenths of a dBm. Differences are real dB.
  - `"mV"`, scale `1`: millivolts on a receiver's analogue signal-strength output (an
    RX5808's RSSI pin). It rises with signal but not as a straight line in dB, and it
    flattens near the top, so differences are millivolts and nothing more. Levels from
    two such Nodes compare only roughly, and not at all with a dB Node.
  - Other units may be added; a client shows any unit it does not know as given.
  - `snr` is `peak` minus the noise floor in the same unit. The name is kept; it is a
    signal-to-noise ratio only when the unit is dB.
  - Clients must not do dB arithmetic (ratios, averaging in linear power, comparing
    Timers) on a unit other than `"dB"`.
- Samples are batched every 20–50 ms. `decimate` lowers the rate.
- `crossings.since` replays buffered crossings after that `seq` (reconnect catch-up).
- A binary sample frame is reserved for v2 (offered via `encodings`).

### 6.5 Reliability and security

- Crossings carry a monotonic `seq` per `boot_id`. A `boot_id` change means the Timer
  rebooted; clients reset their `seq` tracking.
- v1 has no authentication and no encryption, and assumes a trusted race LAN: everything
  is plain HTTP and WebSocket, meant to stay on the local race network. Anyone who can
  reach the Timer on that network can read everything it serves and, with a little effort,
  change it. Keep the Timer off networks that strangers can join, and do not forward its
  port to the internet. An optional bearer token is reserved.
- Control (§6.6) does not change that. It is a technical control that keeps well-behaved
  clients from undoing each other's settings, not a security measure.

### 6.6 Control: one writer at a time

With `capabilities.control`. Any number of clients may read and stream. Writes are every
request under `/oft/v1` that is not a `GET`, except `POST /control`. Without this, two
clients that both write `/config` undo each other's settings, since a `PUT` replaces the
whole config.

**Claims.** A client that means to write says so on its stream, with a name for people to
read (1 to 32 printable ASCII characters; the Timer drops `"`, `\` and anything else):

```json
{"type":"control","claim":"RotorHazard"}
{"type":"control","claim":"RotorHazard","key":"9f3a61c2"}
{"type":"control","release":true}
```

- A claim stands until its stream closes or it sends `release`. One claim per stream; a
  second `claim` on the same stream renames it.
- At most one standing claim **holds** control. A claim made while nobody holds control
  gets it, so the client that claims first is the writer. A claim made while another
  holds it waits. A client has no way to take control from another: only the person at
  the Timer's page moves it (below).
- When the holder's claim ends, control passes to the claim that has stood longest. With
  no claims left, nobody holds control.
- **A dropped stream.** If the holder's stream closes without `release`, its claim stands
  for 10 more seconds and keeps control, and its key keeps working for writes. A `claim`
  that carries the `key` of a standing claim takes that claim up on the new stream, with
  the same id, key and place, from whichever stream had it before (the Timer may not have
  noticed yet that the old one is dead). After 10 s without that, the claim ends. A `key`
  that matches no standing claim is ignored, and the message is an ordinary new claim. A
  waiting claim ends as soon as its stream closes.
- A stream that only claims and never sends `sub` is a normal, long-lived stream. Both
  WebSocket ping frames and `{"type":"ping"}` are answered, so a client can tell a dead
  stream by sending one every few seconds.
- A Timer keeps a limited number of claims (at least 4). A claim over the limit is
  answered with `{"type":"error","code":"control_full","msg":"..."}`. A Timer may also
  limit how many streams are open at once (the RP2350 Timer: 4) and close one over the
  limit with WebSocket code 1013.

After `hello`, and again whenever any claim or the holder changes, the Timer tells every
stream where things stand:

```json
{"type":"control","holder":{"id":3,"name":"RotorHazard"},"claim":5}
{"type":"control","holder":{"id":3,"name":"RotorHazard"},"claim":3,"key":"9f3a61c2"}
{"type":"control","holder":null,"claim":null}
```

`holder` is the claim that holds control. `claim` is the id of this stream's own claim, or
`null`. `key` is present only on the holder's stream. Claim ids are not reused within one
`boot_id`.

**Writes.** While a claim holds control, a write must carry the holder's key in the
`OFT-Control` request header. Any other write is refused with `423` and
`{"error":"controlled by RotorHazard"}`, and changes nothing. While nobody holds control,
writes need no key and one that carries a key is accepted all the same. A holder that
gets a `423` has lost control and learns the rest from its stream.

**Choosing the writer.** When the wrong client holds control (clients connected in the
wrong order, or settings need a change by hand), the person running the Timer puts it right
on the Timer's own page. `POST /control` is for that page alone:

| Method | Path | Body | |
|---|---|---|---|
| GET | `/control` | | `{"holder": 3, "claims": [{"id": 3, "name": "RotorHazard", "holds": true, "connected": true}, {"id": 5, "name": "Timer page", "holds": false, "connected": true}]}`, claims oldest first; `holder` is an id or `null`; `connected` is false for a holder whose stream has dropped and may still come back |
| POST | `/control` | `{"grant": 5}` | Control moves to claim 5; the claim that held it waits. `404` if there is no such claim. Answers as `GET` |
| POST | `/control` | `{"grant": null}` | Nobody holds control, so anyone may write. It stays that way until a new claim or another grant; the standing claims wait. Answers as `GET` |

`POST /control` needs no key: it is the way back in when the holder is the wrong one. The
Timer accepts it only from a page it served itself: the request must carry an `Origin`
header that names the same host and port as its `Host` header, which a browser adds to
every `POST` and a page from anywhere else cannot fake. Anything else gets `403`. A body
without `grant` gets `400`. The page takes control for itself the same way: it makes a
claim and grants it.

**Not security.** Control is a technical control between clients that mean well. It does
not stop someone on the race network who means harm (§6.5):

- The holder's key travels in plain HTTP, in its `control` messages and in the header of
  every write. Anyone who can see that traffic can copy the key and write as the holder.
- A program can set the `Origin` header by hand and use `POST /control` as if it were the
  Timer's page.
- Nothing proves who a claim is: any client can claim under any name, `RotorHazard`
  included.

All of this needs access to the local network the Timer is on. What control does stop is
the ordinary case: two honest clients, or a forgotten browser tab, changing settings
under the one that is running the race.

**What clients do.**

- A client that sets a Timer up on its own (race software) claims when it connects, writes
  only while it holds control or nobody does, and tells its user when another client
  holds it. When another client stops holding control, it sends its settings again, since
  they may have been changed. After a reconnect it claims again with its key.
- The Timer's page claims only when the person at it asks to take control, and releases
  when they are done or when control goes elsewhere, so it is not left waiting in line to
  inherit control from race software.
- A name should tell two installations apart, e.g. `RotorHazard pi-timer`.
- A client other than the Timer's page never sends `POST /control`.
- A client that only watches never claims.
- Every client that shows settings follows `config_rev` in `status`.

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
  - `auto`: enter at floor + `snr_enter` (default 150 counts: 15 dB), exit at enter −
    `hysteresis` (default 50: 5 dB). On a Node whose unit is not dB the same numbers are
    counts of that unit above the floor, and the defaults are not tuned for it.
  - `manual`: absolute enter and exit levels (RotorHazard-style EnterAt/ExitAt), in the
    Node's level unit. The natural mode for a millivolt Node.
  - Each seat uses its own threshold if it has one, else the Timer-wide one (§6.3). Mode and
    values are chosen per seat; `min_lap_ms` stays Timer-wide.
- A **crossing** spans enter to exit. Timers MUST report `t_enter`, `t_exit` and `t_mid`.
- **`t_mid` is the lap timestamp.** It is the midpoint of the times the smoothed trace
  crosses the **edge level** on the rise and on the fall. The edge level defaults to halfway
  in dB between the noise floor and the peak. This is robust to the dip in the middle of the
  pulse caused by the quad antenna's axial null (RotorHazard's plateau midpoint is not).
- `min_lap_ms` suppresses a second crossing within that window.
- **Exit hold-off.** A crossing ends only once the smoothed trace has stayed below the exit
  level for `exit_hold_ms` (default 100, range 0–1000; 0 ends it on the first sample below).
  `t_exit` is the moment the trace first went below, not the end of the hold-off, so the
  setting delays the report by that long but does not move any timestamp. This keeps a pass
  with several lobes as one crossing; smoothing heavy enough to do the same blurs the edges
  and loses weak passes. Dips below the edge level shorter than the hold-off are treated as
  part of the pass on the rising flank too.
- **Pass window.** With `pass_window_ms` above 0 (range 0–10000, default 0 = off), every
  crossing that starts within that time of the first one belongs to the same pass. The
  Timer reports one crossing for it: the one with the highest peak, with its own
  timestamps unchanged. It is reported when the window has closed and no crossing is in
  progress, so clients see it up to `pass_window_ms` late; `seq` is given at that moment.
  `min_lap_ms` then counts from the reported crossing's `t_mid`. This is for tracks where
  the quad flies close by the gate shortly before going through it: the fly-by can reach
  the enter level, and without the window it is the lap and the real pass is suppressed by
  `min_lap_ms`. "Strongest" is used, not "second", because the fly-by does not reach the
  enter level every lap. If the signal never drops below the exit level between the
  fly-by and the pass, they are one crossing and the window changes nothing. A client
  that leaves the field out of a `PUT` switches the window off.
- **Edges.** The rising edge is the trace's last climb through the edge level before the
  enter sample (searched backwards from it); an earlier, separate bump in the pre-trigger
  history is not part of the pass. If the edge level is above the enter level, the rise is
  searched forwards from the enter sample.
- **Holes.** Samples are expected at a steady rate. A hole of up to 256 samples (lost Node
  batches) is filled by linear interpolation before detection, so the buffers stay evenly
  spaced; a longer outage ends a crossing in progress with the `truncated` flag. A hole must
  never be taken for the sample period.
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
9. ~~Does a Timer need race start/stop?~~ **Decided 2026-11-08: no.** A Timer always emits
   crossings; the Race Manager records race-go as its own fact on the Timer clock and filters.
   (Grid's portable-race-day review reached the same answer.)
10. Verify LapRF `rtcTime` units and the C5 BOOT strap pin before relying on either.
11. B5 carrier: which hub IC(s), which C5 module, on-board splitter or one connector per
    module, and total power for 8 C5s plus a Pi (802.3af vs 802.3at)?
12. B5 HAT: right-angle USB jumper vs Zero 2 pogo pins vs the RP2350-over-UART option.
13. ~~Per-seat thresholds.~~ **Done in v0.4:** `config.seats[].threshold` overrides the Timer
    default (§6.3). The rh-oft plugin sends each seat its own levels.
14. Clients must read advertised capability values (e.g. `samples.history.full_rate_s`) rather
    than assume the numbers in this document's examples; `oftd` keeps 600 s, the RP2350 host a
    30 s reduced trace.
15. **Refusing channel plans a Node cannot do.** Not built. Today `PUT /config` accepts any
   seats and frequencies in range, and the Timer finds out what it costs only when the Node
   runs the plan. A Node's sample rate per seat depends on how many tuning positions the
   plan needs, not on the seat count: one position covers channels up to 40 MHz apart
   (two Raceband neighbours, or three on bands A, B and F), and each extra position
   divides the rate. Eight seats spread so that every seat needs its own position would
   run at roughly a quarter of the single-seat rate. The Timer should work out the
   positions a plan needs before accepting it and refuse, with a reason, plans below a
   stated floor: for example, with eight seats, require that the channels pair up so no
   more than four positions are needed. Also to refuse: frequencies outside the Node's
   `range_mhz`, and two seats too close to tell apart. The limits belong in `/info` so race
   software can check a plan before sending it.
16. **Balancing seats over Nodes, Node on/off, seat pinning.** Designed in §4.1, not built:
   it needs the first Timer with more than one Node. To settle then: how a pin and the
   plan limits of question 15 interact, and whether a re-balance may move a seat during a
   heat (it should not).
17. **Wireless split Timers (future idea, nothing planned).** Split timing is rarely used
   because every split gate needs an Ethernet run. Idea: one main Timer wired to the race
   network, and battery-powered split Timers around the course that reach it by radio; the
   main Timer forwards for them, so race software still talks to one place.
   - Each split unit is a complete Timer (Node plus the detector), not a bare Node. It
     timestamps crossings itself and sends crossings, not raw samples, so radio delay
     does not affect timing. Clocks are aligned as in §7; expect about 1 ms over radio,
     enough for splits.
   - Radio candidate: Wi-Fi HaLow (802.11ah, sub-GHz). It carries IP, so the OFT Protocol
     runs over it unchanged, and it is far from the 5.8 GHz the Nodes measure (§4.3 would
     need an exception for it). It shares 902–928 MHz with 900 MHz control links
     (Crossfire, ExpressLRS 900); judged acceptable, since those links are robust and
     long range is not needed here. The C5 cannot do this itself: each unit needs a
     separate HaLow module.
   - To decide: whether the main Timer is a plain network bridge (each split Timer
     appears on the LAN by itself) or a forwarder that presents the split Timers through
     its own protocol endpoint; how split Timers are found and named; what a split
     Timer does while the link is down (keep crossings and replay them); battery life;
     regional bands and duty-cycle limits outside the US.
   - Cheapest first test: an off-the-shelf Ethernet-to-HaLow bridge on an unmodified
     Timer, both on a battery.
