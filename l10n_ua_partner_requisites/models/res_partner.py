from odoo import api, fields, models


class ResPartner(models.Model):
    _inherit = "res.partner"

    # partner requisites
    ua_requisites_ids = fields.One2many(
        comodel_name="res.partner.ua.requisites",
        inverse_name="partner_id",
        string="Periodical Partner Requisites",
    )
    ua_last_requisites_id = fields.Many2one(
        comodel_name="res.partner.ua.requisites",
        string="Last Partner Requisites",
        compute="_compute_ua_last_requisites_id",
        store=True,
        readonly=True,
    )
    ua_current_requisites_id = fields.Many2one(
        comodel_name="res.partner.ua.requisites",
        string="Current Requisites",
        compute="_compute_ua_current_requisites",
        store=False,
        readonly=True,
        help="If date is in context, that this field, returns requisites, "
        "that were active for that date",
    )

    # Requisites-related fields
    ua_legal_name = fields.Char(
        "Legal full name",
        translate=True,
        store=True,
        readonly=True,
        related="ua_last_requisites_id.ua_legal_name",
        help="The full legal name of the partner.",
    )
    ua_legal_short_name = fields.Char(
        translate=True,
        store=True,
        readonly=True,
        related="ua_last_requisites_id.ua_legal_short_name",
        help="The short legal name of the partner.",
    )
    ua_tin = fields.Char(
        "Individual tax identification number",
        related="ua_last_requisites_id.ua_tin",
        size=13,
        readonly=True,
        store=True,
    )
    ua_vat_certificate = fields.Char(
        "VAT certificate number",
        size=13,
        store=True,
        readonly=True,
        related="ua_last_requisites_id.ua_vat_certificate",
    )
    ua_enterprise_code = fields.Char(
        size=13,
        store=True,
        index=True,
        readonly=True,
        related="ua_last_requisites_id.ua_enterprise_code",
    )
    ua_director_reason = fields.Text(
        string="Director Reason",
        store=True,
        readonly=True,
        related="ua_last_requisites_id.ua_director_reason",
    )
    ua_director_id = fields.Many2one(
        comodel_name="res.partner",
        string="Director",
        related="ua_last_requisites_id.ua_director_id",
        readonly=True,
        store=True,
    )
    ua_director_accountant_id = fields.Many2one(
        string="Director Accountant",
        comodel_name="res.partner",
        readonly=True,
        related="ua_last_requisites_id.ua_director_accountant_id",
        store=True,
    )
    ua_responsible_id = fields.Many2one(
        comodel_name="res.partner",
        readonly=True,
        related="ua_last_requisites_id.ua_responsible_id",
        store=True,
    )
    ua_legal_address = fields.Many2one(
        comodel_name="res.partner",
        readonly=True,
        related="ua_last_requisites_id.ua_legal_address",
        store=True,
    )
    ua_postal_address = fields.Many2one(
        "res.partner",
        readonly=True,
        related="ua_last_requisites_id.ua_postal_address",
        store=True,
    )

    @api.depends("ua_requisites_ids", "ua_requisites_ids.partner_id")
    def _compute_ua_last_requisites_id(self):
        """Compute last requisites"""
        for partner in self:
            if partner.ua_requisites_ids:
                partner.ua_last_requisites_id = partner.ua_requisites_ids.sorted(
                    key=lambda r: r.date, reverse=True
                )[0]
            else:
                partner.ua_last_requisites_id = False

    @api.depends("ua_requisites_ids", "ua_requisites_ids.partner_id")
    def _compute_ua_current_requisites(self):
        """Compute last requisites for date specified in context

        Note: In case, when partner have requisites for following dates:
            - 2016-08-09
            - 2015-05-13
            - 2014-01-30
        Then, following examples are valid:

            date_in_context   |   requisites used
            -------------------------------------
            2017-01-12        |   2016-08-09
            2016-09-09        |   2016-08-09
            2016-04-15        |   2015-05-13
            2014-01-30        |   2014-01-30
            2013-11-23        |   2014-01-30   <- NOTE: Edge case
        """
        for partner in self:
            requisites = partner.ua_last_requisites_id
            if self.env.context.get("date", False):
                requisites = self.env["partner.requisites"].search(
                    [
                        ("partner_id", "=", partner.id),
                        ("date", "<=", self.env.context["date"]),
                    ],
                    order="date DESC",
                    limit=1,
                )
                if not requisites:
                    requisites = self.env["partner.requisites"].search(
                        [
                            ("partner_id", "=", partner.id),
                            ("date", ">=", self.env.context["date"]),
                        ],
                        order="date ASC",
                        limit=1,
                    )
            partner.ua_current_requisites_id = requisites
