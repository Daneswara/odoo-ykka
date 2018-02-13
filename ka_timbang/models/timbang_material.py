from odoo import api, fields, models, _
import time

class ka_timbang_material(models.Model):
    _name = "ka_timbang.material"        
    _description = "Timbang Material Non-Tebu"

    name = fields.Char("Nomor", default="/", copy=False)
    truck_id = fields.Char("No Polisi", required=True)
    product_id = fields.Many2one("product.product", string="Product", required=True)
    partner_id = fields.Many2one('res.partner', string="Rekanan", required=True)
    reference = fields.Char("Referensi")
    no_do = fields.Many2one('sale.order', string="Nomor DO")
    tetes_brix_qty = fields.Float("Tetes/Brix")

    date_in = fields.Datetime(string="Tgl. Masuk", default=lambda * a: time.strftime('%Y-%m-%d %H:%M:%S'))
    date_out = fields.Datetime(string="Tgl. Keluar", default=fields.Datetime.now)
    
    weight_in = fields.Float("Masuk (Kg)", required=True)
    weight_out = fields.Float("Keluar (Kg)")
    weight_net = fields.Float("Netto (Kg)")
    
    user_in = fields.Many2one('res.users', string='Operator In', default=lambda self: self._uid)
    user_out = fields.Many2one('res.users', string='Operator Out')
    pos_in = fields.Char("Pos In")
    pos_out =  fields.Char("Pos Out")
    
    angkutan = fields.Char("Angkutan")
    re_print =  fields.Integer('Re-Print', default=0)
    log_note =  fields.Text('Log Note')
    is_correction =  fields.Boolean('Koreksi')

    state = fields.Selection([("in", "Masuk"),("out", "Keluar")],
                        string = "Status",default="in", track_visibility="always", copy=False)
    
    @api.onchange('weight_in','weight_out')
    def onchange_weight_in_out(self):
        self.weight_net = abs(self.weight_in - self.weight_out)
    
    @api.multi
    def get_sequence(self): 
        company_internal_user = self.env.user.company_id.internal_user_id.id
        dt_now = time.strftime('%Y-%m-%d').split('-')
        prefix = dt_now[0] + "/" + dt_now[2] + dt_now[1] + "3"
        sequence_src = self.env['ir.sequence'].search([('code', '=', 'ka_timbang.material')]) 
        for sequence in sequence_src:
            curr_prefix = sequence.prefix
            if prefix != curr_prefix:
                sequence.sudo(company_internal_user).write({'prefix' : prefix, 'number_next' : 1})
        number = self.env['ir.sequence'].next_by_code('ka_timbang.material') 
        return number 

    @api.multi
    def write(self, vals):
        for this in self:
            from_rpc = vals.has_key('weight_out')
            if this.state == 'in' and from_rpc:
                vals.update({'date_out': time.strftime('%Y-%m-%d %H:%M:%S'),
                             'user_out': self._uid,
                             'state': 'out',
                             'weight_net': abs(vals.get('weight_out') - this.weight_in)})
                if this.name == '/':
                    vals.update({'name': self.get_sequence()})
        return super(ka_timbang_material, self).write(vals)