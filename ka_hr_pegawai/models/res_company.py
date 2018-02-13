# ----------------------------------------------------------
# Data jabatan pada tiap company
# author @CakJuice
# website: https://cakjuice.com
# email: hd.brandoz@gmail.com
# ----------------------------------------------------------

from odoo import models, fields

class res_company(models.Model):
	_inherit = 'res.company'

	dept_dirut = fields.Many2one('hr.department', string='Direktur Utama')
	dept_dirprod = fields.Many2one('hr.department', string='Direktur Produksi')
	dept_dirkeu = fields.Many2one('hr.department', string='Direktur Keuangan')
	dept_tuk = fields.Many2one('hr.department', string='T U K')
	dept_log = fields.Many2one('hr.department', string='Logistik')
	manager_log = fields.Many2one('hr.department', string='Manager Logistik')
	dept_sales = fields.Many2one('hr.department', string='Pemasaran')
	kasir_id = fields.Many2one('hr.employee', string='Kasir')
	# new department
	dept_sdm = fields.Many2one('hr.department', string="Dept. SDM")
	# group email
	email_group = fields.Char(string="Grup Email", size=128,
		help="Grup email internal yang digunakan untuk pengumuman karyawan.")
	hr_pensiun_age = fields.Integer(string="Usia Pensiun", help="Untuk menentukan usia pensiun dari pegawai.")
	hr_mpp_month = fields.Integer(string="Bulan MPP", help="Untuk menentukan jumlah bulan sebelum pensiun.")