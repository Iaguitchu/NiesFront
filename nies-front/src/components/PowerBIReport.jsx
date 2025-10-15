import { useEffect, useRef } from "react";
import * as pbi from "powerbi-client";
import { models } from "powerbi-client";

export default function PowerBIReport({ embedUrl, reportId, accessToken, height = "100vh" }) {
  const ref = useRef(null);

  useEffect(() => {
    if (!ref.current || !embedUrl || !accessToken) return;

    const service = new pbi.service.Service(
      pbi.factories.hpmFactory,
      pbi.factories.wpmpFactory,
      pbi.factories.routerFactory
    );

    service.reset(ref.current);

    const report = service.embed(ref.current, {
      type: "report",
      id: reportId,
      embedUrl,
      accessToken,
      tokenType: models.TokenType.Embed,
      settings: {
        panes: { filters: { visible: false } },
        navContentPaneEnabled: true,
        layoutType: models.LayoutType.Custom,
        customLayout: {
          displayOption: models.DisplayOption.FitToPage, 
          // ou models.DisplayOption.FitToWidt
        }
      }
    });
  }, [embedUrl, reportId, accessToken]);

  return (
    <div
      ref={ref}
      style={{
        height,
        width: "100%",
        borderRadius: 8,
        overflow: "hidden",
        background: "#f3f4f6",
      }}
    />
  );
}
