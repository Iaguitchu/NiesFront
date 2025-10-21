import { useParams, useNavigate } from "react-router-dom";
import { useEffect, useState } from "react";
import { api } from "@/services/api";
import SidebarTree from "@/components/SidebarTree";
import DashboardCard from "@/components/DashboardCard";

export default function ReportsByGroup() {
  const { groupId } = useParams();
  const navigate = useNavigate();

  const [tree, setTree] = useState([]);
  const [items, setItems] = useState([]);
  const [erro, setErro] = useState(null);
  const [loading, setLoading] = useState(true);

  // carrega ÁRVORE para a sidebar (1x)
  useEffect(() => {
    let cancel = false;
    (async () => {
      try {
        const { data } = await api.get("/api/powerbi/groups", { params: { tree: true } });
        // se o efeito não foi cancelado, atualiza o estado. Usa data ou array vazio
        if (!cancel) setTree(data || []);
      } catch (e) {
        if (!cancel) console.error(e);
      }
    })();
    return () => { cancel = true; };
  }, []);
  

  // carrega relatórios do grupo (back já traz descendentes ao passar o groupId do pai)
  useEffect(() => {
    if (!groupId) return;
    let cancel = false;
    (async () => {
      try {
        setLoading(true);
        setErro(null);
        const { data } = await api.get("/api/powerbi/reports", { params: { groupId } });
        if (!cancel) setItems(data || []);
      } catch (e) {
        if (!cancel) setErro(e?.response?.data || e.message);
      } finally {
        if (!cancel) setLoading(false);
      }
    })();
    return () => { cancel = true; };
  }, [groupId]);

  return (
    <div className="solucoes">
      <SidebarTree
        tree={tree}
        activeId={groupId ? String(groupId) : null}
        onSelect={(id) => navigate(`/${id}`)} // clicar no rótulo navega
      />

      <main className="solucoes-content">
        <header className="solucoes-head">
          <h1 className="title-reports">Relatórios</h1>
        </header>

        {loading && <div className="state">Carregando dashboards…</div>}
        {erro && <div className="state error">{String(erro)}</div>}
        {!loading && !erro && !items.length && <div className="state">Nenhum relatório neste grupo.</div>}

        <div className="cards">
          {items.map((item, idx) => (
            <DashboardCard
  key={item.id}
  title={item.name}
  titleDescription={item.title_description ?? ""}
  description={item.description ?? "(sem descrição)"}
  imageUrl={item.image_url}          // ou item.img64
  thumbnailUrl={item.thumbnail_url}  // fallback se não tiver imageUrl
  index={idx}
  onClick={() => navigate(`/${groupId}/relatorios/${item.id}`)}
/>
          ))}
        </div>
      </main>
    </div>
  );
}
