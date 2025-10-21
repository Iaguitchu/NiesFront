export default function DashboardCard({
  title,
  titleDescription,
  description,
  imageUrl,
  thumbnailUrl,
  onClick,
}) {
  const bg = imageUrl || thumbnailUrl || ""; // ordem de preferência

  return (
    <div className="dc-card" role="button" tabIndex={0}
         onClick={onClick}
         onKeyDown={(e) => (e.key === "Enter" || e.key === " ") && onClick()}>
      {/* imagem de fundo */}
      <div
        className="dc-bg"
        style={{ backgroundImage: bg ? `url(${bg})` : undefined }}
        aria-hidden
      />

      {/* gradiente e conteúdo em hover */}
      <div className="dc-overlay">
        <h3 className="dc-title">{titleDescription || title}</h3>
        {description && <p className="dc-desc">{description}</p>}
      </div>
    </div>
  );
}
