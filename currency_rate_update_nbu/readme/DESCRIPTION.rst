This module provides base for building exchange rates providers and bundles
following built-in providers:

 * **National Bank of Ukraine**:
   the official currency rate of the Ukrainian hryvnia to foreign currencies.
   Source in UAH, for more details see `corresponding
   NBU page <https://bank.gov.ua/ua/open-data/api-dev>`_.

This module is compatible with ``currency_rate_inverted`` module provided by
OCA, that allows to maintain exchange rates in inverted format, helping to
resolve rounding issues.
