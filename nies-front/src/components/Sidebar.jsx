export default function Sidebar({ groups, activeId, onSelect }) {
  return (
    <aside className="sidebar">
      <div className="sidebar-title">Categorias</div>
      <nav className="sidebar-list">
        {groups.map(g => {
          const active = String(g.id) === String(activeId);
          return (
            <button
              key={g.id}
              className={`sidebar-item ${active ? "active" : ""}`}
              onClick={() => onSelect(g.id)}
            >
              {/* icones ficariam aqui */}
              <div className="bullet" />
              <span>{g.name}</span>
            </button>
          );
        })}
      </nav>
    </aside>
  );
}
