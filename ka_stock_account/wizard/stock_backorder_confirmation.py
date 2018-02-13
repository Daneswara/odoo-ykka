from odoo import api, fields, models, _
from datetime import datetime
import pytz

class StockBackorderConfirmation(models.TransientModel):
    _inherit = 'stock.backorder.confirmation'
    
    @api.multi
    def process(self):
        # additional by PAA : journal date based on date of transfer
        user = self.env.user
        tz = pytz.timezone(user.tz) if user.tz else pytz.utc
        date_transfer = datetime.strptime(self.pick_id.date_transfer, '%Y-%m-%d %H:%M:%S')
        date_transfer = pytz.utc.localize(date_transfer).astimezone(tz)
        date_transfer = datetime.strftime(date_transfer, '%Y-%m-%d')
        self.with_context(force_period_date = date_transfer)._process()