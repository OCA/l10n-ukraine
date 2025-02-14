from odoo import api, fields, models


class ResPartnerUARequisites(models.Model):
    _name = "res.partner.ua.requisites"
    _description = "Partner Requisites"
    _order = "date DESC"

    partner_id = fields.Many2one(
        "res.partner", "Partner", index=True, ondelete="cascade"
    )
    date = fields.Date(
        "Date of requisites",
        index=True,
        required=True,
        default=fields.Date.today(),
        help="Date when requisites become active.",
    )

    ua_legal_name = fields.Char(
        "Legal full name", help="The full legal name of the partner.", translate=True
    )
    ua_legal_short_name = fields.Char(
        help="The short legal name of the partner.", translate=True
    )
    ua_tin = fields.Char("Individual tax identification number", size=13)
    ua_vat_certificate = fields.Char("VAT certificate number", size=13)
    ua_enterprise_code = fields.Char(size=13)
    ua_director_id = fields.Many2one("res.partner", "Director", ondelete="restrict")
    ua_director_reason = fields.Text()
    ua_director_accountant_id = fields.Many2one("res.partner", ondelete="restrict")
    ua_responsible_id = fields.Many2one("res.partner", ondelete="restrict")
    ua_legal_address = fields.Many2one("res.partner")
    ua_postal_address = fields.Many2one("res.partner")

    # Make unique by (partner_id, date)
    _sql_constraints = [
        (
            "partner_id_date_uniq",
            "unique(partner_id, date)",
            "There must be only one requisites record " "for one partner on one date!",
        )
    ]

    @api.model
    def default_get(self, field_list):
        if "partner_id" in self.env.context:
            # Get defaults from partner
            partner = self.env["res.partner"].browse(self.env.context["partner_id"])

            def to_id(obj):
                """Convert object to ID if it is possible"""
                if obj:
                    return obj.id
                return False

            return super(
                ResPartnerUARequisites,
                self.with_context(
                    default_ua_legal_name=partner.ua_legal_name,
                    default_ua_legal_short_name=partner.ua_legal_short_name,
                    default_ua_tin=partner.ua_tin,
                    default_ua_vat_certificate=partner.ua_vat_certificate,
                    default_ua_enterprise_code=partner.ua_enterprise_code,
                    default_ua_director_id=partner.ua_director_id.id,
                    default_ua_director_reason=partner.ua_director_reason,
                    default_ua_director_accountant_id=(
                        partner.ua_director_accountant_id.id
                    ),
                    default_ua_responsible_id=partner.ua_responsible_id.id,
                ),
            ).default_get(field_list)
        return super(ResPartnerUARequisites, self).default_get(field_list)

    def name_get(self):
        res = []
        for r in self:
            res += [(r.id, "%s <%s>" % (r.partner_id.name, r.date))]
        return res

    # TODO: implement copy-on-write bechavior
