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
  const [loading, setLoading] = useState(false);

  const onSendMessage = useCallback(async (text) => {
    const userMsg = { id: nextId(), role: 'user', text };
    setMessages((prev) => [...prev, userMsg]);
    setLoading(true);

    const result = await getBotResponse(text);
    setLoading(false);

    if (result.error) {
      setMessages((prev) => [...prev, {
        id: nextId(),
        role: 'bot',
        text: result.error,
      }]);
      return;
    }

    const botMsg = {
      id: nextId(),
      role: 'bot',
      text: result.hackathons.length
        ? 'Вот подборка хакатонов по вашему запросу:'
        : 'К сожалению, ничего не нашлось. Попробуйте уточнить запрос.',
      hackathons: result.hackathons.length ? result.hackathons : undefined,
      followUpQuestions: result.follow_up_questions.length ? result.follow_up_questions : undefined,
    };
    setMessages((prev) => [...prev, botMsg]);
  }, []);

  return (
    <Routes>
      <Route path="/" element={
        <Layout
          messages={messages}
          onSendMessage={onSendMessage}
          loading={loading}
        />
      } />
      <Route path="/profile" element={<ProfilePage />} />
    </Routes>
  );
}
