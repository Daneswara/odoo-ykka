# -*- coding: utf-8 -*-
from odoo import http

# class KaLogistikPengadaan(http.Controller):
#     @http.route('/ka_logistik_pengadaan/ka_logistik_pengadaan/', auth='public')
#     def index(self, **kw):
#         return "Hello, world"

#     @http.route('/ka_logistik_pengadaan/ka_logistik_pengadaan/objects/', auth='public')
#     def list(self, **kw):
#         return http.request.render('ka_logistik_pengadaan.listing', {
#             'root': '/ka_logistik_pengadaan/ka_logistik_pengadaan',
#             'objects': http.request.env['ka_logistik_pengadaan.ka_logistik_pengadaan'].search([]),
#         })

#     @http.route('/ka_logistik_pengadaan/ka_logistik_pengadaan/objects/<model("ka_logistik_pengadaan.ka_logistik_pengadaan"):obj>/', auth='public')
#     def object(self, obj, **kw):
#         return http.request.render('ka_logistik_pengadaan.object', {
#             'object': obj
#         })