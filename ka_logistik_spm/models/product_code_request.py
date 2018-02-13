from odoo.exceptions import UserError
from odoo import models, fields, api, exceptions

class SpmProductCodeRequest(models.Model):
	_name='spm.product.code.request'
	_inherit = ['mail.thread', 'ir.needaction_mixin']
	_description='Permintaan Kode Barang Baru'
	
	def _get_partner_ids(self):
		res = [(4, partner.id, None) for partner in self.env.user.company_id.notif_kode_barang_baru_partners_ids]
		return res
	
	name = fields.Text('Spek. yang diminta')
	date_request = fields.Date(string='Tanggal Permintaan', required=True, readonly=True, default=fields.Date.today)
	request_by = fields.Many2one('res.users', string='Diminta Oleh', readonly=True, default=lambda self: self._uid)
	partner_ids = fields.Many2many('res.partner', string='Ditujukan Kepada', default=_get_partner_ids)
	spm_line_id = fields.Many2one('logistik.spm.lines', string='Sumber SPM')
	pengajuan_id = fields.Many2one('logistik.pengajuan.spm', related='spm_line_id.pengajuan_id', string='Sumber SPM')
	product_id = fields.Many2one('product.template', 'Kode/Nama Barang')
	uom_id =  fields.Many2one('product.uom', string='Satuan')
	product_desc = fields.Text(string='Spesifikasi', related='product_id.description', readonly=True)
	date_done = fields.Date(string='Tanggal Realisasi', readonly=True)
	done_by = fields.Many2one('res.users', string='Realisasi Oleh', readonly=True)
	note = fields.Text('Keterangan')
	state = fields.Selection([
		('draft', 'Konsep'),
		('send', 'Permintaan Baru'),
		('confirm', 'Konfirmasi'),
		('done', 'Selesai'),
		('cancel', 'Batal')], string='Status', readonly=True, default='draft', track_visibility='onchange')
	operating_unit_id = fields.Many2one('res.partner', required=True, string="Unit/PG", 
        domain=[('is_operating_unit', '=', True)], 
        default=lambda self: self.env['res.users'].operating_unit_default_get(self._uid))
	company_id = fields.Many2one('res.company', string='Perusahaan', required=True, states={'draft': [('readonly', False)]}, default=lambda self: self.env['res.company']._company_default_get('logistik.pengajuan.spm'))
	booked = fields.Boolean('Dibukukan', default=False)
	suspended = fields.Boolean('Tunda', help='Tunda karena spesifikasi barang kurang jelas', default=False)
	
	@api.multi
	def action_draft(self):
		self.write({'state':'draft'})
		
	@api.one
	def action_booked(self):
		self.write({'booked': True})
		
	@api.one
	def action_suspended(self):
		self.write({'suspended': True})

	@api.one
	def action_resume(self):
		self.write({'suspended': False})

	@api.one
	def action_unbooked(self):
		self.write({'booked': False})

# 	@api.multi
# 	def action_send(self):
# 		partner_ids = (p.id for p in self.partner_ids)
# 		followers = [(0,0,{'res_model':self._name, 'partner_id':pid.id}) for pid in self.partner_ids]
# 		self.write({
# 			'state':'send',
# 			'message_follower_ids': followers,
# 			})
# 		body = 'Permintaan Kode Barang baru \n %s' % self.name
# 		post_vars = {'subject': "Permintaan Kode Barang", 'body': body, 'partner_ids': [(partner_ids)],}
# 		self.message_post(type="notification", subtype="mt_comment", **post_vars)
	
	@api.multi
	def action_send(self):
		for this in self:
			this.state = 'send'
			# followers  
			partners_to_send = [partner.id for partner in this.partner_ids]
			followers = [(0,0,{'res_model': self._name, 
							   'subtype_ids': [(4, self.env.ref('ka_logistik_spm.mt_send_product_code_request').id)], 
							   'partner_id': pid}) 
							   for pid in partners_to_send]
			this.write({'message_follower_ids': followers})
			# send message
			email = self.env.ref('ka_logistik_spm.template_product_code_request')
			post_vars = {'message_type': 'notification',
	                     'subtype_id': self.env.ref('ka_logistik_spm.mt_send_product_code_request').id,
	                     'needaction_partner_ids': partners_to_send}
			this.message_post_with_template(email.id, **post_vars)

	@api.multi
	def action_confirm(self):
		self.write({'state':'confirm', 'suspended':False})

	@api.one
	def action_done(self):
		vals = {
			'date_done': fields.Date.today(),
			'done_by': self._uid,
			'state': 'done'	
		}
		product_src = self.env['product.product'].search([('product_tmpl_id','=',self.product_id.id)], limit=1)
		if product_src:
			if self.spm_line_id:
				self.spm_line_id.product_id = product_src.id
			self.write(vals)

	@api.multi
	def action_cancel(self):
		if self.create_uid.id <> self._uid:
			raise exceptions.Warning('Pembatalan SPM hanya dapat dilakukan oleh user bersangkutan')
			return
			
		self.write({'state': 'cancel'})
	
	@api.multi
	def unlink(self):
		if self.state not in('draft', 'send'):
			raise exceptions.Warning('Selain konsep, permintaan tidak dapat dihapus!')
			return

		if self.create_uid.id <> self._uid:
			raise exceptions.Warning('Data ini hanya dapat dilakukan oleh user bersangkutan')
			return

		return super(SpmProductCodeRequest, self).unlink()
		