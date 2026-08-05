{
    "name": "Ukraine - HR Job Classifier (DK 003:2010)",
    "version": "18.0.1.0.0",
    "category": "Localization/Ukraine",
    "license": "AGPL-3",
    "author": "Holodaieva Olha, Odoo Community Association (OCA)",
    "maintainers": ["PeleOlala"],
    "website": "https://github.com/OCA/l10n-ukraine",
    "summary": "Ukrainian National Classifier of Occupations DK 003:2010",
    "countries": ["ua"],
    "depends": [
        "hr",
    ],
    "data": [
        "security/ir.model.access.csv",
        "data/l10n.ua.hr.job.classification.catalog-data.csv",
        "data/l10n.ua.hr.job.classification-data.csv",
        "views/l10n_ua_hr_job_classification_views.xml",
    ],
    "installable": True,
    "application": False,
}
