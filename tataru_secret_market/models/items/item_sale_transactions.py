from odoo import models, fields, api
import requests
import datetime


class ItemSaleTransactions(models.Model):
    _name = 'tataru_secret_market.item_sale_transactions'
    _order = "item_selled, sale_date"

    item_selled = fields.Many2one('tataru_secret_market.items')
    world_id = fields.Many2one('tataru_secret_market.worlds')
    price = fields.Integer()
    buyer_name = fields.Char()
    quantity = fields.Integer()
    high_quality = fields.Boolean()
    sale_date = fields.Datetime()
    sale_date_timestamp = fields.Integer()
    total_price = fields.Integer(compute='_compute_total_price')

    @api.depends('price', 'quantity')
    def _compute_total_price(self):
        for record in self:
            record.total_price = record.price * record.quantity

    @api.model
    def sync_item_transactions(self, item, world):
        try:
            res = requests.get(f"https://universalis.app/api/history/{world.name}/{item.unique_id}")
            res.raise_for_status()
        except requests.exceptions.HTTPError as err:
            raise Exception(err)

        data = res.json()
        for transaction in data["entries"]:
            self.env['tataru_secret_market.item_sale_transactions'].create({
                'item_selled': item.id,
                'world_id': world.id,
                'price': transaction['pricePerUnit'],
                'quantity': transaction['quantity'],
                'sale_date': fields.Datetime.to_string(datetime.datetime.fromtimestamp(int(transaction['timestamp']))),
                'sale_date_timestamp': int(transaction['timestamp']),
                'buyer_name': transaction['buyerName'],
                'high_quality': bool(transaction['hq'])
            })
