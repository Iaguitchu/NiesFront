import { BrowserRouter, Routes, Route } from 'react-router-dom';
import Home from './pages/Home';
import Header from './components/Header';
import Assistencia from './pages/categorias/Assistencia';


export default function App() {
return (
<BrowserRouter>
<Header />
<Routes>
<Route path="/" element={<Home />} />
<Route path="/assistencia" element={<Assistencia />} />
{/* outras rotas */}
</Routes>
</BrowserRouter>
);
}