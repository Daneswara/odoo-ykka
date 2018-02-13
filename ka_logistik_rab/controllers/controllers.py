# -*- coding: utf-8 -*-
from openerp import http

# class LogistikRab(http.Controller):
#     @http.route('/logistik_rab/logistik_rab/', auth='public')
#     def index(self, **kw):
#         return "Hello, world"

#     @http.route('/logistik_rab/logistik_rab/objects/', auth='public')
#     def list(self, **kw):
#         return http.request.render('logistik_rab.listing', {
#             'root': '/logistik_rab/logistik_rab',
#             'objects': http.request.env['logistik_rab.logistik_rab'].search([]),
#         })

#     @http.route('/logistik_rab/logistik_rab/objects/<model("logistik_rab.logistik_rab"):obj>/', auth='public')
#     def object(self, obj, **kw):
#         return http.request.render('logistik_rab.object', {
#             'object': obj
#         })