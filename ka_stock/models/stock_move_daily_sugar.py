from odoo import models, fields, api
from datetime import datetime
import time
from odoo.exceptions import UserError

class StockMoveDailySugar(models.Model):
    _name = "stock.move.daily.sugar"
    _description = "Stock Move Daily Sugar for PT Kebon Agung"
    _inherit = ['mail.thread']
    _order = 'date desc, id desc'
    _template_hasil_timbang_gula = 'ka_stock.template_hasil_timbang_gula'
    
    name = fields.Char(string="Name", default="New", copy=False)
    date = fields.Date(string="Tanggal", default=fields.Datetime.now)
    state = fields.Selection([("draft", "Draft"),
                              ("proposed", "Proposed"),
                              ("done", "Done")],
                                string = "Status", default="draft", track_visibility="always", copy=False)
    product_id = fields.Many2one("product.product", string="Product", default=lambda self: self.env.user.company_id.product_sugar_id)
    real_qty_sugar_mill = fields.Float("Penggilingan Tebu", copy=False)
    real_qty_ms = fields.Float("Pengolahan Kembali MS", copy=False)
    real_qty_raw_sugar = fields.Float("Pengolahan Raw Sugar", copy=False)
    total_production_qty = fields.Float("Total Kuantum", compute="compute_total_qty", copy=False)
#     report_qty = fields.Float("Kuantum Laporan", compute="compute_report_qty", copy=False)
#     real_qty = fields.Float(string="Kuantum Produksi", copy=False)
    product_uom = fields.Many2one("product.uom", string="Unit of Measure")
    company_id = fields.Many2one("res.company", string="Company", default=lambda self: self.env.user.company_id)
    move_ids = fields.One2many("stock.move", "move_daily_id", string="Stock Moves", copy=False)
    bagi_hasil = fields.Boolean("Bagi Hasil", copy=False)
    factory_qty = fields.Float("Gula Milik Pabrik", copy=False)
    farmer_qty = fields.Float("Gula Milik Petani")
    farmer_qty_90 = fields.Float("Gula Non-Natura", copy=False)
    farmer_qty_10 = fields.Float("Gula Natura", copy=False)
    manufacture_daily_id_sugar = fields.Many2one("ka_manufacture.daily", string="Hari Giling")
    
  
    @api.onchange('product_id')
    def onchange_product_id(self):
        self.product_uom = self.product_id.production_package_uom_id.id
 
    @api.onchange('farmer_qty')
    def onchange_farmer_qty(self):
        non_natura_percent = self.env.user.company_id.percentage_bagi_hasil_non_natura / 100
        natura_percent = self.env.user.company_id.percentage_bagi_hasil_natura / 100
        self.farmer_qty_90 = non_natura_percent * self.farmer_qty
        self.farmer_qty_10 = natura_percent * self.farmer_qty
        
    @api.multi   
    def compute_total_qty(self):
        for this in self:
            this.total_production_qty = this.real_qty_sugar_mill + this.real_qty_ms + this.real_qty_raw_sugar
    
    @api.multi
    def unlink(self):
        for this in self:
            if this.state != 'draft':
                raise UserError('Sorry, you cannot delete non-draft transaction.')
        return super(StockMoveDailySugar, self).unlink()
            
    @api.multi
    def action_view_picking(self):
        for this in self:
            domain = [('id', 'in', [x.picking_id.id for x in self.env['stock.move'].search([('move_daily_id','=', this.id)])])]

            return {
                'name': 'Stock Picking',
                'view_type': 'form',
                'view_mode': 'tree,form',
                'domain' : domain,
                'type': 'ir.actions.act_window',
                'res_model': 'stock.picking',
                'target': 'current',  
            }
        
    @api.multi
    def propose_daily_sugar_transaction(self):
        for this in self:
            this.write({'state' : 'proposed'})
        return True
    
    @api.multi
    def set_draft_daily_sugar_transaction(self):
        for this in self:
            this.write({'state': 'draft'})
        return True
    
    @api.multi
    def validate_daily_sugar_transaction(self):
        for this in self:
            line_items_stock = []
            line_items_pg = []
            line_items_tani = []
            line_items_natura = []
            vals = {'state': 'done'}
            if this.name == 'New':
                sequence_src = self.env['ir.sequence'].search([('name','=','Stock Move Daily Sugar'),('company_id','=',self.env.user.company_id.id)], limit=1)
                if not sequence_src:
                    raise UserError('Penomoran untuk produksi harian gula belum ada. Silahkan hubungi Administrator.')
                vals['name'] = sequence_src.next_by_id()
            this.write(vals)
            data_entry = {}
            data_entry_pg = {}
            data_entry_tani = {}
            data_entry_natura ={}
            date_now = datetime.now().date()
            picking_type_id = self.env.user.company_id.picking_type_produce_id.id
            picking_type_factory_id = self.env.user.company_id.picking_type_factory_id.id
            picking_type_farmer_id = self.env.user.company_id.picking_type_farmer_id.id
            picking_type_natura_id = self.env.user.company_id.picking_type_natura_id.id
            location_production_id = this.product_id.property_stock_production.id
            stock_picking_obj = self.env['stock.picking']
                
            vals_stock = {
                'product_id' : this.product_id.id,
                'product_uom_qty' : this.product_uom.factor_inv * this.total_production_qty,
                'product_uom' : this.product_id.uom_id.id,
                'name' : this.product_id.display_name,
                'picking_type_id' : picking_type_id, 
                'location_id' : location_production_id,
                'location_dest_id' : self.env.user.company_id.location_production_dest_id.id,
                'date_expected' : date_now,
                'move_daily_id' : this.id
                    }
            
            line_items_stock.append((0, 0, vals_stock))

            data_entry = {
                'location_id' : location_production_id,
                'location_dest_id' : self.env.user.company_id.location_production_dest_id.id,
                'min_date': date_now,
                'date_transfer': date_now,
                'origin': this.name,
                'move_lines': line_items_stock,
                'picking_type_id': picking_type_id,
                        }

            stock_picking_create = stock_picking_obj.create(data_entry)
            stock_picking_create.action_confirm()
            stock_picking_create.do_transfer()
            
            if this.bagi_hasil == True:
                
                vals_stock_pg = {
                    'product_id' : this.product_id.id,
                    'product_uom_qty' : this.product_uom.factor_inv * this.factory_qty,
                    'product_uom' : this.product_id.uom_id.id,
                    'name' : this.product_id.display_name,
                    'picking_type_id' : picking_type_factory_id, 
                    'location_id' : self.env.user.company_id.location_production_dest_id.id,
                    'location_dest_id' : self.env.user.company_id.location_factory_id.id,
                    'date_expected' : date_now,
                    'move_daily_id' : this.id
                }
                line_items_pg.append((0, 0, vals_stock_pg))
    
                data_entry_pg = {
                    'location_id' : self.env.user.company_id.location_production_dest_id.id,
                    'location_dest_id' : self.env.user.company_id.location_factory_id.id,
                    'min_date': date_now,
                    'date_transfer': date_now,
                    'origin': this.name,
                    'move_lines': line_items_pg,
                    'picking_type_id': picking_type_factory_id,
                }
    
                stock_picking_pg_create = stock_picking_obj.create(data_entry_pg)
                stock_picking_pg_create.action_confirm()
                stock_picking_pg_create.do_transfer()
                
                vals_stock_tani = {
                    'product_id' : this.product_id.id,
                    'product_uom_qty' : this.product_uom.factor_inv * this.farmer_qty_90,
                    'product_uom' : this.product_id.uom_id.id,
                    'name' : this.product_id.display_name,
                    'picking_type_id' : picking_type_farmer_id, 
                    'location_id' : self.env.user.company_id.location_production_dest_id.id,
                    'location_dest_id' : self.env.user.company_id.location_farmer_id.id,
                    'date_expected' : date_now,
                    'move_daily_id' : this.id
                }
                line_items_tani.append((0, 0, vals_stock_tani))
    
                data_entry_tani = {
                    'location_id' : self.env.user.company_id.location_production_dest_id.id,
                    'location_dest_id' : self.env.user.company_id.location_farmer_id.id,
                    'min_date': date_now,
                    'date_transfer': date_now,
                    'origin': this.name,
                    'move_lines': line_items_tani,
                    'picking_type_id': picking_type_farmer_id,
                }
    
                stock_picking_tani_create = stock_picking_obj.create(data_entry_tani)
                stock_picking_tani_create.action_confirm()
                stock_picking_tani_create.do_transfer()
                
                vals_stock_natura = {
                    'product_id' : this.product_id.id,
                    'product_uom_qty' : this.product_uom.factor_inv * this.farmer_qty_10,
                    'product_uom' : this.product_id.uom_id.id,
                    'name' : this.product_id.display_name,
                    'picking_type_id' : picking_type_natura_id, 
                    'location_id' : self.env.user.company_id.location_production_dest_id.id,
                    'location_dest_id' : self.env.user.company_id.location_natura_id.id,
                    'date_expected' : date_now,
                    'move_daily_id' : this.id
                }
                line_items_natura.append((0, 0, vals_stock_natura))
    
                data_entry_natura = {
                    'location_id' : self.env.user.company_id.location_production_dest_id.id,
                    'location_dest_id' : self.env.user.company_id.location_natura_id.id,
                    'min_date': date_now,
                    'date_transfer': date_now,
                    'origin': this.name,
                    'move_lines': line_items_natura,
                    'picking_type_id': picking_type_natura_id,
                }
    
                stock_picking_natura_create = stock_picking_obj.create(data_entry_natura)
                stock_picking_natura_create.action_confirm()
                stock_picking_natura_create.do_transfer()
        return True

    @api.multi
    def print_laporan_harian_gula(self):
        for this in self:
            report_obj = self.env['report']
            template = "ka_stock.template_laporan_harian_gula"
            report = report_obj._get_report_from_name(template)
            data = {}
            datas = {
                'ids': this.id,
                'model': report.model,
                'form': data,
                }
        return report_obj.get_action(self, template, data=datas)

    @api.multi
    def print_hasil_timbang(self):
        for this in self:
            report_obj = self.env['report']
            template = "ka_stock.template_hasil_timbang_gula"
            report = report_obj._get_report_from_name(template)
            data = {}
            datas = {
                'ids': this.id,
                'model': report.model,
                'form': data,
                }
        return report_obj.get_action(self, template, data=datas)

    def get_qty_in_ku(self, qty):
        qty_kg = qty * self.product_uom.factor_inv
        qty_ku = qty_kg / self.product_id.production_uom_id.factor_inv
        return qty_ku
    
    def get_qty_in_ku_from_kg(self, qty_kg):
        qty_ku = qty_kg / self.product_id.production_uom_id.factor_inv
        return qty_ku
    
    def get_qty_yesterday(self):
        yesterday_sum = 0
        stock_move_sugar_obj = self.env['stock.move.daily.sugar'].search([('date', '<', self.date), 
                                                                          ('manufacture_daily_id_sugar.session_id.fiscalyear_id', '=', self.manufacture_daily_id_sugar.session_id.fiscalyear_id.id)]) 
        for stock in stock_move_sugar_obj:
            yesterday_sum += stock.total_production_qty
        return yesterday_sum

    
    def get_qty_yesterday_sugar_mill(self):
        yesterday_sum_sugar_mill = 0
        stock_move_sugar_obj = self.env['stock.move.daily.sugar'].search([('product_id', '=', self.product_id.id),
                                                                          ('date', '<', self.date), 
                                                                          ('manufacture_daily_id_sugar.session_id.fiscalyear_id', '=', self.manufacture_daily_id_sugar.session_id.fiscalyear_id.id)]) 
        for stock in stock_move_sugar_obj:
            yesterday_sum_sugar_mill += stock.real_qty_sugar_mill
        return yesterday_sum_sugar_mill

    def get_qty_yesterday_ms(self):
        yesterday_sum_ms = 0
        stock_move_sugar_obj = self.env['stock.move.daily.sugar'].search([('product_id', '=', self.product_id.id),
                                                                          ('date', '<', self.date), 
                                                                          ('manufacture_daily_id_sugar.session_id.fiscalyear_id', '=', self.manufacture_daily_id_sugar.session_id.fiscalyear_id.id)]) 
        for stock in stock_move_sugar_obj:
            yesterday_sum_ms += stock.real_qty_ms
        return yesterday_sum_ms
    
    def get_qty_yesterday_raw_sugar(self):
        yesterday_sum_raw_sugar = 0
        stock_move_sugar_obj = self.env['stock.move.daily.sugar'].search([('product_id', '=', self.product_id.id),
                                                                          ('date', '<', self.date), 
                                                                          ('manufacture_daily_id_sugar.session_id.fiscalyear_id', '=', self.manufacture_daily_id_sugar.session_id.fiscalyear_id.id)]) 
        for stock in stock_move_sugar_obj:
            yesterday_sum_raw_sugar += stock.real_qty_raw_sugar
        return yesterday_sum_raw_sugar  
    
    def get_qty_today(self):
        yesterday_sum = self.get_qty_yesterday()
        until_today_sum = yesterday_sum + self.total_production_qty
        return until_today_sum
    
    def get_qty_today_sugar_mill(self):
        yesterday_sum = self.get_qty_yesterday_sugar_mill()
        until_today_sum = yesterday_sum + self.real_qty_sugar_mill
        return until_today_sum
    
    def get_qty_today_ms(self):
        yesterday_sum = self.get_qty_yesterday_ms()
        until_today_sum = yesterday_sum + self.real_qty_ms
        return until_today_sum
    
    def get_qty_today_raw_sugar(self):
        yesterday_sum = self.get_qty_yesterday_raw_sugar()
        until_today_sum = yesterday_sum + self.real_qty_raw_sugar
        return until_today_sum
    
    def get_qty_yesterday_factory(self):
        yesterday_sum = 0
        stock_move_sugar_obj = self.env['stock.move.daily.sugar'].search([('product_id', '=', self.product_id.id),
                                                                          ('date', '<', self.date), 
                                                                          ('manufacture_daily_id_sugar.session_id.fiscalyear_id', '=', self.manufacture_daily_id_sugar.session_id.fiscalyear_id.id)]) 
        for stock in stock_move_sugar_obj:
            yesterday_sum += stock.factory_qty
        return yesterday_sum
    
    def get_qty_today_factory(self):
        yesterday_sum = self.get_qty_yesterday_factory()
        until_today_sum = yesterday_sum + self.factory_qty
        return until_today_sum
    
    def get_qty_yesterday_farmer(self):
        yesterday_sum = 0
        stock_move_sugar_obj = self.env['stock.move.daily.sugar'].search([('product_id', '=', self.product_id.id),
                                                                          ('date', '<', self.date), 
                                                                          ('manufacture_daily_id_sugar.session_id.fiscalyear_id', '=', self.manufacture_daily_id_sugar.session_id.fiscalyear_id.id)]) 
        for stock in stock_move_sugar_obj:
            yesterday_sum += stock.farmer_qty
        return yesterday_sum
    
    def get_qty_today_farmer(self):
        yesterday_sum = self.get_qty_yesterday_farmer()
        until_today_sum = yesterday_sum + self.farmer_qty
        return until_today_sum
    
    def get_qty_kontrak_a_yesterday(self):
        yesterday_sum_kontrak_a = 0
        start_date = datetime.strptime(self.date, '%Y-%m-%d')
        limit_year = start_date.year
        start_date = start_date.replace(hour=0, minute=0, second=0)
        start_date = datetime.strftime(start_date, '%Y-%m-%d %H:%M:%S')
        limit_date = datetime(limit_year,1,1,0,0,0)
        limit_date = datetime.strftime(limit_date,"%Y-%m-%d %H:%M:%S")
        stock_move_obj = self.env['stock.move'].search([('product_id', '=', self.product_id.id),
                                                        ('state', '=', 'done'), 
                                                        ('date', '>=', limit_date),
                                                        ('date', '<', start_date),
                                                        ('picking_type_id.is_do_kontrak_a','=', True)
                                                        ])
        for stock in stock_move_obj:
            yesterday_sum_kontrak_a += stock.product_uom_qty
        return yesterday_sum_kontrak_a
       
    def get_qty_kontrak_a_today(self):
        today_sum_kontrak_a = 0
        start_date = datetime.strptime(self.date, '%Y-%m-%d')
        start_date = start_date.replace(hour=0, minute=0, second=0)
        start_date = datetime.strftime(start_date, '%Y-%m-%d %H:%M:%S')
        end_date = datetime.strptime(self.date, '%Y-%m-%d')
        end_date = end_date.replace(hour=23, minute=59, second=59)
        end_date = datetime.strftime(end_date, '%Y-%m-%d %H:%M:%S')
        stock_move_obj = self.env['stock.move'].search([('product_id', '=', self.product_id.id),
                                                        ('state', '=', 'done'),
                                                        ('date', '>=', start_date),
                                                        ('date', '<=', end_date),
                                                        ('picking_type_id.is_do_kontrak_a','=', True)
                                                        ])
        for stock in stock_move_obj:
            today_sum_kontrak_a += stock.product_uom_qty
        return today_sum_kontrak_a
    
    def get_qty_kontrak_a_until_today(self):
        yesterday_sum_kontrak_a = self.get_qty_kontrak_a_yesterday()
        today_sum_kontrak_a = self.get_qty_kontrak_a_today()
        until_today_sum_kontrak_a = yesterday_sum_kontrak_a + today_sum_kontrak_a
        return until_today_sum_kontrak_a
    
    def get_qty_do_yesterday(self):
        yesterday_sum_do = 0
        start_date = datetime.strptime(self.date, '%Y-%m-%d')
        limit_year = start_date.year
        start_date = start_date.replace(hour=0, minute=0, second=0)
        start_date = datetime.strftime(start_date, '%Y-%m-%d %H:%M:%S')
        limit_date = datetime(limit_year,1,1,0,0,0)
        limit_date = datetime.strftime(limit_date,"%Y-%m-%d %H:%M:%S")
        stock_move_obj = self.env['stock.move'].search([('product_id', '=', self.product_id.id),
                                                        ('state', '=', 'done'),
                                                        ('date', '>=', limit_date), 
                                                        ('date', '<', start_date),
                                                        ('picking_id.picking_type_code','=', 'outgoing')
                                                        ])
        for stock in stock_move_obj:
            yesterday_sum_do += stock.product_uom_qty
        return yesterday_sum_do
    
    def get_qty_do_today(self):
        today_sum_do = 0
        start_date = datetime.strptime(self.date, '%Y-%m-%d')
        start_date = start_date.replace(hour=0, minute=0, second=0)
        start_date = datetime.strftime(start_date, '%Y-%m-%d %H:%M:%S')
        end_date = datetime.strptime(self.date, '%Y-%m-%d')
        end_date = end_date.replace(hour=23, minute=59, second=59)
        end_date = datetime.strftime(end_date, '%Y-%m-%d %H:%M:%S')
        stock_move_obj = self.env['stock.move'].search([('product_id', '=', self.product_id.id),
                                                        ('state', '=', 'done'),
                                                        ('date', '>=', start_date),
                                                        ('date', '<=', end_date),
                                                        ('picking_id.picking_type_code','=', 'outgoing')
                                                        ])
        for stock in stock_move_obj:
            today_sum_do += stock.product_uom_qty
        return today_sum_do
    
    def get_qty_do_until_today(self):
        yesterday_sum_do = self.get_qty_do_yesterday()
        today_sum_do = self.get_qty_do_today()
        until_today_sum_do = yesterday_sum_do + today_sum_do
        return until_today_sum_do
    
    def get_qty_natura_yesterday(self):
        yesterday_sum_natura = 0
        start_date = datetime.strptime(self.date, '%Y-%m-%d')
        limit_year = start_date.year
        start_date = start_date.replace(hour=0, minute=0, second=0)
        start_date = datetime.strftime(start_date, '%Y-%m-%d %H:%M:%S')
        limit_date = datetime(limit_year,1,1,0,0,0)
        limit_date = datetime.strftime(limit_date,"%Y-%m-%d %H:%M:%S")
        stock_move_obj = self.env['stock.move'].search([('product_id', '=', self.product_id.id),
                                                        ('state', '=', 'done'),
                                                        ('date', '>=', limit_date), 
                                                        ('date', '<', start_date),
                                                        ('location_id','=', self.env.user.company_id.location_natura_id.id)
                                                        ])
        for stock in stock_move_obj:
            yesterday_sum_natura += stock.product_uom_qty
        return yesterday_sum_natura
    
    def get_qty_natura_today(self):
        today_sum_natura = 0
        start_date = datetime.strptime(self.date, '%Y-%m-%d')
        start_date = start_date.replace(hour=0, minute=0, second=0)
        start_date = datetime.strftime(start_date, '%Y-%m-%d %H:%M:%S')
        end_date = datetime.strptime(self.date, '%Y-%m-%d')
        end_date = end_date.replace(hour=23, minute=59, second=59)
        end_date = datetime.strftime(end_date, '%Y-%m-%d %H:%M:%S')
        stock_move_obj = self.env['stock.move'].search([('product_id', '=', self.product_id.id),
                                                        ('state', '=', 'done'),
                                                        ('date', '>=', start_date),
                                                        ('date', '<=', end_date),
                                                        ('location_id','=', self.env.user.company_id.location_natura_id.id)
                                                        ])
        for stock in stock_move_obj:
            today_sum_natura += stock.product_uom_qty
        return today_sum_natura
    
    def get_qty_natura_until_today(self):
        yesterday_sum_natura = self.get_qty_natura_yesterday()
        today_sum_natura = self.get_qty_natura_today()
        until_today_sum_natura = yesterday_sum_natura + today_sum_natura
        return until_today_sum_natura
    
    def get_qty_tani_yesterday(self):
        yesterday_sum_tani = 0
        start_date = datetime.strptime(self.date, '%Y-%m-%d')
        limit_year = start_date.year
        start_date = start_date.replace(hour=0, minute=0, second=0)
        start_date = datetime.strftime(start_date, '%Y-%m-%d %H:%M:%S')
        limit_date = datetime(limit_year,1,1,0,0,0)
        limit_date = datetime.strftime(limit_date,"%Y-%m-%d %H:%M:%S")
        stock_move_obj = self.env['stock.move'].search([('product_id', '=', self.product_id.id),
                                                        ('state', '=', 'done'), 
                                                        ('date', '>=', limit_date), 
                                                        ('date', '<', start_date),
                                                        ('location_id','=', self.env.user.company_id.location_farmer_id.id)
                                                        ])
        for stock in stock_move_obj:
            yesterday_sum_tani += stock.product_uom_qty
        return yesterday_sum_tani
    
    def get_qty_tani_today(self):
        today_sum_tani = 0
        start_date = datetime.strptime(self.date, '%Y-%m-%d')
        start_date = start_date.replace(hour=0, minute=0, second=0)
        start_date = datetime.strftime(start_date, '%Y-%m-%d %H:%M:%S')
        end_date = datetime.strptime(self.date, '%Y-%m-%d')
        end_date = end_date.replace(hour=23, minute=59, second=59)
        end_date = datetime.strftime(end_date, '%Y-%m-%d %H:%M:%S')
        stock_move_obj = self.env['stock.move'].search([('product_id', '=', self.product_id.id),
                                                        ('state', '=', 'done'),
                                                        ('date', '>=', start_date),
                                                        ('date', '<=', end_date),
                                                        ('location_id','=', self.env.user.company_id.location_farmer_id.id)
                                                        ])
        for stock in stock_move_obj:
            today_sum_tani += stock.product_uom_qty
        return today_sum_tani
    
    def get_qty_tani_until_today(self):
        yesterday_sum_tani= self.get_qty_tani_yesterday()
        today_sum_tani= self.get_qty_tani_today()
        until_today_sum_tani = yesterday_sum_tani + today_sum_tani
        return until_today_sum_tani
    
    def get_sum_qty_yesterday(self):
        sum_qty_yesterday = self.get_qty_kontrak_a_yesterday() + self.get_qty_do_yesterday() + self.get_qty_natura_yesterday() + self.get_qty_tani_yesterday()
        return sum_qty_yesterday
    
    def get_sum_qty_today(self):
        sum_qty_today = self.get_qty_kontrak_a_today() + self.get_qty_do_today() + self.get_qty_natura_today() + self.get_qty_tani_today()
        return sum_qty_today
    
    def get_sum_qty_until_today(self):
        sum_qty_until_today = self.get_qty_kontrak_a_until_today() + self.get_qty_do_until_today() + self.get_qty_natura_until_today() + self.get_qty_tani_until_today()
        return sum_qty_until_today
    
    def get_sum_qty_yesterday_factory(self):
        sum_qty_yesterday_factory = self.get_qty_kontrak_a_yesterday() + self.get_qty_do_yesterday()
        return sum_qty_yesterday_factory
    
    def get_sum_qty_today_factory(self):
        sum_qty_today_factory = self.get_qty_kontrak_a_today() + self.get_qty_do_today() 
        return sum_qty_today_factory
    
    def get_sum_qty_until_today_factory(self):
        sum_qty_until_today_factory = self.get_qty_kontrak_a_until_today() + self.get_qty_do_until_today()
        return sum_qty_until_today_factory
    
    def get_sum_qty_yesterday_farmer(self):
        sum_qty_yesterday_farmer =  self.get_qty_natura_yesterday() + self.get_qty_tani_yesterday()
        return sum_qty_yesterday_farmer
    
    def get_sum_qty_today_farmer(self):
        sum_qty_today_farmer = self.get_qty_natura_today() + self.get_qty_tani_today()
        return sum_qty_today_farmer
        
    def get_sum_qty_until_today_farmer(self):
        sum_qty_until_today_farmer = self.get_qty_natura_until_today() + self.get_qty_tani_until_today()
        return sum_qty_until_today_farmer
    
    def get_residual_do(self):
        residual_do = 0
        stock_quant_obj = self.env['stock.quant'].search([('product_id', '=', self.product_id.id),
                                                        ('location_id.name','=', 'Natura')
                                                        ])
        for stock in stock_quant_obj:
            residual_do += stock.qty
        return residual_do
    
    def get_sugar_not_devide(self):
        sugar_not_devide = 0
        stock_quant_obj = self.env['stock.quant'].search([('product_id', '=', self.product_id.id),
                                                        ('location_id.name','=', 'Stock')
                                                        ])
        for stock in stock_quant_obj:
            sugar_not_devide += stock.qty
        return sugar_not_devide
    