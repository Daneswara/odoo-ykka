# -*- coding: utf-8 -*-
from odoo import http

# class KaLogistikSpm(http.Controller):
#     @http.route('/ka_logistik_spm/ka_logistik_spm/', auth='public')
#     def index(self, **kw):
#         return "Hello, world"

#     @http.route('/ka_logistik_spm/ka_logistik_spm/objects/', auth='public')
#     def list(self, **kw):
#         return http.request.render('ka_logistik_spm.listing', {
#             'root': '/ka_logistik_spm/ka_logistik_spm',
#             'objects': http.request.env['ka_logistik_spm.ka_logistik_spm'].search([]),
#         })

#     @http.route('/ka_logistik_spm/ka_logistik_spm/objects/<model("ka_logistik_spm.ka_logistik_spm"):obj>/', auth='public')
#     def object(self, obj, **kw):
#         return http.request.render('ka_logistik_spm.object', {
#             'object': obj
#         })