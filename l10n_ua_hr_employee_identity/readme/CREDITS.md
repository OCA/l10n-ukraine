The RNOKPP check-digit algorithm follows the specification of the
Ukrainian State Tax Service:

* Weights: `(-1, 5, 7, 9, 4, 6, 10, 5, 7)`
* Control digit: `sum(digit[i] * weight[i]) mod 11 mod 10`
  for `i` in `0..8`

Passport series and number format (2 letters + 6 digits) follows
the old-style Ukrainian internal passport (booklet). The modern
ID-card format is not covered by this module because it is not
required for the state reports currently in scope.

State-report requirements are aligned with:

* **Postanova KMU No. 413** of 17 June 2015 — reporting of new
  hires to the State Tax Service, which requires either RNOKPP
  or passport series + number for individuals who have refused
  RNOKPP for religious reasons.
* **Form 1-DF (4-DF)** — quarterly tax withholding report.
* **Form D1** — monthly unified social contribution report.

Disability group semantics follow the classification maintained
by the Medical and Social Expert Commission (МСЕК) of Ukraine.
