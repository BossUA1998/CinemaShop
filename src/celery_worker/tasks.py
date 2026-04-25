from datetime import datetime, timezone
from celery import shared_task
from database.models import ActivationTokenModel
from database.session import SyncSessionLocal
from sqlalchemy import delete


@shared_task
def delete_activation_token():
    with SyncSessionLocal() as session:
        session.execute(
            delete(ActivationTokenModel)
            .where(ActivationTokenModel.expires_at < datetime.now(timezone.utc))
        )
        session.commit()
