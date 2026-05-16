from datetime import datetime, timezone
from celery import shared_task
from database.models import (
    ActivationTokenModel,
    RefreshTokenModel,
    PasswordResetTokenModel,
)
from database.session import SyncSessionLocal
from sqlalchemy import delete


@shared_task
def delete_expired_tokens():
    with SyncSessionLocal() as session:
        utc_now = datetime.now(timezone.utc)
        for table in (ActivationTokenModel, RefreshTokenModel, PasswordResetTokenModel):
            session.execute(delete(table).where(table.expires_at < utc_now))
        session.commit()
