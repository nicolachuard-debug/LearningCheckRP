import React from 'react';
import './Header.css';

const Header = ({ title = 'Verifica le tue conoscenze', subtitle = '' }) => {
  return (
    <header className="app-header">
      <h1>{title}</h1>
      {subtitle && <p className="app-header__subtitle">{subtitle}</p>}
    </header>
  );
};

export default Header;
