from odoo import _, api, fields, models
from odoo.exceptions import ValidationError


class HrJobClassification(models.Model):
    _name = "l10n.ua.hr.job.classification"
    _description = "Job Classification"
    _order = "code, name"

    name = fields.Char(required=True, index=True)
    code = fields.Char(
        "KP Code",
        required=True,
        index=True,
        help="DK 003:2010 profession code (Класифікатор професій)",
    )
    description = fields.Text()
    active = fields.Boolean(default=True)
    profession_classifier_catalog_id = fields.Many2one(
        "l10n.ua.hr.job.classification.catalog",
        "Profession Classifier Catalog",
        ondelete="restrict",
        index=True,
    )

    # NOTE: КП codes are not unique — one 4-digit code maps to many job titles.
    # Therefore no SQL unique constraint on `code`.


class ProfessionClassifierCatalog(models.Model):
    _name = "l10n.ua.hr.job.classification.catalog"
    _description = "Job Classification Catalog"
    _parent_name = "parent_id"
    _parent_store = True
    _rec_name = "complete_name"
    _order = "code"

    name = fields.Char(required=True)
    code = fields.Char(index=True)
    complete_name = fields.Char(
        compute="_compute_complete_name",
        store=True,
        recursive=True,
    )
    complete_code = fields.Char(
        compute="_compute_complete_code",
        store=True,
        recursive=True,
    )
    parent_id = fields.Many2one(
        "l10n.ua.hr.job.classification.catalog",
        "Parent Catalog",
        index=True,
        ondelete="cascade",
    )
    parent_path = fields.Char(index=True)
    child_ids = fields.One2many(
        "l10n.ua.hr.job.classification.catalog", "parent_id", "Children"
    )
    pc_count = fields.Integer(
        "# Profession Classifier",
        compute="_compute_job_classification_count",
        help="The number of Profession Classifiers under this category "
        "(includes children categories).",
    )
    profession_classifier_ids = fields.One2many(
        comodel_name="l10n.ua.hr.job.classification",
        inverse_name="profession_classifier_catalog_id",
    )
    active = fields.Boolean(default=True)

    @api.depends("code", "parent_id.complete_code")
    def _compute_complete_code(self):
        for prof_class in self:
            if prof_class.parent_id and prof_class.parent_id.code:
                prof_class.complete_code = (
                    f"{prof_class.parent_id.complete_code} / {prof_class.code}"
                )
            else:
                prof_class.complete_code = prof_class.code or ""

    @api.depends("name", "complete_code")
    def _compute_complete_name(self):
        for prof_class in self:
            _comp_code = prof_class.complete_code
            if _comp_code:
                prof_class.complete_name = f"{_comp_code} : {prof_class.name}"
            else:
                prof_class.complete_name = prof_class.name or ""

    @api.depends("profession_classifier_ids")
    def _compute_job_classification_count(self):
        read_group_res = self.env["l10n.ua.hr.job.classification"]._read_group(
            [("profession_classifier_catalog_id", "child_of", self.ids)],
            ["profession_classifier_catalog_id"],
            ["__count"],
        )
        group_data = {catalog.id: count for catalog, count in read_group_res}
        for categ in self:
            count = 0
            for sub_id in categ.search([("id", "child_of", categ.ids)]).ids:
                count += group_data.get(sub_id, 0)
            categ.pc_count = count

    @api.depends("complete_name", "name")
    @api.depends_context("hierarchical_naming")
    def _compute_display_name(self):
        if self.env.context.get("hierarchical_naming", True):
            return super()._compute_display_name()
        for record in self:
            record.display_name = record.name

    @api.constrains("parent_id")
    def _check_catalog_recursion(self):
        if self._has_cycle():
            raise ValidationError(_("You cannot create recursive catalog."))

    def action_view_classifications(self):
        """Open classifications recursively under this catalog and its children.

        Matches the recursive count in ``pc_count`` (both use ``child_of``),
        so the drill-down list shows the same records that were counted.
        """
        self.ensure_one()
        action = self.env["ir.actions.act_window"]._for_xml_id(
            "l10n_ua_hr_job_classifier.l10n_ua_hr_job_classification_action"
        )
        action["domain"] = [
            ("profession_classifier_catalog_id", "child_of", self.id),
        ]
        return action
