from celery import shared_task
from database.models import ActivationTokenModel
from database.session import SyncSessionLocal
from sqlalchemy import delete


@shared_task
def delete_activation_token(token: str):
    with SyncSessionLocal() as session:
        session.execute(
            delete(ActivationTokenModel)
            .where(ActivationTokenModel.token == token)
        )
        session.commit()
