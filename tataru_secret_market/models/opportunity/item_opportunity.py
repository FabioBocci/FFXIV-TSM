import re
from odoo import models, fields, api


class ItemOpportunity(models.Model):
    _name = "tataru_secret_market.item_opportunity"
    _order = "opportunity_percentage desc"

    name = fields.Char(related="item_id.name")
    item_id = fields.Many2one("tataru_secret_market.items", string="Item")
    need_high_quality = fields.Boolean(related="item_id.mostly_hq")

    item_icon = fields.Char(related="item_id.item_icon")
    item_icon_hd = fields.Char(related="item_id.item_icon_hd")

    price_to_sell = fields.Float(compute="_compute_price_to_sell", store=True)
    price_to_buy = fields.Float(compute="_compute_price_to_buy", store=True)
    price_to_craft = fields.Float(compute="_compute_price_to_craft", store=True)

    opportunity_percentage = fields.Float(
        compute="_compute_opportunity_percentage", store=True
    )
    opportunity_type = fields.Selection(
        [
            ("none", "None"),
            ("buy", "Buy"),
            ("craft", "Craft"),
        ],
        compute="_compute_opportunity_percentage",
        store=True,
    )
    opportunity_image = fields.Image("Opportunity Image", public=True)

    item_craftable = fields.Boolean(related="item_id.craftable")
    item_crafting = fields.One2many(related="item_id.crafting_recipe_ids")
    item_availability = fields.One2many(related="item_id.availability_ids")

    last_time_in_list_of_transactions = fields.Datetime()
    dont_delate = fields.Boolean(default=False)  # TODO - create method

    @api.model_create_multi
    def create(self, vals_list):
        vals = super().create(vals_list)
        for record in vals:
            record.last_time_in_list_of_transactions = fields.Datetime.now()
        return vals

    def action_compute_all(self):
        for record in self:
            record._compute_price_to_sell()
            record._compute_price_to_buy()
            record._compute_price_to_craft()
            record._compute_opportunity_percentage()

    def get_availability_filtered(self, world_id):
        self.ensure_one()
        return self.item_availability.filtered(
            lambda x: x.price > 0
            and world_id.id != x.world_id.id
            and (not self.need_high_quality or x.high_quality)
        )

    @api.depends("item_id", "item_id.transactions_ids")
    def _compute_price_to_sell(self):
        if self.env.context.get("ignore_calculation", False):
            return

        for record in self:
            if not record.item_id or len(record.item_id.transactions_ids) <= 0:
                record.price_to_sell = -1
                continue
            use_only_hq = record.item_id.mostly_hq
            record.price_to_sell = int(sum(
                record.item_id.transactions_ids.filtered(
                    lambda x: x.high_quality == use_only_hq or not use_only_hq
                ).mapped("price")
            ) / len(record.item_id.transactions_ids))

    @api.depends("item_id", "item_id.availability_ids")
    def _compute_price_to_buy(self):
        if self.env.context.get("ignore_calculation", False):
            return

        current_world = self.env["tataru_secret_market.worlds"].get_current_world()
        for record in self:
            if not record.item_id or len(record.item_id.availability_ids) <= 0:
                record.price_to_buy = -1
                continue
            filtered_availabilities = record.get_availability_filtered(current_world)
            if filtered_availabilities:
                record.price_to_buy = filtered_availabilities.sorted("price")[0].price
            else:
                record.price_to_buy = -1

    @api.depends(
        "item_id",
        "item_id.crafting_recipe_ids",
        "item_id.crafting_recipe_ids.ingredients_ids",
        "item_id.crafting_recipe_ids.ingredients_ids.item_id",
        "item_id.crafting_recipe_ids.ingredients_ids.item_id.availability_ids",
    )
    def _compute_price_to_craft(self):
        if self.env.context.get("ignore_calculation", False):
            return

        for record in self:
            if not record.item_id or len(record.item_id.crafting_recipe_ids) <= 0:
                record.price_to_craft = -1
                continue

            if not record.item_id.craftable:
                record.price_to_craft = -1
                continue

            # TODO - AVG price ?
            ingredients = record.item_id.crafting_recipe_ids.ingredients_ids
            price = 0
            for ingredient in ingredients:
                availability = ingredient.item_id.availability_ids.filtered(
                    lambda x: x.price > 0
                ).sorted("price", reverse=True)
                if len(availability) <= 0:
                    price = -1
                    break
                price += availability[0].price * ingredient.quantity

            record.price_to_craft = price

    @api.depends("price_to_sell", "price_to_buy", "price_to_craft")
    def _compute_opportunity_percentage(self):
        if self.env.context.get("ignore_calculation", False):
            return

        for record in self:
            if record.price_to_sell <= 0:
                record.opportunity_percentage = 0
                record.opportunity_type = "none"
                continue
            if record.price_to_buy <= 0 and record.price_to_craft <= 0:
                record.opportunity_percentage = 0
                record.opportunity_type = "none"
            elif record.price_to_buy > 0 and record.price_to_craft <= 0:
                if record.price_to_sell <= record.price_to_buy:
                    record.opportunity_percentage = 0
                    record.opportunity_type = "none"
                else:
                    record.opportunity_percentage = (
                        1 - record.price_to_buy / record.price_to_sell
                    )
                    record.opportunity_type = "buy"
            elif record.price_to_craft > 0 and record.price_to_buy <= 0:
                if record.price_to_sell <= record.price_to_craft:
                    record.opportunity_percentage = 0
                    record.opportunity_type = "none"
                else:
                    record.opportunity_percentage = (
                        1 - record.price_to_craft / record.price_to_sell
                    )
                    record.opportunity_type = "craft"
            else:
                if record.price_to_sell <= min(
                    record.price_to_craft, record.price_to_buy
                ):
                    record.opportunity_percentage = 0
                    record.opportunity_type = "none"

                record.opportunity_percentage = 1 - min(
                    record.price_to_craft / record.price_to_sell,
                    record.price_to_buy / record.price_to_sell,
                )
                record.opportunity_type = (
                    "craft" if record.price_to_craft < record.price_to_buy else "buy"
                )
