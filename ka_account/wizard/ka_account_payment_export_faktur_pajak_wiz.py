from cStringIO import StringIO
from odoo import models, fields, api, _
from odoo.exceptions import UserError
from datetime import datetime
import csv
import sys
import base64
import pytz
import urllib2 
from unidecode import unidecode


class ka_account_payment_export_faktur_pajak_wiz(models.TransientModel):
    _name = "ka_account.payment.export.faktur.pajak.wiz"
    
    text1 = fields.Char('Name', default='Pilih jenis pajak, Kemudian Klik Export Pajak')
    text2 = fields.Char('Name', default='Download Link')
    state_x = fields.Selection([("choose", "Choose"),("get", "Get")],
                                string = "State X", default="choose", copy=False)
    export = fields.Selection([("ppn","PPN"),("pph","PPh")],string="Jenis Pajak",default="ppn")
    data_x = fields.Binary('File', readonly=True)
    name = fields.Char('Filename', readonly=True)
    no_urut = fields.Integer(string="No urut")
    
    
    def find_between( self,s, first, last ):
        try:
            start = s.index( first ) + len( first )
            end = s.index( last, start )
            return s[start:end]
        except ValueError:
            return ""
        
    @api.multi
    def create_efaktur(self):
        context = dict(self._context or {})
        data = {}
        active_ids = self.env.context.get('active_ids')
        delimiter = ','
        data['form'] = active_ids
        user = self.env.user
        tz = pytz.timezone(user.tz) if user.tz else pytz.utc
        now = pytz.utc.localize(datetime.now()).astimezone(tz)
        download_time = datetime.strftime(now, "%d-%m-%Y_%H:%M")

        if self.export == "ppn":
            filename = "faktur_pajak_" + download_time + ".csv"
            
            output_head = '"FM"' + delimiter + '"KD_JENIS_TRANSAKSI"' + delimiter + '"FG_PENGGANTI"' + delimiter + '"NOMOR_FAKTUR"' + delimiter + '"MASA_PAJAK"' + delimiter + '"TAHUN_PAJAK"' + delimiter + "TANGGAL_FAKTUR" + delimiter
            output_head += '"NPWP"' + delimiter + '"NAMA"' + delimiter + '"ALAMAT_LENGKAP"' + delimiter + '"JUMLAH_DPP"' + delimiter + '"JUMLAH_PPN"' + delimiter + '"JUMLAH_PPNBM"' + delimiter + '"IS_CREDITABLE"' + '\n'
            
            for p in self.env['ka_account.payment'].browse(data['form']):
                if p.efaktur_url is False :
                    raise UserError(_("Please Fill E-Faktur URL"))
                else :
                    barcode = urllib2.urlopen(p.efaktur_url).read()
                    if barcode == '' or not barcode:
                        return
                    
                    kdJenisTransaksi = self.find_between(barcode, "<kdJenisTransaksi>", "</kdJenisTransaksi>")
                    fgPengganti = self.find_between(barcode, "<fgPengganti>", "</fgPengganti>")
                    nomorFaktur = self.find_between(barcode, "<nomorFaktur>", "</nomorFaktur>")
                    tanggalFaktur = datetime.strftime(datetime.strptime(self.find_between(barcode,"<tanggalFaktur>","</tanggalFaktur>"), "%d/%m/%Y"), "%Y-%m-%d")
                    npwpPenjual = self.find_between(barcode, "<npwpPenjual>", "</npwpPenjual>")
                    namaPenjual = self.find_between(barcode, "<namaPenjual>", "</namaPenjual>")
                    alamatPenjual = self.find_between(barcode, "<alamatPenjual>", "</alamatPenjual>")
                    jumlahDpp = self.find_between(barcode, "<jumlahDpp>", "</jumlahDpp>")
                    jumlahPpn = self.find_between(barcode, "<jumlahPpn>", "</jumlahPpn>")
                    jumlahPpnBm = self.find_between(barcode, "<jumlahPpnBm>", "</jumlahPpnBm>")
                    
                    output_head += '"FM"' + delimiter + '"' + kdJenisTransaksi + '"' + delimiter + '"' + fgPengganti + '"' + delimiter + '"' + nomorFaktur + '"' + delimiter
                    output_head += '"' + datetime.strftime(now, "%m") + '"' + delimiter + '"' + datetime.strftime(now, "%Y") + '"' + delimiter + '"' + tanggalFaktur +'"' + delimiter + '"' + npwpPenjual + '"' + delimiter
                    output_head += '"' + namaPenjual + '"' + delimiter + '"' + alamatPenjual + '"' + delimiter + '"' + str(jumlahDpp) + '"' + delimiter + '"' + str(jumlahPpn) + '"' + delimiter
                    output_head += '"' + jumlahPpnBm + '"' + delimiter + '"1"' + '\n'
        elif self.export == "pph":
            filename = "bukti_tagihan_pph_" + download_time + ".csv"
            
            output_head = ''
            
            for p in self.env['ka_account.payment'].browse(data['form']):
                if p.state !=  'paid' :
                    raise UserError(_("Status Tagihan Belum Dibayar!"))
                else :
                    tgl_bayar = p.date_paid[-2:]+"/"+p.date_paid[5:-3]+"/"+p.date_paid[:4]
                    output_head += '"F113304"' + delimiter + '"'+ p.date_paid[5:-3] +'"' + delimiter + '"'+ p.date_paid[:4] +'"' + delimiter + '"0"' + delimiter + '"' + str(p.no_npwp) + '"' + delimiter + '"' + p.partner_id.name + '"' + delimiter
                    output_head += '"' + p.partner_id.street + '"' + delimiter + '"'+ str(self.no_urut) +'"' + delimiter + '"' + tgl_bayar +'"' + delimiter
                    output_head += '"0"' + delimiter + '"0,25"' + delimiter + '"0"' + delimiter
                    output_head += '"0"' + delimiter + '"0,1"' + delimiter + '"0"' + delimiter
                    output_head += '"0"' + delimiter + '"0,3"' + delimiter + '"0"' + delimiter
                    output_head += '"0"' + delimiter + '"0,45"' + delimiter + '"0"' + delimiter
                    output_head += '"Farmasi"' + delimiter + '"0"' + delimiter + '"0,25"' + delimiter + '"0"' + delimiter
                    output_head += '""' + delimiter
                    output_head += '"0"' + delimiter + '"0"' + delimiter + '"0"' + delimiter
                    output_head += '""' + delimiter
                    output_head += '"0"' + delimiter + '"0"' + delimiter + '"0"' + delimiter
                    output_head += '"PERKEBUNAN"' + delimiter + '"' + str(int(p.amount_dpp)) + '"' + delimiter + '"0,25"' + delimiter + '"' + str(int(p.amount_pph)) + '"' + delimiter
                    output_head += '""' + delimiter
                    output_head += '"0"' + delimiter + '"0,25"' + delimiter + '"0"' + delimiter
                    output_head += '""' + delimiter
                    output_head += '"0"' + delimiter + '"0"' + delimiter + '"0"' + delimiter
                    output_head += '""' + delimiter
                    output_head += '"0"' + delimiter + '"0"' + delimiter + '"0"' + delimiter
                    output_head += '"' + str(int(p.amount_dpp)) + '"' + delimiter + '"' + str(int(p.amount_pph)) + '"' + '\n'      
                    self.no_urut+=1
                
        my_utf8 = output_head.encode("utf-8")
        out=base64.b64encode(my_utf8)
        self.write({'state_x':'get', 'data_x':out, 'name': filename})
        ir_model_data = self.env['ir.model.data']
        form_res = ir_model_data.get_object_reference('ka_account', 'ka_account_payment_export_faktur_pajak_form')#module 'pti_faktur' and 'id wizard form'
        form_id = form_res and form_res[1] or False
        return {
            'name': _('Download csv'),
            'view_type': 'form',
            'view_mode': 'form',
            'res_model': 'ka_account.payment.export.faktur.pajak.wiz', #model wizard
            'res_id': self.id, #id wizard
            'view_id': False,
            'views': [(form_id, 'form')],
            'type': 'ir.actions.act_window',
            'target': 'current'
        }      

        
        