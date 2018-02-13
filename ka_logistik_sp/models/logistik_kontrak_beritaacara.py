from odoo import models, fields, api

class logistik_kontrak_beritaacara(models.Model):
	_name = 'logistik.kontrak.beritaacara'
	_description = "Berita Acara SP Kontrak"

	order_id = fields.Many2one('purchase.order', string='Nomor Kontrak', domain="[('golongan', '=', 'kontrak'), ('state', '=', 'approved')]", required=True)
	pkrat_id = fields.Many2one('account.analytic.account', string='No. Investasi')
	partner_id = fields.Many2one(related='order_id.partner_id', string='Rekanan', readonly=True)
	amount_total = fields.Monetary(related='order_id.amount_total', string="Nilai Total", readonly=True)
	nama_kontrak = fields.Char(related='order_id.nama_kontrak', string='Nama Kontrak', readonly=True)
	total_persen_progress = fields.Float(related='order_id.progress_ba', string="Total Progress (%)", readonly=True)
	total_nilai_progress = fields.Float(related='order_id.progress_sp', string="Total Nilai (Rp)", readonly=True)
	nomor = fields.Char(string='Nomor Berita Acara', size=30, required=True)
	tanggal = fields.Date(string='Tanggal', required=True)
	progress = fields.Float(string='Prosentase Kemajuan (%)', digits=(5, 2), required=True)
	keterangan = fields.Text(string='Keterangan')
	nilai = fields.Float(string='Nilai Pembayaran', digits=(15, 2), required=True)
	date_approved = fields.Date(string='Tgl. Disetujui')
	state = fields.Selection([
		('draft','Draft'),
		('approved','Approved'),
	], string='Status', readonly=True, default='draft')
	invoice_id = fields.Many2one('account.invoice', string='Nomor Tagihan')

	# def onchange_nomor(self, cr, uid, ids, order_id, context=None):
	# 	res = {}
	# 	order = self.pool.get('purchase.order').browse(cr, uid, order_id, context)

	# 	res['partner_id'] = order.partner_id.id
	# 	res['nama_kontrak'] = order.nama_kontrak
	# 	res['amount_total'] = order.amount_total
	# 	res['total_persen_progress'] = order.progress_ba
	# 	res['total_nilai_progress'] = order.progress_sp
	# 	# res['pkrat_id'] = pkrat_id.id
	# 	return  {'value': res}
		
	# def action_approve(self, cr, uid, ids, context=None):
	# 	berita_acara = self.browse(cr, uid, ids, context)[0]
	# 	invoice_lines = []
	# 	invoice_lines.append([0, 0, {'product_id': berita_acara.pkrat_id.product_id.id, 
	# 					'unit_id': berita_acara.pkrat_id.product_id.unit_id.id,
	# 					'kuantum': 1,
	# 					'pkrat_id': berita_acara.pkrat_id.id,
	# 					'harga': berita_acara.nilai,
	# 					'total_harga':berita_acara.nilai,}])
	# 	obj_invoice = self.pool.get('account.invoice')
		
	# 	#Create Draft Invoice
	# 	obj_invoice = self.pool.get('account.invoice')
	# 	invoice = {
	# 		'order_id': berita_acara.order_id.id,
	# 		'nomor_ntb':berita_acara.nomor,
	# 		'tanggal_ntb':berita_acara.tanggal,
	# 		'partner_id':berita_acara.partner_id.id,
	# 		'ppn':berita_acara.nilai * 0.1,
	# 		'total_amount':berita_acara.nilai,
	# 		'line_ids':invoice_lines
	# 	}
	# 	inv_id = obj_invoice.create(cr, uid, invoice, context)
	# 	if inv_id:
	# 		self.write(cr, uid, ids, {'state':'approved', 'invoice_id':inv_id, 'date_approved':date.today().strftime('%Y-%m-%d')}, context)