from odoo import models, fields, api, exceptions
from math import ceil
from datetime import datetime

class logistik_spm(models.Model):
	_name = 'logistik.spm'
	_inherit = ['mail.thread', 'ir.needaction_mixin']
	_description = "SPM / Surat Permintaan Material"
	_order = "tanggal desc"

	nomor = fields.Char(string='Nomor', size=15, readonly=True, default='/')
	no_spm = fields.Char(string='Nomor SPM', size=15, required=True, readonly=True, default='/')
	name =  fields.Char(string='Nomor SPM', compute='_compute_name', store=True)
	split_no = fields.Integer(string='No. Split', readonly=True)
	tanggal = fields.Date(string='Tanggal', required=True, default=fields.Date.today)
	date_validated = fields.Date(string='Tanggal SPM', required=False)
	line_ids = fields.One2many('logistik.spm.lines', 'spm_id', string='Detail SPM', domain=[('parent_id', '=', False)])
	operating_unit_id = fields.Many2one('res.partner', required=True, string="Unit/PG", 
        domain=[('is_operating_unit', '=', True)], 
        default=lambda self: self.env['res.users'].operating_unit_default_get(self._uid))
	company_id = fields.Many2one('res.company', string='Perusahaan', required=True, default=lambda self: self.env['res.company']._company_default_get('logistik.pengajuan.spm'))
	user_id = fields.Many2one('res.users', string='User SPM', states={'draft': [('readonly', False)]}, default=lambda self: self._uid)
	pengadaan = fields.Selection([
		('RD', 'Direksi'),
		('RP', 'Pabrik'),
	], string='Jenis SP', required=True)
	category = fields.Selection([
		('none', 'Belum Dikategorikan'),
		('rab', 'RAB'),
		('nonrab', 'Non RAB'),
		('noncode', 'Tanpa Kode'),
	], string='Jenis SPM')
	state = fields.Selection([
		('draft', 'Konsep'),
		('validated', 'Di-Validasi'), 	#By TUK - PG
		('approved', 'Di-Setujui'),		#by Direksi
		('reject', 'Di-Batalkan')
	], string='Status', track_visibility='onchange', default='draft')
	parent_id = fields.Many2one('logistik.spm', string='SPM Induk', readonly=True)
	note = fields.Text(string='Catatan')
	purchase_ids = fields.One2many('purchase.order', 'spm_id', string='Realisasi SP', readonly=True)

	_sql_constraints = [
		('no_spm_unique', 'UNIQUE(no_spm)', 'Nomor SPM Sudah ada!')
	]

	def week_of_month(self, dt):
		""" Returns the week of the month for the specified date.
		"""
		first_day = dt.replace(day=1)
		dom = dt.day
		adjusted_dom = dom + first_day.weekday()
		return int(ceil(adjusted_dom/7.0))			    
    
	@api.depends('no_spm', 'parent_id', 'split_no')
	def _compute_name(self):
		for s in self:
			s.name = s.get_name(s.parent_id, s.no_spm, s.split_no)

	def get_name(self, parent_id, no_spm, split_no):
		name = "%s(%s)" % (no_spm, split_no) if parent_id else no_spm
		return name

	@api.model
	def create(self, vals):
		if vals.has_key('no_spm') and vals.has_key('operating_unit_id') and not vals['operating_unit_id']:
			vals['operating_unit_id'] = self.get_company_id(vals['no_spm'])
		return super(logistik_spm, self).create(vals)

	@api.multi
	def write(self, vals):
		if vals.has_key('no_spm'):
			vals['operating_unit_id'] = self.get_company_id(vals['no_spm'])
			print vals['operating_unit_id']
		return super(logistik_spm, self).write(vals)

	def get_company_id(self, no_spm):
		if not no_spm:
			return None
			
		if no_spm[0] == "D":
			_code = '1'
		elif no_spm[0] == "K":
			_code = '2'
		elif no_spm[0] == "T":
			_code = '4'

		return self.env['res.company'].sudo().search([('code', '=', _code)], limit=1).partner_id.id

	@api.onchange('no_spm')
	def onchange_spm(self):
		if self.no_spm != '/':
			res = self.env['logistik.spm'].search([('no_spm', '=', self.no_spm)])
			if res:
				raise exceptions.Warning('Nomor SPM Sudah ada!')
			else:
				# self.company_id = self.get_company_id(self.no_spm)
				self.operating_unit_id = self.get_company_id(self.no_spm)

	@api.multi
	def action_reject(self, ids):
		for spm in self:
			spm.line_ids.write({'state':'reject'})
		
		return self.write({'state':'reject'})

	@api.multi
	def _get_sequence(self, category):
		seq = self.env['ir.sequence']
		if category == 'rab':
			return seq.next_by_code('logistik.nomor.spm.rab')
		if category == 'nonrab':
			return seq.next_by_code('logistik.nomor.spm.nonrab')
		if category == 'noncode':
			return seq.next_by_code('logistik.nomor.spm.noncode')

	@api.one
	def action_number(self, no_spm=None):
		nomor = self.no_spm or no_spm
		if nomor == '/':
			nomor = self._get_sequence(self.category)

		for line in [ln for ln in self.line_ids if ln.state in ('draft', 'wait')]:
			line.action_spm_direksi()
			
		self.write({'state':'approved', 'no_spm': nomor})
		return True	
	
	@api.multi
	def get_nomor_spm(self, category, tanggal):
		#get week of month
		dt = datetime.strptime(tanggal,'%Y-%m-%d')
		week = self.week_of_month(dt)
		
		seq_spm = self._get_sequence(category) or False
		
		if not seq_spm:
			raise exceptions.Warning('Penomoran SPM Direksi belum didefinisikan')
			return

		params = {}
		rec_count = 1
		params['bulan'] = int(tanggal[5:7])
		params['tahun'] = int(tanggal[:4])
		# self._cr.execute("""SELECT count(tanggal), date_part('month', tanggal) 
			# FROM logistik_spm  WHERE date_part('year', tanggal) = %s AND date_part('month', tanggal) = %s 
			# GROUP BY 2""" % (params['tahun'], params['bulan']))
		# res = self._cr.fetchone()
		# if res:
			# rec_count = res[0]	
			
		# seq_spm = seq_spm.replace('X', str(rec_count))	#bulan counter
		
		seq_spm = seq_spm.replace('X', str(week))
		nomor = seq_spm.replace(tanggal[2:4], tanggal[3:4])
		return nomor
		
	# #SPM hanya dapat di hapus, apabila belum digolongkan
	@api.multi
	def unlink(self):
		for s in self:
			if s.state == 'draft':
				super(logistik_spm, self).unlink()
			else:
				raise exceptions.Warning('SPM yang sudah di setujui tidak dapat dihapus!')
		return