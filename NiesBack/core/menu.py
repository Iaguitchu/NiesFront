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
        if g.parent_id is None:
            parents.append(item)
        else:
            kids[g.parent_id].append(item)


    parents.sort(key=lambda x: x["name"].lower())
    for v in kids.values():
        v.sort(key=lambda x: x["name"].lower())

    resultado = []
    for p in parents:
        resultado.append({
            "id": p["id"],
            "name": p["name"],
            "children": kids.get(p["id"], []),  # pega filhos ou [] se não tiver
        })
    return resultado