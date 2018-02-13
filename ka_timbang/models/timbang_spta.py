from odoo import api, fields, models, _
import time
from datetime import timedelta, datetime

class ka_timbang_spta(models.Model):
    _name = "ka_timbang.spta"        
    _description = "Surat Perintah Tebang Angkut"
    _order = 'date_out desc'

    @api.multi
    def _get_date_in(self):
        for this in self:
            this.date_in_web = fields.datetime.strptime(this.date_in, '%Y-%m-%d %H:%M:%S') + timedelta(hours=-7)

    @api.multi
    def _get_date_out(self):
        for this in self:
            this.date_out_web = fields.datetime.strptime(this.date_out, '%Y-%m-%d %H:%M:%S') + timedelta(hours=-7)

    # no_penerimaan = fields.Many2one('penerimaan.spta', 'No. Penerimaan', ondelete='restrict', required=False)
    name = fields.Char("Nomor", default="/", copy=False)
    day = fields.Char("Hari(YDM)")
    register = fields.Char("Register")
    truck_id = fields.Char("No Polisi", required=True)
    lori_id = fields.Char("No Lori")
    spta_id = fields.Char("No. SPTA", default="/")

    date_in = fields.Date(string="Tgl. Masuk", default=lambda * a: time.strftime('%Y-%m-%d %H:%M:%S'))
    date_in_web = fields.Datetime(string="Tgl. Masuk", compute='_get_date_in', store=True)	
    date_out = fields.Date(string="Tgl. Keluar", default=fields.Datetime.now)
    date_out_web = fields.Datetime(string="Tgl. Keluar", compute='_get_date_out', store=True)
    
    weight_in = fields.Float("Masuk (Kg)", required=True)
    weight_out = fields.Float("Keluar (Kg)")
    weight_net = fields.Float("Netto (Kg)")
    weight_kw = fields.Float("Netto (Kw)")
    
    user_in = fields.Many2one('res.users', string='Operator In', default=lambda self: self._uid)
    user_out = fields.Many2one('res.users', string='Operator Out')
    pos_in = fields.Char("Pos In")
    pos_out =  fields.Char("Pos Out")
    
    re_print =  fields.Integer('Re-Print', default=0)
    log_note =  fields.Text('Log Note')
    is_correction =  fields.Boolean('Koreksi')
    tebang_by =  fields.Selection([("kud", "KUD"),
                      ("pabrik", "PABRIK"),
                      ("sendiri", "SENDIRI")],
                        string = "Tebang Oleh", default="sendiri")
    state = fields.Selection([("in", "Masuk"),
                      ("out", "Keluar"),
                      ("invoice", "Tagihan"),
                      ("paid", "Terbayar")],
                        string = "Status", default="in", track_visibility="always", copy=False)
    mbs = fields.Selection([('1','MSB(*)'), ('2','MSB(+)'), ('3','MSB'), ('4','Tali P'),
				    ('5','Daduk'), ('6','Akar'), ('7','Sogolan'), ('8','Pucuk'),
				    ('9','Akar Tanah'), ('10','Kocor Air'), ('11','Pucuk dan Sogolan'), ('12','Terbakar'),
				    ('13','Tebu Muda'), ('14','ATPSD'), ('15','Campur Tanah'), ('16','Lelesan'), ('99','?????'),],
                        string = "MBS", default="99")
    
    @api.onchange('weight_in','weight_out')
    def onchange_weight_in_out(self):
        self.weight_net = abs(self.weight_in - self.weight_out)
        self.weight_kw = self.weight_net/100

    @api.multi
    def get_sequence(self):
        for this in self:
            company_internal_user = self.env.user.company_id.internal_user_id.id
            dt_now = time.strftime('%Y-%m-%d').split('-')
            tm_now = time.strftime('%H:%M:%S')
            prefix = dt_now[0] + dt_now[2] + dt_now[1]
            now_date = datetime(int(dt_now[0]), int(dt_now[1]), int(dt_now[2]))

            seq_ids = self.env['ir.sequence'].search([('code', '=', 'ka_timbang.spta')])
            for s in seq_ids:
                curr_prefix = s.prefix
                if prefix != curr_prefix:
                    curr_prefix = prefix

                last_date = datetime(int(curr_prefix[:4]), int(curr_prefix[6:]), int(curr_prefix[4:6]))
                diff_days = (now_date - last_date).days
                
                if diff_days > 1:
                    s.sudo(company_internal_user).write({'prefix' : prefix, 'number_next' : 1})
                else:
                    if ((diff_days == 1) and (tm_now > '05:59:59')) or not s.prefix:
                        s.sudo(company_internal_user).write({'prefix' : prefix, 'number_next' : 1})
            
        number = self.env['ir.sequence'].next_by_code('ka_timbang.spta')
        return number

    @api.multi
    def write(self, vals):
        for this in self:
            
            from_rpc = vals.has_key('weight_out')
            if this.state == 'in' and from_rpc:
                if this.name == '/':
                    vals.update({'name': self.get_sequence()})
                vals.update({
                    'date_out': time.strftime('%Y-%m-%d %H:%M:%S'),
                    'user_out': self._uid,
                    'state': 'out',
                    're_print': 0,
                    'weight_net': abs(vals.get('weight_out') - this.weight_in),
                    'weight_kw': round(vals.get('weight_net') / float(100)),
                    'spta_id': vals.get('name')[4:],
                    'day': vals.get('name')[4:] + vals.get('name')[6:8] + vals.get('name')[4:0]
                    })
        return super(ka_timbang_spta, self).write(vals)
