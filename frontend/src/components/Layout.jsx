import ChatHeader from './ChatHeader';
import ChatWelcome from './ChatWelcome';
import ChatMessages from './ChatMessages';
import ChatInput from './ChatInput';
import Footer from './Footer';
import './Layout.css';

export default function Layout({ messages, onSendMessage, loading }) {
  return (
    <div className="layout">
      <div className="layout-main">
        <ChatHeader />
        <main className="main-content" aria-label="Чат">
          {messages.length === 0 && !loading ? (
            <ChatWelcome />
          ) : (
            <ChatMessages
              messages={messages}
              onQuestionClick={onSendMessage}
              loading={loading}
            />
          )}
        </main>
        <ChatInput onSend={onSendMessage} disabled={loading} />
        <Footer />
      </div>
    </div>
  );
}
