# -*- coding: utf-8 -*-

from odoo import models, fields, api


class DiscordChannel(models.Model):
    _inherit = "discord.channel"

    target_for_messages = fields.Boolean(string="Target for Messages", default=False)

    @api.model
    def get_target_channels_for_tsm_message(self):
        # So this can be more generilized
        return self.search([('target_for_messages', '=', True)])
