{
    "name": "Ukraine - HR Job Classification Link",
    "version": "18.0.1.0.0",
    "category": "Localization/Ukraine",
    "license": "AGPL-3",
    "author": "Holodaieva Olha, Odoo Community Association (OCA)",
    "maintainers": ["PeleOlala"],
    "website": "https://github.com/OCA/l10n-ukraine",
    "summary": "Attach the Ukrainian occupation classifier (DK 003:2010) "
    "to job positions",
    "countries": ["ua"],
    "depends": [
        "hr",
        "l10n_ua_hr_job_classifier",
    ],
    "data": [
        "views/hr_job_views.xml",
    ],
    "installable": True,
    "application": False,
}
