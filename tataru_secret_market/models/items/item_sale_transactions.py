from odoo import models, fields, api
import requests
import datetime
import logging


_logger = logging.getLogger(__name__)


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

    # item fields
    item_icon = fields.Char(related='item_selled.item_icon')
    item_icon_hd = fields.Char(related='item_selled.item_icon_hd')

    @api.depends('price', 'quantity')
    def _compute_total_price(self):
        for record in self:
            record.total_price = record.price * record.quantity

    @api.model
    def sync_item_transactions(self, items, world):
        is_more_then_one = len(items) > 1
        items_str = ",".join([str(item.unique_id) for item in items]) if is_more_then_one else str(items[0].unique_id)
        try:
            res = requests.get(f"https://universalis.app/api/v2/history/{world.name}/{items_str}?entriesToReturn=500&minSalePrice=0&maxSalePrice=2147483647")
            res.raise_for_status()
        except requests.exceptions.HTTPError as err:
            raise Exception(err)

        data = res.json()
        data = data if not is_more_then_one else data["items"]
        for item in items:
            item_json = data if not is_more_then_one else data.get(str(item.unique_id))
            if item_json is None:
                _logger.warning(f"Not found item with id: {str(item.unique_id)} | item name: {item.name} | sellable: {item.sellable}")
                continue
            if "entries" not in item_json or not item_json["entries"]:
                continue
            self.__sync_item_transactions(item, world, item_json["entries"])
            item.last_time_sync_transactions = fields.Datetime.now()

    @api.model
    def __sync_item_transactions(self, item, world, entries):
        transactions = [index for index in item.transactions_ids.ids]
        val_list = []
        for entry in entries:
            # cerco se esiste già
            # se non esiste lo creo
            # (non mi serve aggiornarlo perchè è un dato che non cambia)
            # elimino tutti quelli che non ci sono più
            found = item.transactions_ids.filtered(
                lambda x: x.sale_date_timestamp == int(entry['timestamp']) and x.buyer_name == entry['buyerName'])

            if found:
                found = found[0]
                transactions.remove(found.id)
                continue
            val_list.append({
                'item_selled': item.id,
                'world_id': world.id,
                'price': entry['pricePerUnit'],
                'quantity': entry['quantity'],
                'sale_date': fields.Datetime.to_string(datetime.datetime.fromtimestamp(int(entry['timestamp']))),
                'sale_date_timestamp': int(entry['timestamp']),
                'buyer_name': entry['buyerName'],
                'high_quality': bool(entry['hq'])
            })
        if transactions:
            _logger.info(f"Deleting {len(transactions)} transactions")
            self.env['tataru_secret_market.item_sale_transactions'].browse(transactions).unlink()
        self.env['tataru_secret_market.item_sale_transactions'].create(val_list)
