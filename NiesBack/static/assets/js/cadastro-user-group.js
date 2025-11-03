  const API_BASE = window.location.origin + "/";

  function getCheckedReportIds() {
    return Array.from(document.querySelectorAll('input[name="report"]:checked'))
      .map(i => i.value);
  }

  // SUBMIT do cadastro de grupo
  const form = document.getElementById("createGroupForm");
  form.addEventListener("submit", async (e) => {
    e.preventDefault();

    const name = document.getElementById("exampleInputUsername1").value.trim();
    const description = document.getElementById("exampleTextarea1").value.trim();
    const report_ids = getCheckedReportIds();

    if (!name) {
      alert("Informe o nome do grupo.");
      return;
    }

    const payload = {
      name,
      description: description || null,
      report_ids
    };

    try {
      const resp = await fetch(`${API_BASE}user-groups`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        credentials: "include",
        body: JSON.stringify(payload),
      });

      if (resp.status === 409) {
        const err = await resp.json().catch(() => ({}));
        alert(err.detail || "Já existe um grupo com esse nome.");
        return;
      }
      if (!resp.ok) {
        const err = await resp.json().catch(() => ({}));
        throw new Error(err.detail || "Erro ao criar o grupo.");
      }

      // se o response_model não tem id, você pode nem usar o body
      // const data = await resp.json();

      alert("Grupo criado com sucesso!");
      // recarrega a página pra refletir o novo grupo
      setTimeout(() => window.location.reload(), 150);

    } catch (err) {
      console.error(err);
      alert(err.message);
    }
  });