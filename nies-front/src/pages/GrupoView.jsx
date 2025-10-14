import { useParams } from "react-router-dom";
import { useEffect, useState } from "react";
import { api } from "@/services/api";
import PowerBIReport from "@/components/PowerBIReport";

export default function GrupoView() {
  const { groupId } = useParams();
  const [info, setInfo] = useState(null);
  const [erro, setErro] = useState(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    let cancel = false;
    (async () => {
      try {
        setLoading(true);
        const r = await api.get("/api/powerbi/embed-info", { params: { groupId } });
        if (!cancel) setInfo(r.data);
      } catch (e) {
        if (!cancel) setErro(e?.response?.data || e.message);
      } finally {
        if (!cancel) setLoading(false);
      }
    })();
    return () => { cancel = true; };
  }, [groupId]);

  if (erro) return <p style={{color:"crimson"}}>Erro: {String(erro)}</p>;
  if (loading) return <p>Carregando relatório…</p>;
  if (!info) return <p>Não foi possível carregar o embed.</p>;

  return (
    <div>
      <h1>Relatório</h1>
      <PowerBIReport
        embedUrl={info.embedUrl}
        reportId={info.reportId}
        accessToken={info.accessToken}
      />
    </div>
  );
}
