from django.db import models
from django.contrib.postgres.fields import JSONField
from django.db.models.signals import post_delete
from django.dispatch import receiver

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
    api_key = models.CharField(null=False, max_length=100, unique=True)
    check_type = models.CharField(max_length=10, choices=CHECK_TYPES, null=False)
    point_id = models.IntegerField(null=False)
    
    def __str__(self):
        return self.name
    
class Check(models.Model):
    objects = models.Manager()
    printer_id = models.ForeignKey(Printer)
    ctype = models.CharField(max_length=10, choices=CHECK_TYPES, null=False)
    order = JSONField()
    status = models.CharField(max_length=10, choices=ORDER_STATUSES, null=False)
    pdf_file = models.FileField(upload_to='pdf/')

@receiver(post_delete, sender=Check)
def myfield_delete(sender, instance, **kwargs):
    if instance.pdf_file:
        instance.pdf_file.delete(False)

