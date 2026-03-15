import './UserProfilePanel.css';

export default function UserProfilePanel() {
  return (
    <aside className="user-profile-panel" tabIndex={-1}>
      <h2 className="user-profile-title">User profile</h2>
      <div className="user-profile-content">
        <div className="user-profile-avatar" aria-hidden>
          <svg viewBox="0 0 24 24" fill="currentColor" className="user-profile-avatar-icon">
            <path d="M12 12c2.21 0 4-1.79 4-4s-1.79-4-4-4-4 1.79-4 4 1.79 4 4 4zm0 2c-2.67 0-8 1.34-8 4v2h16v-2c0-2.66-5.33-4-8-4z" />
          </svg>
        </div>
      </div>
    </aside>
  );
}
