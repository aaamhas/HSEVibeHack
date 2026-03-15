import { Link } from 'react-router-dom';
import './ChatHeader.css';

export default function ChatHeader() {
  return (
    <div className="chat-top">
      <Link to="/" className="chat-top-logo-link">
        <h1 className="chat-top-logo">hack<strong>Search</strong></h1>
      </Link>
      <Link
        to="/profile"
        className="chat-top-profile-btn"
        aria-label="Профиль"
      >
        <svg className="profile-icon" viewBox="0 0 24 24" fill="currentColor" aria-hidden>
          <path d="M12 12c2.21 0 4-1.79 4-4s-1.79-4-4-4-4 1.79-4 4 1.79 4 4 4zm0 2c-2.67 0-8 1.34-8 4v2h16v-2c0-2.66-5.33-4-8-4z" />
        </svg>
      </Link>
    </div>
  );
}
