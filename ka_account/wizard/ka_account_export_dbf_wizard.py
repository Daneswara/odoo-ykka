from odoo import models, fields, api, _

class ka_account_export_buktiaua1_wizard(models.TransientModel):
    _name = "ka_account.export.buktiaua1.wizard"
    _description = "Export to BUKTIAU1"
    
    text = fields.Char('Text', default='Ini akan membuat transaksi pada file BUKTIAU1 pada SERVER-FOXPRO. Klik OK untuk melanjutkan')

    def action_export_dbf(self):
        active_ids = self._context.get('active_ids', [])
        self.env['ka_account.voucher'].browse(active_ids).export_to_dbf()
