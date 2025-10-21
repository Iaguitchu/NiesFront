import { Routes, Route, NavLink } from "react-router-dom";
import Groups from "./pages/Groups";
import ReportsByGroup from "./pages/ReportsByGroup";
import ReportView from "./pages/ReportView";
import './App.css';
export default function App() {
  return (
    <div className="app">
      <header className="topbar">
        <div className="brand"><span className="logo-dot" /> <NavLink to="/" end>Logo</NavLink></div>
        <nav className="menu">
          <NavLink to="/" end>Home</NavLink>
        </nav>
      </header>

      <Routes>
        <Route path="/" element={<Groups />} />
        <Route path="/:groupId" element={<ReportsByGroup />} />
        <Route path="/:groupId/relatorios/:reportId" element={<ReportView />} />
      </Routes>
    </div>
  );
}
