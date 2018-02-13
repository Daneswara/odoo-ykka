from odoo import models, fields, api, _

class ReportEstimasi(models.AbstractModel):
    _name = 'report.ka_tanaman.estimasi_perolehan_view'
    _template = 'ka_tanaman.estimasi_perolehan_view'

    def _get_kecamatan(self,company_id):
        result = self.env['res.kecamatan'].search([('company_id', '=', company_id)]).sorted('name')
        return result

    def _get_company(self):
        return self.env.user.company_id.name

    def _luas_tebu(self,kecamatan_id,mtt_id):
        line = self.env['ka_plantation.area.agronomi'].search([('kecamatan_id', '=', kecamatan_id),('mtt_id', '=', mtt_id)])
        sum_luas = 0
        result_sum = ""
        for l in line:
            sum_luas += l.luas
        if sum_luas > 0:
            result_sum = sum_luas
        else:
            result_sum = ""
        return result_sum

    def _jumlah_tebu(self,kecamatan_id,mtt_id):
        line = self.env['ka_plantation.area.agronomi'].search([('kecamatan_id', '=', kecamatan_id),('mtt_id', '=', mtt_id)])
        sum_prod = 0
        result_prod = ""
        for l in line:
            sum_prod += l.taks_produksi
        if sum_prod > 0:
            result_prod = sum_prod
        else:
            result_prod = ""
        return result_prod

    def _tebu_ha(self,kecamatan_id,mtt_id):
    	return self._jumlah_tebu(kecamatan_id,mtt_id) / self._luas_tebu(kecamatan_id,mtt_id)

    def _luas_kecamatan(self,kecamatan_id,mtt_id):
        line = self.env['ka_plantation.register.line'].search([('kecamatan_id', '=', kecamatan_id),('mtt_id', '=', mtt_id),('register_id.state', '=', 'approve')])
        sum_luas = 0
        result_sum = ""
        for l in line:
            sum_luas += l.luas
        if sum_luas > 0:
            result_sum = sum_luas
        else:
            result_sum = ""
        return result_sum

    def _get_produktivitas(self,kecamatan_id,mtt_id):
    	line = self.env['ka_plantation.register.line'].search([('kecamatan_id', '=', kecamatan_id),('mtt_id', '=', mtt_id),('register_id.state', '=', 'approve')])
        sum_prod = 0
        result_prod = ""
        for l in line:
            sum_prod += l.taks_produksi
        if sum_prod > 0:
        	result_prod = sum_prod
        else:
        	result_prod = ""
        return result_prod

    @api.multi
    def render_html(self, docids, data=None):
        report_obj = self.env['report']
        model = self.env.context.get('active_model')
        docs = self.env[model].browse(data['ids'])
        docargs = {
            'data': data['form'],
            'kecamatan': self._get_kecamatan(data['form']['company_id']),
            'company': self._get_company,
            'luas_kecamatan': self._luas_kecamatan,
            'luas_tebu': self._luas_tebu,
            'jumlah_tebu': self._jumlah_tebu,
            'tebu_ha': self._tebu_ha,
            'produktivitas_kecamatan': self._get_produktivitas,
            'doc_ids': self.ids,
            'doc_model': model,
            'docs': docs,
        }
        
        return report_obj.render(self._template, values=docargs)