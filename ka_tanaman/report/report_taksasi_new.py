from odoo import models, fields, api, _

class WizardReportTaksasi(models.TransientModel):
    _name = "ka_plantation.wizard.report.taksasi"

    kecamatan_id = fields.Many2one('res.kecamatan', string="Kecamatan")
    desa_id = fields.Many2one('res.desa.kelurahan', string="Desa / Kelurahan")
    dasar_taksasi = fields.Selection([
        ('intensifikasi', 'Intensifikasi'),
        ('varietas', 'Varietas'),
        ('tanam', 'Masa tanam'),
        ('vartam', 'Varietas Dan Masa tanam'),
    ], string="Hasil Berdasarkan", default='intensifikasi', required=True)

    dasar_wilayah = fields.Selection([
        ('kecamatan', 'Semua Kecamatan'),
        ('desa', 'Semua Desa'),
        ('pilih', 'Pilih Wilayah'),
    ], string="Wilayah", default='kecamatan', required=True)

    @api.onchange('kecamatan_id')
    def _onchange_kecamatan_id(self):
        desa_ids = [x.id for x in self.kecamatan_id.desa_ids]
        return {'domain':{'desa_id': [('id', 'in', desa_ids)]}}

    def tes_call(self):
        default_id = self._context.get('default_sampling_id',False)
        model = self._context.get('default_model',False)
        obj_sampling = self.env[model].browse(default_id)
        vals = {
            'kecamatan_id': self.kecamatan_id.id,
            'desa_id': self.desa_id.id,
            'taksasi': self.dasar_taksasi,
            'wilayah': self.dasar_wilayah
        }

        return obj_sampling.cetak_taksasi(vals)


class ReportTaksasi(models.AbstractModel):
    _name = 'report.ka_tanaman.hasil_taksasi_view'
    _template = 'ka_tanaman.hasil_taksasi_view'
    

    def _get_kecamatan(self, company_id,wilayah,kecamatan_id):
        result = []
        if wilayah == 'pilih':
            result = self.env['res.kecamatan'].search([('id', '=', kecamatan_id),('company_id', '=', company_id)])
        else:
            result = self.env['res.kecamatan'].search([('company_id', '=', company_id)])
        return result

    def _get_desa(self,kecamatan_id,wilayah,desa_id):
        result = []
        if wilayah == 'pilih' and desa_id != None:
            result = self.env['res.desa.kelurahan'].search([('id', '=', desa_id)])
        else:
            result = self.env['res.desa.kelurahan'].search([('kecamatan_id', '=', kecamatan_id)])

        return result
        
    def _get_dasar_taksasi(self,dasar_taksasi):
        result = []
        if dasar_taksasi == 'intensifikasi':
            result = self.env['ka_plantation.intensifikasi'].search([('type', '=', 'tr')]).sorted('id')
        if dasar_taksasi == 'vartam':
            result = self.env['ka_plantation.periode'].search([]).sorted('id')
        if dasar_taksasi == 'tanam':
            result = self.env['ka_plantation.periode'].search([]).sorted('id')
        return result
    
    def _get_kecamatan_varietas(self,dasar_taksasi,data_masak):
        result = []
        if dasar_taksasi == 'varietas' or dasar_taksasi == 'vartam':
            result = self.env['ka_plantation.varietas'].search([('masak_category','=',data_masak)]).sorted('id')
        return result

    def _get_data_masak(self):
        result = ['awal','tengah','akhir']
        return result
        
    def _get_produksi(self,kecamatan_id, dasar_taksasi_id,mtt_id,dasar_taksasi):
        line = self.env['ka_plantation.area.agronomi'].search([('kecamatan_id', '=', kecamatan_id),('mtt_id', '=', mtt_id)])
        sum_produksi = 0
        result_sum = ""
        for l in line:
            if dasar_taksasi == 'intensifikasi':
                if l.intensifikasi_id.id == dasar_taksasi_id:
                    sum_produksi += l.taks_produksi
            if dasar_taksasi == 'varietas':
                if l.varietas_id.id == dasar_taksasi_id:
                    sum_produksi += l.taks_produksi
            if dasar_taksasi == 'tanam':
                if l.tanam_periode_id.id == dasar_taksasi_id:
                    sum_produksi += l.taks_produksi
        if sum_produksi > 0:
            result_sum = sum_produksi
        else:
            result_sum = ""
        return result_sum

    def _get_produksi_desa(self,desa_id,intensifikasi_id,mtt_id):
        line = self.env['ka_plantation.area.agronomi'].search([('desa_id', '=', desa_id),('mtt_id', '=', mtt_id)])
        sum_produksi = 0
        result_sum = ""
        for l in line:
            if l.intensifikasi_id.id == intensifikasi_id:
                sum_produksi += l.taks_produksi
        if sum_produksi > 0:
            result_sum = sum_produksi
        else:
            result_sum = ""
        return result_sum

    def _get_luas(self,kecamatan_id, dasar_taksasi_id,mtt_id,dasar_taksasi):
        line = self.env['ka_plantation.area.agronomi'].search([('kecamatan_id', '=', kecamatan_id),('mtt_id', '=', mtt_id)])
        sum_luas = 0
        result_sum = ""
        for l in line:
            if dasar_taksasi == 'intensifikasi':
                if l.intensifikasi_id.id == dasar_taksasi_id:
                    sum_luas += l.luas
            if dasar_taksasi == 'varietas':
                if l.varietas_id.id == dasar_taksasi_id:
                    sum_luas += l.luas
            if dasar_taksasi == 'tanam':
                if l.tanam_periode_id.id == dasar_taksasi_id:
                    sum_luas += l.luas
        if sum_luas > 0:
            result_sum = sum_luas
        else:
            result_sum = ""
        return result_sum

    def _get_luas_desa(self,desa_id, intensifikasi_id,mtt_id):
        line = self.env['ka_plantation.area.agronomi'].search([('desa_id', '=', desa_id),('mtt_id', '=', mtt_id)])
        sum_luas = 0
        result_sum = ""
        for l in line:
            if l.intensifikasi_id.id == intensifikasi_id:
                sum_luas += l.luas
        if sum_luas > 0:
            result_sum = sum_luas
        else:
            result_sum = ""
        return result_sum

    def _get_luas_intensifikasi(self,dasar_taksasi_id,mtt_id,dasar_taksasi):
        line = []
        if dasar_taksasi == 'intensifikasi':
            line = self.env['ka_plantation.area.agronomi'].search([('intensifikasi_id', '=', dasar_taksasi_id),('mtt_id', '=', mtt_id)])
        if dasar_taksasi == 'varietas':
            line = self.env['ka_plantation.area.agronomi'].search([('varietas_id', '=', dasar_taksasi_id),('mtt_id', '=', mtt_id)])
        if dasar_taksasi == 'tanam':
            line = self.env['ka_plantation.area.agronomi'].search([('tanam_periode_id', '=', dasar_taksasi_id),('mtt_id', '=', mtt_id)])
        sum_luas = 0
        result_sum = ""
        for l in line:
            sum_luas += l.luas
        if sum_luas > 0:
            result_sum = sum_luas
        return result_sum

    def _get_produksi_intensifikasi(self,dasar_taksasi_id,mtt_id,dasar_taksasi):
        line = []
        if dasar_taksasi == 'intensifikasi':
            line = self.env['ka_plantation.area.agronomi'].search([('intensifikasi_id', '=', dasar_taksasi_id),('mtt_id', '=', mtt_id)])
        if dasar_taksasi == 'varietas':
            line = self.env['ka_plantation.area.agronomi'].search([('varietas_id', '=', dasar_taksasi_id),('mtt_id', '=', mtt_id)])
        if dasar_taksasi == 'tanam':
            line = self.env['ka_plantation.area.agronomi'].search([('tanam_periode_id', '=', dasar_taksasi_id),('mtt_id', '=', mtt_id)])
        sum_produksi = 0
        result_sum = ""
        for l in line:
            sum_produksi += l.taks_produksi
        if sum_produksi > 0:
            result_sum = sum_produksi
        return result_sum

    def _get_lenght_taksasi(self,dasar_taksasi):
        print len(self._get_dasar_taksasi(dasar_taksasi)) * 2
        return len(self._get_dasar_taksasi(dasar_taksasi)) * 2

    def _get_lenght_varietas(self,dasar_taksasi,data_masak):
        return (len(self._get_kecamatan_varietas(dasar_taksasi,data_masak)) + 1) * 2

    def _get_company(self):
        return self.env.user.company_id.name

    def _get_luas_vartam(self,varietas_id,tanam_id,mtt_id):
        line = self.env['ka_plantation.area.agronomi'].search([('varietas_id', '=', varietas_id),('tanam_periode_id', '=', tanam_id),('mtt_id', '=', mtt_id)])
        sum_luas = 0
        result_sum = ""
        for l in line:
            sum_luas += l.luas
        if sum_luas > 0:
            result_sum = sum_luas
        return result_sum

    def _get_prod_vartam(self,varietas_id,tanam_id,mtt_id):
        line = self.env['ka_plantation.area.agronomi'].search([('varietas_id', '=', varietas_id),('tanam_periode_id', '=', tanam_id),('mtt_id', '=', mtt_id)])
        sum_prod = 0
        result_sum = ""
        for l in line:
            sum_prod += l.taks_produksi
        if sum_prod > 0:
            result_sum = sum_prod
        return result_sum

    def _get_luas_per_tanam(self,tanam_id,mtt_id,data_masak):
        line = self.env['ka_plantation.area.agronomi'].search([('varietas_id.masak_category', '=', data_masak),('tanam_periode_id', '=', tanam_id),('mtt_id', '=', mtt_id)])
        sum_luas = 0
        result_sum = ""
        for l in line:
            sum_luas += l.luas
        if sum_luas > 0:
            result_sum = sum_luas
        return result_sum

    def _get_prod_per_tanam(self,tanam_id,mtt_id,data_masak):
        line = self.env['ka_plantation.area.agronomi'].search([('varietas_id.masak_category', '=', data_masak),('tanam_periode_id', '=', tanam_id),('mtt_id', '=', mtt_id)])
        sum_prod = 0
        result_sum = ""
        for l in line:
            sum_prod += l.taks_produksi
        if sum_prod > 0:
            result_sum = sum_prod
        return result_sum

    def _get_luas_total_tanam(self,tanam_id,mtt_id):
        data_masak = ['awal','tengah','akhir']
        line = self.env['ka_plantation.area.agronomi'].search([('varietas_id.masak_category', 'in', data_masak),('tanam_periode_id', '=', tanam_id),('mtt_id', '=', mtt_id)])
        sum_luas = 0
        result_sum = ""
        for l in line:
            sum_luas += l.luas
        if sum_luas > 0:
            result_sum = sum_luas
        return result_sum

    def _get_prod_total_tanam(self,tanam_id,mtt_id):
        data_masak = ['awal','tengah','akhir']
        line = self.env['ka_plantation.area.agronomi'].search([('varietas_id.masak_category', 'in', data_masak),('tanam_periode_id', '=', tanam_id),('mtt_id', '=', mtt_id)])
        sum_prod = 0
        result_sum = ""
        for l in line:
            sum_prod += l.taks_produksi
        if sum_prod > 0:
            result_sum = sum_prod
        return result_sum

    @api.multi
    def render_html(self, docids, data=None):
        report_obj = self.env['report']
        model = self.env.context.get('active_model')
        docs = self.env[model].browse(data['ids'])
        kecamatan = self._get_kecamatan(data['form']['company_id'],data['form']['wilayah'],data['form']['kecamatan_id'])
        dasar_taksasi = self._get_dasar_taksasi(data['form']['taksasi'])
        docargs = {
            'data': data['form'],
            'dasar_taksasi': dasar_taksasi,
            'length_taksasi' : self._get_lenght_taksasi(data['form']['taksasi']),
            'length_awal': self._get_lenght_varietas(data['form']['taksasi'],'awal'),
            'length_tengah': self._get_lenght_varietas(data['form']['taksasi'],'tengah'),
            'length_akhir': self._get_lenght_varietas(data['form']['taksasi'],'akhir'),
            'kecamatan': kecamatan,
            'desa': self._get_desa,
            'company': self._get_company,
            'produksi': self._get_produksi,
            'produksi_desa': self._get_produksi_desa,
            'luas': self._get_luas,
            'luas_per_tanam': self._get_luas_per_tanam,
            'prod_per_tanam': self._get_prod_per_tanam,
            'luas_total_tanam': self._get_luas_total_tanam,
            'prod_total_tanam': self._get_prod_total_tanam,
            'luas_desa': self._get_luas_desa,
            'luas_vartam': self._get_luas_vartam,
            'prod_vartam': self._get_prod_vartam,
            'luas_intensifikasi': self._get_luas_intensifikasi,
            'produksi_intensifikasi': self._get_produksi_intensifikasi,
            'kecamatan_varietas': self._get_kecamatan_varietas,
            'masak' : self._get_data_masak,
            'taksasi': data['form']['taksasi'],
            'wilayah': data['form']['wilayah'],
            'desa_id': data['form']['desa_id'],
            'doc_ids': self.ids,
            'doc_model': model,
            'docs': docs,
        }
        
        return report_obj.render(self._template, values=docargs)
