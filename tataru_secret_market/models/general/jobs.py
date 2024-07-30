from odoo import models, fields, api


class Jobs(models.Model):
    _name = 'tataru_secret_market.jobs'

    unique_id = fields.Integer()
    name = fields.Char()
