# -*- coding: utf-8 -*-
from odoo import http

# class BaseWilayah(http.Controller):
#     @http.route('/base_wilayah/base_wilayah/', auth='public')
#     def index(self, **kw):
#         return "Hello, world"

#     @http.route('/base_wilayah/base_wilayah/objects/', auth='public')
#     def list(self, **kw):
#         return http.request.render('base_wilayah.listing', {
#             'root': '/base_wilayah/base_wilayah',
#             'objects': http.request.env['base_wilayah.base_wilayah'].search([]),
#         })

#     @http.route('/base_wilayah/base_wilayah/objects/<model("base_wilayah.base_wilayah"):obj>/', auth='public')
#     def object(self, obj, **kw):
#         return http.request.render('base_wilayah.object', {
#             'object': obj
#         })