import { Link } from 'react-router-dom';
import './ProfilePage.css';

export default function ProfilePage() {
  return (
    <div className="profile-page">
      <header className="profile-page-header">
        <Link to="/" className="profile-page-back">hack<strong>Search</strong></Link>
        <span className="profile-page-title">User profile</span>
      </header>
      <main className="profile-page-main">
        <div className="profile-page-avatar" aria-hidden>
          <svg viewBox="0 0 24 24" fill="currentColor" className="profile-page-avatar-icon">
            <path d="M12 12c2.21 0 4-1.79 4-4s-1.79-4-4-4-4 1.79-4 4 1.79 4 4 4zm0 2c-2.67 0-8 1.34-8 4v2h16v-2c0-2.66-5.33-4-8-4z" />
          </svg>
        </div>
        <Link to="/" className="profile-page-link">На главную</Link>
      </main>
    </div>
  );
}
