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

    @api.depends("result_item_id")
    def _compute_name(self):
        for record in self:
            record.name = "Craft for: " + record.result_item_id.name

    @api.model
    def sync_recipes(self, item_id):
        item_id.ensure_one()

        try:
            res = requests.get(
                f"https://xivapi.com/Item/{item_id.unique_id}?columns=Recipes"
            )
            res.raise_for_status()
        except requests.exceptions.HTTPError as err:
            raise Exception(err)

        data = res.json()

        if data["Recipes"] is None:
            item_id.write({"craftable": False, "crafting_recipe_id": False})
            return

        for recipe in data["Recipes"]:
            recipe_id = self.env["tataru_secret_market.item_recipe"].search(
                [("unique_id", "=", int(recipe["ID"]))]
            )
            job_id = self.env["tataru_secret_market.jobs"].search(
                [("unique_id", "=", int(recipe["ClassJobID"]))]
            )

            if not recipe_id:
                recipe_id = self.env["tataru_secret_market.item_recipe"].create(
                    {
                        "unique_id": int(recipe["ID"]),
                        "result_item_id": item_id.id,
                        "job_id": job_id.id,
                        "level_required": int(recipe["Level"]),
                    }
                )
            else:
                recipe_id.write(
                    {"job_id": job_id.id, "level_required": int(recipe["Level"])}
                )
            item_id.write({"craftable": True, "crafting_recipe_id": recipe_id.id})
            try:
                res = requests.get(
                    f"https://xivapi.com/recipe/{recipe_id.unique_id}?columns=Name,ID,"
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

                find_ing = recipe_id.ingredients_ids.filtered(
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
                            "recipe_id": recipe_id.id,
                        }
                    )


class ItemIngredient(models.Model):
    _name = "tataru_secret_market.item_ingredient"

    item_id = fields.Many2one("tataru_secret_market.items")
    quantity = fields.Integer()

    recipe_id = fields.Many2one("tataru_secret_market.item_recipe")
