# -*- coding: utf-8 -*-
from odoo import http

# class KaHrHolidays(http.Controller):
#     @http.route('/ka_hr_holidays/ka_hr_holidays/', auth='public')
#     def index(self, **kw):
#         return "Hello, world"

#     @http.route('/ka_hr_holidays/ka_hr_holidays/objects/', auth='public')
#     def list(self, **kw):
#         return http.request.render('ka_hr_holidays.listing', {
#             'root': '/ka_hr_holidays/ka_hr_holidays',
#             'objects': http.request.env['ka_hr_holidays.ka_hr_holidays'].search([]),
#         })

#     @http.route('/ka_hr_holidays/ka_hr_holidays/objects/<model("ka_hr_holidays.ka_hr_holidays"):obj>/', auth='public')
#     def object(self, obj, **kw):
#         return http.request.render('ka_hr_holidays.object', {
#             'object': obj
#         })