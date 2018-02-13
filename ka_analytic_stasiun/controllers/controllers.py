# -*- coding: utf-8 -*-
from openerp import http

# class AnalyticStasiun(http.Controller):
#     @http.route('/analytic_stasiun/analytic_stasiun/', auth='public')
#     def index(self, **kw):
#         return "Hello, world"

#     @http.route('/analytic_stasiun/analytic_stasiun/objects/', auth='public')
#     def list(self, **kw):
#         return http.request.render('analytic_stasiun.listing', {
#             'root': '/analytic_stasiun/analytic_stasiun',
#             'objects': http.request.env['analytic_stasiun.analytic_stasiun'].search([]),
#         })

#     @http.route('/analytic_stasiun/analytic_stasiun/objects/<model("analytic_stasiun.analytic_stasiun"):obj>/', auth='public')
#     def object(self, obj, **kw):
#         return http.request.render('analytic_stasiun.object', {
#             'object': obj
#         })