from odoo.tests.common import TransactionCase


class TestRequisites(TransactionCase):
    def setUp(self):
        super(TestRequisites, self).setUp()
        self.ResPartner = self.env["res.partner"]
        self.partner = self.ResPartner.search([], limit=1)[0]

        # Requisites data
        self.requisites_data_2016_08_09 = {
            "date": "2016-08-09",
            "ua_legal_name": "LName Update X3",
            "ua_legal_short_name": "LSName",
            "ua_tin": "TIN",
            "ua_vat_certificate": "PCNumber",
            "ua_enterprise_code": "ECode",
            "ua_director_reason": "CReason",
        }

        self.requisites_data_2015_05_13 = dict(
            self.requisites_data_2016_08_09,
            date="2015-05-13",
            ua_legal_name="LName Update",
        )
        self.requisites_data_2014_01_30 = dict(
            self.requisites_data_2016_08_09,
            date="2014-01-30",
            ua_legal_name="LName",
        )

    def test_10_partner_write_requisite(self):
        self.assertFalse(self.partner.ua_requisites_ids)

        data = self.requisites_data_2014_01_30

        # Ensure all partner fields related to data is False
        for field in data:
            if field not in ["date"]:
                self.assertFalse(self.partner[field])

        # NOTE: using data.copy() to pass copy of data to write method.
        # TODO: Test withou copy, write method must not modify incoming data
        # This is required to avoid it been modified by write method.
        self.partner.write({"ua_requisites_ids": [(0, 0, data.copy())]})

        # Test that partner fields have right values
        for field in data:
            if field not in ["date"]:
                self.assertEqual(self.partner[field], data[field])

        # Ensure requisites record created
        self.assertEqual(len(self.partner.ua_requisites_ids), 1)

        requisites = self.partner.ua_requisites_ids[0]

        # Ensure, requisites record have right values
        for field in data:
            if field not in ["date"]:
                self.assertEqual(requisites[field], data[field])

        # Remove requisite lines and ensure partner's requisites evaluated to
        # False now.
        self.partner.ua_requisites_ids.unlink()

        # Ensure all partner fields related to data is False
        for field in data:
            if field not in ["date"]:
                self.assertFalse(self.partner[field])

    def test_20_requisite_create_changes_partner_requisite(self):
        """Ensure that, when new requisite record is created,
        then corresponding partner fields reflect that change.
        """
        self.assertFalse(self.partner.ua_requisites_ids)

        # Create new requisites record
        data = self.requisites_data_2014_01_30
        self.partner.write({"ua_requisites_ids": [(0, 0, data.copy())]})

        # Ensure requisites record created
        self.assertEqual(len(self.partner.ua_requisites_ids), 1)

        # test legal name is correct
        self.assertEqual(self.partner.ua_legal_name, "LName")

        # Create new record with legal name updated
        data2 = self.requisites_data_2016_08_09
        self.partner.write({"ua_requisites_ids": [(0, 0, data2.copy())]})

        # Ensure requisites record created
        self.assertEqual(len(self.partner.ua_requisites_ids), 2)

        # Test legal name set on partner is correct
        self.assertEqual(self.partner.ua_legal_name, "LName Update X3")

        # Create new record with legal name updated
        data3 = self.requisites_data_2015_05_13
        self.partner.write({"ua_requisites_ids": [(0, 0, data3.copy())]})

        # Ensure requisites record created
        self.assertEqual(len(self.partner.ua_requisites_ids), 3)

        # Test legal name set on partner were not updated.
        # requisites date of `data3` is before requisites date for `data2`
        self.assertEqual(self.partner.ua_legal_name, "LName Update X3")

    def test_30_requisite_write_changes_partner_requisite(self):
        """Ensure that, when requisites record is changed,
        then corresponding partner fields reflect that change.
        """
        self.assertFalse(self.partner.ua_requisites_ids)

        # Create new requisites record
        data = self.requisites_data_2015_05_13.copy()
        self.partner.write({"ua_requisites_ids": [(0, 0, data.copy())]})

        # Ensure requisites record created
        self.assertEqual(len(self.partner.ua_requisites_ids), 1)

        requisites = self.partner.ua_requisites_ids[0]

        # test legal name is correct
        self.assertEqual(self.partner.ua_legal_name, "LName Update")

        # Update requisite's legal name
        requisites.write({"ua_legal_name": "LName Update X42"})

        # test partner's legal name is updated too
        self.assertEqual(self.partner.ua_legal_name, "LName Update X42")

    def test_40_partner_current_requisites(self):
        """Test partner's `current_requisites_id` field"""
        self.assertFalse(self.partner.ua_requisites_ids)
        self.assertFalse(self.partner.ua_last_requisites_id)
        self.assertFalse(self.partner.ua_current_requisites_id)

        # Create new requisites record
        data = self.requisites_data_2014_01_30
        self.partner.write({"ua_requisites_ids": [(0, 0, data.copy())]})

        # Ensure requisites record created
        self.assertEqual(len(self.partner.ua_requisites_ids), 1)

        # test legal name is correct
        self.assertEqual(self.partner.ua_legal_name, "LName")
        self.assertEqual(self.partner.ua_last_requisites_id.ua_legal_name, "LName")
        self.assertEqual(self.partner.ua_current_requisites_id.ua_legal_name, "LName")

        # Create new record with legal name updated
        data2 = self.requisites_data_2015_05_13
        self.partner.write({"ua_requisites_ids": [(0, 0, data2.copy())]})

        # Ensure requisites record created
        self.assertEqual(len(self.partner.ua_requisites_ids), 2)

        # Test legal name set on partner is correct
        self.assertEqual(self.partner.ua_legal_name, "LName Update")
        self.assertEqual(
            self.partner.ua_last_requisites_id.ua_legal_name, "LName Update"
        )
        self.assertEqual(
            self.partner.ua_current_requisites_id.ua_legal_name, "LName Update"
        )

        # TODO Not using now, but have to
        # # Test partner current requisites without date in context
        # partner_1 = self.partner
        # self.assertEqual(partner_1.last_requisites_id,
        #                  partner_1.current_requisites_id)
        # self.assertEqual(
        #     fields.Date.to_string(
        #         partner_1.current_requisites_id.date_requisites),
        #         '2015-05-13')
        #
        # # Test if date = 2016-11-12, then requisites returned are
        # # with date = 2015-05-13
        # partner_2 = self.partner.with_context(date='2016-11-12')
        # self.assertEqual(
        #     fields.Date.to_string(
        #         partner_2.current_requisites_id.date_requisites),
        #         '2015-05-13')
        #
        # # Test if date = 2015-05-13, then requisites returned are
        # # that were date = 2015-05-13
        # partner_3 = self.partner.with_context(date='2015-05-13')
        # self.assertEqual(
        #     fields.Date.to_string(
        #         partner_3.current_requisites_id.date_requisites),
        #         '2015-05-13')
        #
        # # Test if date = 2015-02-20, then requisites returned are
        # # that were date = 2014-01-30
        # partner_4 = self.partner.with_context(date='2015-02-20')
        # self.assertEqual(
        #     fields.Date.to_string(
        #         partner_4.current_requisites_id.date_requisites),
        #         '2014-01-30')
        #
        # # Test if date = 2014-01-30, then requisites returned are
        # # that were date = 2014-01-30
        # partner_5 = self.partner.with_context(date='2015-01-30')
        # self.assertEqual(
        #     fields.Date.to_string(
        #         partner_5.current_requisites_id.date_requisites),
        #         '2014-01-30')
        #
        # # Test if date = 2013-11-27, then requisites returned are
        # # that were date = 2014-01-30
        # partner_6 = self.partner.with_context(date='2013-11-27')
        # self.assertEqual(
        #     fields.Date.to_string(
        #         partner_6.current_requisites_id.date_requisites),
        #         '2014-01-30')

    def test_50_default_get(self):
        PartnerRequisites = self.env["res.partner.ua.requisites"]
        self.assertFalse(self.partner.ua_requisites_ids)

        # Prepare requisites data
        data = self.requisites_data_2014_01_30

        # Ensure all partner fields related to data is False
        for field in data:
            if field not in ["date"]:
                self.assertFalse(self.partner[field])

        # Ensure that default_get without partner in context at this stage
        # returns False for all fields
        default_get = PartnerRequisites.default_get(list(data.keys()))
        for field in data:
            if field not in ["date"]:
                self.assertFalse(default_get.get(field, False))

        # Ensure that default_get with partner in context at this stage
        # returns False for all fields
        default_get = PartnerRequisites.with_context(
            partner_id=self.partner.id
        ).default_get(list(data.keys()))
        for field in data:
            if field not in ["date"]:
                self.assertFalse(default_get.get(field, False))

        # Add requisites record
        self.partner.write({"ua_requisites_ids": [(0, 0, data.copy())]})

        # Ensure that default_get without partner in context at this stage
        # returns False for all fields
        default_get = PartnerRequisites.default_get(list(data.keys()))
        for field in data:
            if field not in ["date"]:
                self.assertFalse(default_get.get(field, False))

        # Ensure that default_get with partner in context at this stage
        # returns correct values for all fields
        default_get = PartnerRequisites.with_context(
            partner_id=self.partner.id
        ).default_get(list(data.keys()))
        for field in data:
            if field not in ["date"]:
                self.assertEqual(default_get.get(field, False), data[field])
