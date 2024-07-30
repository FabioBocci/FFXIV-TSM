from odoo import models, fields, api
import requests
import datetime


class Items(models.Model):
    _name = 'tataru_secret_market.items'
    _description = 'tataru_secret_market.items'

    unique_id = fields.Integer(index=True)
    name = fields.Char()
    sellable = fields.Boolean()
    craftable = fields.Boolean(compute="_compute_craftable_item", index=True, store=True)
    crafting_recipe_id = fields.One2many('tataru_secret_market.item_recipe', 'result_item_id')
    ingredients_ids = fields.One2many('tataru_secret_market.item_ingredient', 'item_id')
    recipe_for = fields.One2many(related="ingredients_ids.recipe_id.result_item_id", string="Recipe for")
    transactions_ids = fields.One2many('tataru_secret_market.item_sale_transactions', 'item_selled')
    transactions_count_last_24h = fields.Integer(compute='_compute_transactions_count')
    transactions_count_last_7d = fields.Integer(compute='_compute_transactions_count')

    availability_ids = fields.One2many('tataru_secret_market.item_availability', 'item_id')

    last_time_sync_transactions = fields.Datetime()
    last_time_sync_availability = fields.Datetime()

    @api.depends('transactions_ids', 'transactions_ids.sale_date')
    def _compute_transactions_count(self):
        for record in self:
            record.transactions_count_last_24h = len(record.transactions_ids.filtered(lambda x: x.sale_date > (fields.Datetime.now() - datetime.timedelta(days=1))))
            record.transactions_count_last_7d = len(record.transactions_ids.filtered(lambda x: x.sale_date > (fields.Datetime.now() - datetime.timedelta(days=7))))

    @api.depends('crafting_recipe_id')
    def _compute_craftable_item(self):
        for record in self:
            record.craftable = bool(record.crafting_recipe_id)

    @api.model
    def sync_items(self):
        try:
            res = requests.get("https://raw.githubusercontent.com/ffxiv-teamcraft/ffxiv-teamcraft/master/libs/data/src/lib/json/items.json")
            res.raise_for_status()
            res_markettable = requests.get("https://universalis.app/api/v2/marketable")
            res_markettable.raise_for_status()
        except requests.exceptions.HTTPError as err:
            raise Exception(err)

        data = res.json()
        markettable_list_key = [int(item_key) for item_key in res_markettable.json()]

        for key, item in data.items():
            if item["en"] is None or item["en"] == "":
                continue
            item_id = self.env['tataru_secret_market.items'].search([('unique_id', '=', int(key))])

            if not item_id:
                self.env['tataru_secret_market.items'].create({
                    'unique_id': int(key),
                    'name': item['en'],
                    'sellable': int(key) in markettable_list_key,
                    'craftable': False
                })
            else:
                item_id.write({
                    'name': item['en'],
                    'sellable': int(key) in markettable_list_key,
                })

    def sync_item_transactions(self):
        current_world = self.env['tataru_secret_market.worlds'].get_current_world()
        transactions_model = self.env['tataru_secret_market.item_sale_transactions']
        for record in self:
            record.transactions_ids.unlink()  # TODO - non cancellare ma aggiornare i dati aggiungend
            transactions_model.sync_item_transactions(record, current_world)

    def sync_item_availability(self):
        current_world = self.env['tataru_secret_market.worlds'].get_current_world()
        availability_model = self.env['tataru_secret_market.item_availability']
        availability_model.sync_item_availability(self, current_world.data_center_id)
