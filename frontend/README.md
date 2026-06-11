# Frontend Documentation

## React + TypeScript Frontend for RAG System

This is a production-grade React + TypeScript frontend for the Local MultiAgentic RAG System.

## Project Structure

```
src/
├── components/
│   ├── Chat/               # Chat interface component
│   ├── Sidebar/            # Session management sidebar
│   ├── SourcesPanel/       # Retrieved sources display
│   └── Common/             # Shared components
├── pages/                  # Page components (future)
├── services/
│   └── apiService.ts       # API client for backend communication
├── hooks/
│   └── index.ts            # Custom React hooks
├── types/
│   └── index.ts            # TypeScript interfaces
├── utils/
│   └── index.ts            # Utility functions
├── styles/
│   ├── globals.css         # Global styles
│   └── theme.ts            # Theme configuration
├── constants/              # Application constants
├── App.tsx                 # Root component
└── main.tsx                # React entry point
```

## Installation

```bash
npm install
```

## Development

```bash
npm run dev
```

Server runs on `http://localhost:3000`

## Build

```bash
npm run build
```

Output is in `dist/` directory

## Features

### Components

- **Chat Component**
  - Message display with auto-scroll
  - User message styling
  - Assistant response rendering
  - Loading states
  - Source attribution

- **Sidebar Component**
  - Session list
  - Create new session
  - Delete session
  - Session timestamps
  - Active session highlighting

- **SourcesPanel Component**
  - Display retrieved chunks
  - Show source metadata
  - Copy functionality
  - Score display

### Custom Hooks

- `useChat()` - Chat state and operations
- `useSessions()` - Session management
- `useKnowledgeBase()` - Knowledge base operations
- `useWebSocket()` - WebSocket connection handling

### Services

- `apiService.ts` - Centralized API communication
  - Chat endpoints
  - Session management
  - Knowledge base operations
  - PDF upload

## Styling

### Theme

The application uses a cyberpunk-inspired dark theme with:
- Cyan accents (#00f0ff)
- Deep blue backgrounds
- Smooth transitions
- Glassmorphism effects

### Customization

Edit `src/styles/theme.ts` to customize colors and fonts.

## API Integration

The frontend communicates with the backend via:

### REST API
- `POST /api/chat/message` - Send message
- `GET /api/chat/sessions` - Get sessions
- `POST /api/chat/session/create` - Create session
- `DELETE /api/chat/session/{id}` - Delete session
- `GET /api/knowledge/stats` - Get KB stats

### WebSocket
- `WS /api/chat/ws/{session_id}` - Streaming responses

## Environment Variables

Create `.env` file:

```
VITE_API_URL=http://localhost:8000
VITE_API_TIMEOUT=30000
VITE_ENABLE_DEBUG=false
```

## Type Safety

Full TypeScript support with types defined in `src/types/index.ts`:
- `Message`
- `ChatSession`
- `ChunkSource`
- `KnowledgeStats`
- And more...

## Performance

- Lazy loading of components
- Optimized re-renders with React.memo
- Debounced API calls
- Efficient state management

## Browser Support

- Chrome/Edge 90+
- Firefox 88+
- Safari 14+

## Troubleshooting

### API Connection Failed
- Verify backend is running on `http://localhost:8000`
- Check `VITE_API_URL` environment variable
- Check browser console for CORS errors

### Styles Not Loading
- Clear browser cache
- Rebuild with `npm run build`
- Check if CSS files are in correct path

### WebSocket Connection Issues
- Verify backend WebSocket endpoint is accessible
- Check firewalls/proxies
- Review browser console errors

## Contributing

Follow the existing code style:
- Use functional components with hooks
- Keep components small and reusable
- Add TypeScript types for all props
- Document complex logic

## Production Build

```bash
npm run build
# Output in dist/ directory
# Serve with: npx serve dist
```
