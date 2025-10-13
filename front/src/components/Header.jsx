import { Link, NavLink } from 'react-router-dom';
import './Header.css';


 function Header() {
return (
<header className="header">
<div className="logo">Inovação Saúde</div>
<nav>
<NavLink to="/">Home</NavLink>
<NavLink to="/solucoes">Soluções</NavLink>
</nav>
</header>
);
}

export default Header

