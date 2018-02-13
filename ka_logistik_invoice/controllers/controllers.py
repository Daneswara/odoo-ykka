# -*- coding: utf-8 -*-
from odoo import http

# class KaLogistikInvoice(http.Controller):
#     @http.route('/ka_logistik_invoice/ka_logistik_invoice/', auth='public')
#     def index(self, **kw):
#         return "Hello, world"

#     @http.route('/ka_logistik_invoice/ka_logistik_invoice/objects/', auth='public')
#     def list(self, **kw):
#         return http.request.render('ka_logistik_invoice.listing', {
#             'root': '/ka_logistik_invoice/ka_logistik_invoice',
#             'objects': http.request.env['ka_logistik_invoice.ka_logistik_invoice'].search([]),
#         })

#     @http.route('/ka_logistik_invoice/ka_logistik_invoice/objects/<model("ka_logistik_invoice.ka_logistik_invoice"):obj>/', auth='public')
#     def object(self, obj, **kw):
#         return http.request.render('ka_logistik_invoice.object', {
#             'object': obj
#         })