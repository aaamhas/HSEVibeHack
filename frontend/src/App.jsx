import { useState, useCallback } from 'react';
import { Routes, Route } from 'react-router-dom';
import Layout from './components/Layout';
import ProfilePage from './pages/ProfilePage';
import { getBotResponse } from './services/chat';
import './App.css';

let messageId = 0;
function nextId() {
  messageId += 1;
  return String(messageId);
}

export default function App() {
  const [messages, setMessages] = useState([]);

  const onSendMessage = useCallback((text) => {
    const userMsg = { id: nextId(), role: 'user', text };
    setMessages((prev) => [...prev, userMsg]);

    const hackathons = getBotResponse(text);
    const botMsg = {
      id: nextId(),
      role: 'bot',
      text: hackathons.length ? 'Вот подборка хакатонов по вашему запросу:' : 'Попробуйте указать месяц (например, март или апрель) или «онлайн».',
      hackathons: hackathons.length ? hackathons : undefined,
    };
    setMessages((prev) => [...prev, botMsg]);
  }, []);

  return (
    <Routes>
      <Route path="/" element={<Layout messages={messages} onSendMessage={onSendMessage} />} />
      <Route path="/profile" element={<ProfilePage />} />
    </Routes>
  );
}
