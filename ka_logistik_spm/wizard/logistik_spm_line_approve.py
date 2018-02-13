# from lxml import etree
# from openerp.osv.orm import setup_modifiers
from odoo import models, fields, api, exceptions

#split and validation SPM
class logistik_spm_line_approve(models.TransientModel):
	_name = 'logistik.spm.line.approve'
	_description = "Persetujuan Permintaan Material Oleh TUK"
	
	line_id = fields.Many2one('logistik.spm.lines', string='Pengajuan')
 	stasiun_id = fields.Many2one('account.analytic.stasiun', string='Stasiun', domain="[('type', '=', 'normal')]", readonly=True)
	pkrat_id = fields.Many2one('logistik.pkrat', string='No. Investasi')
	pkrat_name = fields.Char(string='Nama Proyek', size=64, readonly=True)
	tgl_minta = fields.Date(string='Tgl.Diminta', readonly=True)
	# product_id = fields.Many2one('product.product', string='Kode/Nama Barang')
	product_id = fields.Many2one('product.product', string='Kode/Nama Barang')
	product_desc = fields.Text(string='Spesifikasi Barang', related='product_id.description', readonly=True)
	spesifikasi = fields.Text(string='Spek Yang Diminta')
	account_id = fields.Many2one('account.account', string='No. Perkiraan')
	rab_id = fields.Many2one('logistik.rab', string='Perkiraan di-RAB', help='Nomor RAB/Perkiraan yang terdaftar Rencana Pemakaian')
	kuantum_spm = fields.Float(string='Jml. Diminta', digits=(11, 2), readonly=True)
	perk_id = fields.Many2one('account.account', string='No. Perkiraan')
	kuantum = fields.Float(string='Jml. Setuju', digits=(11, 2), required=True)
	alasan = fields.Char(string='Alasan', size=64)
	less_qty = fields.Boolean(string='Less Qty')
	catatan = fields.Char(string='Catatan', size=64, readonly=True)
	gambar = fields.Binary(string='Contoh Gambar', readonly=True)
	pengadaan = fields.Selection([
		('RD','Direksi'),
		('RP','Pabrik'),
	], string='Pengadaan Oleh', required=True)
	category = fields.Selection([
		('rab','RAB'),
		('nonrab','Non RAB'),
		('noncode','Tanpa Kode'),
	], string='Jenis SPM', required=True)
	
	@api.model
	def default_get(self, fields_list):
		active_model = self._context['active_model']
		res = super(logistik_spm_line_approve, self).default_get(fields_list)
		record_id = self._context and self._context.get('active_id', False) or False
		line = self.env[active_model].browse(record_id)
		res.update(
			tgl_minta = line.tgl_minta,
			stasiun_id = line.stasiun_id.id,
			spesifikasi = line.spesifikasi,
			pkrat_id = line.pkrat_id.id,
			pkrat_name = line.pkrat_name,
			product_id = line.product_id.id,
			rab_id = line.rab_id.id,
			account_id = line.account_id.id,
			kuantum_spm =line.kuantum_spm,
			kuantum = line.kuantum_spm,
			alasan = line.alasan,
			pengadaan = line.pengadaan,
			catatan = line.catatan,
			gambar = line.gambar,
			category = line.category,
		)
		return res
	
	# def fields_view_get(self, cr, uid, view_id, view_type, context=None, toolbar=False, submenu=False):
	# 	active_model =  context['active_model']
	# 	res = super(logistik_spm_line_approve, self).fields_view_get(cr, uid, view_id=view_id, view_type=view_type, context=context, toolbar=toolbar, submenu=submenu)
	# 	record_id = context and context.get('active_id', False) or False
	# 	line = self.pool.get(active_model).browse(cr, uid, record_id, context=context)
	# 	if line.product_id:
	# 		doc = etree.XML(res['arch'])
	# 		nodes = doc.xpath("//field[@name='product_id']")
	# 		for node in nodes:
	# 			node.set('readonly', '1')
	# 			setup_modifiers(node, res['fields']['product_id'])
	# 		res['arch'] = etree.tostring(doc)
	# 	return res

	@api.one
	def _check_rab(self):
		# find RAB if exist
		# cari id di fiscalyear berdasarkan tahun dari tgl minta, 
		# setelah dapat id digunakan untuk search di logistik_rab dengan parameter (id fiscalyear & product_id)
		if not self.account_id or not self.product_id:
			return
		
		params = {}
		str_year = self.tgl_minta[:4]
		year_id = self.env['ka.account.fiscalyear'].search([('name', '=', str_year)])
		if not year_id:
			raise exceptions.Warning('Tahun pembukuan untuk pengadaan tanggal diminta tersebut belum dibuat')
			return

		params['prod_id'] = self.product_id.id
		params['account_id'] = self.account_id.id
		params['tahun'] = str_year
		rab_id = self.env['logistik.rab'].get_rab_available(params)
		if rab_id:
			self.rab_id = rab_id
			self.category = 'rab'

	@api.onchange('product_id', 'account_id')
	def onchange_account_id(self):
		self.rab_id = None
		if not self.product_id:
			self.category = 'noncode'
		else:
			self.category = 'nonrab'
			self._check_rab()

	def _get_kuantum_exceptions(self):
		raise exceptions.Warning('"Jml. Setuju" tidak boleh lebih besar dari "Jml. Diminta"!')

	@api.onchange('kuantum')
	def onchange_kuantum(self):
		if self.kuantum > self.kuantum_spm:
			self._get_kuantum_exceptions()
			return
		self.less_qty = (self.kuantum < self.kuantum_spm)
		
	@api.one
	def do_simpan(self):
		if self.kuantum > self.kuantum_spm:
			self._get_kuantum_exceptions()
			return
		vals = {}
		active_model = self._context['active_model']
		active_ids = self._context and self._context.get('active_ids', False) or False
		vals = {
			'rab_id': self.rab_id.id,
			'product_id': self.product_id.id,
			'account_id': self.account_id.id,
			'category': self.category,
			'pengadaan': self.pengadaan,
			'spesifikasi': self.spesifikasi,
			'kuantum': self.kuantum,
			'alasan': self.alasan,
			'pkrat_id': self.pkrat_id.id,
			'btn_test': 'validated',
		}
		res = self.env[active_model].browse(active_ids)
		res.write(vals)
		return {'type': 'ir.actions.act_window_close'}