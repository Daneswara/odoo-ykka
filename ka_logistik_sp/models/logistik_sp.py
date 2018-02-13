from odoo import models, fields, api

class logistik_sp(models.Model):
	_inherit = 'purchase.order'

	spm_id = fields.Many2one('logistik.spm', string='Nomor SPM')
	is_extended = fields.Boolean(string='Diperpanjang')
	alasan = fields.Char(string='Alasan', size=150, readonly=True, track_visibility='onchange')
# 	nama_kontrak = fields.Char(string='Nama Kontrak', size=128)
# 	tgl_mulai = fields.Date(string='Tanggal Mulai') #untuk kontrak
# 	tgl_selesai = fields.Date(string='Tanggal Selesai') #untuk kontrak
# 	beritaacara_ids = fields.One2many('logistik.kontrak.beritaacara', 'order_id', string='Berita Acara')
# 	golongan = fields.Selection([
# 		('agen', 'Agen'),
# 		('import', 'Import'),
# 		('tender', 'Tender'),
# 		('repeat', 'Repeate'),
# 		('kontrak', 'Kontrak')
# 	], string='Golongan', readonly=True, default='agen')
	pengadaan = fields.Selection(related='spm_id.pengadaan', store=True, selection=[
		('RD', 'Direksi'),
		('RP', 'Lokal')
	], string='Jenis SP')
	ttd_dir = fields.Many2one('hr.employee', string='Tanda Tangan-1')
	ttd_keu = fields.Many2one('hr.employee', string='Tanda Tangan-2')
	ttd_div = fields.Many2one('hr.employee', string='Kadiv. Terkait')
	ttd_log = fields.Many2one('hr.employee', string='Kabag. Logistik')
	ref_investasi = fields.Char(compute='_compute_investasi', string='No. Proyek', store=True)
# 	progress_ba =  fields.Float(compute='_compute_progress', string="Progress (%)")
# 	progress_sp =  fields.Float(compute='_compute_progress', string="Progress SP (Rp)")
# 	date_planned = fields.Date(string='Tgl. Serah')

	_defaults = {
		'notes': 'Harga belum termasuk PPN dan belum dipotong PPH'
	}

	@api.multi
	def _compute_investasi(self):
		for s in self:
			ref_investasi = ''
			for line in s.order_line:
				ref_investasi += (line.account_analytic_id.code or '') + ', '
				ref_investasi = ref_investasi.strip(', ')
			s.ref_investasi = ref_investasi

	@api.multi
	def _compute_progress(self):
		for s in self:
			s.progress_ba = sum(ba.progress for ba in s.beritaacara_ids)
			s.progress_sp = sum(ba.nilai for ba in s.beritaacara_ids)

	# #override origin methode to choose account from main company
	# def _prepare_invoice(self, cr, uid, order, line_ids, context=None):
	# 	"""Prepare the dict of values to create the new invoice for a
	# 	   purchase order. This method may be overridden to implement custom
	# 	   invoice generation (making sure to call super() to establish
	# 	   a clean extension chain).

	# 	   :param browse_record order: purchase.order record to invoice
	# 	   :param list(int) line_ids: list of invoice line IDs that must be
	# 								  attached to the invoice
	# 	   :return: dict of value to create() the invoice
	# 	"""
	# 	company_id = order.company_id.id
	# 	if not order.spm_id.id:
	# 		company_id = context['force_company']

	# 	if order.pengadaan == 'RD':
	# 		company_id = context['force_company']
					
	# 	journal_ids = self.pool['account.journal'].search(
	# 		cr, uid, [('type', '=', 'purchase'),
	# 		('company_id', '=', company_id)
	# 	], limit=1)
		
	# 	if not journal_ids:
	# 		raise osv.except_osv(
	# 			_('Error!'),
	# 			_('Define purchase journal for this company: "%s" (id:%d).') % \
	# 			(order.company_id.name, order.company_id.id))
		
	# 	return {
	# 		'name': order.partner_ref or order.name,
	# 		'reference': order.partner_ref or order.name,
	# 		'account_id': order.partner_id.property_account_payable.id,
	# 		'type': 'in_invoice',
	# 		'partner_id': order.partner_id.id,
	# 		'currency_id': order.currency_id.id,
	# 		'journal_id': len(journal_ids) and journal_ids[0] or False,
	# 		'invoice_line': [(6, 0, line_ids)],
	# 		'origin': order.name,
	# 		'fiscal_position': order.fiscal_position.id or False,
	# 		'payment_term': order.payment_term_id.id or False,
	# 		'company_id': company_id,
	# 	}

	# def action_invoice_create(self, cr, uid, ids, context=None):
	# 	"""Generates invoice for given ids of purchase orders and links that invoice ID to purchase order.
	# 	:param ids: list of ids of purchase orders.
	# 	:return: ID of created invoice.
	# 	:rtype: int
	# 	"""
	# 	context = dict(context or {})

	# 	inv_obj = self.pool.get('account.invoice')
	# 	inv_line_obj = self.pool.get('account.invoice.line')

	# 	res = False
	# 	uid_company_id = self.pool.get('res.users').browse(cr, uid, uid, context=context).company_id.id
	# 	for order in self.browse(cr, uid, ids, context=context):
	# 		context.pop('force_company', None)
	# 		if order.company_id.id != uid_company_id:
	# 			#if the company of the document is different than the current user company, force the company in the context
	# 			#then re-do a browse to read the property fields for the good company.
	# 			context['force_company'] = order.company_id.id
				
	# 			#if order from direksi/main company
	# 			if order.pengadaan == 'RD':
	# 				context['force_company'] = uid_company_id
	# 			if not order.spm_id.id:
	# 				context['force_company'] = uid_company_id
	# 			order = self.browse(cr, uid, order.id, context=context)

	# 		# generate invoice line correspond to PO line and link that to created invoice (inv_id) and PO line
	# 		inv_lines = []
	# 		for po_line in order.order_line:
	# 			acc_id = self._choose_account_from_po_line(cr, uid, po_line, context=context)
	# 			inv_line_data = self._prepare_inv_line(cr, uid, acc_id, po_line, context=context)
	# 			inv_line_id = inv_line_obj.create(cr, uid, inv_line_data, context=context)
	# 			inv_lines.append(inv_line_id)
	# 			po_line.write({'invoice_lines': [(4, inv_line_id)]})

	# 		# get invoice data and create invoice
	# 		inv_data = self._prepare_invoice(cr, uid, order, inv_lines, context=context)
	# 		inv_id = inv_obj.create(cr, uid, inv_data, context=context)

	# 		# compute the invoice
	# 		inv_obj.button_compute(cr, uid, [inv_id], context=context, set_total=True)

	# 		# Link this new invoice to related purchase order
	# 		order.write({'invoice_ids': [(4, inv_id)]})
	# 		res = inv_id
	# 	return res
		
	# #Create picking yang disesuaikan dengan tempat pengiriman barang
	# #Setting company_id = peminta barang
	# #Over Write original methode
	# def action_picking_create(self, cr, uid, ids, context=None):
	# 	for order in self.browse(cr, uid, ids):
	# 		picking_vals = {
	# 			'picking_type_id': order.picking_type_id.id,
	# 			'partner_id': order.partner_id.id,
	# 			'date': max([l.date_planned for l in order.order_line]),
	# 			'origin': order.name,
	# 			'company_id': order.picking_type_id.warehouse_id.company_id.id
	# 		}
	# 		picking_id = self.pool.get('stock.picking').create(cr, uid, picking_vals, context=context)
	# 		self._create_stock_moves(cr, uid, order, order.order_line, picking_id, context=context)
	
	# #Perpanjangan Tanggal Pengiriman
	# def action_extend_date(self, cr, uid, ids, data, context=None):
	# 	sp = self.read(cr, uid, ids, ['date_delivery'], context)
	# 	res = self.write(cr, uid, ids, {'date_delivery': data.tanggal, 'alasan': data.alasan, 'is_extended':True})
	# 	return res

	# override purchase_order button_draft()
	@api.one
	def action_cancel_draft(self):
		# back name to original name
		splitname = self.name.split('-B')
		return self.write({'state': 'draft', 'name': splitname[0]})

	# override purchase_order button_cancel()
	@api.one
	def action_cancel(self, back_tender, back_agen, alasan=''):
		# cari sequence untuk no batal
		listpo = self.search([('name', 'like', self.name + '-B%')], order="name desc")
		suffix = '-B'
		if len(listpo) <= 0:
			suffix += '01'
		else:
			splitname = listpo[0].name.split('-B')
			if len(splitname) <= 1 or splitname[1] == '':
				suffix += '01'
			else:
				last = int(splitname[1]) + 1
				if last < 10:
					suffix += '0' + str(last)
				else:
					suffix += str(last)
		# end of cari sequence untuk no batal

		if back_tender:
			tender_id = self.spp_id.tender_id.id
			tender = self.env['logistik.tender'].browse(tender_id)
			tender.write({'state': 'spp'})
			spp = self.env['logistik.spp'].search([('tender_id', '=', tender_id)], limit=1)
			spp.write({'state': 'draft'})

		if back_agen:
			spp_id = self.spp_id.id
			spp = self.env['logistik.spp'].browse(spp_id)
			spp.write({'state': 'draft'})

		notes = self.notes + '\n' if self.notes else ''
		notes += "ALASAN BATAL: " + alasan
		self.write({'name': (self.name + suffix), 'notes': notes})
		return super(logistik_sp, self).button_cancel()
