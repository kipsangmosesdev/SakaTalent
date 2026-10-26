from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0013_training_target_per_competition'),
    ]

    operations = [
        migrations.AddField(
            model_name='trainingresult',
            name='session_type',
            field=models.CharField(
                choices=[
                    ('event_test', 'Full-event time trial'),
                    ('speed', 'Acceleration / top speed'),
                    ('speed_endurance', 'Speed endurance'),
                    ('intervals', 'Intervals'),
                    ('tempo', 'Tempo / steady run'),
                    ('easy', 'Easy / recovery'),
                    ('technique', 'Technique / event drills'),
                    ('strength', 'Strength / conditioning'),
                    ('other', 'Other session'),
                ],
                default='event_test',
                max_length=20,
            ),
        ),
        migrations.AlterField(
            model_name='trainingresult',
            name='result',
            field=models.DecimalField(blank=True, decimal_places=2, max_digits=10, null=True),
        ),
        migrations.AlterField(
            model_name='trainingresult',
            name='notes',
            field=models.TextField(blank=True),
        ),
    ]
