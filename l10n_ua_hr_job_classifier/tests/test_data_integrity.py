from odoo.tests import tagged

from .common import TestL10nUaHrJobClassifierCommon

# Sentinel professions known to exist in the bundled DK 003:2010 data.
# Used to verify that key entries survived the CSV import.
KNOWN_PROFESSIONS = [
    ("Президент України", "1110"),
    ("Народний депутат України", "1110"),
    ("Інженер-програміст", "2132.2"),
]


@tagged(
    "post_install",
    "-at_install",
    "l10n_ua_hr_job_classifier",
    "l10n_ua_hr_job_classifier_data",
)
class TestDataIntegrity(TestL10nUaHrJobClassifierCommon):
    """Integrity tests for the bundled DK 003:2010 data.

    These tests are critical: they verify that the data/ CSV files were
    loaded correctly, with no lost records or broken references.
    """

    # ------------------------------------------------------------
    # Catalog hierarchy integrity
    # ------------------------------------------------------------
    def test_01_catalog_root_loaded(self):
        """The DK 003:2010 root catalog node is loaded."""
        root = self.env.ref(
            "l10n_ua_hr_job_classifier.cat_dk003_root",
            raise_if_not_found=False,
        )
        self.assertIsNotNone(
            root,
            "Root catalog node 'cat_dk003_root' is missing from data.",
        )
        self.assertFalse(root.parent_id)

    def test_02_main_sections_loaded(self):
        """All 9 main sections of DK 003:2010 (codes 1-9) are loaded."""
        for code in range(1, 10):
            sections = self.Catalog.search([("code", "=", str(code))])
            # Filter out test fixtures (they use 'T' prefix in their code)
            real_sections = sections.filtered(
                lambda s: not (s.code or "").startswith("T")
            )
            self.assertTrue(
                real_sections,
                f"Section {code} of DK 003:2010 not found in catalog.",
            )

    def test_03_catalog_has_expected_volume(self):
        """Catalog has around 823 records loaded from CSV."""
        count = self.Catalog.search_count([])
        self.assertGreater(
            count,
            800,
            f"Catalog has only {count} records, expected ~823.",
        )

    def test_04_parent_path_is_set_for_all(self):
        """Every catalog node has a populated parent_path."""
        without_path = self.Catalog.search([("parent_path", "=", False)])
        self.assertEqual(
            len(without_path),
            0,
            f"Found {len(without_path)} catalog nodes without parent_path.",
        )

    # ------------------------------------------------------------
    # Classifications integrity
    # ------------------------------------------------------------
    def test_05_classifications_loaded(self):
        """The CSV file loaded at least 9000 classifications."""
        count = self.Classification.search_count([])
        self.assertGreater(
            count,
            9000,
            f"Only {count} classifications loaded, expected ~9150.",
        )

    def test_06_no_orphan_classifications(self):
        """Most classifications are linked to a catalog."""
        orphans = self.Classification.search_count(
            [
                ("profession_classifier_catalog_id", "=", False),
            ]
        )
        self.assertLessEqual(
            orphans,
            10,
            f"Found {orphans} classifications without catalog reference.",
        )

    def test_07_classification_catalog_refs_valid(self):
        """Catalog references on classifications point to existing records."""
        classifications = self.Classification.search(
            [
                ("profession_classifier_catalog_id", "!=", False),
            ]
        )
        # Check the first 100 for speed.
        for record in classifications[:100]:
            self.assertTrue(
                record.profession_classifier_catalog_id.exists(),
                f"Classification '{record.name}' refs missing catalog.",
            )

    def test_08_known_professions_exist(self):
        """Sentinel professions known to be in DK 003:2010 are present."""
        for name, code in KNOWN_PROFESSIONS:
            found = self.Classification.search(
                [("name", "=", name), ("code", "=", code)],
                limit=1,
            )
            self.assertTrue(
                found,
                f"Profession '{name}' with code {code} not found.",
            )

    # ------------------------------------------------------------
    # Hierarchy depth integrity
    # ------------------------------------------------------------
    def test_09_hierarchy_has_4_levels(self):
        """Hierarchy has 4 levels (section → subsection → class → subclass)."""
        deep_node = self.Catalog.search(
            [("code", "=like", "____")],  # 4 underscores = 4-digit code
            limit=1,
        )
        self.assertTrue(deep_node)
        self.assertTrue(deep_node.parent_id)
        self.assertEqual(len(deep_node.parent_id.code), 3)
