# -*- coding: utf-8 -*-
from openerp import http

# class HrPegawai(http.Controller):
#     @http.route('/hr_pegawai/hr_pegawai/', auth='public')
#     def index(self, **kw):
#         return "Hello, world"

#     @http.route('/hr_pegawai/hr_pegawai/objects/', auth='public')
#     def list(self, **kw):
#         return http.request.render('hr_pegawai.listing', {
#             'root': '/hr_pegawai/hr_pegawai',
#             'objects': http.request.env['hr_pegawai.hr_pegawai'].search([]),
#         })

#     @http.route('/hr_pegawai/hr_pegawai/objects/<model("hr_pegawai.hr_pegawai"):obj>/', auth='public')
#     def object(self, obj, **kw):
#         return http.request.render('hr_pegawai.object', {
#             'object': obj
#         })