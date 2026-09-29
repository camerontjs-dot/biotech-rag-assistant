# Cold Chain Shipping of Refrigerated and Frozen Product

## Scope

This procedure covers the packing, dispatch and receipt of temperature-controlled product leaving the warehouse on the shipping dock RM-146 (Grade D). It applies to refrigerated product held at 2 to 8 degrees C and to frozen product held at minus 20 degrees C, shipped in the validated passive shippers SHP-12 and SHP-08. Storage before dispatch is covered by SOP-WH-092: refrigerated stock is picked from the cold room CR-1 in RM-140 and frozen stock from the freezer FZ-1.

## Who does what

| Role | Responsibility |
| --- | --- |
| Shipping operator | Conditions coolant, packs out, starts loggers, completes FRM-WH-401 |
| Warehouse supervisor | Confirms lane and shipper, releases the shipment for dispatch |
| QA reviewer | Assesses excursions, decides the disposition of a shipment that has left its allowance |
| Receiving site contact | Confirms receipt, downloads the logger and reports the reading |

## Choosing the shipper

Each shipper has a validated duration, which is the time its payload stays inside the required range under the summer ambient profile used in its validation. SHP-12 is validated for 72 hours and SHP-08 for 48 hours. The transit time authorised for a shipment is the validated duration less a buffer of 6 hours, so SHP-12 may be used for lanes of up to 66 hours and SHP-08 for lanes of up to 42 hours. The warehouse supervisor compares the forecast transit time from the carrier with that figure before the shipment is built and chooses the next larger shipper if the lane is longer. Lane L-4 is a special case: its maximum transit time is taken from the validated shipping lane profile SLP-0114 and is not derived from the rule above.

## Conditioning the coolant

Coolant is conditioned before use so that it is at its working temperature and not merely cold.

- Refrigerated gel packs MAT-3402 are held at 2 to 8 degrees C for at least 12 hours.
- Frozen packs MAT-3405 are held at minus 20 degrees C for at least 24 hours.
- When frozen packs are used in a refrigerated pack-out, they are tempered at room temperature for 45 minutes first, so that the product does not freeze against them.

Packs that have been taken out of conditioning for longer than 2 hours before use are returned to conditioning for a fresh cycle. Packs with leaks or dents are discarded.

## Packing out

Pack-out is the interval from opening the product carton to closing the shipper, and it takes no more than 20 minutes. Everything the operator needs is set out beforehand: the shipper, the conditioned packs, the logger, the labels and FRM-WH-401. The packs are placed against the walls of the shipper according to the pack-out diagram for the shipper type, the product is placed in the centre, and the shipper is sealed with tamper tape. The operator writes the seal number on the form and photographs the loaded shipper before closing. A pack-out that runs over the time limit is not shipped; the product is returned to storage and the pack-out is restarted with fresh coolant.

## Data loggers

Every shipper carries a logger of the LGR-2210 to LGR-2260 series recording at intervals of 5 minutes. A shipment of a full pallet carries two loggers, one at the top and one in the centre of the load. The logger is started at least 15 minutes before pack-out and its start is checked against a reference clock and a reading of the current temperature. It is placed in the centre of the payload, never against a coolant pack or the wall. The logger number is written on FRM-WH-401. A shipment must not leave the dock if the logger start check fails; the shipper is opened, the logger is replaced and the pack-out clock is restarted.

## Dispatch rules

Shipments leave the dock no later than 14:00 on Monday to Thursday. Lanes with a forecast transit time of more than 48 hours are not dispatched on a Friday, because a delay over the weekend cannot be recovered. The shipping operator confirms with the carrier that the pick-up time is inside the cut-off and that the carrier has a temperature-controlled vehicle if the lane needs one. Returns of used shippers and packs from the receiving site are handled as set out in the carrier contract CTR-0009.

## Excursion allowances

An excursion is any period during which the logger records a temperature outside the required range. The allowances below apply to the whole shipment, counted cumulatively.

| Product | Allowance |
| --- | --- |
| Refrigerated, 2 to 8 degrees C | Up to 60 minutes outside the range in total, with no reading above 12 degrees C and none below 0 degrees C |
| Frozen, minus 20 degrees C | Up to 2 hours in total above minus 15 degrees C |

A shipment whose logger shows more than its allowance is placed in quarantine on arrival, and the receiving site notifies QA within 4 hours of downloading the logger. QA decides the disposition after reviewing the logger trace, the pack-out record and any stability data for the product. A shipment that stays inside the allowance is released on the receiving site's confirmation, and the download is filed with the shipment record.

## Receipt and download

The receiving site downloads the logger within 24 hours of receipt and sends the trace to the sending site. Receipt is confirmed to the sender on FRM-WH-410 within 1 working day. A receiving site that finds a broken seal, a shipper that has been opened, or a logger that has stopped, reports it at once and holds the product in quarantine pending QA review.

## Investigating a failed shipment

When a shipment is quarantined for an excursion, a deviation is opened under SOP-QA-101. The investigation compares the trace with the pack-out record, the conditioning log of the packs, the transit time against the authorised time and the weather at the origin. The worked example DVX-5006 shows how a cold room excursion is recorded, and the same headings are used for a shipping excursion. A change to a lane, a shipper type or a carrier goes through SOP-QA-118 before it is used.

## Calibration of loggers

Loggers are calibrated against a certified reference on the interval set in SOP-EN-131, and a logger that has been dropped or has a cracked case is withdrawn until it has been checked. The minimum battery life a logger must show before it is issued is taken from the vendor datasheet for the logger model, and the shipping operator checks the battery indicator at issue.

## Related documents

- SOP-WH-092 Cold Room and Freezer Operation
- SOP-QA-101 Deviation Management
- DVX-5006 Worked Example: Cold Room Excursion Deviation Report
- SOP-EN-131 Calibration Programme and Interval Management
- SOP-QA-118 Change Control

## Revision history

| Version | Effective | Summary of change |
| --- | --- | --- |
| 2.0 | 2024-02-05 | Added the frozen product allowance and the Friday dispatch rule. Loggers recorded every 10 minutes. Excursion allowance of 90 minutes with a peak of no more than 15 degrees C, and QA notified within 8 hours. Frozen allowance of 3 hours. Pack-out limited to 30 minutes, tempering of 30 minutes, transit buffer of 12 hours, logger download within 48 hours, receipt confirmation within 2 working days, dispatch cut-off at 15:00. |
| 3.0 | 2026-04-13 | Shortened the logger interval, excursion allowance, peak temperature, pack-out time and transit buffer, lengthened tempering, brought forward the cut-off and the download and confirmation times. |
