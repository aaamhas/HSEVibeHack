import './HackathonCard.css';

function formatDate(dateStr) {
  if (!dateStr) return '—';
  const d = new Date(dateStr);
  return d.toLocaleDateString('ru-RU', { day: 'numeric', month: 'long', year: 'numeric' });
}

function formatLabel(format) {
  const labels = { online: 'Онлайн', offline: 'Офлайн', hybrid: 'Гибрид' };
  return labels[format] || format || '';
}

function getGoogleCalendarUrl(h) {
  const start = h.start_date ? new Date(h.start_date) : new Date();
  const end = h.end_date ? new Date(h.end_date) : new Date(start.getTime() + 12 * 3600000);
  const fmt = (d) => d.toISOString().replace(/[-:]/g, '').slice(0, 15);
  const params = new URLSearchParams({
    action: 'TEMPLATE',
    text: h.title,
    dates: `${fmt(start)}/${fmt(end)}`,
    details: h.description || '',
    location: h.location || '',
  });
  return `https://calendar.google.com/calendar/render?${params.toString()}`;
}

export default function HackathonCard({ hackathon: h }) {
  const calendarUrl = getGoogleCalendarUrl(h);

  return (
    <div className="hackathon-card">
      <h3 className="hackathon-card-title">{h.title}</h3>

      <p className="hackathon-card-date">
        {formatDate(h.start_date)}
        {h.end_date && h.end_date !== h.start_date && ` — ${formatDate(h.end_date)}`}
      </p>

      <p className="hackathon-card-meta">
        {formatLabel(h.format)}
        {h.location && ` · ${h.location}`}
        {h.registration_deadline && ` · Дедлайн: ${formatDate(h.registration_deadline)}`}
      </p>

      {h.theme && <span className="hackathon-card-tag">{h.theme}</span>}
      {h.skill_level && h.skill_level !== 'any' && (
        <span className="hackathon-card-tag">{h.skill_level}</span>
      )}
      {h.prize && <span className="hackathon-card-tag">🏆 {h.prize}</span>}

      {h.technologies && h.technologies.length > 0 && (
        <div className="hackathon-card-techs">
          {h.technologies.map((t) => (
            <span key={t.id || t.name} className="hackathon-card-tech">{t.name}</span>
          ))}
        </div>
      )}

      {h.description && (
        <p className="hackathon-card-desc">{h.description}</p>
      )}

      <div className="hackathon-card-actions">
        <a href={calendarUrl} target="_blank" rel="noopener noreferrer" className="hackathon-card-calendar-btn">
          Добавить в календарь
        </a>
        {h.url && (
          <a href={h.url} target="_blank" rel="noopener noreferrer" className="hackathon-card-link">
            Подробнее
          </a>
        )}
      </div>
    </div>
  );
}
