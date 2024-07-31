from odoo import models, fields, api
import requests


class Jobs(models.Model):
    _name = "tataru_secret_market.jobs"

    unique_id = fields.Integer()
    name = fields.Char()

    @api.model
    def sync_jobs(self, starting):
        try:
            res = requests.get("https://xivapi.com/ClassJob")
            # https://xivapi.com/ClassJob -> lista di tutti i jobs
            # https://xivapi.com/ClassJob/{id} -> dettagli di un job specifico
            res.raise_for_status()
        except requests.exceptions.HTTPError as err:
            raise Exception(err)

        data = res.json()

        for job in data["Results"]:
            job_id = self.env["tataru_secret_market.jobs"].search(
                [("unique_id", "=", int(job["ID"]))]
            )

            if not job_id:
                self.env["tataru_secret_market.jobs"].create(
                    {"unique_id": int(job["ID"]), "name": job["Name"]}
                )
            else:
                job_id.write({"name": job["Name"]})

        # TODO - Implementare la sincronizzazione dei jobs
