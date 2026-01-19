# Generated migration to convert is_approved to status and add business fields

from django.db import migrations, models
from decimal import Decimal


def convert_is_approved_to_status(apps, schema_editor):
    """
    Convert existing is_approved boolean to status field.
    - is_approved=True -> status='APPROVED'
    - is_approved=False -> status='PENDING'
    """
    Seller = apps.get_model('sellers', 'Seller')
    for seller in Seller.objects.all():
        if seller.is_approved:
            seller.status = 'APPROVED'
        else:
            seller.status = 'PENDING'
        seller.save()


def reverse_convert_status_to_is_approved(apps, schema_editor):
    """
    Reverse migration: convert status back to is_approved.
    """
    Seller = apps.get_model('sellers', 'Seller')
    for seller in Seller.objects.all():
        seller.is_approved = (seller.status == 'APPROVED')
        seller.save()


class Migration(migrations.Migration):

    dependencies = [
        ('sellers', '0001_initial'),
    ]

    operations = [
        # Step 1: Add new fields (nullable first)
        migrations.AddField(
            model_name='seller',
            name='status',
            field=models.CharField(
                choices=[('PENDING', 'Pending'), ('APPROVED', 'Approved'), ('REJECTED', 'Rejected')],
                default='PENDING',
                max_length=20,
                help_text='Seller application status'
            ),
        ),
        migrations.AddField(
            model_name='seller',
            name='business_name',
            field=models.CharField(blank=True, help_text='Optional business name', max_length=200),
        ),
        migrations.AddField(
            model_name='seller',
            name='business_description',
            field=models.TextField(blank=True, help_text='Optional business description'),
        ),
        migrations.AddField(
            model_name='seller',
            name='updated_at',
            field=models.DateTimeField(auto_now=True),
        ),
        
        # Step 2: Convert existing data
        migrations.RunPython(convert_is_approved_to_status, reverse_convert_status_to_is_approved),
        
        # Step 3: Make status non-nullable (now that all data is converted)
        migrations.AlterField(
            model_name='seller',
            name='status',
            field=models.CharField(
                choices=[('PENDING', 'Pending'), ('APPROVED', 'Approved'), ('REJECTED', 'Rejected')],
                default='PENDING',
                max_length=20,
                help_text='Seller application status'
            ),
        ),
        
        # Step 4: Remove old is_approved field
        migrations.RemoveField(
            model_name='seller',
            name='is_approved',
        ),
        
        # Step 5: Update Meta options
        migrations.AlterModelOptions(
            name='seller',
            options={'ordering': ['-created_at'], 'verbose_name': 'Seller', 'verbose_name_plural': 'Sellers'},
        ),
    ]

