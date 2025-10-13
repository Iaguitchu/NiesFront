import { useState, useEffect } from 'react';
import CategoryCard from '../components/CategoryCard';
import './Home.css';

const GRUPO = [
{ title: 'Assistência Farmacêutica', to: '/assistencia', icon: '💊' },
{ title: 'Atenção Primária', to: '/atencao', icon: '🏥' },
{ title: 'Gestão', to: '/gestao', icon: '📊' },
{ title: 'Indicadores', to: '/indicadores', icon: '📈' },
{ title: 'Redes', to: '/redes', icon: '🕸️' },
{ title: 'Vigilância', to: '/vigilancia', icon: '🔎' },
];


function Home() {


// Exemplo de como usar o skeleton
const [loading, setLoading] = useState(false); //true




// useEffect(() => {
// const t = setTimeout(() => setLoading(false));
// return () => clearTimeout(t);
// }, []);


return (
<div>
    <div className="hero">
        <h1>O que você deseja saber sobre saúde?</h1>
        <input type="text" placeholder="Buscar..." />
    </div>

    <div className="categories">
        {(loading ? Array.from({ length: 6 }) : GRUPO).map((item, idx) => (
            <CategoryCard key={idx} loading={loading} to={item?.to || '#'} title={item?.title || ''} icon={item?.icon} />))}
    </div>
</div>
);
}
export default Home