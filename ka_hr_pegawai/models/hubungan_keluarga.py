# ----------------------------------------------------------
# Data keluarga pegawai
# author @CakJuice
# website: https://cakjuice.com
# email: hd.brandoz@gmail.com
# ----------------------------------------------------------

from odoo import models, fields, api

class KaHrHubunganKeluarga(models.Model):
	_name = 'ka_hr.hubungan.keluarga'
	_description = "SDM Hubungan Keluarga"

	name = fields.Char(string="Nama Hub. Keluarga")

class KaHrEmployeeKeluarga(models.Model):
	_name = 'ka_hr.employee.keluarga'
	_description = "SDM Hubungan Keluarga Pegawai"

	employee_id = fields.Many2one('hr.employee', string="Nama Karyawan", required=True)
	hub_keluarga_id = fields.Many2one('ka_hr.hubungan.keluarga', string="Hubungan Keluarga", required=True)
	name_keluarga = fields.Char(string="Nama Keluarga", size=128, required=True)
