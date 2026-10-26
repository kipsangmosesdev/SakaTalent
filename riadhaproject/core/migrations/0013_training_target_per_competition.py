from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0012_trainingtarget_competition_date_and_more'),
    ]

    operations = [
        migrations.RemoveConstraint(
            model_name='trainingtarget',
            name='unique_training_target_per_event',
        ),
        migrations.AddConstraint(
            model_name='trainingtarget',
            constraint=models.UniqueConstraint(
                fields=('plan', 'event', 'competition_date'),
                name='unique_training_target_per_event_date',
            ),
        ),
    ]
