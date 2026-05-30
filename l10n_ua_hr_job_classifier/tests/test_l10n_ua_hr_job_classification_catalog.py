from psycopg2 import IntegrityError

from odoo.exceptions import UserError
from odoo.tests import tagged
from odoo.tools import mute_logger

from .common import TestL10nUaHrJobClassifierCommon


@tagged("post_install", "-at_install", "l10n_ua_hr_job_classifier")
class TestCatalog(TestL10nUaHrJobClassifierCommon):
    """Tests for model l10n.ua.hr.job.classification.catalog."""

    def test_01_create_root_catalog(self):
        """Create node root for parent_id."""
        root = self.Catalog.create(
            {
                "name": "Standalone Root",
                "code": "8",
            }
        )
        self.assertFalse(root.parent_id)
        self.assertEqual(root.code, "8")
        self.assertEqual(root.complete_name, "8 : Standalone Root")

    def test_02_create_child_catalog(self):
        """Creating a child node with parent_id."""
        child = self.Catalog.create(
            {
                "name": "Child of Root",
                "code": "91",
                "parent_id": self.cat_root.id,
            }
        )
        self.assertEqual(child.parent_id, self.cat_root)

    def test_03_complete_name_hierarchy(self):
        """complete_name contains the full path, including all parent directories."""
        self.assertEqual(
            self.cat_subclass.complete_name, "T1 / T11 / T111 / T1111 : Test Subclass"
        )

    def test_04_complete_name_without_code(self):
        """complete_name works correctly for nodes without code."""
        nameless = self.Catalog.create(
            {
                "name": "No Code Node",
            }
        )
        self.assertEqual(nameless.complete_name, "No Code Node")

    def test_05_complete_name_updates_on_parent_change(self):
        """complete_name is updated when parent_id changes."""
        new_parent = self.Catalog.create(
            {
                "name": "New Parent",
                "code": "7",
            }
        )
        self.cat_sub.parent_id = new_parent
        self.cat_sub.invalidate_recordset(["complete_name"])
        # Child node now has an updated complete_name
        self.assertIn("7 / T11", self.cat_class.complete_name)

    def test_06_parent_path_is_set(self):
        """parent_path is populated automatically via _parent_store."""
        self.assertTrue(self.cat_subclass.parent_path)
        # The path must contain the ids of all parents
        path_ids = [int(x) for x in self.cat_subclass.parent_path.split("/") if x]
        # The last id in the path is the node itself
        self.assertIn(self.cat_root.id, path_ids)
        self.assertIn(self.cat_sub.id, path_ids)
        self.assertIn(self.cat_class.id, path_ids)

    def test_07_pc_count_zero_when_no_classifications(self):
        """pc_count = 0 for a catalogue with no classifications."""
        empty_cat = self.Catalog.create(
            {
                "name": "Empty",
                "code": "6",
            }
        )
        self.assertEqual(empty_cat.pc_count, 0)

    def test_08_pc_count_includes_direct_classifications(self):
        """pc_count takes into account the direct classifications under the node."""
        self.Classification.create(
            {
                "name": "Direct Profession",
                "code": "9999",
                "profession_classifier_catalog_id": self.cat_subclass.id,
            }
        )
        # invalidate cached compute
        self.cat_subclass.invalidate_recordset(["pc_count"])
        self.assertGreaterEqual(self.cat_subclass.pc_count, 1)

    def test_09_pc_count_recursive(self):
        """pc_count recursively takes into account the classifications
        in subdirectories."""
        # In setUp we already have self.classification in cat_subclass
        # Recursively it should be visible from cat_root
        self.cat_root.invalidate_recordset(["pc_count"])
        self.assertGreaterEqual(self.cat_root.pc_count, 1)

    def test_10_recursion_validation(self):
        """An attempt to make a node the parent of itself is blocked."""
        with self.assertRaises(UserError):
            self.cat_root.parent_id = self.cat_root

    def test_11_recursion_through_chain(self):
        """A circular dependency via the parent chain is blocked."""
        with self.assertRaises(UserError):
            self.cat_root.parent_id = self.cat_subclass

    def test_12_required_name(self):
        """name is required."""
        with self.assertRaises(IntegrityError), mute_logger("odoo.sql_db"):
            self.Catalog.create({"code": "5"})

    def test_13_active_flag_default(self):
        """active = True by default."""
        new_cat = self.Catalog.create(
            {
                "name": "Active Test",
                "code": "4",
            }
        )
        self.assertTrue(new_cat.active)

    def test_14_archived_catalog_not_in_default_search(self):
        """Archived directories do not appear in the standard search."""
        archived = self.Catalog.create(
            {
                "name": "Archived Cat",
                "code": "3",
                "active": False,
            }
        )
        found = self.Catalog.search([("name", "=", "Archived Cat")])
        self.assertFalse(found)

        found_with_inactive = self.Catalog.with_context(active_test=False).search(
            [("name", "=", "Archived Cat")]
        )
        self.assertIn(archived, found_with_inactive)

    def test_15_child_of_domain(self):
        """Domain ("id", "child_of", X) return node."""
        descendants = self.Catalog.search(
            [
                ("id", "child_of", self.cat_root.id),
            ]
        )
        self.assertIn(self.cat_root, descendants)
        self.assertIn(self.cat_sub, descendants)
        self.assertIn(self.cat_class, descendants)
        self.assertIn(self.cat_subclass, descendants)

    def test_16_action_view_classifications(self):
        """action_view_classifications returns recursive domain."""
        action = self.cat_root.action_view_classifications()
        self.assertEqual(action["res_model"], "l10n.ua.hr.job.classification")
        self.assertEqual(
            action["domain"],
            [("profession_classifier_catalog_id", "child_of", self.cat_root.id)],
        )
