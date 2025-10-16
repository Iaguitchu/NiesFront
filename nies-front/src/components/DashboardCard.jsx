export default function DashboardCard({ title, description, thumbnailUrl, onClick, index = 0 }) {
  return (
      <div className="dashboard-card reveal" style={{ animationDelay: `${index * 100}ms` }} onClick={onClick}role="button"
          tabIndex={0}>
      <div className="dash-thumb">
        {thumbnailUrl ? <img src={thumbnailUrl} alt={title} /> : <div className="thumb-empty" />}
      </div>
      <div className="dash-info">
        <h3>{title}</h3>
      </div>
    </div>
  );
}
