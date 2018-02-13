from odoo import models, fields, api

class logistik_spm_approve(models.TransientModel):
	_name = 'logistik.spm.approve'
	_description = 'Validasi SPM'
	
	spm_id = fields.Many2one('logistik.spm', string='Nomor SPM', required=True, readonly=True)
	stasiun_id = fields.Many2one('account.analytic.stasiun', string='Stasiun', required=True, readonly=True)
	split_no = fields.Integer(string='No. Split', readonly=True)
	tanggal = fields.Date(string='Tanggal SPM', required=True, readonly=True)
	line_ids = fields.One2many('logistik.spm.approve.lines', 'wizard_id', string='Detail SPM')
	
	@api.model
	def default_get(self, fields_list):
		res = super(logistik_spm_approve, self).default_get(fields_list)
		spm_ids = self._context.get('active_ids', [])
		active_model = self._context.get('active_model')

		spm_id, = spm_ids
		res.update(spm_id = spm_id)
		spm = self.env['logistik.spm'].browse(spm_id)
		spm_lines = [self._partial_spm(m) for m in spm.line_ids if m.state == 'confirm']
		res.update(line_ids = spm_lines, tanggal = spm.tanggal, split_no = spm.split_no, stasiun_id = spm.stasiun_id.id)
		return res

	def _partial_spm(self, spm_line):
		lines = {
			'spm_line_id': spm_line.id,
			'product_id' : spm_line.product_id.id,
			'spesifikasi': spm_line.spesifikasi,
			'unit_id': spm_line.unit_id.id,
			'kuantum' : spm_line.kuantum,
			'qty_partial' : spm_line.kuantum,
			'pkrat_id' : spm_line.pkrat_id.id,
			'tgl_minta' : spm_line.tgl_minta,
		}
		return lines

	# def do_partial(self, cr, uid, ids, context=None):
	# 	obj_spm = self.pool.get('logistik.spm')
	# 	partial = self.browse(cr, uid, ids[0], context=context)
	# 	check = [line for line in partial.line_ids if (line.kuantum - line.qty_partial) < 0 ]
	# 	if len(check) > 0:
	# 		raise osv.except_osv('PERHATIAN!', 'Kuantum Realisasi tidak boleh lebih besar dari Kuantum yang Di-Setujui')
	# 	res = obj_spm.action_approve(cr, uid, partial, context)
	# 	return res