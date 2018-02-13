# -*- coding: utf-8 -*-
from openerp import http

# class LogistikMaster(http.Controller):
#     @http.route('/logistik_master/logistik_master/', auth='public')
#     def index(self, **kw):
#         return "Hello, world"

#     @http.route('/logistik_master/logistik_master/objects/', auth='public')
#     def list(self, **kw):
#         return http.request.render('logistik_master.listing', {
#             'root': '/logistik_master/logistik_master',
#             'objects': http.request.env['logistik_master.logistik_master'].search([]),
#         })

#     @http.route('/logistik_master/logistik_master/objects/<model("logistik_master.logistik_master"):obj>/', auth='public')
#     def object(self, obj, **kw):
#         return http.request.render('logistik_master.object', {
#             'object': obj
#         })