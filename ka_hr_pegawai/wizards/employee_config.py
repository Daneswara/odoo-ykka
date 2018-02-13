# ----------------------------------------------------------
# Data config kepegawaian
# author @CakJuice
# website: https://cakjuice.com
# email: hd.brandoz@gmail.com
# ----------------------------------------------------------

from odoo import models, fields, api

class KaHrPegawaiConfigWizard(models.TransientModel):
	_name = 'ka_hr_pegawai.config.wizard'

	company_id = fields.Many2one('res.company', string="Unit/PG", required=True,
		default=lambda self: self.env.user.company_id)
	hr_pensiun_age = fields.Integer(related='company_id.hr_pensiun_age', string="Usia Pensiun",
		help="Untuk menentukan usia pensiun dari pegawai.")
	hr_mpp_month = fields.Integer(related='company_id.hr_mpp_month', string="Bulan MPP",
		help="Untuk menentukan jumlah bulan sebelum pensiun.")

	@api.multi
	def save_data(self):
		self.company_id.hr_pensiun_age = self.hr_pensiun_age
		self.company_id.hr_mpp_month = self.hr_mpp_month