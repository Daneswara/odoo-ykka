# -*- coding: utf-8 -*-
from odoo import http

# class KaFingerspot(http.Controller):
#     @http.route('/ka_fingerspot/ka_fingerspot/', auth='public')
#     def index(self, **kw):
#         return "Hello, world"

#     @http.route('/ka_fingerspot/ka_fingerspot/objects/', auth='public')
#     def list(self, **kw):
#         return http.request.render('ka_fingerspot.listing', {
#             'root': '/ka_fingerspot/ka_fingerspot',
#             'objects': http.request.env['ka_fingerspot.ka_fingerspot'].search([]),
#         })

#     @http.route('/ka_fingerspot/ka_fingerspot/objects/<model("ka_fingerspot.ka_fingerspot"):obj>/', auth='public')
#     def object(self, obj, **kw):
#         return http.request.render('ka_fingerspot.object', {
#             'object': obj
#         })