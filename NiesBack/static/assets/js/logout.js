document.addEventListener("click", (e) => {
  const a = e.target.closest('a[data-action="logout"]');
  if (!a) return;

  e.preventDefault();

  fetch("/auth/logout", {
    method: "POST",
    credentials: "include", // garante envio de cookies se necessário
  })
  .finally(() => {
    // limpa qualquer token que tenha guardado
    localStorage.removeItem("access_token");
    localStorage.removeItem("refresh_token");
    // manda pra tela de login
    window.location.href = "/";
  });
});