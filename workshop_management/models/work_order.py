# -*- coding: utf-8 -*-
from odoo.exceptions import MissingError
from odoo import api, fields, models, _


class WorkOrder(models.Model):
    """Class defined for creating work order"""
    _name = 'work.order'
    _description = "Work order details"
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _rec_name = "order_no"

    order_no = fields.Char(string='Order', readonly=True,
                           default=lambda self: _('New'))
    appointment_no = fields.Char(string="Appointment no", readonly=True)
    customer_id = fields.Many2one('res.partner', string="Customer")
    vehicle_id = fields.Many2one('fleet.vehicle', string="Vehicle")
    booking_date = fields.Date(string="Booking date",
                               default=fields.Date.today())
    appointment_date = fields.Date(string="Appointment date")
    odo_meter = fields.Float(string="Total Odo-meter")
    phone = fields.Char(related='customer_id.phone', string="Phone")
    state = fields.Selection(
        [('draft', 'Draft'), ('running', 'Running'), ('hold', 'Hold'),
         ('done', 'Done'), ('request_approved', 'Request approved'),
         ('repaired', 'Repaired'), ('received', 'Received'),
         ('request_rejected', 'Request rejected'),
         ('cancelled', 'Cancelled'), ('waiting', 'Waiting for parts')],
        string='State', default='draft')
    start_date = fields.Datetime(string="Start date")
    end_date = fields.Datetime(string="End date")
    notes = fields.Html(string="Notes")
    extra_components_ids = fields.One2many('extra.components', 'extra_comp_id',
                                           string="Extra Components")
    payment_option = fields.Boolean(string="Payment option")
    mechanic_id = fields.Many2one('hr.employee', string="Mechanic")
    hourly_cost = fields.Monetary(related="mechanic_id.hourly_cost",
                                  currency_field='company_currency_id')
    company_id = fields.Many2one('res.company', string='Company', readonly=True,
                                 default=lambda self: self.env.company)
    company_currency_id = fields.Many2one('res.currency',
                                          related='company_id.currency_id',
                                          string="Company Currency",
                                          readonly=True)
    service_cost = fields.Float(string='Service cost')
    material_order_ids = fields.One2many('material.order', 'material_order_id',
                                         string="Material orders")
    invoice_id = fields.Many2one('account.move', string="Invoice")
    payment_method_type = fields.Selection(
        [('pay_immediately', 'Pay immediately'),
         ('pay_on_acc', 'Pay on account')], default='pay_immediately')

    @api.model
    def create(self, vals_list):
        """Declaring function for creating unique sequence number
        for each order"""
        if vals_list.get('order_no', 'New') == 'New':
            vals_list['order_no'] = self.env['ir.sequence'].next_by_code(
                'workshop.order.sequence') or 'New'
        result = super().create(vals_list)
        return result

    def start_work(self):
        """Function defined for calculating the start time of the work"""
        if not self.mechanic_id:
            raise MissingError("Please select a Mechanic to start the work")
        self.start_date = fields.Datetime.now()
        self.write({'state': 'running'})

    def stop_work(self):
        """Function defined for calculating the end time of the work"""
        self.end_date = fields.Datetime.now()
        start_datetime = fields.Datetime.from_string(self.start_date)
        end_datetime = fields.Datetime.from_string(self.end_date)
        time_difference = end_datetime - start_datetime
        hours = time_difference.total_seconds() / 3600
        self.service_cost = self.hourly_cost * hours
        self.write({'state': 'done'})

    def request_approval(self):
        """Function defined for requesting approval from
        the customers to add extra components"""
        self.write({'state': 'hold'})

    def work_confirm(self):
        """Function defined for confirming the work order"""
        mail_template = self.env.ref(
            'workshop_management.work_done_email_template')
        mail_template.send_mail(self.id, force_send=True)
        self.write({'state': 'repaired'})

    def work_cancel(self):
        """Function defined for cancel the work order"""
        self.write({'state': 'cancelled'})

    def order_parts(self):
        """Function defined for change the work order to the waiting state"""
        self.write({'state': 'waiting'})
        return {'name': 'purchase order',
                'type': 'ir.actions.act_window',
                'res_model': 'work.purchase',
                'view_mode': 'form',
                "target": 'new',
                'context': {
                    'default_order': self.id
                }
                }

    def smart_button_purchase(self):
        """Function defined for appointment smart button in the work order"""
        return {
            'type': 'ir.actions.act_window',
            'name': 'purchase',
            'view_mode': 'form',
            'res_model': 'purchase.order',
            'domain': [('origin', '=', self.id)],
            'res_id': self.id,
            'context': {'create': False}
        }

    def continue_work(self):
        """Function defined for change the work order to draft state"""
        self.write({'state': 'running'})

    def create_invoice(self):
        """Function defined for creating invoice for the materials used
        in the work order and work cost of the mechanic"""
        self.invoice_id = self.env['account.move'].create(
            {'move_type': 'out_invoice',
             'partner_id': self.customer_id.id,
             'state': 'draft',
             'invoice_date': fields.Date.today(),
             })
        for rec in self.material_order_ids:
            self.env['account.move.line'].create({
                'product_id': rec.materials_id.id,
                'move_id': self.invoice_id.id,
                'quantity': rec.quantity,
                'price_unit': rec.price})
        mechanic_cost = self.env['product.product'].search(
            [('name', '=', 'Mechanic cost')])
        if mechanic_cost:
            mechanic_cost.write({'lst_price': self.service_cost})
            self.env['account.move.line'].create({
                'product_id': mechanic_cost.id,
                'move_id': self.invoice_id.id,
                'quantity': 1,
                'price_unit': mechanic_cost.lst_price})
        else:
            mech_cost = self.env['product.product'].create(
                {'name': 'Mechanic cost', 'lst_price': self.service_cost})
            self.env['account.move.line'].create({
                'product_id': mech_cost.id,
                'move_id': self.invoice_id.id,
                'quantity': 1,
                'price_unit': mech_cost.lst_price})
        return {
            'type': 'ir.actions.act_window',
            'name': 'Invoice',
            'res_model': 'account.move',
            'view_mode': 'form',
            'move_type': 'out_invoice',
            'res_id': self.invoice_id.id,
            'target': 'current'
        }

    def receive_vehicle(self):
        """Function defined for deliver vehicle to customer"""
        pay_account = self.customer_id.pay_on_account
        if pay_account or self.invoice_id.payment_state == 'paid':
            self.write({'state': 'received'})
        else:
            raise MissingError(
                "Please make the payment before receiving the vehicle")

    def smart_button_invoice(self):
        """Function defined for appointment smart button in the work order"""
        return {
            'type': 'ir.actions.act_window',
            'name': 'invoice',
            'view_mode': 'form',
            'res_model': 'account.move',
            'res_id': self.invoice_id.id,
            'context': {'create': False}
        }

    def create_report(self):
        """Function defined for creating report for the work order"""
        data = {'form_data': self.read()[0],
                'material': self.material_order_ids.ids}
        return self.env.ref(
            'workshop_management.action_report_work_order').report_action(
            self, data=data)

    @api.onchange('customer_id')
    def _onchange_payment_method_type(self):
        """Function defined for enabling selection field based on customer"""
        if self.customer_id.pay_on_account:
            self.payment_option = True
