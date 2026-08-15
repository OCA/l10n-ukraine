This module connects Ukrainian job positions (`hr.job`) with the
Ukrainian National Classifier of Occupations DK 003:2010.

It adds a single Many2one field on `hr.job`:

* **Job Classification (DK 003:2010)** — links the job position to
  its official classification code.

The field is hidden from the form when the company country is not
Ukraine, so the module can be safely installed on multi-country
deployments. It is also exposed in the job search view for
filtering and grouping.
