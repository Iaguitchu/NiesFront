export default function CategoryCard({ title, onClick }) {
  return (
    <button className="category-card" onClick={onClick}>
      <div className="category-icon" aria-hidden />
      <span>{title}</span>
    </button>
  );
}
