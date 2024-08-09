# -*- coding: utf-8 -*-

from odoo import models, fields, api
import datetime

MAX_NUMBER_OF_OPPORTUNITIES = 10

class ItemOpportunity(models.Model):
    _inherit = "tataru_secret_market.item_opportunity"

    last_time_send_on_discord = fields.Datetime()
    send_this_opportunity = fields.Boolean(default=True)

    def __get_opportunity_text(self):
        world_column_width = 15
        price_column_width = 10
        quantity_column_width = 10
        total_price_with_tax_column_width = 20
        retainer_column_width = 20
        self.ensure_one()

        if self.opportunity_type == "buy":
            table_text = f"{f'World'.ljust(world_column_width)} {f'Price'.ljust(price_column_width)} {f'Quantity'.ljust(quantity_column_width)} {f'Total Price (Taxed)'.ljust(total_price_with_tax_column_width)} {f'Retainer'.ljust(retainer_column_width)}\n"
            table_text += f"{''.ljust(world_column_width + price_column_width + quantity_column_width + total_price_with_tax_column_width + retainer_column_width + 4, '-')}\n"

            current_world = self.env['tataru_secret_market.worlds'].get_current_world()
            # Set the column widths
            for availability in self.get_availability_filtered(current_world)[:MAX_NUMBER_OF_OPPORTUNITIES]:
                # Format each column with a fixed width
                world_name = availability.world_id.name.ljust(world_column_width)
                price = f"{availability.price} Gil".ljust(price_column_width)
                quantity = f"{availability.quantity}x".ljust(quantity_column_width)
                total_price_with_tax = f"{availability.total_price_with_tax} Gil".ljust(total_price_with_tax_column_width)
                retainer_name = f"{availability.reteiner_name}".ljust(retainer_column_width)

                # Combine into a single line
                table_text += f"{world_name} {price} {quantity} {total_price_with_tax} {retainer_name}\n"

            return f""" You can buy this item at a lower price than the average selling price. Here:
```{table_text}
```
"""

        elif self.opportunity_type == "craft":
            return "You can craft this item and sell it at a higher price than the average selling price."
            # TODO - implement

    def __convert_to_discord_text(self):
        message = f"""{'Hello @ here, I have found a new opportunity for you!' if self.last_time_send_on_discord is False else 'Opportunity is still available! (Updated)'}
Item: [{self.name}](<https://www.garlandtools.org/db/#item/{self.item_id.unique_id}>)
[Universalis](<https://universalis.app/market/{self.item_id.unique_id}>)
Percentage of Opportunity: **{int(self.opportunity_percentage * 100)}%**
Avg. Selling Price: **{int(self.price_to_sell)}**
Type Opportunity: **{self.opportunity_type}**
{self.__get_opportunity_text()}
--------------------------------------------------------------------------------
        """
        return message

    @api.model
    def send_opportunities_to_discord(self, opportunities, discord_channels):
        if not discord_channels:
            return
        for opportunity in opportunities:
            text = opportunity.__convert_to_discord_text()
            # TODO - è possibile che il text sia troppo lungo per discord ed andrebbe diviso in messaggi più piccoli
            discord_channels.send_message(f"MSG - Update Discord Opportunity {opportunity.name}", text, False)
            opportunity.last_time_send_on_discord = fields.Datetime.now()

    @api.model
    def cron_send_opportunities(self):
        opportunities = self.env["tataru_secret_market.item_opportunity"].search([
            "&",
            "&",
            "&",
            ("opportunity_percentage", "<", 0.9),
            ("send_this_opportunity", "=", True),
            ("opportunity_type", "=", "buy"),
            "|",
            ("last_time_send_on_discord", "=", False),
            ("last_time_send_on_discord", "<", fields.Datetime.now() - datetime.timedelta(hours=12))
        ], limit=10, order="opportunity_percentage DESC")
        discord_channels = self.env['discord.channel'].get_target_channels_for_tsm_message()
        self.env["tataru_secret_market.item_opportunity"].send_opportunities_to_discord(opportunities, discord_channels)
