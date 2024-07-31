from odoo import models, api, fields
import datetime


class GeneralLoader(models.AbstractModel):
    _name = "tataru_secret_market.general_loader"

    @api.model
    def load_all_data(self):
        self.env["tataru_secret_market.worlds"].with_delay().sync_worlds(None)
        self.env["tataru_secret_market.data_centers"].with_delay().sync_datacenter(None)
        self.env["tataru_secret_market.data_centers"].with_delay().sync_datacenter(None)
        self.env["tataru_secret_market.jobs"].with_delay().sync_jobs(None)
        self.env["tataru_secret_market.items"].with_delay().sync_items(None)

    @api.model
    def sync_worlds(self, use_job=True):
        if use_job:
            self.env["tataru_secret_market.worlds"].with_delay().sync_worlds(None)
        else:
            self.env["tataru_secret_market.worlds"].sync_worlds(None)

    @api.model
    def sync_datacenters(self, use_job=True):
        if use_job:
            self.env["tataru_secret_market.data_centers"].with_delay().sync_datacenter(
                None
            )
        else:
            self.env["tataru_secret_market.data_centers"].sync_datacenter(None)

    @api.model
    def sync_jobs(self, use_job=True):
        if use_job:
            self.env["tataru_secret_market.jobs"].with_delay().sync_jobs(None)
        else:
            self.env["tataru_secret_market.jobs"].sync_jobs(None)

    @api.model
    def cron_sync_items_transactions(self):
        # prendo tutti gli item che non hanno transazioni sincronizzate da più di 1 giorno
        items = self.env["tataru_secret_market.items"].search(
            [
                "|",
                (
                    "last_time_sync_transactions",
                    "<",
                    fields.Datetime.now() - datetime.timedelta(days=1),
                ),
                ("last_time_sync_transactions", "=", False),
            ]
        )

        # divido in batch da 8
        batch = self.env["queue.job.batch"].get_new_batch("Sync item transactions")
        for item_batch in [items[i : i + 8] for i in range(0, len(items), 8)]:
            self.with_context(
                job_batch_id=batch
            ).with_delay().sync_items_transactions_job(item_batch)

    @api.model
    def sync_items_transactions_job(self, items):
        current_world = self.env["tataru_secret_market.worlds"].get_current_world()
        transactions_model = self.env["tataru_secret_market.item_sale_transactions"]
        for record in items:
            record.transactions_ids.unlink()
            transactions_model.sync_item_transactions(record, current_world)
            record.last_time_sync_transactions = fields.Datetime.now()
