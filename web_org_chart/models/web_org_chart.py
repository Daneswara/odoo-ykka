# -*- coding: utf-8 -*-
# See LICENSE file for full copyright and licensing details.

from odoo import api, fields, models, _


class hr_employee(models.Model):
    _inherit = 'hr.department'

    @api.model
    def get_dept_parent_childs (self,ids,parent_id):
         dept_details = []
         child_ids = []
         for department in self.browse(ids):
            job_title = False
            dept_parent_id = department.parent_id.id
            if parent_id[0] == department.id :
                dept_parent_id = False
            for child in department.child_ids :
                child_ids.append(child.id)
            if department.manager_id.job_id :
                job_title = department.manager_id.job_id.name
            dept_details.append({
                                 'dept_id':"dept_"+str(department.id),
                                 'dept_name':department.name,
                                 'dept_parent_id':"dept_"+ str(dept_parent_id),
                                 'dept_employee_id':department.manager_id.id,
                                 'dept_employee_name':department.manager_id.name,
                                 'dept_employee_email':department.manager_id.work_email,
                                 'dept_employee_job_title':job_title,
                             })
         return [dept_details,child_ids]

    @api.model
    def get_department_details(self,ids, parent_id):
         dept_details = [];
         dept_parent_childs_object = self.get_dept_parent_childs;
         loop=True;
         while(loop):
             dept_parent_childs_details=dept_parent_childs_object(ids, parent_id)
             for data in dept_parent_childs_details[0]:
                 dept_details.append(data);
             if dept_parent_childs_details[1] :
                ids = dept_parent_childs_details[1];
             else :
                loop=False;
         return dept_details

    @api.multi
    def employee_dept(self,ids):
        employee_obj = self.env['hr.employee']
        employee_ids = employee_obj.search([])
        department_ids = self.search([])
        dept_details = []
        emp_details = []

        for employee in employee_ids:
            if employee.parent_id :
                emp_details.append({
                                    'emp_name':employee.name,
                                    'emp_id':employee.id,
                                    'parent':employee.parent_id.id,
                                    'emp_email':employee.work_email,
                                    'emp_job_title':employee.job_id.name
                                });
                                
        if ids:
          parent_id = ids
          dept_details = self.get_department_details(ids, parent_id)
          return [emp_details,dept_details]
        else :
            for department in department_ids:
                dept_details.append({
                                 'dept_id':"dept_"+str(department.id),
                                 'dept_name':department.name,
                                 'dept_parent_id':"dept_"+ str(department.parent_id.id),
                                 'dept_employee_id':department.manager_id.id,
                                 'dept_employee_name':department.manager_id.name,
                                 'dept_employee_email':department.manager_id.work_email,
                                 'dept_employee_job_title':department.manager_id.job_id.name,
                             })
            return [emp_details,dept_details]
