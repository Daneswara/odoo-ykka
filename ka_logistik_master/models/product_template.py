from odoo import models, fields, api
from odoo.exceptions import UserError

class product_product(models.Model):
	_inherit = 'product.product'
	
	default_code = fields.Char('Internal Reference', index=True, required=True)
	

class product_template(models.Model):
	_inherit = 'product.template'

	default_code = fields.Char(
        'Internal Reference', compute='_compute_default_code',
        inverse='_set_default_code', store=True, required=True)
	#Disable Translation
	name = fields.Char('Name', index=True, required=True, translate=False)
	description = fields.Text(
		'Description', translate=False,
		help="A precise description of the Product, used only for internal information purposes.")
	description_purchase = fields.Text(
		'Purchase Description', translate=False,
		help="A description of the Product that you want to communicate to your vendors. "
			"This description will be copied to every Purchase Order, Receipt and Vendor Bill/Refund.")
	description_sale = fields.Text(
		'Sale Description', translate=False,
		help="A description of the Product that you want to communicate to your customers. "
			"This description will be copied to every Sale Order, Delivery Order and Customer Invoice/Refund")
	
	jenis = fields.Selection([
		('R','Rutin'),
		('V','Vital'),
		('M','Modal'),
		('G','Giling')
	], string='Jenis')
	pengadaan = fields.Selection([
		('RD','Direksi'),
		('RP','Pabrik')
	], string='Pengadaan Oleh')
	pabrikan = fields.Char(string='Pabrikan', size=15, help="Nama pabrik pembuat barang")
	ref_pabrik = fields.Char(string='No. Ref Pabrik', size=25, help="Nomor referensi pabrik")
	more_spec = fields.Text(string='Detail Spesifikasi')
	last_value = fields.Float(digits=(12, 2), string='Cek Nilai')
	old_code = fields.Char(string='Kode Lama', size=32)

	_sql_constraints = [('default_code_unique', 'unique(default_code)', 'Kode Barang tidak boleh dobel!')]

	@api.onchange('categ_id')
	def onchange_category_id(self):
		if self.categ_id and self.categ_id.code:
			self.default_code = self.categ_id.code[:5]

	@api.model
	def default_get(self, fields):
		ext = super(product_template, self).default_get(fields)
		ext['company_id'] = False
		return ext
	
	@api.model
	def create(self, vals):
		res = super(product_template,self).create(vals)
		if not res.default_code:
			raise UserError('Kode barang tidak boleh kosong!')
		return res
	
	# @override
	# @api.one
	# def write(self, vals):
		# res = super(product_template, self).write(vals)
		# if vals.has_key('name'):
			# tmpl_id = self.product_tmpl_id.id
			# self._cr.execute('update product_template set name=%s where id=%s', (vals['name'], tmpl_id))
		# return res