# Generated by Django 4.1.12 on 2023-11-21 20:09

from django.db import migrations, models
import django.utils.timezone
import uuid


class Migration(migrations.Migration):

    initial = True

    dependencies = [
    ]

    operations = [
        migrations.CreateModel(
            name='Payment',
            fields=[
                ('id', models.IntegerField(editable=False, primary_key=True, serialize=False, verbose_name='Identifiant du paiement')),
                ('amount', models.DecimalField(decimal_places=2, max_digits=6, verbose_name='Montant')),
            ],
            options={
                'verbose_name': 'Paiement',
                'verbose_name_plural': 'Paiements',
            },
        ),
        migrations.CreateModel(
            name='Product',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('price', models.DecimalField(decimal_places=2, max_digits=5, verbose_name='prix')),
                ('name', models.CharField(max_length=50, verbose_name='intitulé')),
                ('desc', models.CharField(max_length=50, verbose_name='description')),
                ('category', models.CharField(choices=[('PLAYER_REG', 'Inscription joueur⋅euse'), ('MANAGER_REG', 'Inscription manager'), ('PIZZA', 'Pizza')], default='PIZZA', max_length=20, verbose_name='Catégorie de produit')),
                ('available_from', models.DateTimeField(blank=True, default=django.utils.timezone.now, verbose_name='Disponible à partir de')),
                ('available_until', models.DateTimeField(verbose_name="Disponible jusqu'à")),
            ],
        ),
        migrations.CreateModel(
            name='ProductCount',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('count', models.IntegerField(default=1, verbose_name='Quantité')),
            ],
            options={
                'verbose_name': "Quantité d'un produit",
                'verbose_name_plural': 'Quantités de produits',
            },
        ),
        migrations.CreateModel(
            name='Transaction',
            fields=[
                ('id', models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ('payment_status', models.CharField(blank=True, choices=[('FAILED', 'échouée'), ('SUCCEEDED', 'Réussie'), ('PENDING', 'En attente'), ('REFUNDED', 'Remboursé')], default='PENDING', max_length=10, verbose_name='État de la Transaction')),
                ('creation_date', models.DateTimeField(verbose_name='Date de creation')),
                ('last_modification_date', models.DateTimeField(verbose_name='Date de dernière modification')),
                ('intent_id', models.IntegerField(editable=False, null=True, verbose_name='Identifiant du formulaire de paiement')),
                ('order_id', models.IntegerField(editable=False, null=True, verbose_name='Identifiant de commande')),
                ('amount', models.DecimalField(decimal_places=2, default=0.0, max_digits=5, verbose_name='Montant')),
            ],
            options={
                'ordering': ['-last_modification_date'],
            },
        ),
    ]
