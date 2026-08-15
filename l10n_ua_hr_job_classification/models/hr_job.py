from odoo import fields, models


class HrJob(models.Model):
    _inherit = "hr.job"

    l10n_ua_hr_job_classification_id = fields.Many2one(
        comodel_name="l10n.ua.hr.job.classification",
        string="Job Classification (DK 003:2010)",
        tracking=True,
        help="Official job classification according to the Ukrainian "
        "National Classifier of Occupations DK 003:2010. Used in "
        "state HR reports and statistical filings.",
    )
