# -*- coding: utf-8 -*-
from odoo import http

# class KaHrPayroll(http.Controller):
#     @http.route('/ka_hr_payroll/ka_hr_payroll/', auth='public')
#     def index(self, **kw):
#         return "Hello, world"

#     @http.route('/ka_hr_payroll/ka_hr_payroll/objects/', auth='public')
#     def list(self, **kw):
#         return http.request.render('ka_hr_payroll.listing', {
#             'root': '/ka_hr_payroll/ka_hr_payroll',
#             'objects': http.request.env['ka_hr_payroll.ka_hr_payroll'].search([]),
#         })

#     @http.route('/ka_hr_payroll/ka_hr_payroll/objects/<model("ka_hr_payroll.ka_hr_payroll"):obj>/', auth='public')
#     def object(self, obj, **kw):
#         return http.request.render('ka_hr_payroll.object', {
#             'object': obj
#         })