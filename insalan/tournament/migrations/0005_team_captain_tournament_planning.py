# Generated by Django 4.1.12 on 2024-01-19 22:34

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('tournament', '0004_alter_caster_image_alter_event_logo_and_more'),
    ]

    operations = [
        migrations.AddField(
            model_name='team',
            name='captain',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='team_captain', to='tournament.player', verbose_name='Capitaine'),
        ),
        migrations.AddField(
            model_name='tournament',
            name='planning',
            field=models.CharField(blank=True, default='', max_length=300, verbose_name='Nom du content du planning du tournoi'),
        ),
    ]
