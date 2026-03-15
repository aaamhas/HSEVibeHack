import ChatHeader from './ChatHeader';
import ChatWelcome from './ChatWelcome';
import ChatMessages from './ChatMessages';
import ChatInput from './ChatInput';
import Footer from './Footer';
import './Layout.css';

export default function Layout({ messages, onSendMessage }) {
  return (
    <div className="layout">
      <div className="layout-main">
        <ChatHeader />
        <main className="main-content" aria-label="Чат">
          {messages.length === 0 ? (
            <ChatWelcome />
          ) : (
            <ChatMessages messages={messages} />
          )}
        </main>
        <ChatInput onSend={onSendMessage} />
        <Footer />
      </div>
    </div>
  );
}
