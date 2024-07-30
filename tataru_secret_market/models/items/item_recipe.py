from odoo import models, fields, api


class ItemRecipe(models.Model):
    _name = 'tataru_secret_market.item_recipe'

    unique_id = fields.Integer()

    ingredients_ids = fields.One2many('tataru_secret_market.item_ingredient', 'recipe_id')

    result_item_id = fields.Many2one('tataru_secret_market.items')

    job_id = fields.Many2one('tataru_secret_market.jobs')
    level_required = fields.Integer()


class ItemIngredient(models.Model):
    _name = 'tataru_secret_market.item_ingredient'

    unique_id = fields.Integer(related='item_id.unique_id')

    item_id = fields.Many2one('tataru_secret_market.items')
    quantity = fields.Integer()

    recipe_id = fields.Many2one('tataru_secret_market.item_recipe')
