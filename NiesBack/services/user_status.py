from datetime import date
from sqlalchemy.orm import Session
from models.models_rbac import User, UserStatus

def enforce_validity_window(db: Session, user: User) -> None:
    today = date.today()

    # 1) Se tem janela (valid_from/valid_to), verifica se hoje está dentro.
    inside_window = True
    if user.valid_from and today < user.valid_from:
        inside_window = False
    if user.valid_to and today > user.valid_to:
        inside_window = False

    # 2) Se usuário está pending mas a data já permite, promove para approved
    if user.status == UserStatus.pending and inside_window:
        user.status = UserStatus.approved
        db.add(user)
        db.commit()
        db.refresh(user)
