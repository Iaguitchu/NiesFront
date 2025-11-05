from collections import defaultdict
from models.models import Group

def build_menu(db):
    rows = (
        db.query(Group.id, Group.name, Group.parent_id)
          .filter(Group.is_active.is_(True))
          .all()
    )
    parents, kids = [], defaultdict(list)
    for g in rows:
        item = {"id": g.id, "name": g.name}
        (parents if g.parent_id is None else kids[g.parent_id]).append(item)

    parents.sort(key=lambda x: x["name"].lower())
    for v in kids.values():
        v.sort(key=lambda x: x["name"].lower())

    return [{"id": p["id"], "name": p["name"], "children": kids.get(p["id"], [])}
            for p in parents]
