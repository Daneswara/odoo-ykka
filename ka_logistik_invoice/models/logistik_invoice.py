from odoo import models, fields, api, exceptions

class logistik_invoice(models.Model):
	_name = 'logistik.invoice'

	name = fields.Char(string="Nomor Pengajuan", size=32, readonly=True, default="/")
	date_submit = fields.Date(string="Tanggal Pengajuan", readonly=True)
	order_id = fields.Many2one('purchase.order', string="Nomor SP", required=True, size=32)
	partner_id = fields.Many2one(related='order_id.partner_id', store=True, readonly=True)
	date_planned = fields.Datetime(related='order_id.date_planned', store=True, readonly=True)
	company_id = fields.Many2one(related='order_id.company_id', store=True, string="Unit/PG", readonly=True)
	order_amount = fields.Monetary(related='order_id.amount_total', string="Total Nilai SP", readonly=True)
	date_order = fields.Datetime(related='order_id.date_order', string="Tanggal SP", readonly=True)
	invoice_number = fields.Char(string="Nomor Tagihan", required=True, size=32)
	date_invoice = fields.Date(string="Tanggal Tagihan", required=True)
	tax_number = fields.Char(string="Nomor Faktur Pajak", required=True, size=32)
	tax_date = fields.Date(string="Tanggal Faktur", required=True)
	amount_untaxed = fields.Float(string="Nilai", digits=(12, 2), required=True)
	amount_tax = fields.Float(string="PPN", digits=(12, 2), required=True)
	amount_pph = fields.Float(string="PPh", digits=(12, 2), required=True, default=0)
	amount_total = fields.Float(string="Total", digits=(12, 2), compute='_amount_total', store=True, readonly=True)
	state = fields.Selection([
		('draft', "Draft"),
		('approved', "Pengajuan"),
		('paid', "Terbayar")
	], default='draft', string="Status")
	ntb_number = fields.Char(string="Nomer NTB", size=24, required=True)
	ntb_date = fields.Date(string="Tanggal NTB", required=True)
	term_percent = fields.Float(string="Pembayaran", digits=(5, 2), required=True, default=100)
	total_invoiced = fields.Float(related='order_id.total_invoiced', string='Total Tertagih', readonly=True)
	invoice_balance =fields.Float(related='order_id.invoice_balance', string='Sisa Tagihan', readonly=True)	
	account_invoice_id = fields.Many2one('account.invoice', string='Invoice', readonly=True)
	# invoice_tax_ids = fields.Many2many('account.tax', 'logistik_invoice_taxs', 'logistik_invoice_id', 'tax_id', string='Pajak', domain=[('parent_id', '=', False), ('type_tax_use', '=', 'purchase')], default=lambda self: self._get_default_tax())
	invoice_tax_ids = fields.Many2many('account.tax', 'logistik_invoice_taxs', 'logistik_invoice_id', 'tax_id', string='Pajak', default=lambda self: self._get_default_tax())

	@api.model
	def _get_default_tax(self):
		tax = self.env['account.tax'].search([('type_tax_use', '=', 'purchase')])
		return tax

	@api.depends('amount_untaxed', 'amount_tax', 'amount_pph')
	def _amount_total(self):
		self.amount_total = self.amount_untaxed + self.amount_tax - self.amount_pph
	
	@api.onchange('order_id')
	def onchange_order_id(self):
		for r in self:
			r.amount_untaxed = self.invoice_balance
			r.amount_tax = self.amount_untaxed * 0.1
			r.amount_pph = 0
			r.amount_total = self.amount_untaxed  + self.amount_tax 


	@api.onchange('amount_untaxed')
	def onchange_amount_untaxed(self):
		self.amount_tax = self.amount_untaxed * 0.1
		self.amount_total = self.amount_untaxed  + self.amount_tax  - self.amount_pph

	@api.onchange('amount_tax')
	def onchange_amount_tax(self):
		self.amount_total = self.amount_untaxed  + self.amount_tax  - self.amount_pph

	@api.onchange('amount_pph')
	def onchange_amount_pph(self):
		self.amount_total = self.amount_untaxed  + self.amount_tax  - self.amount_pph

	@api.onchange('date_invoice')
	def action_onchange_date_invoice(self):
		self.tax_date = self.date_invoice

	@api.multi
	def action_approved(self):
		self.state = 'approved'
		self.date_submit = fields.Date.today()
		if self.name == '/':
			self.name = self.env['ir.sequence'].get('logistik.invoice.nomor.pengajuan')	
		self._create_account_invoice()

	@api.multi
	def action_draft(self):
		invoice = self.env['account.invoice']
		if self.account_invoice_id:
			if self.account_invoice_id.state != 'draft':
				raise exceptions.Warning('Tagihan tidak dapat dibatalkan karena sudah diproses bagian akunting.')
				return
		self.state = 'draft'
		self.date_submit = None
		self.name = None
		self.account_invoice_id.unlink()

	@api.multi
	def _prepare_invoice_line(self):
		line_name = ''
		for line in self.order_id.order_line:
			line_name = line_name + line.product_id.default_code + '[' + str(line.product_qty) + line.product_id.uom_id.name + ']'
			
		vals = {
			'name':self.order_id.name + ' : ' + line_name,
			'quantity': 1,
			'price_unit': self.amount_untaxed,
			'price_total': self.amount_untaxed,
		}
		return vals
		
	@api.multi
	def _create_account_invoice(self):
		print '=============================='
		print self._prepare_invoice_line()
		# company_id = self.env.context.get('company_id') or self.env.user.company_id.id
		# invoice = self.env['account.invoice']		
		# code = self.ntb_number[len(self.ntb_number)-1:]
		# journal = self.env['account.journal'].search([('code', '=', code), ('company_id', '=', company_id)])
		# if not journal:
			# raise exceptions.Warning('Jurnal dengan kode %s tidak dapat ditemukan' % code)
		# vals = {
			# 'partner_id': self.partner_id.id,
			# 'origin': self.order_id.name,
			# 'date_iinvoice': self.date_submit,
			# 'account_id': journal.default_debit_account_id.id,
			# 'journal_id': journal.id,
			# 'type': 'in_invoice',
			# }
		# invoice_id = invoice.create(vals)
		# self.account_invoice_id = invoice_id
		
		
		
		## Kari Disek ......... self.order_id.write({'invoice_ids': [(4, invoice_id)]})