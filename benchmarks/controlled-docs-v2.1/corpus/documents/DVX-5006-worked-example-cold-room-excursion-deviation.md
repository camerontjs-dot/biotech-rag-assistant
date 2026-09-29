# Worked Example: Cold Room Excursion Deviation Report

## How to read this example

This is a completed deviation record for a temperature excursion in the cold room CR-1, laid out under the headings of FRM-QA-101 and FRM-QA-104. It shows the level of detail expected under SOP-QA-101 for a Major deviation and how the storage rules of SOP-WH-092 feed into it. Names of people are replaced by their roles.

## Summary

Deviation DV-2511 records a rise in the temperature of CR-1 on the night of 11 November 2025. The high temperature alarm sounded at 02:34 after the 20-minute alarm delay, the on-duty warehouse operator acknowledged it at 02:41, and the reading peaked at 9.7 degrees C at 02:58. The temperature was above 8 degrees C for 52 minutes in total. Three pallets of product PRD-311, from lots LT-251103 and LT-251107, were in the room. The stock was moved to CR-2 at 03:49, 1 hour 35 minutes after the excursion began.

## Timeline

| Time | Event |
| --- | --- |
| 02:14 | Probe EQ-0911 first reads above 8 degrees C |
| 02:34 | High temperature alarm sounds after the 20-minute delay |
| 02:41 | Operator acknowledges the alarm and starts FRM-WH-405 |
| 02:58 | Peak reading of 9.7 degrees C |
| 03:02 | On-call technician arrives and finds the compressor not running |
| 03:06 | Compressor restarted by bypassing the start relay; reading returns to 8 degrees C |
| 03:49 | Stock moved to CR-2 because the fault had not been cleared |

## What was found

The technician found that the compressor had not restarted after the routine defrost cycle. The door was closed and the fans were running, so the temperature rose slowly, and the independent probe EQ-0911 and the control probe EQ-0910 agreed within 0.4 degrees C throughout. There was no damage to the evaporator and no ice build-up on the return air grille.

## Containment

The operator reported the event at 08:10 on the same morning, well inside the 24 hours allowed, and the warehouse supervisor confirmed that the three pallets were held in CR-2, on the quarantine shelf, with a hold label. No stock was picked from CR-1 or CR-2 for shipment until QA had decided.

## Initial assessment and classification

The warehouse supervisor completed the initial assessment on the next working day. QA classified the deviation on 12 November 2025, 1 working day after the report, as Major: product quality could have been affected, the excursion lasted more than 30 minutes and the cold room could not be shown to be fit for use until the fault was understood. The investigation was due 35 calendar days after classification, on 17 December 2025.

## Batch impact assessment

The impact assessment on FRM-QA-108 compared the logger trace with the excursion data in the stability record of PRD-311, which shows that the product tolerates up to 11 degrees C for as long as 3 hours without a change in potency or appearance. The excursion of 52 minutes at a peak of 9.7 degrees C was well inside that experience, and QA also checked the retained samples of both lots. Both lots were assessed as unaffected. No extra testing was requested.

## Investigation and root cause

A cross-functional meeting with warehouse, engineering, QC and QA was held on 14 November 2025, 2 working days after classification. Engineering examined the removed start relay and found worn contacts that had failed to close when the defrost heater switched off. The maintenance history showed that the relay had been replaced 6 years earlier and that it was not on the preventive maintenance list. Human error was considered and ruled out: the operator's response met the 10-minute acknowledgement time.

## Recurrence check

The investigator searched the deviation system for the previous 12 months and found 1 earlier cold room alarm, caused by a door left open, which had a different cause. Fewer than 3 similar deviations were found, so a CAPA was not mandatory on the recurrence rule, but the QA Manager decided to raise one because the failure point was a component without any planned maintenance.

## CAPA

CAPA CP-2519 was opened as Major. Its actions were to replace the start relays of both cold rooms, add them to the preventive maintenance schedule at a 24-month interval, and add a compressor run signal to the alarm panel so that a stopped compressor raises an alarm at once instead of after the temperature delay.

## Disposition

QA reviewed the logger trace, the impact assessment and the stability record and released both lots on 20 November 2025. The stock was returned to CR-1 only after mapping checks confirmed that the room held its range for 24 hours with the new relay fitted.

## Closure

The deviation was closed on 5 December 2025, 12 days before the due date, with the CAPA number entered in the record. The QA Manager signed the closure.

## Revision history

| Version | Effective | Change |
| --- | --- | --- |
| 1.0 | 2025-12-08 | First issue of the worked example. |
