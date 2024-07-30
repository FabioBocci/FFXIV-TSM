# -*- coding: utf-8 -*-
# from odoo import http


# class TataruSecretMarket(http.Controller):
#     @http.route('/tataru_secret_market/tataru_secret_market', auth='public')
#     def index(self, **kw):
#         return "Hello, world"

#     @http.route('/tataru_secret_market/tataru_secret_market/objects', auth='public')
#     def list(self, **kw):
#         return http.request.render('tataru_secret_market.listing', {
#             'root': '/tataru_secret_market/tataru_secret_market',
#             'objects': http.request.env['tataru_secret_market.tataru_secret_market'].search([]),
#         })

#     @http.route('/tataru_secret_market/tataru_secret_market/objects/<model("tataru_secret_market.tataru_secret_market"):obj>', auth='public')
#     def object(self, obj, **kw):
#         return http.request.render('tataru_secret_market.object', {
#             'object': obj
#         })
