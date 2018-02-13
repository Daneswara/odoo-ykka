# -*- coding: utf-8 -*-
from odoo import http

# class KaStock(http.Controller):
#     @http.route('/ka_stock/ka_stock/', auth='public')
#     def index(self, **kw):
#         return "Hello, world"

#     @http.route('/ka_stock/ka_stock/objects/', auth='public')
#     def list(self, **kw):
#         return http.request.render('ka_stock.listing', {
#             'root': '/ka_stock/ka_stock',
#             'objects': http.request.env['ka_stock.ka_stock'].search([]),
#         })

#     @http.route('/ka_stock/ka_stock/objects/<model("ka_stock.ka_stock"):obj>/', auth='public')
#     def object(self, obj, **kw):
#         return http.request.render('ka_stock.object', {
#             'object': obj
#         })