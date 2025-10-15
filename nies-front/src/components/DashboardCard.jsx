export default function DashboardCard({ title, thumbnailUrl, onClick }) {
  return (
    <div className="dashboard-card" onClick={onClick} role="button" tabIndex={0}>
      <div className="dash-thumb">
        {thumbnailUrl ? <img src={thumbnailUrl} alt={title} /> : <div className="thumb-empty" />}
      </div>
      <div className="dash-info">
        <h3>{title}</h3>
      </div>
    </div>
  );
}
