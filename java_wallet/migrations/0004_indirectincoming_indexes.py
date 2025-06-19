from django.db import migrations, models

class Migration(migrations.Migration):
    dependencies = [
        ("java_wallet", "0003_rename_indirecincoming_indirectincoming"),
    ]

    operations = [
        migrations.AddIndex(
            model_name="IndirectIncoming",
            index=models.Index(fields=["account_id"], name="indirect_incoming_id_index"),
        ),
        migrations.AddIndex(
            model_name="IndirectIncoming",
            index=models.Index(fields=["transaction_id"], name="indirect_incoming_tx_idx"),
        ),
    ]