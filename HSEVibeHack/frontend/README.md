# Frontend — hackSearch

React (Vite) приложение: чат-бот подбора хакатонов, тёмная тема, layout по макету.

## Команды

- `npm install` — зависимости
- `npm run dev` — режим разработки
- `npm run build` — сборка
- `npm run preview` — просмотр сборки

## Иконки

В интерфейсе используются **кастомные inline SVG** (кнопка отправки, профиль и т.д.) и спрайт `public/icons.svg` (symbols: bluesky, discord, documentation, github, social, x). Отдельный внешний icon pack не подключён; при желании можно заменить на **Lucide React** или **Heroicons** для единого стиля.

## Данные

Хакатоны для демо заданы в `src/data/hackathons.js`. Ответы бота формируются в `src/services/chat.js` (фильтр по месяцу, онлайн и т.д.). Для продакшена можно заменить на вызов бэкенд-API.
