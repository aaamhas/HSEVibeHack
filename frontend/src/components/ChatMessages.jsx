import HackathonCard from './HackathonCard';
import './ChatMessages.css';

export default function ChatMessages({ messages }) {
  return (
    <div className="chat-messages">
      {messages.map((msg) => (
        <div key={msg.id} className={`chat-message chat-message--${msg.role}`}>
          {msg.role === 'user' && <p className="chat-message-text">{msg.text}</p>}
          {msg.role === 'bot' && (
            <>
              {msg.text && <p className="chat-message-text">{msg.text}</p>}
              {msg.hackathons && msg.hackathons.length > 0 && (
                <div className="chat-message-cards">
                  {msg.hackathons.map((h) => (
                    <HackathonCard key={h.id} hackathon={h} />
                  ))}
                </div>
              )}
            </>
          )}
        </div>
      ))}
    </div>
  );
}
