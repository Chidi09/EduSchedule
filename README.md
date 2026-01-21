# EduSchedule

A comprehensive educational scheduling and management system built with Vue.js frontend and FastAPI backend.

## Project Structure

```
EduSchedule/
├── eduschedule-frontend/    # Vue.js frontend application
│   ├── src/                 # Source code
│   ├── public/              # Static assets
│   ├── package.json         # Node.js dependencies
│   └── ...
├── eduschedule-backend/     # FastAPI backend application
│   ├── api/                 # API routes
│   ├── core/                # Core functionality
│   ├── schemas/             # Pydantic schemas
│   ├── services/            # Business logic
│   ├── main.py             # Application entry point
│   └── ...
└── README.md               # This file
```

## Features

- 📅 Schedule management
- 👥 User authentication and authorization
- 📚 Educational content organization
- 🔥 Firebase integration
- 📱 Responsive design
- 🚀 Fast and modern tech stack

## Tech Stack

### Frontend
- **Vue.js 3** - Progressive JavaScript framework
- **TypeScript** - Type-safe JavaScript
- **Tailwind CSS** - Utility-first CSS framework
- **Vite** - Fast build tool

### Backend
- **FastAPI** - Modern Python web framework
- **Python 3.8+** - Programming language
- **Pydantic** - Data validation using Python type annotations
- **Firebase** - Backend-as-a-Service platform

## Getting Started

### Prerequisites

- Node.js 16+ and npm/yarn
- Python 3.8+
- Firebase account and project

### Installation

1. **Clone the repository**
   ```bash
   git clone <repository-url>
   cd EduSchedule
   ```

2. **Backend Setup**
   ```bash
   cd eduschedule-backend
   
   # Create virtual environment
   python -m venv venv
   
   # Activate virtual environment
   # On Windows:
   venv\Scripts\activate
   # On macOS/Linux:
   source venv/bin/activate
   
   # Install dependencies
   pip install -r requirements.txt
   
   # Set up Firebase service account
   # Place your firebase-service-account.json in the backend directory
   
   # Run the development server
   uvicorn main:app --reload
   ```

3. **Frontend Setup**
   ```bash
   cd eduschedule-frontend
   
   # Install dependencies
   npm install
   # or
   yarn install
   
   # Run the development server
   npm run dev
   # or
   yarn dev
   ```

### Environment Variables

#### Backend (.env)
```
FIREBASE_PROJECT_ID=your-project-id
DATABASE_URL=your-database-url
SECRET_KEY=your-secret-key
```

#### Frontend (.env)
```
VITE_API_BASE_URL=http://localhost:8000
VITE_FIREBASE_API_KEY=your-api-key
VITE_FIREBASE_AUTH_DOMAIN=your-auth-domain
VITE_FIREBASE_PROJECT_ID=your-project-id
```

## API Documentation

Once the backend is running, visit:
- **Swagger UI**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc

## Development

### Code Style

- **Frontend**: ESLint + Prettier configuration
- **Backend**: Black + isort for Python formatting

### Testing

```bash
# Backend tests
cd eduschedule-backend
pytest

# Frontend tests
cd eduschedule-frontend
npm run test
```

## Deployment

### Backend Deployment
The FastAPI backend can be deployed to platforms like:
- Heroku
- Railway
- Google Cloud Run
- AWS Lambda

### Frontend Deployment
The Vue.js frontend can be deployed to:
- Netlify
- Vercel
- Firebase Hosting
- GitHub Pages

## Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/AmazingFeature`)
3. Commit your changes (`git commit -m 'Add some AmazingFeature'`)
4. Push to the branch (`git push origin feature/AmazingFeature`)
5. Open a Pull Request

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## Support

If you have any questions or need help, please open an issue in the repository.

## Acknowledgments

- Vue.js team for the amazing framework
- FastAPI team for the excellent Python web framework
- Firebase team for the backend services
- All contributors who help improve this project