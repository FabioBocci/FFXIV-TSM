# -*- coding: utf-8 -*-
# from odoo import http


# class TsmXDiscord(http.Controller):
#     @http.route('/tsm_x_discord/tsm_x_discord', auth='public')
#     def index(self, **kw):
#         return "Hello, world"

#     @http.route('/tsm_x_discord/tsm_x_discord/objects', auth='public')
#     def list(self, **kw):
#         return http.request.render('tsm_x_discord.listing', {
#             'root': '/tsm_x_discord/tsm_x_discord',
#             'objects': http.request.env['tsm_x_discord.tsm_x_discord'].search([]),
#         })

#     @http.route('/tsm_x_discord/tsm_x_discord/objects/<model("tsm_x_discord.tsm_x_discord"):obj>', auth='public')
#     def object(self, obj, **kw):
#         return http.request.render('tsm_x_discord.object', {
#             'object': obj
#         })
