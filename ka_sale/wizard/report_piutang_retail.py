from openerp import models, fields, api, _


@api.model
def _lang_get(self):
    return self.env['res.lang'].get_installed()

class report_piutang_retail(models.TransientModel):
    _name = "report.piutang.retail.wiz"
    
    @api.model
    def default_get(self,fields):
        res = super(report_piutang_retail,self).default_get(fields)
        product_retail = self.env.user.company_id.product_sugar_retail_id
        if product_retail:
            sale_category_src = self.env['ka_sale.order.category'].search([('product_ids','=',product_retail.id)],limit=1)
            if sale_category_src:
                res['sale_category_id'] = sale_category_src.id
        return res
    
    sale_category_id = fields.Many2one('ka_sale.order.category', 'Sale Category')
    date_limit = fields.Date('Date')
    lang = fields.Selection(_lang_get, string='Language', default=lambda self: self.env.ref('base.lang_id').code,
                            help="If the selected language is loaded in the system, all documents related to "
                                 "this contact will be printed in this language. If not, it will be English.")

    @api.multi
    def generate_report_piutang_retail(self):
        report_obj = self.env['report']
        template = 'ka_sale.template_report_piutang_retail'
        report = report_obj._get_report_from_name(template)
        domain = {
            'sale_category_id': self.sale_category_id.id,
            'date_limit': self.date_limit
            }
        values = {
            'ids': self.ids,
            'model': report.model,
            'form': domain
            }
        return report_obj.get_action(self, template, data=values)
    

class report_piutang_retail_qweb(models.AbstractModel):
    _name = 'report.ka_sale.template_report_piutang_retail'
    _template = 'ka_sale.template_report_piutang_retail'

    def get_invoice_ids(self, sale_category_id, date_end):
        invoice_src = self.env['account.invoice'].search([('sale_category_id','=',sale_category_id),
                                                          ('date_invoice','<=',date_end),
                                                          ('state','=','open')])
        return [invoice for invoice in invoice_src]
    
    def get_notes(self, sale_category_id, date_end):
        notes = []
        for invoice in self.get_invoice_ids(sale_category_id, date_end):
            if invoice.comment:
                notes.append(invoice.comment)
        return notes
    
    def get_picking_id(self, invoice_id):
        source_uid = self.env.user.company_id.intercompany_user_id.id
        res = list()
        for inv_line in invoice_id.invoice_line_ids:
            for so_line in inv_line.sale_line_ids:
                if so_line.order_id.saleorder_type == 'rkout':
                    for picking in so_line.order_id.sudo(source_uid).dest_so_id.picking_ids:
                        if picking not in res and picking.state == 'done':
                            res.append(picking)
                else:
                    for picking in so_line.order_id.picking_ids:
                        if picking not in res and picking.state == 'done':
                            res.append(picking)
        return res

    @api.multi
    def render_html(self, docids, data=None):
        report_obj = self.env['report']
        model = self.env.context.get('active_model')
        docs = self.env[model].browse(self.env.context.get('active_id'))
        docargs = {
            'data': data['form'],
            'doc_ids': self.ids,
            'doc_model': model,
            'docs': docs,
            'get_invoice_ids': self.get_invoice_ids,
            'get_notes': self.get_notes,
            'get_picking_id': self.get_picking_id
            }
        return report_obj.render(self._template, docargs)
    