import './HackathonCard.css';

function formatDate(dateStr) {
  const d = new Date(dateStr);
  return d.toLocaleDateString('ru-RU', { day: 'numeric', month: 'long', year: 'numeric' });
}

function getGoogleCalendarUrl(hackathon) {
  const start = new Date(hackathon.date);
  start.setHours(10, 0, 0, 0);
  const end = new Date(hackathon.date);
  end.setHours(22, 0, 0, 0);
  const format = (d) => d.toISOString().replace(/[-:]/g, '').slice(0, 15);
  const params = new URLSearchParams({
    action: 'TEMPLATE',
    text: hackathon.name,
    dates: `${format(start)}/${format(end)}`,
    details: hackathon.description || '',
  });
  return `https://calendar.google.com/calendar/render?${params.toString()}`;
}

export default function HackathonCard({ hackathon }) {
  const calendarUrl = getGoogleCalendarUrl(hackathon);

  return (
    <div className="hackathon-card">
      <h3 className="hackathon-card-title">{hackathon.name}</h3>
      <p className="hackathon-card-date">{formatDate(hackathon.date)}</p>
      <p className="hackathon-card-meta">
        {hackathon.online ? 'Онлайн' : hackathon.location} · Дедлайн: {formatDate(hackathon.deadline)}
      </p>
      {hackathon.description && (
        <p className="hackathon-card-desc">{hackathon.description}</p>
      )}
      <div className="hackathon-card-actions">
        <a
          href={calendarUrl}
          target="_blank"
          rel="noopener noreferrer"
          className="hackathon-card-calendar-btn"
        >
          Добавить в календарь
        </a>
        {hackathon.url && (
          <a href={hackathon.url} target="_blank" rel="noopener noreferrer" className="hackathon-card-link">
            Сайт
          </a>
        )}
      </div>
    </div>
  );
}
