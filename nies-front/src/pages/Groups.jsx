import { useEffect, useState } from "react";
import { Link } from "react-router-dom";
import { api } from "@/services/api";

export default function Groups() {
  const [groups, setGroups] = useState([]);
  const [erro, setErro] = useState(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    let cancel = false;
    (async () => {  
      try {
        const r = await api.get("/api/powerbi/groups");
        if (!cancel) setGroups(r.data);
      } catch (e) {
        if (!cancel) setErro(e?.response?.data || e.message);
      } finally {
        if (!cancel) setLoading(false);
      }
    })();
    return () => { cancel = true; };
  }, []);

  if (erro) return <p style={{color:"crimson"}}>Erro: {String(erro)}</p>;
  if (loading) return <p>Carregando grupos…</p>;
  if (!groups.length) return <p>Nenhum grupo cadastrado.</p>;

  return (
    <div>
      <h1>Grupos</h1>
      <ul style={{ lineHeight: "2rem" }}>
        {groups.map(g => (
          <li key={g.id}>
            <Link to={`/grupos/${g.id}`}>{g.name}</Link>
          </li>
        ))}
      </ul>
    </div>
  );
}
