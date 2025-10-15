import { useEffect, useState } from "react";
import { useNavigate } from "react-router-dom";
import { api } from "@/services/api";
import CategoryCard from "@/components/CategoryCard";

export default function Groups() {
  const [groups, setGroups] = useState([]);
  const [q, setQ] = useState("");
  const [erro, setErro] = useState(null);
  const [loading, setLoading] = useState(true);
  const navigate = useNavigate();

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

  const filtered = q.trim()
    ? groups.filter(g => g.name.toLowerCase().includes(q.toLowerCase()))
    : groups;

  return (
    <main className="home">
      <section className="hero">
        <h1>O que você deseja saber sobre saúde?</h1>
        <div className="search">
          <input
            value={q}
            onChange={e => setQ(e.target.value)}
            placeholder="Busque por uma categoria…"
          />
        </div>
      </section>

      <section className="categories">
        <h2>Categorias de produtos</h2>
        {loading && <div className="state">Carregando…</div>}
        {erro && <div className="state error">{String(erro)}</div>}

        <div className="categories-row">
          {filtered.map(g => (
            <CategoryCard
              key={g.id}
              title={g.name}
              onClick={() => navigate(`/${g.id}`)}
            />
          ))}
        </div>
      </section>
    </main>
  );
}
