from odoo import models, fields, api
from datetime import datetime
import pytz
import tempfile
import base64
import os
import csv


class BankSatementLineImport(models.TransientModel):
    _name = "bank.statement.line.import.wizard"
    _description = "Model to Import Bank Statement Line"

    data_file = fields.Binary("File(*.csv)", required=True)

    @api.multi
    def import_bank_statement_line(self):
        self.ensure_one()
        statement_id = self._context.get('active_id', False)
        data = base64.decodestring(self.data_file)
        fobj = tempfile.NamedTemporaryFile(delete=False)
        fname = fobj.name
        fobj.write(data)
        fobj.close()
        crd = csv.reader(open(fname,"rb"))
        head = crd.next()[0].split(';')
        statement_lines = []
        for row in crd:
            statement_lines.append(row)
        
        statement_lines.reverse()
        for row in statement_lines:
            date = datetime.strptime(row[1], '%d/%m/%y')
            date = datetime.strftime(date, '%Y-%m-%d')
            transaction_code = row[3]
            description_code = row[4].strip()
            description = row[5].strip()
            ref = row[6]
            debit = row[7]
            debit = float(debit.strip().replace(',',''))
            credit = row[8]
            credit = float(credit.strip().replace(',',''))            
             
            label = str(transaction_code)
            if description_code != '':
                label += ' - ' + description_code
            if description != '':
                label += ' - ' + description
                 
            amount = 0.0
            if debit > 0:
                amount -= debit
            elif credit > 0:
                amount += credit
             
            self.env['account.bank.statement.line'].create({'statement_id' : statement_id,
                                                            'date' : date,
                                                            'name' : label,
                                                            'ref' : ref,
                                                            'amount' : amount
                                                            })
            
        
        
        
        