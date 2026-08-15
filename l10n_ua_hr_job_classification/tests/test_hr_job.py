from odoo.tests.common import TransactionCase


class TestL10nUaHrJobClassification(TransactionCase):
    """Tests for the l10n_ua_hr_job_classification module."""

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.Job = cls.env["hr.job"]
        cls.Classification = cls.env["l10n.ua.hr.job.classification"]
        # Use the first available classification from the seeded data
        cls.classification = cls.Classification.search([], limit=1)

    def test_01_field_exists(self):
        """The classification field is available on hr.job."""
        self.assertIn(
            "l10n_ua_hr_job_classification_id",
            self.Job._fields,
        )

    def test_02_create_job_without_classification(self):
        """A job position can be created without any classification."""
        job = self.Job.create({"name": "Test Position"})
        self.assertFalse(job.l10n_ua_hr_job_classification_id)

    def test_03_create_job_with_classification(self):
        """A job position can be created with a classification."""
        self.assertTrue(
            self.classification,
            "l10n_ua_hr_job_classifier seed data should include "
            "at least one classification.",
        )
        job = self.Job.create(
            {
                "name": "Test Position with Classification",
                "l10n_ua_hr_job_classification_id": self.classification.id,
            }
        )
        self.assertEqual(
            job.l10n_ua_hr_job_classification_id,
            self.classification,
        )

    def test_04_change_classification(self):
        """Job classification can be changed on an existing job."""
        job = self.Job.create({"name": "Test Position"})
        job.l10n_ua_hr_job_classification_id = self.classification
        self.assertEqual(
            job.l10n_ua_hr_job_classification_id,
            self.classification,
        )

    def test_05_clear_classification(self):
        """Job classification can be cleared."""
        job = self.Job.create(
            {
                "name": "Test Position",
                "l10n_ua_hr_job_classification_id": self.classification.id,
            }
        )
        job.l10n_ua_hr_job_classification_id = False
        self.assertFalse(job.l10n_ua_hr_job_classification_id)
