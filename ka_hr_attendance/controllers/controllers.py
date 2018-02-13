# -*- coding: utf-8 -*-
from odoo import http

# class KaHrAttendance(http.Controller):
#     @http.route('/ka_hr_attendance/ka_hr_attendance/', auth='public')
#     def index(self, **kw):
#         return "Hello, world"

#     @http.route('/ka_hr_attendance/ka_hr_attendance/objects/', auth='public')
#     def list(self, **kw):
#         return http.request.render('ka_hr_attendance.listing', {
#             'root': '/ka_hr_attendance/ka_hr_attendance',
#             'objects': http.request.env['ka_hr_attendance.ka_hr_attendance'].search([]),
#         })

#     @http.route('/ka_hr_attendance/ka_hr_attendance/objects/<model("ka_hr_attendance.ka_hr_attendance"):obj>/', auth='public')
#     def object(self, obj, **kw):
#         return http.request.render('ka_hr_attendance.object', {
#             'object': obj
#         })