const API_BASE = import.meta.env.VITE_API_URL || 'http://localhost:8000';

/**
 * Send user query to backend AI search and return structured response.
 * @param {string} userText
 * @returns {Promise<{hackathons: Array, follow_up_questions: Array, parsed_query: Object}>}
 */
export async function getBotResponse(userText) {
  try {
    const params = new URLSearchParams({ q: userText, limit: '10' });
    const resp = await fetch(`${API_BASE}/hackathons/search/ai?${params}`);

    if (!resp.ok) {
      throw new Error(`API error: ${resp.status}`);
    }

    const data = await resp.json();
    return {
      hackathons: data.hackathons || [],
      follow_up_questions: data.follow_up_questions || [],
      parsed_query: data.parsed_query || {},
    };
  } catch (err) {
    console.error('Chat API error:', err);
    return {
      hackathons: [],
      follow_up_questions: [],
      parsed_query: {},
      error: 'Не удалось подключиться к серверу. Попробуйте позже.',
    };
  }
}
