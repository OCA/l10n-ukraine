from odoo.tests.common import TransactionCase


class TestL10nUaHrJobClassifierCommon(TransactionCase):
    """Common setup for l10n_ua_hr_job_classifier tests."""

    @classmethod
    def setUpClass(cls):
        super().setUpClass()

        cls.Catalog = cls.env["l10n.ua.hr.job.classification.catalog"]
        cls.Classification = cls.env["l10n.ua.hr.job.classification"]

        # Test hierarchy with T-prefixed codes to avoid collisions with
        # real DK 003:2010 data loaded from CSV.
        cls.cat_root = cls.Catalog.create(
            {
                "name": "Test Root Section",
                "code": "T1",
            }
        )
        cls.cat_sub = cls.Catalog.create(
            {
                "name": "Test Subsection",
                "code": "T11",
                "parent_id": cls.cat_root.id,
            }
        )
        cls.cat_class = cls.Catalog.create(
            {
                "name": "Test Class",
                "code": "T111",
                "parent_id": cls.cat_sub.id,
            }
        )
        cls.cat_subclass = cls.Catalog.create(
            {
                "name": "Test Subclass",
                "code": "T1111",
                "parent_id": cls.cat_class.id,
            }
        )

        cls.classification = cls.Classification.create(
            {
                "name": "Test Profession",
                "code": "T9999",
                "profession_classifier_catalog_id": cls.cat_subclass.id,
            }
        )
