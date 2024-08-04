# -*- coding: utf-8 -*-

# from odoo import models, fields, api


# class tsm_x_discord(models.Model):
#     _name = 'tsm_x_discord.tsm_x_discord'
#     _description = 'tsm_x_discord.tsm_x_discord'

#     name = fields.Char()
#     value = fields.Integer()
#     value2 = fields.Float(compute="_value_pc", store=True)
#     description = fields.Text()
#
#     @api.depends('value')
#     def _value_pc(self):
#         for record in self:
#             record.value2 = float(record.value) / 100
