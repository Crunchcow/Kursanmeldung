from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('courses', '0003_registration_terms_accepted'),
    ]

    operations = [
        migrations.AddField(
            model_name='registration',
            name='iban',
            field=models.CharField(default='', max_length=34, verbose_name='IBAN'),
            preserve_default=False,
        ),
        migrations.AddField(
            model_name='registration',
            name='bic',
            field=models.CharField(blank=True, max_length=11, verbose_name='BIC'),
        ),
        migrations.AddField(
            model_name='registration',
            name='account_holder',
            field=models.CharField(default='', max_length=200, verbose_name='Kontoinhaber'),
            preserve_default=False,
        ),
    ]
