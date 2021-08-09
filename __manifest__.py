{
    'name': 'Pedidos Operarios',
    'version': '1.0',
    'category': 'Pedidos Operarios',
    'summary': 'Pedidos Operarios',
    'depends': ['purchase'],
    'data': [
        'security/group.xml',
        'security/ir.model.access.csv',
        'views/pedidos_operarios.xml',
        'data/ir_sequence.xml',
    ],
    'demo': [
        ],
    'css': [],
    'installable': True,
    'auto_install': False,
    'application': True,
}
