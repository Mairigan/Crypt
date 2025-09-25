import React, { useState } from 'react';
import { Link, useLocation } from 'react-router-dom';
import '../styles/Header.css';

const Header = () => {
  const [isMenuOpen, setIsMenuOpen] = useState(false);
  const location = useLocation();

  const toggleMenu = () => {
    setIsMenuOpen(!isMenuOpen);
  };

  return (
    <header className="header">
      <div className="container header-content">
        <Link to="/" className="logo">
          <i className="fas fa-bullseye"></i>
          <span>SolSniper Pro</span>
        </Link>
        
        <button className="mobile-menu-toggle" onClick={toggleMenu}>
          <span></span>
          <span></span>
          <span></span>
        </button>
        
        <nav className={`nav ${isMenuOpen ? 'nav-open' : ''}`}>
          <ul>
            <li><Link to="/" className={location.pathname === '/' ? 'active' : ''}>Home</Link></li>
            <li><Link to="/features" className={location.pathname === '/features' ? 'active' : ''}>Features</Link></li>
            <li><Link to="/how-it-works" className={location.pathname === '/how-it-works' ? 'active' : ''}>How It Works</Link></li>
            <li><Link to="/community" className={location.pathname === '/community' ? 'active' : ''}>Community</Link></li>
            <li><Link to="/contact" className={location.pathname === '/contact' ? 'active' : ''}>Contact</Link></li>
          </ul>
        </nav>
        
        <a href="https://t.me/Raydi_Bot" className="cta-button">
          <i className="fab fa-telegram"></i> Start Sniping
        </a>
      </div>
    </header>
  );
};

export default Header;
