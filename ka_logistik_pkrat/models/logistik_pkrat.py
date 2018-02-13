from odoo import models, fields, api

class logistik_pkrat(models.Model):
	_name = 'logistik.pkrat'
	_description = "Anggaran/PKRAT"
	_table = "logistik_pkrat"
	_inherits = {'account.analytic.account': 'account_analytic_id'}
	_rec_name = 'code'
	_order = 'fiscal_year desc'

	spesifikasi = fields.Text(string='Spesifikasi')
	account_analytic_id = fields.Many2one('account.analytic.account', string='Account Analytic', required=True, ondelete="cascade")
	# stasiun_id = fields.Many2one('account.analytic.stasiun', string='Stasiun', domain="[('company_id', '=', company_id), ('type', '=', 'normal')]", required=True)
	stasiun_id = fields.Many2one('account.analytic.stasiun', string='Stasiun', required=True)
	department_id = fields.Many2one(string='Bagian', related='stasiun_id.department_id', store=True, readonly=True)
	# fiscal_year = fields.Many2one('ka.account.fiscalyear', string='Tahun Anggaran', domain="[('company_id', '=', company_id)]", required=True)
	fiscal_year = fields.Many2one('ka.account.fiscalyear', string='Tahun Anggaran', required=True)
	# account_id = fields.Many2one('account.account', string='No. Perkiraan', domain="[('company_id', '=', company_id)]")
	account_id = fields.Many2one('account.account', string='No. Perkiraan')
	product_id = fields.Many2one('product.template', string='Referensi Barang')
	nilai =  fields.Float(string='Nilai Proyek', digits=(16, 2), required=True)
	kontrak_ids = fields.One2many('logistik.pkrat.kontrak', 'pkrat_id', string='Kontrak')
	fisik_ids = fields.One2many('logistik.pkrat.fisik', 'pkrat_id', string='Realisasi Fisik')
	tahap = fields.Selection([
		('1','Satu'),
		('2','Dua'),
		('3','Tiga'),
	], string='Tahap Realisasi')
	no_ijin = fields.Char(string='No. Perijinan', size=15)
	no_setuju = fields.Char(string='No. Persetujuan', size=15)
	tgl_ijin = fields.Date(string='Tgl. Perijinan')
	tgl_setuju = fields.Date(string='Tgl. Persetujuan')
	pkrat_state = fields.Selection([
		('none','None'),
		('draft','Permohonan'),
		('comfirm','Di-Ijinkan'),
		('approved','Di-Setujui'),
	], string='State', default='none')
	operating_unit_id = fields.Many2one('res.partner', string="Unit/PG", domain=[('is_operating_unit', '=', True)])


	# @override
	@api.model
	def name_search(self, name='', args=None, domain=[], operator='ilike', limit=80):
		if not args:
			args = []

		if name:
			record = self.search([('code', operator, name)] + args, limit=limit)
			if not record:
				record = self.search([('name', operator, name)] + args, limit=limit)
		else:
			record = self.search(args, limit=limit)

		return record.name_get()

	# @override
	@api.multi
	def unlink(self, ids):
		unlink_ids = []
		pkrat = self.browse(ids)
		for r in pkrat:
			unlink_ids.append(r.account_analytic_id.id)
		super(logistik_pkrat, self).unlink(ids)
		return self.env['account.analytic.account'].unlink(unlink_ids)