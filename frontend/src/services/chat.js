import { hackathons, monthNames } from '../data/hackathons.js';

function parseMonthFromText(text) {
  const lower = text.toLowerCase();
  for (let i = 0; i < monthNames.length; i++) {
    if (lower.includes(monthNames[i])) return i + 1;
  }
  const monthNum = text.match(/\b(0?[1-9]|1[0-2])\b/);
  return monthNum ? parseInt(monthNum[0], 10) : null;
}

function parseYear(text) {
  const m = text.match(/\b(20\d{2})\b/);
  return m ? parseInt(m[1], 10) : new Date().getFullYear();
}

function filterByMonth(list, month, year) {
  if (!month) return list;
  return list.filter((h) => {
    const d = new Date(h.date);
    return d.getMonth() + 1 === month && d.getFullYear() === (year || d.getFullYear());
  });
}

function filterByOnline(list, text) {
  const lower = text.toLowerCase();
  if (lower.includes('онлайн') || lower.includes('online')) return list.filter((h) => h.online);
  if (lower.includes('офлайн') || lower.includes('оффлайн') || lower.includes('очно')) return list.filter((h) => !h.online);
  return list;
}

export function getBotResponse(userText, allHackathons = hackathons) {
  let result = [...allHackathons];
  const month = parseMonthFromText(userText);
  const year = parseYear(userText);
  result = filterByMonth(result, month, year);
  result = filterByOnline(result, userText);
  if (result.length === 0) result = allHackathons.slice(0, 3);
  return result.slice(0, 5);
}
