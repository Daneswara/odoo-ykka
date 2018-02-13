# -*- coding: utf-8 -*-
from odoo import http

# class KaLogistikSp(http.Controller):
#     @http.route('/ka_logistik_sp/ka_logistik_sp/', auth='public')
#     def index(self, **kw):
#         return "Hello, world"

#     @http.route('/ka_logistik_sp/ka_logistik_sp/objects/', auth='public')
#     def list(self, **kw):
#         return http.request.render('ka_logistik_sp.listing', {
#             'root': '/ka_logistik_sp/ka_logistik_sp',
#             'objects': http.request.env['ka_logistik_sp.ka_logistik_sp'].search([]),
#         })

#     @http.route('/ka_logistik_sp/ka_logistik_sp/objects/<model("ka_logistik_sp.ka_logistik_sp"):obj>/', auth='public')
#     def object(self, obj, **kw):
#         return http.request.render('ka_logistik_sp.object', {
#             'object': obj
#         })