from odoo import models, fields, api
import requests


class ItemRecipe(models.Model):
    _name = "tataru_secret_market.item_recipe"

    MAX_SIZE_OF_INGREDIENTS = 8

    unique_id = fields.Integer()

    ingredients_ids = fields.One2many(
        "tataru_secret_market.item_ingredient", "recipe_id"
    )

    result_item_id = fields.Many2one("tataru_secret_market.items")

    job_id = fields.Many2one("tataru_secret_market.jobs")
    level_required = fields.Integer()

    name = fields.Char(compute="_compute_name")
    sellable = fields.Boolean(related="result_item_id.sellable")
    item_icon = fields.Char(related="result_item_id.item_icon")
    item_icon_hd = fields.Char(related="result_item_id.item_icon_hd")

    @api.depends("result_item_id")
    def _compute_name(self):
        for record in self:
            record.name = f"Craft for: {record.result_item_id.name} job: {record.job_id.name} level: {record.level_required}"

    @api.model
    def sync_recipes(self, item_id):
        item_id.ensure_one()

        recipe_id = self.env["tataru_secret_market.item_recipe"].search(
            [("result_item_id", "=", item_id.id)]
        )

        if not recipe_id:
            return

        for recipe in recipe_id:
            try:
                res = requests.get(
                    f"https://xivapi.com/recipe/{recipe.unique_id}?columns=Name,ID,"
                    + "AmountIngredient0,AmountIngredient1,AmountIngredient2,AmountIngredient3,AmountIngredient4,AmountIngredient5,AmountIngredient6,AmountIngredient7,"
                    + "ItemIngredient0.ID,ItemIngredient1.ID,ItemIngredient2.ID,ItemIngredient3.ID,ItemIngredient4.ID,ItemIngredient5.ID,ItemIngredient6.ID,ItemIngredient7.ID"
                )
                res.raise_for_status()
            except requests.exceptions.HTTPError as err:
                raise Exception(err)
                # AmountIngredient0
                # AmountIngredient
            ammounts_keys = [
                f"AmountIngredient{i}" for i in range(self.MAX_SIZE_OF_INGREDIENTS)
            ]
            item_ids_keys = [
                f"ItemIngredient{i}" for i in range(self.MAX_SIZE_OF_INGREDIENTS)
            ]
            data = res.json()
            for i in range(self.MAX_SIZE_OF_INGREDIENTS):
                if data[ammounts_keys[i]] is None or int(data[ammounts_keys[i]]) == 0:
                    continue

                ingredient_id = self.env["tataru_secret_market.items"].search(
                    [("unique_id", "=", int(data[item_ids_keys[i]]["ID"]))]
                )

                if not ingredient_id:
                    # TODO - log error
                    continue

                find_ing = recipe.ingredients_ids.filtered(
                    lambda x: x.item_id.id == ingredient_id.id
                )

                if find_ing:
                    find_ing.write({"quantity": data[ammounts_keys[i]]})
                    continue
                else:
                    self.env["tataru_secret_market.item_ingredient"].create(
                        {
                            "item_id": ingredient_id.id,
                            "quantity": int(data[ammounts_keys[i]]),
                            "recipe_id": recipe.id,
                        }
                    )


class ItemIngredient(models.Model):
    _name = "tataru_secret_market.item_ingredient"

    item_id = fields.Many2one("tataru_secret_market.items")
    quantity = fields.Integer()

    recipe_id = fields.Many2one("tataru_secret_market.item_recipe")

    # item fields
    item_icon = fields.Char(related="item_id.item_icon")
    item_icon_hd = fields.Char(related="item_id.item_icon_hd")
    name = fields.Char(related="item_id.name")
    item_is_craftable = fields.Boolean(related="item_id.craftable")
    item_sellable = fields.Boolean(related="item_id.sellable")

    # recipe fields
    recipe_icon = fields.Char(related="recipe_id.item_icon")
    recipe_icon_hd = fields.Char(related="recipe_id.item_icon_hd")
    recipe_name = fields.Char(related="recipe_id.name")
    recipe_sellable = fields.Boolean(related="recipe_id.sellable")
    recipe_job_id = fields.Many2one(related="recipe_id.job_id")
    recipe_level_required = fields.Integer(related="recipe_id.level_required")
    # recipe_full_ingredients = fields.one2many("tataru_secret_market.item_ingredient", related="recipe_id.ingredients_ids")
