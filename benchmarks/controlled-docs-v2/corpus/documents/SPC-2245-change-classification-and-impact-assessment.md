# Change Classification and Impact Assessment Matrix

## Purpose

SOP-QA-118 requires every change request to be given one of three classes. This specification is the reference the QA reviewer uses to assign the class, and it also fixes the approvers, the verification batches and the validation paperwork that follow from it. Where a proposed change fits more than one row, the higher class applies. Where it fits none, the QA reviewer classifies it by comparison with the nearest row and records the comparison.

## Process parameter changes

A qualified process parameter is one whose range was set in a validation or qualification study. The size of a change is measured against the width of that qualified range.

| Size of change | Class |
| --- | --- |
| Up to 2 percent of the qualified range | Class 1 |
| More than 2 percent and up to 5 percent of the qualified range | Class 2 |
| More than 5 percent of the qualified range | Class 3 |

A change of fill volume of no more than 2 percent of the nominal volume is Class 2, and any larger change in fill volume is Class 3. A change of batch size of up to 10 percent is Class 2, and one of more than 10 percent is Class 3.

## Equipment, facilities and utilities

| Change | Class |
| --- | --- |
| Replacement of a part with the same part number from the same supplier | Class 1 |
| Replacement of a filter with one of a different pore size, for example from 0.2 um to 0.1 um | Class 3 |
| A new equipment model in place of an existing one | Class 3 |
| Change to the layout of a Grade A or Grade B room | Class 3 |
| Change of a room pressure differential setpoint of 5 Pa or more | Class 3 |
| Change of a room pressure differential setpoint of less than 5 Pa | Class 2 |
| Change of the temperature setpoint of a qualified storage unit by up to 1 degree C | Class 2 |
| Change of the temperature setpoint of a qualified storage unit by more than 1 degree C | Class 3 |

## Materials, suppliers and cleaning

| Change | Class |
| --- | --- |
| A new supplier of primary packaging | Class 3 |
| A new supplier of an excipient | Class 3 |
| A new supplier of a cleaning agent with the same formulation | Class 2 |
| Change of the concentration of a cleaning agent by up to 10 percent | Class 2 |
| Change of a hold time by up to 10 percent of the validated maximum | Class 2 |
| Change of a hold time by more than 10 percent of the validated maximum | Class 3 |

## Sterilisation, air handling and equipment position

| Change | Class |
| --- | --- |
| Change of a steam sterilisation cycle time by up to 5 minutes | Class 2 |
| Change of a steam sterilisation cycle time by more than 5 minutes | Class 3 |
| Change of the air change rate of a classified room by up to 10 percent | Class 2 |
| Change of the air change rate of a classified room by more than 10 percent | Class 3 |
| Moving fixed equipment by up to 2 m inside a Grade C or Grade D room | Class 2 |
| Moving fixed equipment by more than 2 m inside a Grade A or Grade B room | Class 3 |
| Change of the shipper type on a lane with a transit time over 48 hours | Class 3 |
| A software patch that shifts calculated results by more than 0.5 percent | Class 3 |

A change of an in-process hold time by up to 2 hours is Class 2 when the validated maximum is 24 hours or less, and training records for any change are checked 3 days before go-live.

## Systems, labels and documents

A software patch that touches GMP data is Class 2, and a patch that its vendor marks as urgent is classified within 1 day. The risk score above which a software change is treated as Class 3 comes from the risk assessment RAS-0044. A change to label text that does not alter product identification is Class 2. An editorial correction to a document, such as a typing error or a broken cross-reference, needs no change request and is made under SOP-QA-105.

## Approvers

| Class | Approvers |
| --- | --- |
| Class 1 | QA reviewer |
| Class 2 | QA Manager and the head of the department making the change |
| Class 3 | QA Head, Production Head and Engineering Head |

Approvals are recorded on the change record (FRM-QA-301 and the impact assessment FRM-QA-304) before any implementation work starts, except for emergency changes as described in SOP-QA-118.

## Verification after implementation

| Class | Verification batches | Validation impact statement |
| --- | --- | --- |
| Class 1 | None | Not required |
| Class 2 | 1 batch | Not required |
| Class 3 | 3 consecutive batches | Required |

The verification batches are the first batches made after go-live, and they are reviewed within 10 days of batch release against the expectations written in the request. A failed verification batch stops further use of the changed process until the change board has decided how to proceed. For a Class 3 change the validation impact statement says which validation reports are affected and whether any part of a study must be repeated. Where a Class 3 change involves a room that supports aseptic operations, the room is also sampled under SOP-QC-214 before the first verification batch.

## Supplier changes

A change of supplier is assessed together with the qualification steps in SOP-WH-064. The change is not closed until the new supplier has been qualified and the first lots have been received and released, and the change owner records the lot numbers of those first deliveries on the implementation checklist.

## Review of this specification

The matrix is reviewed every 24 months by QA with the heads of production and engineering, and earlier when a change classified under it turns out to have been classified too low. A change that was reclassified upward after implementation is discussed at the next change board meeting, within 7 days.

## Revision history

| Version | Effective | Change |
| --- | --- | --- |
| 1.0 | 2024-06-10 | First issue alongside SOP-QA-118 version 3.0. |
| 1.1 | 2026-05-04 | Added the pressure differential and setpoint rows and the note on supplier changes. |
