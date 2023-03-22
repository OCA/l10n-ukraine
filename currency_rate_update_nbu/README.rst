========================
Currency Rate Update NBU
========================

This module provides base for building exchange rates providers and bundles
following built-in providers:

 * **National Bank of Ukraine**:
   the official currency rate of the Ukrainian hryvnia to foreign currencies.
   Source in UAH, for more details see `corresponding
   NBU page <https://bank.gov.ua/ua/open-data/api-dev>`_.

This module is compatible with ``currency_rate_inverted`` module provided by
OCA, that allows to maintain exchange rates in inverted format, helping to
resolve rounding issues.

**Table of contents**

.. contents::
   :local:

Configuration
=============

To enable scheduled currency rates update:

# Go to *Invoicing > Configuration > Settings*
# Ensure *Automatic Currency Rates (OCA)* is checked

To configure currency rates providers:

# Go to *Invoicing > Configuration > Currency Rates Providers*
# The default NBU provider will be added during module installation with two
available currencies: USD, EUR.

Usage
=====

To update historical currency rates:

# Go to *Invoicing > Configuration > Currency Rates Providers*
# Select the "National Bank of Ukraine" provider
# Add or remove available currencies if you need.
# Launch *Actions > Update Rates Wizard*
# Configure date interval and click *Update*

Bug Tracker
===========

Bugs are tracked on `GitHub Issues <https://github.com/OCA/l10n-ukraine/issues>`_.
In case of trouble, please check there if your issue has already been reported.
If you spotted it first, help us smashing it by providing a detailed and welcomed
`feedback <https://github.com/OCA/l10n-ukraine/issues/new?body=module:%20currency_rate_update_nbu%0Aversion:%2014.0%0A%0A**Steps%20to%20reproduce**%0A-%20...%0A%0A**Current%20behavior**%0A%0A**Expected%20behavior**>`_.

Do not contact contributors directly about support or help with technical issues.

Credits
=======

Authors
~~~~~~~

* GarazdCreation

Contributors
~~~~~~~~~~~~

* Yurii Razumovskyi <garazdcreation@gmail.com>

Maintainers
~~~~~~~~~~~

This module is maintained by the OCA.

.. image:: https://odoo-community.org/logo.png
   :alt: Odoo Community Association
   :target: https://odoo-community.org

OCA, or the Odoo Community Association, is a nonprofit organization whose
mission is to support the collaborative development of Odoo features and
promote its widespread use.

This module is part of the `OCA/l10n-ukraine <https://github.com/OCA/l10n-ukraine/tree/14.0/currency_rate_update_nbu>`_ project on GitHub.

You are welcome to contribute. To learn how please visit https://odoo-community.org/page/Contribute.
