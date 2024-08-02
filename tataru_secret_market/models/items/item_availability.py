from odoo import models, fields, api
import requests
from datetime import datetime


class ItemAvailability(models.Model):
    _name = 'tataru_secret_market.item_availability'
    _order = "total_price_with_tax"

    # general infos
    item_id = fields.Many2one('tataru_secret_market.items')
    world_id = fields.Many2one('tataru_secret_market.worlds')
    world_name = fields.Char(related='world_id.name')
    data_center_id = fields.Many2one(related='world_id.data_center_id')
    item_name = fields.Char(related='item_id.name')
    listing_id = fields.Char()

    # item infos
    high_quality = fields.Boolean()
    price = fields.Integer()
    quantity = fields.Integer()
    tax = fields.Integer()
    total_price = fields.Integer(compute='_compute_total_price')
    total_price_with_tax = fields.Integer(compute='_compute_total_price')

    # retainer infos
    reteiner_name = fields.Char()
    reteiner_id = fields.Char()

    @api.depends('price', 'quantity', 'tax')
    def _compute_total_price(self):
        for record in self:
            record.total_price = record.price * record.quantity
            record.total_price_with_tax = record.total_price + record.tax

    @api.model
    def sync_item_availability(self, items, data_center):
        is_more_then_one = len(items) > 1
        items_str = ",".join([str(item.unique_id) for item in items]) if is_more_then_one else str(items[0].unique_id)
        api_url = f"https://universalis.app/api/{data_center.name}/{items_str}?listings=50&entries=0"

        try:
            res = requests.get(api_url)
            res.raise_for_status()
        except requests.exceptions.HTTPError as err:
            raise Exception(err)

        data = res.json()

        # TODO - CODE REFATORING!
        if not is_more_then_one:
            item = items[0]
            item.availability_ids.unlink()  # per il momento elimino tutto e ricreo poi andrebbe cercato di aggiornare e basta
            if "listings" not in data or not data["listings"]:
                return
            for entry in data["listings"]:
                world_id = self.env['tataru_secret_market.worlds'].search([('unique_id', '=', int(entry['worldID']))])
                self.env['tataru_secret_market.item_availability'].create([{
                    'item_id': item.id,
                    'world_id': world_id.id,
                    'high_quality': bool(entry['hq']),
                    'price': entry['pricePerUnit'],
                    'quantity': entry['quantity'],
                    'tax': entry['tax'],
                    'reteiner_name': entry['retainerName'],
                    'reteiner_id': entry['retainerID'],
                    'listing_id': entry['listingID']
                }])

        else:
            items_list_json = data["items"]
            for item_json in items_list_json:
                item = items.filtered(lambda x: x.unique_id == int(item_json["itemID"])).ensure_one()
                item.availability_ids.unlink()
                # time = item_json["lastUploadTime"]

                item.universalis_last_sync_time_availability = fields.Datetime.now()
                for entry in item_json["listings"]:
                    world_id = self.env['tataru_secret_market.worlds'].search([('unique_id', '=', int(entry['worldID']))])
                    self.env['tataru_secret_market.item_availability'].create([{
                        'item_id': item.id,
                        'world_id': world_id.id,
                        'high_quality': bool(entry['hq']),
                        'price': entry['pricePerUnit'],
                        'quantity': entry['quantity'],
                        'tax': entry['tax'],
                        'reteiner_name': entry['retainerName'],
                        'reteiner_id': entry['retainerID'],
                        'listing_id': entry['listingID']
                    }])
