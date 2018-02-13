# ----------------------------------------------------------
# Data pendidikan karyawan
# inherit from hr.employee.graduate
# author @CakJuice
# website: https://cakjuice.com
# email: hd.brandoz@gmail.com
# ----------------------------------------------------------

from odoo import models, fields

class hr_employee_graduate(models.Model):
	_name = 'hr.employee.graduate'
	_description = "SDM Riwayat Pendidikan Pegawai"

	employee_id = fields.Many2one('hr.employee', string='Pegawai', required=True)
	graduate_id = fields.Many2one('hr.graduate', string='Pendidikan', required=True)
	lembaga = fields.Char(string='Lembaga', size=32)
	jurusan = fields.Char(string='Jurusan', size=32)
	tahun = fields.Char(string='Tahun', size=4)
	
class hr_employee_course(models.Model):
	_name = 'hr.employee.course'
	_description = "SDM Riwayat Pendidikan Non Formal"

	employee_id = fields.Many2one('hr.employee', string='Pegawai', required=True)
	lembaga = fields.Char(string='Lembaga', size=32)
	keterangan = fields.Char(string='Uraian/Materi', size=256)
	tahun = fields.Char(string='Tahun', size=4)	