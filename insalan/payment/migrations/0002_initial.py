# Generated by Django 4.1.12 on 2023-11-21 20:09

from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        ('tournament', '0001_initial'),
        ('payment', '0001_initial'),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.AddField(
            model_name='transaction',
            name='payer',
            field=models.ForeignKey(null=True, on_delete=django.db.models.deletion.SET_NULL, to=settings.AUTH_USER_MODEL, verbose_name='Utilisateur'),
        ),
        migrations.AddField(
            model_name='transaction',
            name='products',
            field=models.ManyToManyField(through='payment.ProductCount', to='payment.product'),
        ),
        migrations.AddField(
            model_name='productcount',
            name='product',
            field=models.ForeignKey(editable=False, null=True, on_delete=django.db.models.deletion.SET_NULL, to='payment.product', verbose_name='Produit'),
        ),
        migrations.AddField(
            model_name='productcount',
            name='transaction',
            field=models.ForeignKey(editable=False, on_delete=django.db.models.deletion.CASCADE, to='payment.transaction', verbose_name='Transaction'),
        ),
        migrations.AddField(
            model_name='product',
            name='associated_tournament',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, to='tournament.tournament', verbose_name='Tournoi associé'),
        ),
        migrations.AddField(
            model_name='payment',
            name='transaction',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='payment.transaction', verbose_name='Transaction'),
        ),
        migrations.AddConstraint(
            model_name='productcount',
            constraint=models.UniqueConstraint(fields=('transaction', 'product'), name='product_count_m2m_through'),
        ),
    ]
