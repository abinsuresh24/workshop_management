# -*- coding: utf-8 -*-
from datetime import timedelta
from odoo import api, fields, models, _


class WorkshopAppointment(models.Model):
    """Class defined for adding appoint details of the customers"""
    _name = 'workshop.appointment'
    _description = "Workshop appointment details"
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _rec_name = "appointment_no"

    appointment_no = fields.Char(string="Appointment number", readonly=True,
                                 default=lambda self: _('New'))
    customer_id = fields.Many2one('res.partner', string="Name",
                                  help="Name of the customer")
    address = fields.Char(related='customer_id.contact_address',
                          string="Address")
    phone = fields.Char(related='customer_id.phone', string="Phone")
    email = fields.Char(related='customer_id.email', string="Email")
    state = fields.Selection([('draft', 'Draft'), ('confirmed', 'Confirmed'),
                              ('received', 'Vehicle Received'),
                              ('to_work', 'To Work'),
                              ('cancelled', 'Cancelled')],
                             string='State', default='draft')
    vehicle_id = fields.Many2one('fleet.vehicle', string="Vehicle",
                                 domain="[('driver_id', '=', customer_id)]",
                                 help="Vehicle to repair")
    total_km = fields.Float(string="Last odo-meter",
                            related="vehicle_id.odometer",
                            help="Total odo-meter reading")
    booking_date = fields.Date(string="Booking date",
                               default=fields.Date.today())
    appointment_date = fields.Date(string='Appointment date', required=True,
                                   help="Appointment date for the service")
    compliant_ids = fields.One2many('workshop.complaints', 'workshop_id')
    responsible_id = fields.Many2one('res.users', 'Responsible User',
                                     default=lambda self: self.env.user)
    company_id = fields.Many2one('res.company', string="Company name",
                                 help="Company name",
                                 default=lambda self: self.env.company)
    notes = fields.Html(string="Notes")
    work_order_id = fields.Many2one('work.order')
    maintenance_reminder = fields.Boolean(string="Maintenance reminder",
                                          help="Sends an automatic reminder "
                                               "for the maintenance for every "
                                               "5000 km or 6 months")
    service_km = fields.Float(string="service time odo meter")
    other_vehicle_ids = fields.Many2many('fleet.vehicle',
                                         string="Other vehicles",
                                    domain="[('driver_id', '=', customer_id)]",
                                    help="Other vehicles owned by customers")

    def appointment_confirm(self):
        """Function defined for confirming appointment"""
        mail_template = self.env.ref(
            'workshop_management.confirmation_email_template')
        mail_template.send_mail(self.id, force_send=True)
        self.service_km = self.total_km
        self.write({'state': 'confirmed'})

    def appointment_cancel(self):
        """Function defined for cancelling appointment"""
        self.write({'state': 'cancelled'})

    def receive_vehicle(self):
        """Function defined for receiving vehicle and add a pop-up to
        collect additional details from the customer"""
        self.write({'state': 'received'})
        return {
            'name': 'Other complaints',
            'type': 'ir.actions.act_window',
            'res_model': 'other.complaints',
            'view_mode': 'form',
            "target": 'new',
            "context": {
                'active_id': self.id,
                'default_appointment': self.appointment_no,
            },
        }

    def vehicle_pickup(self):
        """Function defined for pick-up the vehicle from the customer
         and place a work order for the vehicle"""
        self.work_order_id = self.env['work.order'].create({
            'customer_id': self.customer_id.id,
            'appointment_no': self.appointment_no,
            'vehicle_id': self.vehicle_id.id,
            'appointment_date': self.appointment_date,
            'odo_meter': self.total_km,
        })
        self.write({'state': 'to_work'})

    @api.model
    def create(self, vals_list):
        """Declaring function for creating unique sequence number
        for each booking"""
        if vals_list.get('appointment_no', 'New') == 'New':
            vals_list['appointment_no'] = self.env['ir.sequence'].next_by_code(
                'workshop.appointment.sequence') or 'New'
        result = super().create(vals_list)
        return result

    def reminder_mail(self):
        """Function defined for sending reminder request
        one day before the appointment date"""
        today = fields.Date.today()
        tomorrow = today + timedelta(days=1)
        for rec in self.search([]):
            if rec.appointment_date == tomorrow:
                mail_template = self.env.ref(
                    'workshop_management.reminder_email_template')
                mail_template.send_mail(rec.id, force_send=True)

    def smart_button_work_order(self):
        """Function defined for adding smart button to show the
        work order for the appointment"""
        return {
            'type': 'ir.actions.act_window',
            'name': 'work_order',
            'view_mode': 'form',
            'res_model': 'work.order',
            'res_id': self.work_order_id.id,
            'context': {'create': False}
        }

    def maintenance_mail(self):
        """Function defined for sending maintenance request for each 5000km
        or 6 months intervals"""
        for rec in self.search([]):
            if rec.maintenance_reminder:
                maintenance_month = fields.Date.add(rec.appointment_date,
                                                    months=6)
                maintenance_km = rec.service_km + 5000
                if rec.service_km or rec.appointment_date:
                    if rec.total_km > maintenance_km or \
                            fields.date.today() == maintenance_month:
                        mail_template = self.env.ref(
                            'workshop_management.maintenance_email_template')
                        mail_template.send_mail(rec.id, force_send=True)
