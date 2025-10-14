import { useParams } from "react-router-dom";
import { useEffect, useState } from "react";
import { api } from "@/services/api";
import PowerBIReport from "@/components/PowerBIReport";

export default function ReportView() {
  const { reportId } = useParams();
  const [info, setInfo] = useState(null);
  const [erro, setErro] = useState(null);

  useEffect(() => {
    let cancel = false;
    (async () => {
      try {
        const r = await api.get("/api/powerbi/embed-info", { params: { reportId } });
        if (!cancel) setInfo(r.data);
      } catch (e) {
        if (!cancel) setErro(e?.response?.data || e.message);
      }
    })();
    return () => { cancel = true; };
  }, [reportId]);

  if (erro) return <p style={{color:"crimson"}}>Erro: {String(erro)}</p>;
  if (!info) return <p>Carregando…</p>;

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
