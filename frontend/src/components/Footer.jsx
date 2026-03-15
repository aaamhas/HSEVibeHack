import './Footer.css';

export default function Footer() {
  return (
    <footer className="footer">
      <div className="footer-logo-wrap">
        <img src="/logo.png" alt="HSE Hack Club" className="footer-logo-img" />
      </div>
      <nav className="footer-links">
        <div className="footer-col">
          <a href="#help">Помощь</a>
          <a href="#contacts">Контакты</a>
          <a href="#blog">Блог</a>
          <a href="#about">О нас</a>
        </div>
        <div className="footer-col">
          <span className="footer-social-label">Мы в соц. сетях:</span>
        </div>
      </nav>
    </footer>
  );
}
