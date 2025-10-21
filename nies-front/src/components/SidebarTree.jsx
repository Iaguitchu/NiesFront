import { useMemo, useState, useEffect } from "react";

/** verifica se um id está dentro da subárvore de "node" */
function containsId(node, id) {
  if (!id) return false;
  if (String(node.id) === String(id)) return true;
  return (node.children || []).some((c) => containsId(c, id));
}

function Node({ node, level = 0, activeId, onSelect }) {
  // abre por padrão se o nó for o ativo OU se contiver o ativo na subárvore
  const defaultOpen = useMemo(() => containsId(node, activeId), [node, activeId]);
  const [open, setOpen] = useState(defaultOpen);

  // se o activeId mudar (navegação), mantenha coerente com o caminho atual
  useEffect(() => setOpen(containsId(node, activeId)), [node, activeId]);

  const hasChildren = node.children && node.children.length > 0;
  const isActive = String(node.id) === String(activeId);

  return (
    <div className="st-node">
      <div
        className={`st-row ${isActive ? "st-active" : ""}`}
        style={{ paddingLeft: 12 + level * 14 }}
        onClick={() => onSelect(node.id)} // clicar no rótulo navega (mostra relatórios do pai)
        role="button"
        tabIndex={0}
        onKeyDown={(e) => (e.key === "Enter" || e.key === " ") && onSelect(node.id)}
      >
        {/* se tem filho mostra a seta */}
        {hasChildren ? (
          <button className={`st-chevron ${open ? "open" : ""}`}
          aria-expanded={open}  
           onClick={(e) => { e.stopPropagation(); setOpen(v => !v);}}> ▶ </button>
          
        ) : (
          <span className="st-bullet">•</span>)}

        <span className="st-label">{node.name}</span>
      </div>

      
      {hasChildren && open && (
        <div className="st-children">
          {node.children.map((child) => (
            <Node
              key={child.id}
              node={child}
              level={level + 1}
              activeId={activeId}
              onSelect={onSelect}
            />
          ))}
        </div>
      )}
    </div>
  );
}

export default function SidebarTree({ tree = [], activeId, onSelect }) {
  return (
    <aside className="st-aside">
      <div className="st-title">Categorias</div>
      <nav className="st-list">
        {tree.map((root) => (
          <Node
            key={root.id}
            node={root}
            level={0}
            activeId={activeId}
            onSelect={onSelect}
          />
        ))}
      </nav>
    </aside>
  );
}
