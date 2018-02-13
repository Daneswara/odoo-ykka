# -*- coding: utf-8 -*-
from odoo import http

# class KaLogistikPkrat(http.Controller):
#     @http.route('/ka_logistik_pkrat/ka_logistik_pkrat/', auth='public')
#     def index(self, **kw):
#         return "Hello, world"

#     @http.route('/ka_logistik_pkrat/ka_logistik_pkrat/objects/', auth='public')
#     def list(self, **kw):
#         return http.request.render('ka_logistik_pkrat.listing', {
#             'root': '/ka_logistik_pkrat/ka_logistik_pkrat',
#             'objects': http.request.env['ka_logistik_pkrat.ka_logistik_pkrat'].search([]),
#         })

#     @http.route('/ka_logistik_pkrat/ka_logistik_pkrat/objects/<model("ka_logistik_pkrat.ka_logistik_pkrat"):obj>/', auth='public')
#     def object(self, obj, **kw):
#         return http.request.render('ka_logistik_pkrat.object', {
#             'object': obj
#         })