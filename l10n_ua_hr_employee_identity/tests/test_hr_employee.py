from datetime import date

from odoo.exceptions import ValidationError
from odoo.tests.common import TransactionCase

from ..models.hr_employee import check_rnokpp


class TestL10nUaHrEmployee(TransactionCase):
    """Tests for the l10n.ua.hr.employee module."""

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.Employee = cls.env["hr.employee"]
        # Ukraine country
        cls.ua_country = cls.env.ref("base.ua")
        # A Ukrainian company for context
        cls.ua_company = cls.env["res.company"].create(
            {
                "name": "UA Test Company",
                "country_id": cls.ua_country.id,
            }
        )

    # ---- check_rnokpp function tests -------------------------------

    def test_01_check_rnokpp_valid(self):
        """A properly-formed RNOKPP passes the check-digit test."""
        self.assertTrue(check_rnokpp("1234567899"))

    def test_02_check_rnokpp_invalid_check_digit(self):
        """A wrong check digit fails."""
        self.assertFalse(check_rnokpp("1234567890"))

    def test_03_check_rnokpp_wrong_length(self):
        """Anything shorter or longer than 10 digits is invalid."""
        self.assertFalse(check_rnokpp("12345"))
        self.assertFalse(check_rnokpp("12345678901"))

    def test_04_check_rnokpp_non_digits(self):
        """Non-numeric values fail."""
        self.assertFalse(check_rnokpp("abcdefghij"))
        self.assertFalse(check_rnokpp("12345 6789"))

    def test_05_check_rnokpp_empty(self):
        """Empty / None values return False."""
        self.assertFalse(check_rnokpp(""))
        self.assertFalse(check_rnokpp(None))

    # ---- Model constraint tests ------------------------------------

    def test_06_create_employee_with_valid_rnokpp(self):
        """An employee can be created with a valid RNOKPP."""
        emp = self.Employee.create(
            {
                "name": "Ivan Petrenko",
                "company_id": self.ua_company.id,
                "l10n_ua_rnokpp": "1234567899",
            }
        )
        self.assertEqual(emp.l10n_ua_rnokpp, "1234567899")

    def test_07_create_employee_with_invalid_rnokpp_raises(self):
        """Invalid RNOKPP raises ValidationError."""
        with self.assertRaises(ValidationError):
            self.Employee.create(
                {
                    "name": "Ivan Petrenko",
                    "company_id": self.ua_company.id,
                    "l10n_ua_rnokpp": "1234567890",  # wrong check digit
                }
            )

    def test_08_refused_with_rnokpp_raises(self):
        """Cannot have both refused=True and a filled RNOKPP."""
        with self.assertRaises(ValidationError):
            self.Employee.create(
                {
                    "name": "Ivan Petrenko",
                    "company_id": self.ua_company.id,
                    "l10n_ua_rnokpp": "1234567899",
                    "l10n_ua_rnokpp_refused": True,
                }
            )

    def test_09_refused_without_rnokpp_ok(self):
        """Refused=True with empty RNOKPP is valid."""
        emp = self.Employee.create(
            {
                "name": "Ivan Petrenko",
                "company_id": self.ua_company.id,
                "l10n_ua_rnokpp_refused": True,
                "l10n_ua_passport_series": "ЕА",
                "l10n_ua_passport_number": "338960",
            }
        )
        self.assertTrue(emp.l10n_ua_rnokpp_refused)
        self.assertFalse(emp.l10n_ua_rnokpp)

    def test_10_passport_series_wrong_format_raises(self):
        """Passport series must be exactly 2 letters."""
        with self.assertRaises(ValidationError):
            self.Employee.create(
                {
                    "name": "Ivan Petrenko",
                    "company_id": self.ua_company.id,
                    "l10n_ua_rnokpp_refused": True,
                    "l10n_ua_passport_series": "ABC",  # 3 letters
                    "l10n_ua_passport_number": "338960",
                }
            )

    def test_11_passport_number_wrong_format_raises(self):
        """Passport number must be exactly 6 digits."""
        with self.assertRaises(ValidationError):
            self.Employee.create(
                {
                    "name": "Ivan Petrenko",
                    "company_id": self.ua_company.id,
                    "l10n_ua_rnokpp_refused": True,
                    "l10n_ua_passport_series": "ЕА",
                    "l10n_ua_passport_number": "3389",  # 4 digits
                }
            )

    def test_12_disability_fields_stored(self):
        """Disability fields are simply stored, no cross-validation."""
        emp = self.Employee.create(
            {
                "name": "Ivan Petrenko",
                "company_id": self.ua_company.id,
                "l10n_ua_disability_group": "group2",
                "l10n_ua_disability_certificate": "МСЕК-12345",
                "l10n_ua_disability_expiry_date": "2027-06-30",
            }
        )
        self.assertEqual(emp.l10n_ua_disability_group, "group2")
        self.assertEqual(emp.l10n_ua_disability_certificate, "МСЕК-12345")

    def test_13_eddr_number_stored(self):
        """EDDR number is stored without validation."""
        emp = self.Employee.create(
            {
                "name": "Ivan Petrenko",
                "company_id": self.ua_company.id,
                "l10n_ua_eddr_number": "20200101-12345",
            }
        )
        self.assertEqual(emp.l10n_ua_eddr_number, "20200101-12345")

    def test_14_check_rnokpp_impossible_date(self):
        """RNOKPP with an out-of-range encoded date fails."""
        # 98765 days = year 2170, impossible
        self.assertFalse(check_rnokpp("9876543215"))

    def test_15_check_rnokpp_wrong_gender(self):
        """RNOKPP encoded gender must match employee gender."""
        # 2249112314 encodes male (9th digit = 1, odd)
        self.assertTrue(check_rnokpp("2249112314", gender="male"))
        self.assertFalse(check_rnokpp("2249112314", gender="female"))
        # Gender "other" or None is not cross-checked
        self.assertTrue(check_rnokpp("2249112314", gender="other"))
        self.assertTrue(check_rnokpp("2249112314", gender=None))

    def test_16_check_rnokpp_birthday_match(self):
        """RNOKPP encoded birthday must match given birthday."""
        # 2249212318 encodes 1961-07-31 male
        self.assertTrue(check_rnokpp("2249212318", birthday=date(1961, 7, 31)))
        self.assertFalse(check_rnokpp("2249212318", birthday=date(1961, 7, 30)))
        # And with matching gender
        self.assertTrue(
            check_rnokpp(
                "2249212318",
                birthday=date(1961, 7, 31),
                gender="male",
            )
        )
