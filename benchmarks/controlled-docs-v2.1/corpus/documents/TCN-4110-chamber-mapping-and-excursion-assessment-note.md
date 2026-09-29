# Chamber Mapping and Excursion Assessment Note

## What this note is for

This note explains how a stability chamber is mapped to show that it holds its condition everywhere samples are placed, and how the size and length of an excursion are turned into a decision about the samples inside. It supports SOP-QC-236 and works with the conditions in SPC-2271. The interval at which each chamber is mapped is the one in SOP-QC-236, and this note describes what happens at each mapping.

## Mapping design

Each chamber CH-01 to CH-05 is mapped with 15 calibrated probes: one at each of the 8 corners, one at the centre of each of the 4 shelves selected for the study, one at the door side and two next to the chamber's control and monitoring probes. Probes record every minute for 48 hours, and the readings of the chamber's own probes are taken from the monitoring system EQ-1410 for comparison. The mapping is done twice, once with the chamber empty and once with a representative load, because a full chamber behaves differently from an empty one and it is the loaded state that matters for samples.

## Acceptance

The mapping passes when every probe stays within plus or minus 2 degrees C of the setpoint and, for the humidity chambers CH-01 to CH-03, within plus or minus 5 percent RH, throughout the 48 hours. The report names the warmest and coldest positions and the position with the highest and lowest humidity, and the monitoring probe is placed at the position that is most at risk. Positions that fall outside the limits are marked on the shelf and are not used for samples.

## Door-open test

In each mapping the door is opened for 1 minute with the chamber in its loaded state, and the temperature at the door probe and at the centre probe is followed until it returns to within tolerance. The chamber passes when both probes recover within 15 minutes. A chamber that takes longer is not used for studies that need frequent access until the cause has been found and a repeat test has passed.

## Power interruption test

Once, when a chamber is first qualified and again after any change to its power supply, the mains supply is cut for 30 minutes to confirm that the backup supply takes over and that the chamber recovers. The temperature and humidity are followed for 2 hours after power returns, and the chamber must be back within tolerance in that time.

## The three tiers of excursion

An excursion is measured against the setpoint, not against the edge of the tolerance band. The assessment depends on how long it lasted and how far the reading went.

| Tier | Size and duration | Action |
| --- | --- | --- |
| A | Any excursion lasting up to 4 hours and not beyond 5 degrees C from the setpoint | Recorded on the chamber log, no assessment |
| B | More than 2 degrees C from the setpoint for more than 4 hours, up to 24 hours | Documented assessment on FRM-QC-305 by QC chemistry and QA |
| C | Longer than 24 hours, or more than 5 degrees C from the setpoint at any time | Samples flagged and excluded from shelf life data until a decision is made |

For humidity the assessment starts when the reading is more than 5 percent RH from the setpoint for more than 8 hours, and tier C applies after 48 hours or when the reading is more than 10 percent RH from the setpoint.

## What an assessment looks at

An assessment starts from the trace of the chamber and from the stability behaviour of the product. It states the peak, the total time outside tolerance and the time at each level, compares them with the accelerated data for the product, and considers whether the samples were in a part of the chamber that would have been affected. It concludes that the samples remain valid, are valid with a note in the report, or are excluded. The conclusion is signed by the stability coordinator and the QC chemistry manager and reviewed by QA.

## Common weaknesses

- A mapping load that does not represent a real load.
- Probes placed against a wall, where air movement is different.
- An assessment that uses the display reading instead of the monitoring trace.
- A tier decision made without the trace, from a remembered alarm.
- Positions that failed mapping remaining in use.

## Revision history

| Version | Effective | Change |
| --- | --- | --- |
| 1.0 | 2025-03-03 | First issue. |
