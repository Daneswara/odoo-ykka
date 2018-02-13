from odoo import models, fields, api, _

class ka_account_journal(models.Model):
	_inherit = 'account.journal'

	@api.multi
	def action_bank_masuk(self):
		ctx = self._context.copy()
		ctx.update({'journal_id': self.id, 'default_journal_id': self.id, 'default_journal_type': 'bank', 'type': 'inbound'})
		return {
			'type': 'ir.actions.act_window',
			'view_type': 'form',
			'view_mode': 'form',
			'res_model': 'ka_account.voucher',
			'context': ctx,
			'domain': [('type', '=', 'inbound')],
		}

	@api.multi
	def action_bank_keluar(self):
		ctx = self._context.copy()
		ctx.update({'journal_id': self.id, 'default_journal_id': self.id, 'default_journal_type': 'bank', 'type': 'outbound'})
		return {
			'type': 'ir.actions.act_window',
			'view_type': 'form',
			'view_mode': 'form',
			'res_model': 'ka_account.voucher',
			'context': ctx,
			'domain': [('type', '=', 'outbound')],
		}

	@api.multi
	def action_cash_masuk(self):
		ctx = self._context.copy()
		ctx.update({'journal_id': self.id, 'default_journal_id': self.id, 'default_journal_type': 'cash', 'type': 'inbound'})
		return {
			'type': 'ir.actions.act_window',
			'view_type': 'form',
			'view_mode': 'form',
			'res_model': 'ka_account.voucher',
			'context': ctx,
			'domain': [('type', '=', 'inbound')],
		}

	@api.multi
	def action_cash_keluar(self):
		ctx = self._context.copy()
		ctx.update({'journal_id': self.id, 'default_journal_id': self.id, 'default_journal_type': 'cash', 'type': 'outbound'})
		return {
			'type': 'ir.actions.act_window',
			'view_type': 'form',
			'view_mode': 'form',
			'res_model': 'ka_account.voucher',
			'context': ctx,
			'domain': [('type', '=', 'outbound')],
		}