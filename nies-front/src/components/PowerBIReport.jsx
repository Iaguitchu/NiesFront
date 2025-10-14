import { useEffect, useRef } from "react";
import * as pbi from "powerbi-client";
import { models } from "powerbi-client";

export default function PowerBIReport({ embedUrl, reportId, accessToken, height="80vh" }) {
  const ref = useRef(null);

  useEffect(() => {
    if (!ref.current || !embedUrl || !accessToken) return; // se não tiver embedUrl ou accessToken, não faz nada

    // Cria a instância do serviço do SDK powerbi-client
    const service = new pbi.service.Service(
      pbi.factories.hpmFactory,
      pbi.factories.wpmpFactory,
      pbi.factories.routerFactory
    );

    service.reset(ref.current);
    service.embed(ref.current, {
      type: "report",
      id: reportId,
      embedUrl,
      accessToken,
      tokenType: models.TokenType.Embed,
      settings: {
        panes: { filters: { visible: false } }, // oculta o painel de filtros lateral
        navContentPaneEnabled: true // mantém a navegação de abas/páginas do relatório visível.
      }
    });
  }, [embedUrl, reportId, accessToken]);

  return <div ref={ref} style={{ height, width: "100%", borderRadius: 8, overflow: "hidden", background: "#f3f4f6" }} />
}
