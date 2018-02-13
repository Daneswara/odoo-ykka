# -*- coding: utf-8 -*-
# See LICENSE file for full copyright and licensing details.
{
    'name' : 'Web Organizational Chart',
    'version': '10.0.1.0.0',
    'summary': 'Hierarchical Structure of Companies Employee',
    'category': 'Tools',
    'author': 'Serpent Consulting Services Pvt. Ltd.',
    'website': 'http://www.serpentcs.com',
    'license': 'AGPL-3',
    'data': [
        "views/templates.xml",
        "views/web_org_chart.xml",
    ],
    'depends' : ['hr'],
    'qweb': ['/static/src/xml/*.xml'],
    'price': 20,
    'currency': 'EUR',
}
