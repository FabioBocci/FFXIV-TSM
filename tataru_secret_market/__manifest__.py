# -*- coding: utf-8 -*-
{
    'name': "Tataru's Secret Market",

    'description': """

    """,

    'author': "TSM",

    # Categories can be used to filter modules in modules listing
    # Check https://github.com/odoo/odoo/blob/16.0/odoo/addons/base/data/ir_module_category_data.xml
    # for the full list
    'category': 'application',
    'version': '16.0.0.1',

    # any module necessary for this one to work correctly
    'depends': ['base'],

    # always loaded
    'data': [
        'security/ir.model.access.csv',
        "views/items/items.xml",
        "views/general/data_centers.xml",
        "views/general/worlds.xml",
    ],
}
