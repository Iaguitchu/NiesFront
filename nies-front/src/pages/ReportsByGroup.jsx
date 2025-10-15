import { useParams, useNavigate } from "react-router-dom";
import { useEffect, useMemo, useState } from "react";
import { api } from "@/services/api";
import Sidebar from "@/components/Sidebar";
import DashboardCard from "@/components/DashboardCard";

export default function ReportsByGroup() {
  const { groupId } = useParams();
  const navigate = useNavigate();

  const [groups, setGroups] = useState([]);
  const [items, setItems] = useState([]);
  const [erro, setErro] = useState(null);
  const [loading, setLoading] = useState(true);

  // carrega grupos para sidebar
  useEffect(() => {
    let cancel = false;
    (async () => {
      try {
        const r = await api.get("/api/powerbi/groups");
        if (!cancel) {
          setGroups(r.data);
          if (!groupId && r.data.length) navigate(`/${r.data[0].id}`, { replace: true });
        }
      } catch { /* silencioso */ }
    })();
    return () => { cancel = true; };
  }, [groupId, navigate]);

  // carrega dashboards do grupo
  useEffect(() => {
    if (!groupId) return;
    let cancel = false;
    (async () => {
      try {
        setLoading(true);
        setErro(null);
        // ajuste o nome do param conforme seu back (groupId vs group_id):
        const r = await api.get("/api/powerbi/reports", { params: { groupId } });
        if (!cancel) setItems(r.data);
      } catch (e) {
        if (!cancel) setErro(e?.response?.data || e.message);
      } finally {
        if (!cancel) setLoading(false);
      }
    })();
    return () => { cancel = true; };
  }, [groupId]);

  const activeGroup = useMemo(
    () => groups.find(g => String(g.id) === String(groupId)),
    [groups, groupId]
  );

  return (
    <div className="solucoes">
      <Sidebar
        groups={groups}
        activeId={groupId ? String(groupId) : null}
        onSelect={id => navigate(`/${id}`)}
      />

      <main className="solucoes-content">
        <header className="solucoes-head">
          <h1>{activeGroup ? activeGroup.name : "Soluções"}</h1>
          <p>Selecione um dashboard na lista abaixo.</p>
        </header>

        {loading && <div className="state">Carregando dashboards…</div>}
        {erro && <div className="state error">{String(erro)}</div>}
        {!loading && !erro && !items.length && <div className="state">Nenhum relatório neste grupo.</div>}

        <div className="grid">
          {items.map(item => (
            <DashboardCard
              key={item.id}
              title={item.name}
              thumbnailUrl={item.thumbnail_url}
              onClick={() => navigate(`/${groupId}/relatorios/${item.id}`)}
            />
          ))}
        </div>
      </main>
    </div>
  );
}
