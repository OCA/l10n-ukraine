from datetime import date, timedelta

from odoo import _, api, fields, models
from odoo.exceptions import ValidationError

_RNOKPP_WEIGHTS = (-1, 5, 7, 9, 4, 6, 10, 5, 7)
_RNOKPP_BASE_DATE = date(1899, 12, 31)


def check_rnokpp(value, birthday=False, gender=False):
    """Return True if ``value`` is a valid Ukrainian RNOKPP.

    Full validation:

    - Ten digits with a valid check digit.
    - The date-of-birth encoded in the first five digits must lie
      between 1900-01-01 and today.
    - If ``birthday`` is passed, it must match the encoded date
      exactly.
    - If ``gender`` is passed as ``"male"`` or ``"female"``, it
      must match the parity of the 9th digit (odd → male,
      even → female). Other gender values are not cross-checked.

    Empty or None values return False.
    """
    value = (value or "").strip()
    if len(value) != 10 or not value.isdigit():
        return False
    digits = [int(c) for c in value]
    # Check digit
    weighted_sum = sum(d * w for d, w in zip(digits[:9], _RNOKPP_WEIGHTS, strict=False))
    control = weighted_sum % 11 % 10
    if control != digits[9]:
        return False
    # Encoded date-of-birth must be within a realistic range
    encoded_birthday = _RNOKPP_BASE_DATE + timedelta(days=int(value[:5]))
    if not (date(1900, 1, 1) <= encoded_birthday <= date.today()):
        return False
    # Optional birthday cross-check
    if birthday and encoded_birthday != birthday:
        return False
    # Optional gender cross-check (only for male/female)
    if gender and gender in ("male", "female"):
        encoded_gender = "male" if digits[8] % 2 == 1 else "female"
        if encoded_gender != gender:
            return False
    return True


class HrEmployee(models.Model):
    _inherit = "hr.employee"

    # RNOKPP and passport for those who refused it
    l10n_ua_rnokpp = fields.Char(
        string="RNOKPP",
        tracking=True,
        help="Tax registration number issued by the State Tax Service "
        "of Ukraine. Distinct from the generic Identification No. "
        "Required for state reports (1-DF, 413, Д1) unless the "
        "employee has refused it for religious reasons.",
    )
    l10n_ua_rnokpp_refused = fields.Boolean(
        string="Refused RNOKPP",
        tracking=True,
        help="The employee has officially declined RNOKPP for religious "
        "reasons (with a corresponding mark in the passport). When "
        "set, RNOKPP must be empty; passport series and number are "
        "used instead in state reports.",
    )
    l10n_ua_passport_series = fields.Char(
        string="Passport Series",
        tracking=True,
        help="Two-letter series of the internal passport (booklet). ",
    )
    l10n_ua_passport_number = fields.Char(
        string="Passport Number",
        tracking=True,
        help="Six-digit number of the internal passport (booklet). ",
    )

    # EDDR
    l10n_ua_eddr_number = fields.Char(
        string="EDDR Number",
        tracking=True,
        help="Unique record number in the Unified State Demographic "
        "Register. Optional — included in tax reports if available.",
    )

    # Disability
    l10n_ua_disability_group = fields.Selection(
        selection=[
            ("group1", "Group I"),
            ("group2", "Group II"),
            ("group3", "Group III"),
        ],
        string="Disability Group",
        tracking=True,
        help="Current disability group. Empty means no disability. "
        "History of changes is preserved in the chatter.",
    )
    l10n_ua_disability_certificate = fields.Char(
        string="Disability Certificate",
        tracking=True,
        help="Number of the disability certificate (МСЕК). Required "
        "when the disability group is set.",
    )
    l10n_ua_disability_expiry_date = fields.Date(
        string="Certificate Expiry Date",
        tracking=True,
        help="Date when the disability certificate expires. After this "
        "date the employee must undergo a re-examination by MSEK "
        "to renew the certificate or re-evaluate the disability "
        "group.",
    )

    @api.constrains(
        "l10n_ua_rnokpp",
        "l10n_ua_rnokpp_refused",
        "birthday",
        "gender",
    )
    def _check_l10n_ua_rnokpp(self):
        for rec in self:
            value = (rec.l10n_ua_rnokpp or "").strip()
            if rec.l10n_ua_rnokpp_refused:
                if value:
                    raise ValidationError(
                        _(
                            "%s: RNOKPP is filled while marked as refused — "
                            "clear one of them."
                        )
                        % rec.display_name
                    )
                continue
            if not value:
                continue
            if not check_rnokpp(
                value,
                birthday=rec.birthday,
                gender=rec.gender,
            ):
                raise ValidationError(
                    _(
                        "Invalid RNOKPP “%(v)s” for %(emp)s: check the "
                        "10 digits, the check digit, the encoded date "
                        "(must match the birthday if set), and the "
                        "encoded gender (must match the employee "
                        "gender if set to male or female)."
                    )
                    % {"v": value, "emp": rec.display_name}
                )

    @api.constrains(
        "l10n_ua_passport_series",
        "l10n_ua_passport_number",
    )
    def _check_l10n_ua_passport_format(self):
        for rec in self:
            series = (rec.l10n_ua_passport_series or "").strip()
            number = (rec.l10n_ua_passport_number or "").strip()
            if series and (len(series) != 2 or not series.isalpha()):
                raise ValidationError(
                    _("%s: Passport series must be 2 letters (e.g. " "“ЕА”).")
                    % rec.display_name
                )
            if number and (len(number) != 6 or not number.isdigit()):
                raise ValidationError(
                    _("%s: Passport number must be 6 digits.") % rec.display_name
                )
