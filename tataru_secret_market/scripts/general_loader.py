from odoo import models, api, fields
import datetime


class GeneralLoader(models.AbstractModel):
    _name = "tataru_secret_market.general_loader"

    @api.model
    def load_all_data(self):
        self.env["tataru_secret_market.worlds"].with_delay().sync_worlds(None)
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
                "&",
                "|",
                (
                    "last_time_sync_transactions",
                    "<",
                    fields.Datetime.now() - datetime.timedelta(days=1),
                ),
                ("last_time_sync_transactions", "=", False),
                ("sellable", "=", True),
            ]
        )
        # TODO - dovremmo cercare di limitarlo un po' di più con ulteririori filtri

        # divido in batch da 8
        batch = self.env["queue.job.batch"].get_new_batch("Sync item transactions")
        time = fields.Datetime.now()
        for item_batch in [items[i : i + 100] for i in range(0, len(items), 100)]:
            self.with_context(
                job_batch_id=batch
            ).with_delay(eta=time).sync_items_transactions_job(item_batch)
            time += datetime.timedelta(seconds=5)

    @api.model
    def sync_items_transactions_job(self, items):
        current_world = self.env["tataru_secret_market.worlds"].get_current_world()
        transactions_model = self.env["tataru_secret_market.item_sale_transactions"]
        for record in items:
            transactions_model.sync_item_transactions(record, current_world)
            record.last_time_sync_transactions = fields.Datetime.now()

        return "Transactions synced for: {}".format("\n".join(item.name for item in items))

    @api.model
    def cron_sync_items_availability(self):
        # prendo tutti gli item che non hanno transazioni sincronizzate da più di 1 giorno
        items = self.env["tataru_secret_market.items"].search(
            [
                "&",
                "|",
                (
                    "last_time_sync_availability",
                    "<",
                    fields.Datetime.now() - datetime.timedelta(days=0),
                ),
                ("last_time_sync_availability", "=", False),
                ("sellable", "=", True),
            ]
        )
        # TODO - dovremmo cercare di limitarlo un po' di più con ulteririori filtri

        # divido in batch da 8
        batch = self.env["queue.job.batch"].get_new_batch("Sync item availability")
        time = fields.Datetime.now()
        for item_batch in [items[i : i + 100] for i in range(0, len(items), 100)]:
            self.with_context(
                job_batch_id=batch
            ).with_delay(eta=time).sync_items_availability_job(item_batch)
            time += datetime.timedelta(seconds=5)

    @api.model
    def sync_items_availability_job(self, items):
        items.sync_item_availability()

        return "Availability synced for: {}".format("\n".join(item.name for item in items))

    # Runned 1 every week
    @api.model
    def cron_sync_jobs(self):
        self.env["tataru_secret_market.jobs"].with_delay().sync_jobs(None)

    # Runned 1 every week
    @api.model
    def cron_sync_items(self):
        self.env["tataru_secret_market.items"].with_delay().sync_items(None)

    # Runned 1 every week
    @api.model
    def cron_sync_datacenters_and_worlds(self):
        self.sync_datacenters(True)
        self.sync_worlds(True)

    @api.model
    def cron_sync_item_data(self):
        # prendo tutti gli item
        items = self.env["tataru_secret_market.items"].search(
            [
                "|",
                (
                    "last_time_sync_data",
                    "<",
                    fields.Datetime.now() - datetime.timedelta(days=0),
                ),
                ("last_time_sync_data", "=", False),
            ])
        # divido in batch da 8
        batch = self.env["queue.job.batch"].get_new_batch("Sync item data")
        time = fields.Datetime.now()
        for item_batch in [items[i : i + 8] for i in range(0, len(items), 8)]:
            self.with_context(
                job_batch_id=batch
            ).with_delay(eta=time).sync_item_data_job(item_batch)
            time += datetime.timedelta(seconds=1)  # TODO - rendere tipo 10 minuti in produzione per non sovraccaricare il server

    @api.model
    def sync_item_data_job(self, items):
        for item in items:
            self.env["tataru_secret_market.items"].sync_item_data(item)

        return "Data synced for: \n {}".format("\n".join(" - " + item.name for item in items))

    @api.model
    def cron_sync_item_recipe(self):
        # prendo tutti gli item craftabili
        items = self.env["tataru_secret_market.items"].search(
            [
                "|",
                (
                    "last_time_sync_recipe",
                    "<",
                    fields.Datetime.now() - datetime.timedelta(days=7),
                ),
                ("last_time_sync_recipe", "=", False),
            ])
        # divido in batch da 8
        batch = self.env["queue.job.batch"].get_new_batch("Sync item recipe")
        time = fields.Datetime.now()
        for item_batch in [items[i : i + 8] for i in range(0, len(items), 8)]:
            self.with_context(
                job_batch_id=batch
            ).with_delay(eta=time).sync_item_recipe_job(item_batch)
            time += datetime.timedelta(seconds=1)

    @api.model
    def sync_item_recipe_job(self, items):
        items.sync_item_recipe()
        return "Recipe synced for: {}".format("\n".join(item.name for item in items))

    @api.model
    def cron_load_opportunities(self):
        items = self.env["tataru_secret_market.items"].search([('sellable', '=', True), ("transactions_count_last_7d", ">", 0)], limit=1000, order="transactions_count_last_7d desc")

        batch = self.env["queue.job.batch"].get_new_batch("Load opportunities")
        for item_batch in [items[i : i + 100] for i in range(0, len(items), 100)]:
            self.with_context(
                job_batch_id=batch
            ).with_delay().load_opportunities_job(item_batch)

    @api.model
    def load_opportunities_job(self, items):
        for item in items:
            old_opportunity = self.env["tataru_secret_market.item_opportunity"].search(
                [("item_id", "=", item.id)]
            )
            if old_opportunity:
                old_opportunity.last_time_in_list_of_transactions = fields.Datetime.now()
            else:
                self.env["tataru_secret_market.item_opportunity"].create(
                    {"item_id": item.id}
                )

        return "Opportunities loaded for: \n {}".format("\n".join("- " + item.name for item in items))

    @api.model
    def cron_delete_old_oppotunities(self):
        # delete all opportunities that are older than 1 week
        opportunities = self.env["tataru_secret_market.item_opportunity"].search(
            [
                ("last_time_in_list_of_transactions", "<", fields.Datetime.now() - datetime.timedelta(days=30)),
                ("dont_delate", "=", False),
            ]
        )
        opportunities.unlink()
        return "Deleted {} old opportunities".format(len(opportunities))

    @api.model
    def cron_opportunities_update(self):
        items = self.env["tataru_secret_market.item_opportunity"].search([]).mapped("item_id")
        batch = self.env["queue.job.batch"].get_new_batch("Update opportunities")
        time = fields.Datetime.now()
        for opportunity_batch in [items[i : i + 20] for i in range(0, len(items), 20)]:
            self.with_context(
                job_batch_id=batch
            ).with_delay(eta=time).sync_items_availability_job(opportunity_batch)
            self.with_context(
                job_batch_id=batch
            ).with_delay(eta=time).sync_items_transactions_job(opportunity_batch)
            time += datetime.timedelta(seconds=10)
