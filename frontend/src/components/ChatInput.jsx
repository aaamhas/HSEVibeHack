import { useState } from 'react';
import './ChatInput.css';

export default function ChatInput({ onSend, disabled }) {
  const [value, setValue] = useState('');

  const handleSubmit = (e) => {
    e.preventDefault();
    if (disabled) return;
    const trimmed = value.trim();
    if (!trimmed) return;
    onSend(trimmed);
    setValue('');
  };

  return (
    <form className="chat-input-wrap" onSubmit={handleSubmit}>
      <div className="chat-input-wrap-inner">
        <input
          type="text"
          className="chat-input"
          placeholder={disabled ? "Поиск..." : "Введите текст"}
          disabled={disabled}
          value={value}
          onChange={(e) => setValue(e.target.value)}
          aria-label="Сообщение"
        />
        <button type="submit" className="chat-send-btn" aria-label="Отправить">
          <svg className="chat-send-icon" viewBox="0 0 24 24" fill="currentColor" aria-hidden>
            <path d="M2.01 21L23 12 2.01 3 2 10l15 2-15 2z" />
          </svg>
        </button>
      </div>
    </form>
  );
}
