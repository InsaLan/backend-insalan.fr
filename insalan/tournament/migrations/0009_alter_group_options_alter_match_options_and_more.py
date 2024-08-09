# Generated by Django 4.1.12 on 2024-03-18 15:53

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('tournament', '0008_group_match_swissround_game_team_per_match_and_more'),
    ]

    operations = [
        migrations.AlterModelOptions(
            name='group',
            options={'ordering': ['tournament', 'name'], 'verbose_name': 'Poule', 'verbose_name_plural': 'Poules'},
        ),
        migrations.AlterModelOptions(
            name='match',
            options={'ordering': ['round_number', 'index_in_round']},
        ),
        migrations.AddField(
            model_name='game',
            name='validators',
            field=models.CharField(choices=[('None', 'Pas de Validation de nom'), ('LoL', 'Validation League of Legends')], default='None', max_length=42, verbose_name='Validateurs de pseudo'),
        ),
        migrations.AddIndex(
            model_name='bracket',
            index=models.Index(fields=['tournament'], name='tournament__tournam_53161f_idx'),
        ),
        migrations.AddIndex(
            model_name='event',
            index=models.Index(fields=['name'], name='tournament__name_34212c_idx'),
        ),
        migrations.AddIndex(
            model_name='event',
            index=models.Index(fields=['year', 'month'], name='tournament__year_450f04_idx'),
        ),
        migrations.AddIndex(
            model_name='game',
            index=models.Index(fields=['name'], name='tournament__name_e36285_idx'),
        ),
        migrations.AddIndex(
            model_name='game',
            index=models.Index(fields=['short_name'], name='tournament__short_n_96ae17_idx'),
        ),
        migrations.AddIndex(
            model_name='group',
            index=models.Index(fields=['tournament'], name='tournament__tournam_51551a_idx'),
        ),
        migrations.AddIndex(
            model_name='match',
            index=models.Index(fields=['round_number'], name='tournament__round_n_ea1d43_idx'),
        ),
        migrations.AddIndex(
            model_name='match',
            index=models.Index(fields=['index_in_round'], name='tournament__index_i_c8cc2b_idx'),
        ),
        migrations.AddIndex(
            model_name='player',
            index=models.Index(fields=['user'], name='tournament__user_id_5fe5ae_idx'),
        ),
        migrations.AddIndex(
            model_name='player',
            index=models.Index(fields=['team'], name='tournament__team_id_984008_idx'),
        ),
        migrations.AddIndex(
            model_name='substitute',
            index=models.Index(fields=['team'], name='tournament__team_id_b37e33_idx'),
        ),
        migrations.AddIndex(
            model_name='substitute',
            index=models.Index(fields=['user'], name='tournament__user_id_3aa125_idx'),
        ),
        migrations.AddIndex(
            model_name='substitute',
            index=models.Index(fields=['payment_status'], name='tournament__payment_074383_idx'),
        ),
        migrations.AddIndex(
            model_name='swissround',
            index=models.Index(fields=['tournament'], name='tournament__tournam_39df4d_idx'),
        ),
        migrations.AddIndex(
            model_name='team',
            index=models.Index(fields=['tournament'], name='tournament__tournam_2e8d86_idx'),
        ),
        migrations.AddIndex(
            model_name='tournament',
            index=models.Index(fields=['event'], name='tournament__event_i_c84d86_idx'),
        ),
        migrations.AddIndex(
            model_name='tournament',
            index=models.Index(fields=['game'], name='tournament__game_id_557a46_idx'),
        ),
    ]