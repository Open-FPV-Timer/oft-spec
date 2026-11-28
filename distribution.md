# Getting OFT onto hardware: releases, the site, updates

Plan, agreed 2026-11-28. Not built, except where it says so.

## The gap

Someone who is not the developer cannot get the firmware. As of 2026-11-28:

- **RP2350 Timer firmware:** no download anywhere. The built files are kept out of git and
  no repo has a release. The only route is to build from source.
- **Node firmware:** the flasher site (oft.reconfpv.com) installs the current build over
  USB. The file for updating a Node through its Timer is on the site at
  `firmware/esp32c5/firmware.bin`, but nothing says so.
- **`oftd` for a Raspberry Pi:** build from source.

## What a person should be able to do

Go to one site and get everything needed to install or update any Timer and any Node, with
the versions that belong together shown side by side.

## The three steps

1. **Releases.** Each firmware repo publishes a GitHub release per version, with the files
   a person needs. Releases are the storage: history, checksums, stable links.

   | Repo | Files | Used for |
   |---|---|---|
   | `oft-timer-rp2350` | `oft-timer.uf2` | first install over USB (hold BOOT, copy to the `RP2350` drive) |
   | | `oft-timer.bin` | update from the Timer's page |
   | `oft-node-c5` | `oft-node-c5.bin` | update through a Timer's page |
   | | `oft-node-c5-full.bin` | first install over USB with esptool, at offset 0 |
   | `oft` | `oftd` built for the Pi | install or update on a Raspberry Pi Timer |

   One version number across the set: a Timer, a Node and an `oftd` with the same number
   were tested together.

2. **The site, in its own repo.** Today the flasher site is built from `oft-node-c5`, which
   is a fork of another project and only knows about Nodes. The site for the whole system
   gets its own small repo, gathers the latest release of each part, and offers:

   - Node firmware: flash from the browser (as now), and the file for updates.
   - RP2350 Timer firmware: the `.uf2` with the BOOT-button steps, and the `.bin`.
   - `oftd`: the program and how to install it.
   - Which versions belong together.

3. **Update from the Timer's page.** A Timer is often on a network with no internet, but
   the browser looking at its page usually has it. The page fetches the newest firmware
   from the site and hands it to the Timer, for the Timer itself and for its Nodes, so
   nobody downloads a file. It needs the site to serve the files to other pages
   (cross-origin), and the page to say plainly what it is about to install.

   This is a Timer's own management (spec, "What this document is"): it is not part of the
   OFT Protocol, and race software has no part in it.

## State

- 0.2.0 exists as built files only (2026-11-28): Timer build 217993303, Node firmware from
  `oft-node-c5` `fdb1168`. Both are running on a one-Node Timer, put there by the developer
  over the network.
- No release has been published.
