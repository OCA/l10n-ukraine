This addon adds following fields to res.partner model:

- Legal full name
- Legal short name
- Individual tax identification number
- Enterprise code
- Chief reason
- Director
- Chief accountant
- Responsible officer

Data for these fields is stored in separate model,
so it is possible to have values for this fields for different dates,
which is useful in cases, when company change some of this information.


Partner's requisites for specified date
---------------------------------------

It is possible to compute requisites for specified date.
For this case, there is implemented field ``current_requisites_id``,
which looks for ``date`` key in context, and returns requisites,
that was active for that date. If no specified date is before earliest
requisites defined for partner, earliest requisites will be returned

For example, partner have requisites for following dates:

- 2016-08-09
- 2015-05-13
- 2014-01-30

Then, following pairs are valid:

+-----------------+------------------+---------------------+
| date_in_context | requisites used  | Notes               |
+=================+==================+=====================+
|2017-01-12       |   2016-08-09     |                     |
+-----------------+------------------+---------------------+
|2016-09-09       |   2016-08-09     |                     |
+-----------------+------------------+---------------------+
|2016-04-15       |   2015-05-13     |                     |
+-----------------+------------------+---------------------+
|2014-01-30       |   2014-01-30     |                     |
+-----------------+------------------+---------------------+
|2013-11-23       |   2014-01-30     | Edge case           |
+-----------------+------------------+---------------------+
