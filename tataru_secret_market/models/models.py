# -*- coding: utf-8 -*-

# from odoo import models, fields, api


# class tataru_secret_market(models.Model):
#     _name = 'tataru_secret_market.tataru_secret_market'
#     _description = 'tataru_secret_market.tataru_secret_market'

#     name = fields.Char()
#     value = fields.Integer()
#     value2 = fields.Float(compute="_value_pc", store=True)
#     description = fields.Text()
#
#     @api.depends('value')
#     def _value_pc(self):
#         for record in self:
#             record.value2 = float(record.value) / 100
