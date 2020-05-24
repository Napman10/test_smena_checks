from django.db import models
from django.contrib.postgres.fields import JSONField

CHECK_TYPES = (
    ('client', 'Client'),
    ('kitchen', 'Kitchen')
)

ORDER_STATUSES = (
    ('new', 'New'),
    ('rendered', 'Rendered'),
    ('printed', 'Printed')
)

class Printer(models.Model):
    objects = models.Manager()
    name = models.CharField(null=False, max_length=100)
    api_key = models.CharField(null=False, max_length=100)
    check_type = models.CharField(max_length=10, choices=CHECK_TYPES)
    point_id = models.IntegerField(null=False)
    
class Check(models.Model):
    objects = models.Manager()
    printer_id = models.ForeignKey(Printer)
    type = models.CharField(max_length=10, choices=CHECK_TYPES)
    order = JSONField()
    status = models.CharField(max_length=10, choices=ORDER_STATUSES)
    pdf_file = models.FileField(upload_to='pdf/')
    

# Create your models here.
