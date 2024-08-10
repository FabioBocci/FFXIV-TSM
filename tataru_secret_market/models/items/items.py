from odoo import models, fields, api
import requests
import datetime


class Items(models.Model):
    _name = 'tataru_secret_market.items'
    _description = 'tataru_secret_market.items'

    unique_id = fields.Integer(index=True)
    name = fields.Char()
    sellable = fields.Boolean()
    craftable = fields.Boolean(index=True, store=True)
    used_for_crafting = fields.Boolean(compute='_compute_used_for_crafting', store=True)
    item_icon = fields.Char()
    item_icon_hd = fields.Char()
    crafting_recipe_ids = fields.One2many('tataru_secret_market.item_recipe', 'result_item_id')
    ingredients_ids = fields.One2many('tataru_secret_market.item_ingredient', 'item_id')
    # recipe_for = fields.One2many(related="ingredients_ids.recipe_id")
    transactions_ids = fields.One2many('tataru_secret_market.item_sale_transactions', 'item_selled')
    transactions_count_last_24h = fields.Integer(compute='_compute_transactions_count', store=True)
    transactions_count_last_7d = fields.Integer(compute='_compute_transactions_count', store=True)
    mostly_hq = fields.Boolean(compute='_compute_transactions_count', store=True)

    availability_ids = fields.One2many('tataru_secret_market.item_availability', 'item_id')

    last_time_sync_transactions = fields.Datetime()
    last_time_sync_availability = fields.Datetime()
    last_time_sync_recipe = fields.Datetime()
    last_time_sync_data = fields.Datetime()

    universalis_last_sync_time_availability = fields.Datetime()

    @api.depends('transactions_ids', 'transactions_ids.sale_date')
    def _compute_transactions_count(self):
        require_hq_percentage = self.env["ir.config_parameter"].sudo().get_param("require_hq_percentage", 0.5)
        for record in self:
            if not record.sellable:
                record.transactions_count_last_24h = 0
                record.transactions_count_last_7d = 0
                record.mostly_hq = False

            record.transactions_count_last_24h = len(record.transactions_ids.filtered(lambda x: x.sale_date > (fields.Datetime.now() - datetime.timedelta(days=1))))
            record.transactions_count_last_7d = len(record.transactions_ids.filtered(lambda x: x.sale_date > (fields.Datetime.now() - datetime.timedelta(days=7))))
            record.mostly_hq = len(record.transactions_ids.filtered(lambda x: x.high_quality)) / len(record.transactions_ids) > require_hq_percentage if len(record.transactions_ids) > 0 else False

    @api.depends('ingredients_ids')
    def _compute_used_for_crafting(self):
        for record in self:
            record.used_for_crafting = len(record.ingredients_ids) > 0

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

    def action_sync_item_data(self):
        for entry in self:
            entry.sync_item_data(entry)

    @api.model
    def sync_item_data(self, item_id):
        item_id.ensure_one()
        try:
            res = requests.get(f"https://xivapi.com/item/{item_id.unique_id}?columns=ID,Icon,IconHD,Recipes")
            res.raise_for_status()
        except requests.exceptions.HTTPError as err:
            raise Exception(err)

        data = res.json()

        update_dict = {
            "item_icon": "https://xivapi.com" + data['Icon'],
            "item_icon_hd": "https://xivapi.com" + data['IconHD']
        }

        recipes = data['Recipes']
        if recipes is None:
            update_dict['craftable'] = False
            update_dict['crafting_recipe_ids'] = False
        else:
            for recipe in recipes:
                job_id = self.env['tataru_secret_market.jobs'].search([('unique_id', '=', int(recipe['ClassJobID']))])
                recipe_id = self.env['tataru_secret_market.item_recipe'].search([('unique_id', '=', int(recipe['ID']))])

                if not recipe_id:
                    recipe_id = self.env['tataru_secret_market.item_recipe'].create({
                        'unique_id': int(recipe['ID']),
                        'result_item_id': item_id.id,
                        "job_id": job_id.id,
                        "level_required": recipe['Level'],
                    })
                else:
                    recipe_id.write({
                        'result_item_id': item_id.id,
                        "job_id": job_id.id,
                        "level_required": recipe['Level'],
                    })
            update_dict['craftable'] = True
        item_id.write(update_dict)
        item_id.last_time_sync_data = fields.Datetime.now()

    def sync_item_full_data(self):
        self.with_delay().sync_item_transactions()
        self.with_delay().sync_item_availability()
        self.with_delay().sync_item_recipe()
        self.with_delay().sync_item_data(self)

    def sync_item_transactions(self):
        current_world = self.env['tataru_secret_market.worlds'].get_current_world()
        transactions_model = self.env['tataru_secret_market.item_sale_transactions']
        transactions_model.sync_item_transactions(self, current_world)

    def sync_item_availability(self):
        current_world = self.env['tataru_secret_market.worlds'].get_current_world()
        availability_model = self.env['tataru_secret_market.item_availability']
        availability_model.sync_item_availability(self, current_world.data_center_id)
        self.last_time_sync_availability = fields.Datetime.now()

    def sync_item_recipe(self):
        recipe_model = self.env['tataru_secret_market.item_recipe']
        for record in self:
            recipe_model.sync_recipes(record)
            record.last_time_sync_recipe = fields.Datetime.now()
