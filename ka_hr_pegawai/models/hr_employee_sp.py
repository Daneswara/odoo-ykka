# ----------------------------------------------------------
# Surat Peringatan Pegawai
# author @CakJuice
# website: https://cakjuice.com
# email: hd.brandoz@gmail.com
# ----------------------------------------------------------

import base64
import calendar
from datetime import datetime
from odoo import models, fields, api
from odoo.exceptions import ValidationError
from odoo.tools import DEFAULT_SERVER_DATE_FORMAT as DATE_FORMAT

class KaHrEmployeeSP(models.Model):
	_name = 'hr.employee.sp'
	_description = "SDM Surat Peringatan"
	_order = 'id desc'
	_REPORT_NAME = 'ka_hr_pegawai.report_ka_hr_employee_sp_view'

	NAME_TELAT_WEEKLY = "Surat Peringatan I (Pertama)"
	ACUAN_TELAT_WEEKLY = """Bab II Pasal 5 Ayat 9a, yang berbunyi: \"Datang terlambat 2 kali dalam seminggu, tanpa alasan yang bisa diterima.\""""
	ALASAN_TELAT_WEEKLY = "Datang terlambat pada "
	NAME_TELAT_MONTHLY = "Surat Peringatan I (Pertama)"
	ACUAN_TELAT_MONTHLY = """Bab II Pasal 5 Ayat 9a, yang berbunyi: \"Datang terlambat 3 kali dalam sebulan, tanpa alasan yang bisa diterima.\""""
	ALASAN_TELAT_MONTHLY = "Datang terlambat pada "

	nomor = fields.Char(string="No. SP", size=64, required=True,
		readonly=True, default='/')
	date_sp = fields.Date(string="Tanggal SP", required=True, default=fields.Date.today,
		readonly=True, states={'draft': [('readonly', False)]})
	name = fields.Char(string="Deskripsi SP", required=True,
		readonly=True, states={'draft': [('readonly', False)]})
	employee_id = fields.Many2one('hr.employee', string="Nama Pegawai", required=True, domain=[('pensiun', '=', False)],
		readonly=True, states={'draft': [('readonly', False)]})
	level = fields.Selection([
		(1, 'SP 1'),
		(2, 'SP 2'),
		(3, 'SP 3'),
	], default=1, required=True, readonly=True, states={'draft': [('readonly', False)]})
	acuan = fields.Text(string="Acuan", required=True,
		readonly=True, states={'draft': [('readonly', False)]})
	alasan = fields.Text(string="Alasan", required=True,
		readonly=True, states={'draft': [('readonly', False)]})
	company_id = fields.Many2one('res.company', related='employee_id.company_id', string="Unit/PG", 
		readonly=True, required=True)
	state = fields.Selection([
		('draft', "Draft"),
		('approved', "Disetujui"),
		('canceled', "Dibatalkan"),
	], string="Status", default='draft')

	# _sql_constraints = [
	# 	('hr_employee_sp_unique', 'UNIQUE(nomor, company_id)', "Nomor SP sudah ada! Tidak boleh sama!")
	# ]

	def create_sp_telat_weekly(self, employee_id, str_date):
		return self.create({
			'employee_id': employee_id,
			'name': self.NAME_TELAT_WEEKLY,
			'acuan': self.ACUAN_TELAT_WEEKLY,
			'alasan': self.ALASAN_TELAT_WEEKLY + " {}.".format(str_date,),
		})

	def create_sp_telat_monthly(self, employee_id, str_date):
		return self.create({
			'employee_id': employee_id,
			'name': self.NAME_TELAT_MONTHLY,
			'acuan': self.ACUAN_TELAT_MONTHLY,
			'alasan': self.ALASAN_TELAT_MONTHLY + " {}.".format(str_date,),
		})

	@api.model
	def create(self, vals):
		"""get company_id by employee"""
		if not vals.has_key('company_id'):
			employee = self.env['hr.employee'].browse(vals['employee_id'])
			vals['company_id'] = employee.company_id.id

		"""Customize sequence date_range"""
		sequences = self.env['ir.sequence'].search([
			('code', 'like', self._name + '%'),
			('company_id', '=', vals['company_id'])
		], limit=1)
		
		if len(sequences) > 0:
			sequence = sequences[0]
			date_now = datetime.now().date()
			is_create_range = False
			if sequence.date_range_ids and len(sequence.date_range_ids) > 0:
				last_range = sequence.date_range_ids[-1]
				date_to_obj = datetime.strptime(last_range.date_to, DATE_FORMAT)
				if date_to_obj.month != date_now.month:
					is_create_range = True
			else:
				is_create_range = True
			
			if is_create_range:
				last_day = calendar.monthrange(date_now.year, date_now.month)[1]
				date_range = self.env['ir.sequence.date_range'].create({
					'number_next': 1,
					'date_from': '{}-{}-01'.format(date_now.year, date_now.month),
					'date_to': '{}-{}-{}'.format(date_now.year, date_now.month, last_day),
					'sequence_id': sequence.id
				})
				date_range._cr.commit()

			vals['nomor'] = sequence.next_by_id()
			return super(KaHrEmployeeSP, self).create(vals)
		else:
			raise ValidationError("Nomor urutan belum diset! Hubungi Administrator!")

	def get_ttd_dirut(self):
		return self.company_id.dept_dirut.manager_id.name

	def get_ttd_job(self):
		return self.company_id.dept_dirut.manager_id.job_id.name

	def get_email_cc(self):
		return self.company_id.dept_sdm.manager_id.work_email or ''

	def get_subject_name(self):
		return '{}_({})'.format(self.name, self.nomor).replace(' ', '_')

	def _get_attachment(self):
		attachments = self.env['ir.attachment'].search([
			('res_model', '=', self._name),
			('res_id', '=', self.id)
		], limit=1)

		attachment_name = self.get_subject_name()
		attachment = None

		pdf = self.env['report'].get_pdf([self.id], self._REPORT_NAME)
		if len(attachments) > 0:
			attachment = attachments[0]
			attachment.write({
				'name': attachment_name,
				'datas': base64.encodestring(pdf),
				'datas_fname': attachment_name + ".pdf",
				'store_fname': attachment_name,
			})

			self._cr.commit()
		else:
			attachment = self.env['ir.attachment'].create({
				'name': attachment_name,
				'type': 'binary',
				'datas': base64.encodestring(pdf),
				'datas_fname': attachment_name + ".pdf",
				'store_fname': attachment_name,
				'res_model': self._name,
				'res_id': self.id,
				'mimetype': 'application/x-pdf',
			})
			self._cr.commit()

		return attachment

	def _remove_attachment(self):
		attachments = self.env['ir.attachment'].search([
			('res_model', '=', self._name),
			('res_id', '=', self.id)
		], limit=1)

		if len(attachments) > 0:
			attachment = attachments[0]
			attachment.unlink()
			self._cr.commit()

	@api.multi
	def action_draft(self):
		for s in self:
			s.state = 'draft'
			s._remove_attachment()

	@api.multi
	def action_approve(self):
		for s in self:
			if not s.employee_id.work_email or not s.company_id.email:
				raise ValidationError("Email pegawai belum diisi!")
			if not s.company_id.email:
				raise ValidationError("Email Unit/PG belum diisi!")

			s.state = 'approved'
			attachment = s._get_attachment()
			template = s.env.ref('ka_hr_pegawai.template_mail_employee_sp_approved')
			mail = s.env['mail.template'].browse(template.id)
			mail.attachments_ids = attachment
			s._cr.commit()
			mail.send_mail(s.id, force_send=True)
			mail.attachments_ids = None
			s._cr.commit()
			s.env.user.notify_info("Email pemberitahuan persetujuan sudah dikirim ke karyawan yang bersangkutan!")

	@api.multi
	def action_cancel(self):
		for s in self:
			old_state = s.state
			s.state = 'canceled'
			s._remove_attachment()
			
			if old_state == 'draft':
				continue

			template = s.env.ref('ka_hr_pegawai.template_mail_employee_sp_canceled')
			mail = s.env['mail.template'].browse(template.id)
			mail.send_mail(s.id, force_send=True)
			s.env.user.notify_info("Email pemberitahuan pembatalan sudah dikirim ke karyawan yang bersangkutan!")