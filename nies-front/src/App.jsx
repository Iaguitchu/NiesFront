import { Routes, Route, Link, NavLink } from 'react-router-dom'
import Home from './pages/Home'
import Groups from './pages/Groups'
import GrupoView from './pages/GrupoView'

export default function App() {
  return (
    <div style={{ padding: 16 }}>
      <header style={{ display: 'flex', gap: 16, marginBottom: 16 }}>
        <NavLink to="/" end>Home</NavLink>
        <NavLink to="/grupos">Grupos</NavLink>
      </header>

      <Routes>
        <Route path="/" element={<Home />} />
        <Route path="/grupos" element={<Groups />} />
        <Route path="/grupos/:groupId" element={<GrupoView />} />
      </Routes>
    </div>
  )
}
