This module adds Ukrainian-specific fields to `hr.employee` required
for state tax reports and social benefit records.

**Identification:**

* **RNOKPP** — Ukrainian tax registration number (Реєстраційний
  номер облікової картки платника податків). Ten digits with a
  check digit, kept separate from Odoo's generic `identification_id`
  because it is a distinct state document with its own issuing
  authority and use in tax reports.
* **Refused RNOKPP** — flag for individuals who have officially
  declined RNOKPP for religious reasons.
* **Passport series and number** — internal passport (booklet)
  fields.
* **EDDR number** — record number in the Unified State Demographic
  Register (Єдиний державний демографічний реєстр).

**Disability:**

* **Disability group** (I / II / III) under Ukrainian legislation.
* **Disability certificate** — MSEK certificate number.
* **Review date** — date when the disability status must be
  re-evaluated by MSEK.

All fields are hidden from the employee form unless the company
country is set to Ukraine, so the module can be safely installed on
multi-country deployments.
