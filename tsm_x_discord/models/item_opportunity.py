# -*- coding: utf-8 -*-

from odoo import models, fields, api
import datetime
from PIL import Image, ImageDraw, ImageFont
import requests
from io import BytesIO
import base64
import logging

_logger = logging.getLogger(__name__)

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

            current_world = self.env["tataru_secret_market.worlds"].get_current_world()
            # Set the column widths
            for availability in self.get_availability_filtered(current_world)[
                :MAX_NUMBER_OF_OPPORTUNITIES
            ]:
                # Format each column with a fixed width
                world_name = availability.world_id.name.ljust(world_column_width)
                price = f"{availability.price} Gil".ljust(price_column_width)
                quantity = f"{availability.quantity}x".ljust(quantity_column_width)
                total_price_with_tax = f"{availability.total_price_with_tax} Gil".ljust(
                    total_price_with_tax_column_width
                )
                retainer_name = f"{availability.reteiner_name}".ljust(
                    retainer_column_width
                )

                # Combine into a single line
                table_text += f"{world_name} {price} {quantity} {total_price_with_tax} {retainer_name}\n"

            return f"""```{table_text}
```"""

        elif self.opportunity_type == "craft":
            return "You can craft this item and sell it at a higher price than the average selling price."
            # TODO - implement

    def __convert_to_discord_text(self, include_image_url=True):
        image_url = self._get_image_url() or "" if include_image_url else ""
        if len(image_url) > 0:
            image_url = f"[Image]({image_url})"
        message = f"""{'Hello @ here, I have found a new opportunity for you!' if self.last_time_send_on_discord is False else 'Opportunity is still available! (Updated)'}
Item: [{self.name}](<https://www.garlandtools.org/db/#item/{self.item_id.unique_id}>)
[Universalis](<https://universalis.app/market/{self.item_id.unique_id}>)
Percentage of Opportunity: **{int(self.opportunity_percentage * 100)}%**
Avg. Selling Price: **{int(self.price_to_sell)}**
Type Opportunity: **{self.opportunity_type}**
You can buy this item at a lower price than the average selling price. Here:
{self.__get_opportunity_text()}--------------------------------------------------------------------------------
{image_url}
        """
        return message

    @api.model
    def send_opportunities_to_discord(
        self, opportunities, discord_channels, include_image=True
    ):
        if not discord_channels:
            return
        for opportunity in opportunities:
            if not opportunity.opportunity_image and include_image:
                opportunity.create_image()
            text = opportunity.__convert_to_discord_text(include_image)
            # TODO - è possibile che il text sia troppo lungo per discord ed andrebbe diviso in messaggi più piccoli
            discord_channels.send_message(
                f"MSG - Update Discord Opportunity {opportunity.name}", text, False
            )
            opportunity.last_time_send_on_discord = fields.Datetime.now()

    @api.model
    def cron_send_opportunities(self):
        opportunities = self.env["tataru_secret_market.item_opportunity"].search(
            [
                "&",
                "&",
                "&",
                "&",
                ("opportunity_percentage", "<", 0.9),
                ("opportunity_percentage", ">", 0.3),
                ("send_this_opportunity", "=", True),
                ("opportunity_type", "=", "buy"),
                "|",
                ("last_time_send_on_discord", "=", False),
                (
                    "last_time_send_on_discord",
                    "<",
                    fields.Datetime.now() - datetime.timedelta(hours=12),
                ),
            ],
            limit=5,
            order="opportunity_percentage DESC",
        )
        discord_channels = self.env[
            "discord.channel"
        ].get_target_channels_for_tsm_message()
        should_send_image = (
            self.env["ir.config_parameter"]
            .sudo()
            .get_param("tataru_secret_market.send_image_to_discord", False)
        )
        self.env["tataru_secret_market.item_opportunity"].send_opportunities_to_discord(
            opportunities, discord_channels, should_send_image
        )

    def _get_image_url(self):
        self.ensure_one()
        if self.opportunity_type == "none":
            return False

        if not self.opportunity_image:
            return False

        # get base url
        base_url = self.env["ir.config_parameter"].sudo().get_param("web.base.url")
        return f"{base_url}/web/image/tataru_secret_market.item_opportunity/{self.id}/opportunity_image"

    def create_image(self):
        # Get base image and font paths from configuration
        base_image_path = (
            self.env["ir.config_parameter"]
            .sudo()
            .get_param("tataru_secret_market.base_image_path")
        )
        base_font_path = (
            self.env["ir.config_parameter"]
            .sudo()
            .get_param("tataru_secret_market.base_font_path")
        )

        if not base_image_path or not base_font_path:
            _logger.warning("Base image path or font path not configured.")
            return

        for record in self:
            if record.opportunity_type == "none":
                record.opportunity_image = False
                continue

            try:
                # Load the base image
                base_image = Image.open(base_image_path)

                # Load and process the overlay image (item icon)
                response = requests.get(record.item_icon_hd)
                overlay_image = Image.open(BytesIO(response.content))
                overlay_image = overlay_image.resize((180, 180))  # Resize as needed

                # Paste the overlay image onto the base image with transparency
                base_image.paste(overlay_image, (920, 44), overlay_image)

                # Initialize ImageDraw
                draw = ImageDraw.Draw(base_image)

                # Load the font
                title = ImageFont.truetype(base_font_path, size=34)  # Adjust as needed

                # Load the font
                font = ImageFont.truetype(base_font_path, size=24)  # Adjust as needed

                # Draw text on the image
                draw.text(
                    (410, 160),
                    record.item_id.name,
                    font=title,
                    fill=(0, 0, 0),  # Black color
                )

                draw.text(
                    (200, 200),
                    f"Percentage of Opportunity: {int(record.opportunity_percentage * 100)}%   Avg. Selling Price: {int(record.price_to_sell)}",
                    font=font,
                    fill=(0, 0, 0),
                )

                draw.text(
                    (200, 230),
                    "You can buy this item at a lower price than the average selling price. Here:",
                    font=font,
                    fill=(0, 0, 0),
                )

                table_position = (200, 250)
                draw.text(
                    table_position,
                    str(record.__get_opportunity_text().replace("```", "")),
                    font=font,
                    fill=(0, 0, 0),
                )

                # Convert the image to a PNG and encode it in base64
                image_stream = BytesIO()
                base_image.save(image_stream, format="PNG")
                image_base64 = base64.b64encode(image_stream.getvalue()).decode("ascii")

                # Save the base64-encoded image to the opportunity_image field
                record.opportunity_image = image_base64

                # Add logs
                _logger.info("Image created for item: %s", record.item_id.name)

            except Exception as e:
                _logger.error(
                    "Failed to create image for item %s: %s",
                    record.item_id.name,
                    str(e),
                )
