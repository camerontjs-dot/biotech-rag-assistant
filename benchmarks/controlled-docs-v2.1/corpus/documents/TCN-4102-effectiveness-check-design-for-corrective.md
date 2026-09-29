# Effectiveness Check Design for Corrective Actions

## Summary

This technical note explains how to design the effectiveness check that SOP-QA-172 requires for Critical and Major CAPAs. It is guidance for action owners, check owners and QA reviewers. It does not add requirements of its own; where it uses a number, the number is the working standard used by the CAPA review board when it judges whether a check was adequate.

## What a check has to show

A corrective action is effective when the condition that caused the event no longer produces it. That is a different question from whether the action was carried out. A retraining session can be completed on time and still leave the cause untouched, so the check looks for evidence in the process itself, not in the paperwork of the action.

A good check has four parts: a measure that is tied to the failure, a source of data that exists independently of the action, a window long enough for the failure to have recurred if it were going to, and a criterion fixed in advance.

## Choosing the measure

The measure follows the failure mode. The examples below show the usual pairs.

| Failure mode | Measure | Data source |
| --- | --- | --- |
| Labels applied to the wrong lot | Count of label reconciliation discrepancies per batch | Batch records |
| Late reading of environmental plates | Proportion of plates read outside the planned window | Monitoring forms |
| Unplanned calibration lapses | Number of instruments past due at the weekly review | Calibration schedule |
| Repeated incomplete batch records | Proportion of records returned by QA for missing entries | Review log |

A measure that could improve without the cause being fixed, such as the total number of deviations opened, is not accepted. Nor is a measure that the action owner can influence directly by changing how the data is recorded.

## The observation window

The window must be at least 3 consecutive batches or 60 days, whichever is longer. For events that normally occur weekly or more often, a window of 30 days gives enough opportunities to see a recurrence and is accepted instead. The window starts when the last action in the plan has been closed, not when the plan was approved, and it stops early only if the criterion has already failed. The check owner reviews the data at 30 days and again at 60 days into the window so that a failing criterion is seen early. A check that has collected no data after 21 days is reported to the board. Where a measure depends on monthly data, the window is rounded up to whole months and at least 3 months of data are used, so that one unusual month cannot decide the result. A window is never longer than 12 months without the board's agreement, because a check that runs for a year has usually stopped answering the original question.

## How much to review

The check owner reviews at least 15 records within the window, or every record if fewer than 15 exist. At least 20 percent of the records in the sample are checked again by a second reviewer. Where records are numerous, they are chosen by a rule fixed beforehand, such as every third batch, so that the selection cannot be steered toward good results. The rule is written in the plan.

## Setting the criterion

The criterion is written before the actions are finished. For a failure that should not happen at all, the criterion is zero repeat events in the window. For a failure that is a rate, such as the proportion of late reads, the criterion is a reduction of at least 50 percent against the baseline of the previous 12 months, together with no single month worse than the baseline mean. The confidence that a small sample supports is judged with the sampling tables in the statistical sampling guide SSG-0004, and a check owner who is unsure of the right table asks the QA statistician before the window opens.

## A worked illustration

A packaging line had 6 label reconciliation discrepancies in the 12 months before its corrective actions, a baseline of 0.5 per month. The plan set a criterion of zero repeats in a window of at least 3 consecutive batches or 60 days. The last action closed on a Monday, and the line then ran 4 batches over 74 days. The check owner, a supervisor from another shift, drew every third record from a pool of 45, which gave 15 records, and found no discrepancy in any of them. The report reached QA 4 working days after the window ended, and the conclusion was effective.

## Who carries out the check

The check owner is never the action owner. Where the process is small and the only knowledgeable person is the action owner, a colleague from another shift or department collects the data and the action owner is available only to answer questions. The check owner records what was reviewed, how the sample was drawn and who supplied the data.

## Reporting

The result is reported on FRM-QA-210 within 5 working days of the end of the window. The report states the measure, the window dates, the number of records reviewed, the result against the criterion and a conclusion of effective, not effective or inconclusive. An inconclusive result, for example because too few batches were made in the window, extends the window rather than closing the check.

## When a check fails

A failed check does not reopen the original CAPA automatically. The check owner and the QA CAPA coordinator decide whether the original actions were incomplete, whether the root cause was wrong, or whether a new cause has appeared. A new plan is written under SOP-QA-172, and the failed check is cited as its source.

## Common weaknesses

- The measure changes between the plan and the report.
- The window starts before the last action is closed.
- Records are chosen by the person whose work is being judged.
- A success is declared on the strength of one good month.
- The check is attached to the deviation, not to the CAPA, and is never seen by the board.

## Revision history

| Version | Effective | Change |
| --- | --- | --- |
| 1.0 | 2025-07-14 | First issue. |
