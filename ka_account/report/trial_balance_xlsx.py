from openerp import api, fields, models, _
from datetime import datetime
  

try:
    from openerp.addons.report_xlsx.report.report_xlsx import ReportXlsx
except ImportError:
    class ReportXlsx(object):
        def __init__(self, *args, **kwargs):
            pass


class Trial_Balance_Xlsx(ReportXlsx):

    def generate_xlsx_report(self, workbook, data, account_report):
        #################################################################################
        header_style = workbook.add_format({'bold': 1,'align':'center','valign':'vcenter'})
        header_style.set_font_name('Arial')
        header_style.set_font_size('10')
        header_style.set_text_wrap()
        header_style.set_bottom(8)
        #################################################################################
        header1_center = workbook.add_format({'bold': 1,'align':'center','valign':'vcenter'})
        header1_center.set_font_name('Arial')
        header1_center.set_font_size('8')
        header1_center.set_border()
        header1_center.set_text_wrap()
        #################################################################################
        header2_left = workbook.add_format({'bold': 1,'align':'left','valign':'vcenter'})
        header2_left.set_font_name('Arial')
        header2_left.set_font_size('8')
        header2_left.set_text_wrap()
        #################################################################################
        header3_style = workbook.add_format({'bold': 1,'align':'center','valign':'vcenter'})
        header3_style.set_font_name('Arial')
        header3_style.set_font_size('8')
        header3_style.set_text_wrap()
        #################################################################################
        normal_left_border = workbook.add_format({'valign':'vcenter','align':'left'})
        normal_left_border.set_text_wrap()
        normal_left_border.set_font_name('Arial')
        normal_left_border.set_font_size('8')
        normal_left_border.set_border()
        normal_left_border.set_text_wrap()
        #################################################################################
        bold_left_border = workbook.add_format({'bold': 1,'valign':'vcenter','align':'left'})
        bold_left_border.set_text_wrap()
        bold_left_border.set_font_name('Arial')
        bold_left_border.set_font_size('8')
        bold_left_border.set_border()
        #################################################################################
        normal_right_border = workbook.add_format({'valign':'vcenter','align':'right'})
        normal_right_border.set_text_wrap()
        normal_right_border.set_font_name('Arial')
        normal_right_border.set_font_size('8')
        normal_right_border.set_border()
        #################################################################################
        bold_right_border = workbook.add_format({'bold': 1,'valign':'vcenter','align':'right'})
        bold_right_border.set_text_wrap()
        bold_right_border.set_font_name('Arial')
        bold_right_border.set_font_size('8')
        bold_right_border.set_border()
        #################################################################################
        normal_center_border = workbook.add_format({'valign':'vcenter','align':'center'})
        normal_center_border.set_text_wrap()
        normal_center_border.set_font_name('Arial')
        normal_center_border.set_font_size('8')
        normal_center_border.set_border()
        
        worksheet = workbook.add_worksheet("Neraca Bulanan")
        worksheet.set_paper(9)
        worksheet.set_portrait()
        worksheet.set_margins(0.3, 0.3, 0.5, 0.5)
        worksheet.freeze_panes(5, 0)
        worksheet.set_column('A:A', 7)
        worksheet.set_column('B:B', 23)
        worksheet.set_column('C:C', 12)
        worksheet.set_column('D:D', 12)
        worksheet.set_column('E:E', 12)
        worksheet.set_column('F:F', 12)
        worksheet.set_column('G:G', 8)
        
        worksheet.set_row(0,18)
        worksheet.set_row(1,18)
        worksheet.set_row(2,18)
        worksheet.set_row(4,22)

        date_to = datetime.strftime(datetime.strptime(account_report.date_to, '%Y-%m-%d'),'%d-%m-%Y')
        
        worksheet.merge_range('A1:B1','PT. KEBON AGUNG',header2_left)
        worksheet.merge_range('A2:B2',self.env.user.company_id.name.upper(),header2_left)
        worksheet.merge_range('A3:B3',self.env.user.company_id.city.upper(),header2_left)
        worksheet.merge_range('C2:D2','NERACA BULANAN',header_style)
        worksheet.merge_range('C3:D3','s/d '+ date_to,header3_style)
        
        worksheet.write(4,0,'No. Perk',header1_center)
        worksheet.write(4,1,'Nama Perkiraan',header1_center)
        worksheet.write(4,2,'Saldo Awal',header1_center)
        worksheet.write(4,3,'Debit',header1_center)
        worksheet.write(4,4,'Kredit',header1_center)
        worksheet.write(4,5,'Saldo Akhir',header1_center)
        worksheet.write(4,6,'R.A.B.P \n(1=1000)',header1_center)
        
        opening_str = 0.0
        debit_str = 0.0
        credit_str = 0.0
        ending_str = 0.0
        
        total_opening_balance = 0.0
        total_debit = 0.0
        total_credit = 0.0
        total_ending_balance = 0.0
        
        row = 4
        for account in self.env['account.financial.report'].search([('parent_id','=',account_report.account_report_id.id)], order='sequence asc') :
            row +=1
            worksheet.set_row(row,18)
            if account.code:
                worksheet.write(row,0,account.code,normal_center_border)
            worksheet.merge_range(row,1,row,6,account.name,bold_left_border)
            worksheet.write(row,6,'',normal_center_border)
            
            subtotal_opening_balance = 0.0
            subtotal_debit = 0.0
            subtotal_credit = 0.0
            subtotal_ending_balance = 0.0
            
            for acc in account.account_ids:
                row +=1
                worksheet.set_row(row,18)
                
                self.env.cr.execute("""select sum(move_line.balance) from account_move_line move_line
                                join account_account account on move_line.account_id = account.id
                                where account_id = %s and date < %s""", (acc.id, account_report.date_from))
                open_balance = self.env.cr.dictfetchone()
                if open_balance['sum'] == None:
                    open_balance['sum'] = 0.0
                opening_str = str('{0:,.2f}'.format(float(open_balance['sum']))).replace('.', '%').replace(',', '.').replace('%', ',')
                    
                self.env.cr.execute("""select sum(move_line.debit) from account_move_line move_line
                            join account_account account on move_line.account_id = account.id
                            where account_id = %s and date >= %s and date <= %s""", (acc.id, account_report.date_from, account_report.date_to))
                debit = self.env.cr.dictfetchone()
                if debit['sum'] == None:
                    debit['sum'] = 0.0
                debit_str = str('{0:,.2f}'.format(float(debit['sum']))).replace('.', '%').replace(',', '.').replace('%', ',')
                    
                self.env.cr.execute("""select sum(move_line.credit) from account_move_line move_line
                            join account_account account on move_line.account_id = account.id
                            where account_id = %s and date >= %s and date <= %s""", (acc.id, account_report.date_from, account_report.date_to))
                credit = self.env.cr.dictfetchone()
                if credit['sum'] == None:
                    credit['sum'] = 0.0
                credit_str = str('{0:,.2f}'.format(float(credit['sum']))).replace('.', '%').replace(',', '.').replace('%', ',')
                    
                end_balance = open_balance['sum'] + debit['sum'] - credit['sum']
                ending_str = str('{0:,.2f}'.format(float(end_balance))).replace('.', '%').replace(',', '.').replace('%', ',')
                
                worksheet.write(row,0,acc.code,normal_center_border)
                worksheet.write(row,1,acc.name,normal_left_border)
                worksheet.write(row,2,opening_str,normal_right_border)
                worksheet.write(row,3,debit_str,normal_right_border)
                worksheet.write(row,4,credit_str,normal_right_border)
                worksheet.write(row,5,ending_str,normal_right_border)
                worksheet.write(row,6,'-',normal_center_border)
                
                subtotal_opening_balance += open_balance['sum']
                subtotal_debit += debit['sum']
                subtotal_credit += credit['sum']
                subtotal_ending_balance += end_balance
            
            row +=1
            worksheet.set_row(row,18)
            worksheet.write(row,0,'',normal_left_border)
            worksheet.merge_range(row, 0, row, 1, 'JUMLAH', bold_right_border)
            worksheet.write(row,2,str('{0:,.2f}'.format(float(subtotal_opening_balance))).replace('.', '%').replace(',', '.').replace('%', ','),bold_right_border)
            worksheet.write(row,3,str('{0:,.2f}'.format(float(subtotal_debit))).replace('.', '%').replace(',', '.').replace('%', ','),bold_right_border)
            worksheet.write(row,4,str('{0:,.2f}'.format(float(subtotal_credit))).replace('.', '%').replace(',', '.').replace('%', ','),bold_right_border)
            worksheet.write(row,5,str('{0:,.2f}'.format(float(subtotal_ending_balance))).replace('.', '%').replace(',', '.').replace('%', ','),bold_right_border)
            worksheet.write(row,6,'-',normal_center_border)

            total_opening_balance += subtotal_opening_balance
            total_debit += subtotal_debit
            total_credit += subtotal_credit
            total_ending_balance += subtotal_ending_balance
        
        row +=1
        worksheet.set_row(row,18)
        worksheet.write(row,0,'',normal_left_border)
        worksheet.merge_range(row, 0, row, 1, 'JUMLAH SEMUA', bold_right_border)
        worksheet.write(row,2,str('{0:,.2f}'.format(float(total_opening_balance))).replace('.', '%').replace(',', '.').replace('%', ','),bold_right_border)
        worksheet.write(row,3,str('{0:,.2f}'.format(float(total_debit))).replace('.', '%').replace(',', '.').replace('%', ','),bold_right_border)
        worksheet.write(row,4,str('{0:,.2f}'.format(float(total_credit))).replace('.', '%').replace(',', '.').replace('%', ','),bold_right_border)
        worksheet.write(row,5,str('{0:,.2f}'.format(float(total_ending_balance))).replace('.', '%').replace(',', '.').replace('%', ','),bold_right_border)
        worksheet.write(row,6,'-',normal_center_border)

        workbook.close()
        
Trial_Balance_Xlsx('report.trial.balance.xlsx',
            'ka_trial.balance.report.wizard')