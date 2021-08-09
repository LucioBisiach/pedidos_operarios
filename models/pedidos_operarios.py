# -*- coding: utf-8 -*-

from odoo import models, fields, multi_process, api, _
from odoo.exceptions import ValidationError

from datetime import datetime

import logging
_logger = logging.getLogger(__name__)


class PurchaseOrders(models.Model):
    _inherit = 'purchase.order'

    pedidos_id = fields.Many2one('pedidos.operarios', required=False, string="Pedido")

class PedidosOperarios(models.Model):
    _name = 'pedidos.operarios'

    name = fields.Char(string="N° Pedido", copy=False, readonly=True)

    fecha_pedido = fields.Date(string="Fecha", required=True)

    user_id = fields.Many2one('res.users', string="Operario", default=lambda self:self.env.user, required=True)

    supervisor_id = fields.Many2one('res.users', string="Usuarios", required=True)

    pedidos_ids = fields.One2many('linea.pedidos.operarios', 'ref_pedidos', ondelete="cascade", string="Pedidos")

    estado = fields.Selection(string='', selection=[
        ('espera', 'En Espera'), 
        ('confirmado', 'Confirmado'), 
        ('rechazado', 'Rechazado')], default='espera')

    email_enviado = fields.Boolean(string="Email enviado a supervisor", readonly=True)

    current_user = fields.Many2one('res.users','Current User', default=lambda self: self.env.user)

    total_purchases = fields.Integer(compute='_get_total_purchase', store=False)

    purchase_orders_ids = fields.One2many('purchase.order', 'pedidos_id', string="Compras")

    email_enviado_sup = fields.Boolean(string="Email enviado a compras", readonly=True)
    
    @api.model
    def create(self, vals):
        if vals.get('name', _('Nuevo')) == _('Nuevo'):
            vals['name'] = self.env['ir.sequence'].next_by_code(
                'pedidos.operarios') or _('Nuevo') + ' '
        res = super(PedidosOperarios, self).create(vals)
        return res


    def _get_total_purchases(self):
        self.total_purchases = sum(order.amount_untaxed for order in self.purchase_orders_ids.filtered(lambda s: s.state in ('purchase')))
    
    def act_show_purchases(self):  
        action = self.env.ref('purchase.purchase_form_action')

        result = {
            'name': action.name,
            'help': action.help,
            'type': action.type,
            'view_mode': action.view_mode,
            'target': action.target,
            'res_model': action.res_model,
            'context': {
                'default_pedidos_id': self.ids[0],
                'default_date_order': self.fecha_pedido,
                'default_date_planned': self.fecha_pedido
            }
        }
        result['domain'] = "[('id','in',[" + \
            ','.join(map(str, self.purchase_orders_ids.ids))+"])]"
        return result

    def estado_aprobado(self):
        for obj in self:
            obj.estado = 'confirmado'

    def estado_rechazado(self):
        for obj in self:
            obj.estado = 'rechazado'

    def estado_en_espera(self):
        for obj in self:
            obj.estado = 'espera'

    def mail_operario_supervisor(self):
        email_operario = self.user_id.login
        email_operario_smtp = self.env['ir.mail_server'].search([('smtp_user', '=', email_operario)])

        mail_content = "Hola " + self.supervisor_id.name + ", el operario " + self.user_id.name + " realizó el pedido: " + self.name + ". Ingrese al sistema para obtener mas información sobre el mismo"
        if email_operario_smtp:
                main_content = {
                    'subject': _('Pedido-%s Operario %s') % (self.name, str(self.fecha_pedido)),
                    'author_id': self.user_id.name,
                    'body_html': mail_content,
                    'email_to': self.supervisor_id.login,
                    'auto_delete': False,
                    'email_from': email_operario
                }

                self.email_enviado = True

    def mail_supervisor_compras(self):
        email_compras = self.env['res.users'].search([('tipo','=','admcompras')])

        for admcompras in email_compras:

            mail_content = "Hola " + admcompras.name + ", el supervisor " + self.supervisor_id.name + " solicita el pedido: " + self.name + ". Ingrese al sistema para obtener mas información sobre el mismo"
            
            email_supervisor = self.supervisor_id.login
            email_supervisor_smtp = self.env['ir.mail_server'].search([('smtp_user', '=', email_supervisor)])

            if email_operario_smtp:
                    main_content = {
                        'subject': _('Pedido-%s Supervisor %s') % (self.name, str(self.fecha_pedido)),
                        'author_id': self.supervisor_id.name,
                        'body_html': mail_content,
                        'email_to': admcompras.login,
                        'auto_delete': False,
                        'email_from': email_supervisor
                    }

                    self.email_enviado_sup = True
        


class LineaPedidosOperarios(models.Model):
    _name = 'linea.pedidos.operarios'

    name = fields.Many2one('product.template', string="Producto", required=True)
    cantidad = fields.Float(string="Cantidad", default=1, required=True)
    comentario = fields.Char(string="Comentario")

    ref_pedidos = fields.Many2one('pedidos.operarios', invisible=True)



class ResUsers(models.Model):
    _inherit = 'res.users'

    tipo = fields.Selection([('operario', 'Operario'), ('supervisor', 'Supervisor'), ('admcompras', 'Administrador Compras'),('otro', 'Otro')], string="Tipo", required=True)
