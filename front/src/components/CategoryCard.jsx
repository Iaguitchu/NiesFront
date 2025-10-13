import { Link } from 'react-router-dom';
import './card.css';



function CategoryCard({ to, title, icon, loading }) {
if (loading) return <div className="card skeleton" />;


return (
<Link to={to} className="card">
<div className="icon">{icon}</div>
<div className="title">{title}</div>
</Link>
);
}

export default CategoryCard