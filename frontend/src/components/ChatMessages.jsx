import HackathonCard from './HackathonCard';
import './ChatMessages.css';

export default function ChatMessages({ messages, onQuestionClick, loading }) {
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
              {msg.followUpQuestions && msg.followUpQuestions.length > 0 && (
                <div className="chat-follow-up">
                  <p className="chat-follow-up-label">Уточните запрос:</p>
                  <div className="chat-follow-up-btns">
                    {msg.followUpQuestions.map((q, i) => (
                      <button
                        key={i}
                        className="chat-follow-up-btn"
                        onClick={() => onQuestionClick?.(q)}
                      >
                        {q}
                      </button>
                    ))}
                  </div>
                </div>
              )}
            </>
          )}
        </div>
      ))}
      {loading && (
        <div className="chat-message chat-message--bot">
          <p className="chat-message-text chat-loading">Ищу хакатоны...</p>
        </div>
      )}
    </div>
  );
}
