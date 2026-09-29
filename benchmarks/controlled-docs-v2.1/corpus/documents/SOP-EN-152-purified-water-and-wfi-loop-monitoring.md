# Purified Water and WFI Loop Monitoring

## Scope

This procedure governs the routine monitoring of the purified water (PW) loop LP-01 and the water for injection (WFI) loop LP-02, from the generation skid in RM-120 (Grade D) through the storage tanks in RM-122 (Grade D) to the use points and returns on the production floor. It covers the sampling schedule, the sampling technique, the operating parameters that are watched between samples, and the response to an alert or an action level. The alert and action levels themselves are in SPC-2252, and sanitization of the loops is in SOP-EN-158.

## The systems

| Item | PW | WFI |
| --- | --- | --- |
| Loop | LP-01 | LP-02 |
| Storage tank | TK-101 | TK-201 |
| Sample points | PT-01 to PT-12 | PT-21 to PT-28 |
| Return point | PT-12 | PT-28 |
| In-line conductivity | EQ-1101 | EQ-1201 |
| In-line TOC analyser | EQ-1102 | EQ-1202 |

The PW loop also carries the ultraviolet unit EQ-1110, and the WFI return carries the temperature probe EQ-1210.

## Roles

| Role | Responsibility |
| --- | --- |
| Utilities technician | Takes samples from the loops, reads operating parameters, responds to alarms |
| QC chemistry analyst | Tests TOC and conductivity offline and reports results |
| QC microbiology analyst | Plates and reads microbial samples and endotoxin tests |
| Utilities engineer | Reviews trends, owns the schedule and the sanitization plan |
| QA reviewer | Reviews action-level results and decides on the use of affected points |

## Sampling schedule

Every use point, for example PT-04 at the laboratory bench or PT-23 at the stopper processor, is sampled on a rotating schedule, and the return points are sampled daily because they show the state of the whole loop.

| Loop | Points | Frequency |
| --- | --- | --- |
| PW | Use points PT-01 to PT-11 | Each point at least once every 14 days |
| PW | Return point PT-12 | Daily |
| WFI | Use points PT-21 to PT-27 | Each point at least once every 7 days |
| WFI | Return point PT-28 | Daily |
| WFI | Endotoxin at PT-21 and PT-28 | Weekly |

The sampling frequency for endotoxin on the PW loop follows the water system monitoring plan WMP-0011. The schedule is drawn up so that the same point is not always sampled on the same weekday, and so that no two consecutive samples of a loop come from neighbouring points on the same branch. A sample missed for any reason is taken on the next working day and the reason is written on FRM-EN-301. Each round is planned so that no technician collects more than 6 samples in one visit.

## Sampling technique

The technician wears clean gloves and a mask, and does not touch the inside of the outlet. Before sampling the technician sanitises the outside of the outlet with sterile 70 percent isopropyl alcohol and leaves it in contact for 30 seconds. The outlet is then flushed for 3 minutes at full flow into a drain, so that the sample is water from the loop and not from the outlet valve. The technician fills the sterile 100 mL bottle (MAT-5015) to the mark without letting the bottle touch the outlet, closes it at once, and labels it with the point number, the time and the initials.

Samples travel to the laboratory in a clean box and are received within 1 hour of collection. A sample that is delayed longer than that is discarded and the point is sampled again, because organisms multiply in a stored sample and would show a false high count. The time of collection and the time of receipt are both written on FRM-EN-301.

## Operating parameters watched between samples

The technician reads the loop parameters at the start of each shift and records them on the round sheet.

| Parameter | PW | WFI |
| --- | --- | --- |
| Loop temperature | 20 to 25 degrees C | Held at 80 degrees C, with the return at 75 degrees C or higher |
| Flow velocity at the return | Recorded | 1.2 m/s or higher |
| Tank level | Not below 30 percent | Not below 30 percent |
| Alarm on low return temperature | Not applicable | After more than 10 minutes below 75 degrees C |

The utilities engineer reviews the round sheets every week. A drop of the WFI return below 75 degrees C for more than 10 minutes is treated as a possible stagnation event, and the loop is inspected before the next sample is taken.

## In-line instruments

The in-line conductivity and TOC analysers give a continuous reading. Each is compared with an offline measurement once a week, as set out in SPC-2252, and the offline TOC check for each analyser is written on the round sheet. The UV lamp of EQ-1110 has its intensity checked every month and is replaced at 8000 hours of operation even when its intensity reading is still acceptable. Calibration of the instruments follows SOP-EN-131.

## Alert-level results

A result at or above an alert level is a sign of drift, not yet a failure. The point is resampled within 24 hours. If the resample is below the alert level the point returns to its normal schedule, and if it is at or above it a second time the utilities engineer starts an investigation into the loop. Two consecutive alert-level results at the same point also start an investigation, even when the results are for different attributes.

## Action-level results

An action-level result at a point stops the use of water from that point at once, and the technician places a tag on the outlet. QA is notified within 2 hours of the result being known, a deviation is raised under SOP-QA-101, and the point is resampled together with the two points nearest to it upstream. Use of the point resumes only when the QA reviewer has accepted the investigation and two consecutive samples are below the alert level.

## Trending

Every month, the utilities engineer plots each attribute for each loop, by point and over the last 12 months, and looks for upward drift, seasonal patterns and points that are repeatedly near an alert level. The monthly review is signed by the utilities engineer and the QC manager and is sent to QA.

## Tanks and vent filters

The tanks TK-101 and TK-201 are fitted with hydrophobic vent filters. The interval for the integrity test of the vent filters follows the filter maintenance schedule FMS-0006, and a wet or damaged vent filter is replaced at once and the tank sampled afterwards. During the first 30 days after the commissioning of any new loop, the alert level for the total viable count comes from the qualification protocol issued for that loop, and the levels in SPC-2252 apply afterwards.

## Records

Sampling records, round sheets, laboratory results and monthly trend reviews are kept for the periods set in POL-0004. Results are also entered on FRM-QC-201 and in the laboratory system so that they can be trended by point and by date, and each sanitization of a loop is recorded on FRM-EN-305.

## Related documents

- SPC-2252 Water Quality Specification: PW and WFI
- SOP-EN-158 Loop Sanitization and Return to Service
- SOP-QA-101 Deviation Management
- SOP-EN-131 Calibration Programme and Interval Management
- POL-0004 Records Retention Policy

## Revision history

| Version | Effective | Summary of change |
| --- | --- | --- |
| 2.0 | 2023-08-07 | Introduced the daily return-point sampling. PW use points sampled every 28 days and WFI use points every 14 days, flush of 1 minute, samples received within 2 hours, alert results resampled within 48 hours, QA notified within 4 hours of an action result, temperature alarm after 15 minutes below 75 degrees C, return flow velocity of 1.0 m/s, UV lamp replaced at 10000 hours. |
| 3.0 | 2026-01-26 | Shortened the sampling intervals, lengthened the flush, shortened the transport, resampling, notification and alarm times, raised the flow velocity and lowered the UV lamp replacement interval. |
