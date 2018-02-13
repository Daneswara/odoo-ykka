# ----------------------------------------------------------
# Data config setting cuti & absensi SDM
# author @CakJuice
# website: https://cakjuice.com
# email: hd.brandoz@gmail.com
# ---------------------------------------------------------

from odoo import models, fields, api

class KaHrHolidaysConfigWizard(models.TransientModel):
	_name = 'ka_hr.holidays.config.wizard'

	company_id = fields.Many2one('res.company', string="Unit/PG", required=True,
		default=lambda self: self.env.user.company_id)
	hr_holidays_yearly_item = fields.Many2one(related='company_id.hr_holidays_yearly_item',
		string="Item Alokasi Cuti Tahunan", domain=[('holiday_type', '=', 'add')])
	hr_holidays_yearly_periodic = fields.Integer(related='company_id.hr_holidays_yearly_periodic',
		string="Periode Cuti Tahunan", default=1)
	hr_holidays_max_sisa_yearly = fields.Integer(related='company_id.hr_holidays_max_sisa_yearly',
		string="Max. Sisa Cuti Tahunan", default=0)
	hr_holidays_big_item = fields.Many2one(related='company_id.hr_holidays_big_item',
		string="Item Alokasi Cuti Besar", domain=[('holiday_type', '=', 'add')])
	hr_holidays_big_periodic = fields.Integer(related='company_id.hr_holidays_big_periodic',
		string="Periode Cuti Besar", default=1)
	hr_holidays_max_sisa_big = fields.Integer(related='company_id.hr_holidays_max_sisa_big',
		string="Max. Sisa Cuti Besar", default=0)
	hr_holidays_group_item = fields.Many2one(related='company_id.hr_holidays_group_item',
		string="Item Pengurang Cuti Bersama", domain=[('holiday_type', '=', 'remove'), ('leave_type', '=', 'cuti')])
	hr_holidays_inhaldagen_item = fields.Many2one(related='company_id.hr_holidays_inhaldagen_item',
		string="Item Alokasi Cuti Inhaldagen", domain=[('holiday_type', '=', 'add')])
	hr_holidays_inhaldagen_expire = fields.Integer(related='company_id.hr_holidays_inhaldagen_expire',
		string="Jumlah Kadaluwarsa Inhaldagen")

	@api.multi
	def save_data(self):
		self.company_id.hr_holidays_yearly_item = self.hr_holidays_yearly_item
		self.company_id.hr_holidays_yearly_periodic = self.hr_holidays_yearly_periodic
		self.company_id.hr_holidays_max_sisa_yearly = self.hr_holidays_max_sisa_yearly
		self.company_id.hr_holidays_big_item = self.hr_holidays_big_item
		self.company_id.hr_holidays_big_periodic = self.hr_holidays_big_periodic
		self.company_id.hr_holidays_max_sisa_big = self.hr_holidays_max_sisa_big
		self.company_id.hr_holidays_group_item = self.hr_holidays_group_item
		self.company_id.hr_holidays_inhaldagen_item = self.hr_holidays_inhaldagen_item
		self.company_id.hr_holidays_inhaldagen_expire = self.hr_holidays_inhaldagen_expire