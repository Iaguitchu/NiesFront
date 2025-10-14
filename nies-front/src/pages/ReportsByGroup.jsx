import { useParams, Link } from "react-router-dom";
import { useEffect, useState } from "react";
import { api } from "@/services/api";

export default function ReportsByGroup() {
  const { groupId } = useParams();
  const [items, setItems] = useState([]);
  const [erro, setErro] = useState(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    let cancel = false;
    (async () => {
      try {
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

  if (erro) return <p style={{color:"crimson"}}>Erro: {String(erro)}</p>;
  if (loading) return <p>Carregando relatórios…</p>;
  if (!items.length) return <p>Nenhum relatório neste grupo.</p>;

  return (
    <div>
      <h1>Relatórios</h1>
      <ul style={{ lineHeight: "2rem" }}>
        {items.map(item => (
          <li key={item.id}>
            <Link to={`/grupos/${groupId}/relatorios/${item.id}`}>{item.name}</Link>
          </li>
        ))}
      </ul>
    </div>
  );
}
