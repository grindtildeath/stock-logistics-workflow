# Copyright 2020 Camptocamp SA
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl)
from odoo import _, api, fields, models


class ResPartner(models.Model):

    _inherit = "res.partner"

    delivery_time_preference = fields.Selection(
        [("direct", "As soon as possible"), ("fix_weekdays", "Fixed week days")],
        string="Delivery time schedule preference",
        default="direct",
        required=True,
        help="Define the scheduling preference for delivery orders:\n\n"
        "* As soon as possible: Do not postpone deliveries\n"
        "* Fixed week days: Postpone deliveries to the next preferred "
        "weekday",
    )

    delivery_time_window_ids = fields.One2many(
        'partner.delivery.time.window', 'partner_id'
    )

    def get_delivery_windows(self, day_name=None):
        """
        Return the list of delivery windows by partner id for the given day

        :param day: The day name (see time.weekday, ex: 0,1,2,...)
        :return: dict partner_id: delivery_window recordset
        """
        res = {}
        domain = [("partner_id", "in", self.ids)]
        if day_name is not None:
            week_day_id = self.env["time.weekday"]._get_id_by_name(
                day_name
            )
            domain.append(("weekday_ids", "in", week_day_id))
        windows = self.env["partner.delivery.time.window"].search(
            domain
        )
        for window in windows:
            if not res.get(window.partner_id.id):
                res[window.partner_id.id] = self.env["partner.delivery.time.window"].browse()
            res[window.partner_id.id] |= window
        return res

    def is_in_delivery_window(self, date_time):
        self.ensure_one()
        windows = self.get_delivery_windows(date_time.weekday())
        for w in windows:
            if w.get_start_time() <= date_time.time() <= w.get_end_time():
                return True
        return False
