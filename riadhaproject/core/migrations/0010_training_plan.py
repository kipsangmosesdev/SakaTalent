import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0009_performance_supporting_document'),
    ]

    operations = [
        migrations.CreateModel(
            name='TrainingPlan',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('championship_date', models.DateField()),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('athlete', models.OneToOneField(on_delete=django.db.models.deletion.CASCADE, related_name='training_plan', to='core.athleteprofile')),
            ],
        ),
        migrations.CreateModel(
            name='TrainingTarget',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('target_result', models.DecimalField(decimal_places=2, max_digits=10)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('event', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='training_targets', to='core.event')),
                ('plan', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='targets', to='core.trainingplan')),
            ],
            options={
                'ordering': ('event__name',),
                'constraints': [models.UniqueConstraint(fields=('plan', 'event'), name='unique_training_target_per_event')],
            },
        ),
        migrations.CreateModel(
            name='TrainingResult',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('training_date', models.DateField()),
                ('result', models.DecimalField(decimal_places=2, max_digits=10)),
                ('notes', models.CharField(blank=True, max_length=240)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('target', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='training_results', to='core.trainingtarget')),
            ],
            options={
                'ordering': ('-training_date', '-created_at'),
            },
        ),
    ]
