# -*- coding: utf-8 -*-
from odoo import http

# class Ykka(http.Controller):
#     @http.route('/ykka/ykka/', auth='public')
#     def index(self, **kw):
#         return "Hello, world"

#     @http.route('/ykka/ykka/objects/', auth='public')
#     def list(self, **kw):
#         return http.request.render('ykka.listing', {
#             'root': '/ykka/ykka',
#             'objects': http.request.env['ykka.ykka'].search([]),
#         })

#     @http.route('/ykka/ykka/objects/<model("ykka.ykka"):obj>/', auth='public')
#     def object(self, obj, **kw):
#         return http.request.render('ykka.object', {
#             'object': obj
#         })