# Copyright (C) 2018 - Today: GRAP (http://www.grap.coop)
# @author: Sylvain LE GAL (https://twitter.com/legalsylvain)
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from datetime import datetime

from odoo import _, api, fields, models
from odoo.exceptions import UserError


class IrCronInactivityPeriod(models.Model):
    _name = "ir.cron.inactivity.period"

    cron_id = fields.Many2one(comodel_name="ir.cron", ondelete="cascade", required=True)
    type = fields.Selection(
        string="Type",
        selection=[
            ("hour", "Hour"),
        ],
        required=True,
        default="hour",
    )
    inactivity_hour_begin = fields.Float(string="Begin Hour", default=0)
    inactivity_hour_end = fields.Float(string="End Hour", default=1)

    @api.constrains("inactivity_hour_begin", "inactivity_hour_end")
    def _check_activity_hour(self):
        for period in self:
            if period.inactivity_hour_begin < 0 and period.inactivity_hour_begin >= 24:
                raise UserError(_("The Begin Hour must be between 0 and 23"))
            if period.inactivity_hour_end < 0 and period.inactivity_hour_end >= 24:
                raise UserError(_("The End Hour must be between 0 and 23"))

    def _check_inactivity_period(self):
        res = []
        for period in self:
            res.append(period._check_inactivity_period_one())
        return res

    def _check_inactivity_period_one(self):
        self.ensure_one()
        now = fields.Datetime.context_timestamp(self, datetime.now())
        if self.type == "hour":
            begin_inactivity = now.replace(
                hour=int(self.inactivity_hour_begin),
                minute=int((self.inactivity_hour_begin % 1) * 60),
                second=0,
            )
            end_inactivity = now.replace(
                hour=int(self.inactivity_hour_end),
                minute=int((self.inactivity_hour_end % 1) * 60),
                second=0,
            )
            return now >= begin_inactivity and now < end_inactivity
        else:
            raise UserError(
                _("Unimplemented Feature: Inactivity Period type '%s'") % (self.type)
            )
