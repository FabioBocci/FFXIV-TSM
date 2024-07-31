from odoo import models, fields, api
import requests


class DataCenters(models.Model):
    _name = "tataru_secret_market.data_centers"

    name = fields.Char(required=True)
    region = fields.Char(required=True)

    worlds_ids = fields.One2many("tataru_secret_market.worlds", "data_center_id")

    @api.model
    def sync_datacenter(self, starting):
        try:
            res = requests.get("https://universalis.app/api/v2/data-centers")
            res.raise_for_status()
        except requests.exceptions.HTTPError as err:
            raise Exception(err)

        data = res.json()

        for dc in data:
            data_center = self.env["tataru_secret_market.data_centers"].search(
                [("name", "=", dc["name"])]
            )

            if not data_center:
                data_center = self.env["tataru_secret_market.data_centers"].create(
                    {"name": dc["name"], "region": dc["region"]}
                )

            for world in dc["worlds"]:
                world_id = self.env["tataru_secret_market.worlds"].search(
                    [("unique_id", "=", int(world))]
                )

                if not world_id:
                    self.env["tataru_secret_market.worlds"].create(
                        {
                            "unique_id": world,
                            "name": str(world) + "TO SYNC",
                            "data_center_id": data_center.id,
                        }
                    )
                else:
                    world_id.write({"data_center_id": data_center.id})
