export default function CategoryCard({ title, onClick, index = 0 }) {
  return (
    <button className="category-card reveal" style={{ animationDelay: `${index * 100}ms` }} onClick={onClick}>
      <div className="category-icon" aria-hidden />
      <span>{title}</span>
    </button>
  );
}
