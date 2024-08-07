from odoo import models, fields, api
import requests
import logging
import time


_logger = logging.getLogger(__name__)


class ItemAvailability(models.Model):
    _name = 'tataru_secret_market.item_availability'
    _order = "total_price_with_tax"

    # general infos
    item_id = fields.Many2one('tataru_secret_market.items', index=True)
    world_id = fields.Many2one('tataru_secret_market.worlds', index=True)
    world_name = fields.Char(related='world_id.name')
    data_center_id = fields.Many2one(related='world_id.data_center_id')
    item_name = fields.Char(related='item_id.name')
    listing_id = fields.Char(index=True)

    # item infos
    high_quality = fields.Boolean()
    price = fields.Integer()
    quantity = fields.Integer(index=True)
    tax = fields.Integer()
    total_price = fields.Integer(compute='_compute_total_price', store=True)
    total_price_with_tax = fields.Integer(compute='_compute_total_price', store=True)

    # retainer infos
    reteiner_name = fields.Char(index=True)
    reteiner_id = fields.Char(index=True)

    @api.depends('price', 'quantity', 'tax')
    def _compute_total_price(self):
        for record in self:
            record.total_price = record.price * record.quantity
            record.total_price_with_tax = record.total_price + record.tax

    @api.model
    def sync_item_availability(self, items, data_center):
        is_more_then_one = len(items) > 1
        items_str = ",".join([str(item.unique_id) for item in items]) if is_more_then_one else str(items[0].unique_id)
        # TODO - max 100 items per request
        api_url = f"https://universalis.app/api/v2/{data_center.name}/{items_str}?listings=100&entries=0"
        before_request = time.time()
        try:
            res = requests.get(api_url)
            res.raise_for_status()
        except requests.exceptions.HTTPError as err:
            raise Exception(err)
        after_request = time.time()
        data = res.json()
        _logger.info(f"Request to Universalis for {api_url} took : {after_request - before_request} seconds")
        data = data if not is_more_then_one else data.get("items")
        for item in items:
            item_json = data if not is_more_then_one else data.get(str(item.unique_id))
            if item_json is None:
                _logger.warning(f"Not found item with id: {str(item.unique_id)} | item name: {item.name} | sellable: {item.sellable}")

            if "listings" not in item_json or not item_json["listings"]:
                continue
            self.__sync_item_availability(item, item_json["listings"])
        after_sync = time.time()
        _logger.info(f"Sync for {items_str} took : {after_sync - after_request} seconds")

    @api.model
    def __sync_item_availability(self, item, listings):
        availability_ids = [index for index in item.availability_ids.ids]
        val_list = []
        world_chache = {}
        for entry in listings:
            world_id = world_chache.get(int(entry['worldID'])) or self.env['tataru_secret_market.worlds'].search([('unique_id', '=', int(entry['worldID']))])
            world_chache[int(entry['worldID'])] = world_id
            listing_id = item.availability_ids.filtered(lambda x: x.listing_id == entry['listingID']
                                                        and x.world_id.id == world_id.id
                                                        and x.reteiner_id == entry['retainerID']
                                                        and x.reteiner_name == entry['retainerName']
                                                        and x.quantity == entry['quantity']
                                                        )
            # listing_id = self.env['tataru_secret_market.item_availability'].search([
            #     ("reteiner_id", "=", entry['retainerID']),
            #     ("reteiner_name", "=", entry['retainerName']),
            #     ("quantity", "=", entry['quantity']),
            #     ('item_id', '=', item.id),
            #     ('world_id', '=', world_id.id)], limit=1)
            if listing_id:
                listing_id = listing_id[0]
                listing_id.write({
                    'item_id': item.id,
                    'world_id': world_id.id,
                    'high_quality': bool(entry['hq']),
                    'price': entry['pricePerUnit'],
                    'quantity': entry['quantity'],
                    'tax': entry['tax'],
                    'reteiner_name': entry['retainerName'],
                    'reteiner_id': entry['retainerID'],
                })
                if listing_id.id in availability_ids:
                    availability_ids.remove(listing_id.id)
            else:
                val_list.append({
                    'item_id': item.id,
                    'world_id': world_id.id,
                    'high_quality': bool(entry['hq']),
                    'price': entry['pricePerUnit'],
                    'quantity': entry['quantity'],
                    'tax': entry['tax'],
                    'reteiner_name': entry['retainerName'],
                    'reteiner_id': entry['retainerID'],
                    'listing_id': entry['listingID']
                })
        if availability_ids:
            _logger.info(f"Deleting {len(availability_ids)} availability")
            self.env['tataru_secret_market.item_availability'].browse(availability_ids).unlink()
        self.env['tataru_secret_market.item_availability'].create(val_list)
