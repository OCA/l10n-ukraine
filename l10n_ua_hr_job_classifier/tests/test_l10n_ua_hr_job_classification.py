from psycopg2 import IntegrityError

from odoo.tests import tagged
from odoo.tools import mute_logger

from .common import TestL10nUaHrJobClassifierCommon


@tagged("post_install", "-at_install", "l10n_ua_hr_job_classifier")
class TestHrJobClassification(TestL10nUaHrJobClassifierCommon):
    """Tests for the l10n.ua.hr.job.classification model."""

    def test_01_create_classification(self):
        """A classification can be created with the required fields."""
        new_class = self.Classification.create(
            {
                "name": "Software Engineer",
                "code": "2132.2",
                "profession_classifier_catalog_id": self.cat_subclass.id,
            }
        )
        self.assertEqual(new_class.name, "Software Engineer")
        self.assertEqual(new_class.code, "2132.2")
        self.assertEqual(
            new_class.profession_classifier_catalog_id,
            self.cat_subclass,
        )

    def test_02_code_is_required(self):
        """The code field is mandatory."""
        with self.assertRaises(IntegrityError), mute_logger("odoo.sql_db"):
            self.Classification.create({"name": "No Code Profession"})

    def test_03_name_is_required(self):
        """The name field is mandatory."""
        with self.assertRaises(IntegrityError), mute_logger("odoo.sql_db"):
            self.Classification.create({"code": "1234"})

    def test_04_duplicate_codes_allowed(self):
        """Duplicate KP codes are allowed by design.

        This is critical for Ukrainian usage: one 4-digit KP code maps
        to many distinct job titles.
        """
        class_1 = self.Classification.create(
            {
                "name": "Position One",
                "code": "1110",
                "profession_classifier_catalog_id": self.cat_subclass.id,
            }
        )
        class_2 = self.Classification.create(
            {
                "name": "Position Two",
                "code": "1110",
                "profession_classifier_catalog_id": self.cat_subclass.id,
            }
        )
        self.assertEqual(class_1.code, class_2.code)
        self.assertNotEqual(class_1.id, class_2.id)

    def test_05_classification_without_catalog(self):
        """A classification may exist without a catalog reference."""
        orphan = self.Classification.create(
            {
                "name": "Orphan Profession",
                "code": "0000",
            }
        )
        self.assertFalse(orphan.profession_classifier_catalog_id)

    def test_06_active_flag(self):
        """A classification is active by default and can be archived."""
        new_class = self.Classification.create(
            {
                "name": "Active Test",
                "code": "8888",
            }
        )
        self.assertTrue(new_class.active)
        new_class.active = False
        self.assertFalse(new_class.active)

    def test_07_search_by_code(self):
        """Pattern search by KP code with =like operator."""
        class_a = self.Classification.create(
            {
                "name": "Test Search A",
                "code": "99991",
                "profession_classifier_catalog_id": self.cat_subclass.id,
            }
        )
        class_b = self.Classification.create(
            {
                "name": "Test Search B",
                "code": "99992",
                "profession_classifier_catalog_id": self.cat_subclass.id,
            }
        )
        found = self.Classification.search([("code", "=like", "9999%")])
        self.assertIn(class_a, found)
        self.assertIn(class_b, found)

    def test_08_search_by_catalog_child_of(self):
        """Search classifications by any node in the catalog hierarchy."""
        found = self.Classification.search(
            [
                (
                    "profession_classifier_catalog_id",
                    "child_of",
                    self.cat_root.id,
                ),
            ]
        )
        self.assertIn(self.classification, found)

    def test_09_ondelete_restrict_catalog(self):
        """Deleting a catalog used by a classification is restricted."""
        with self.assertRaises(IntegrityError), mute_logger("odoo.sql_db"):
            self.cat_subclass.unlink()
