from odoo import models, fields, api
import requests


class Worlds(models.Model):
    _name = 'tataru_secret_market.worlds'
    _order = "unique_id"

    unique_id = fields.Integer(required=True, index=True)
    name = fields.Char(required=True, index=True)

    data_center_id = fields.Many2one('tataru_secret_market.data_centers', index=True)

    @api.model
    def sync_worlds(self, starting):
        try:
            res = requests.get("https://universalis.app/api/v2/worlds")
            res.raise_for_status()
        except requests.exceptions.HTTPError as err:
            raise Exception(err)

        data = res.json()

        for world in data:
            world_id = self.env['tataru_secret_market.worlds'].search([('unique_id', '=', world['id'])])

            if not world_id:
                self.env['tataru_secret_market.worlds'].create({
                    'unique_id': world['id'],
                    'name': world['name'],
                    'data_center_id': False
                })
            else:
                world_id.write({'name': world['name']})

    @api.model
    def get_current_world(self):
        #TODO - generalizzarlo
        return self.env['tataru_secret_market.worlds'].search([('unique_id', '=', 401)])
