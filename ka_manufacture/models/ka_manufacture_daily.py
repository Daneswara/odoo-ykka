from odoo import models, fields, api, _

class ManufactureDaily(models.Model):
    _name = "ka_manufacture.daily"
    _description = "Manufacture Daily for PT Kebon Agung"
    _inherit = ['mail.thread']
    
    
    name = fields.Char(string="Name", default="New")
    session_id = fields.Many2one("ka_manufacture.session", string="Session")
    date = fields.Date("Tanggal Giling")
    in_day = fields.Integer("Hari Giling Ke")
    bruto_capacity = fields.Float("Kapasitas Bruto TCD")
    sugarcane_milled_tr = fields.Float("Tebu tergiling TR - Ton")
    sugarcane_milled_ts = fields.Float("Tebu tergiling TS - Ton")
    sugarcane_milled_total = fields.Float(string="Total tergiling - Ton", compute="get_total_sugarcane")
    rendement_tr = fields.Float("Rendemen TR - %")
    rendement_ts = fields.Float("Rendemen TS - %")
    rendement_avg = fields.Float("Rendemen Rata2 - %", compute="get_average_rendement")
    qty_packer = fields.Float("Produksi Gula (Mesin Packer) - Ton")
    company_id = fields.Many2one("res.company", string="Company", default=lambda self: self.env.user.company_id)
    state = fields.Selection([("draft", "Draft"),
                              ("open", "Open"),
                              ("close", "Close")],
                                string = "Status", default="draft", track_visibility="always")    

    @api.multi
    @api.depends('sugarcane_milled_tr', 'sugarcane_milled_ts')
    def get_total_sugarcane(self):
        for this in self:
            total_qty = 0
            total_qty = this.sugarcane_milled_tr + this.sugarcane_milled_ts
            this.sugarcane_milled_total = total_qty
    
    @api.multi
    @api.depends('rendement_tr', 'rendement_ts')
    def get_average_rendement(self):
        for this in self:
            this.rendement_avg = (this.rendement_tr + this.rendement_ts)/2
            
 