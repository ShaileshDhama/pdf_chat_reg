# Advanced Legal Document Analysis System

A powerful legal document analysis system that combines AI, AR, and real-time collaboration features to revolutionize legal document processing and review.

## Key Features

### AI-Powered Document Analysis
- Advanced PDF analysis using GPT-4 and LlamaIndex
- Intelligent clause comparison and similarity search
- OCR support with multilingual capabilities
- AI-powered contract generation and risk assessment
- Legal-specific question answering and summarization

### Real-Time Collaboration
- AI-driven document chatbot with legal context
- Real-time collaborative document review
- WebRTC video conferencing for live interactions
- Multi-language translation functionality
- Team annotations and comments

### Immersive AR Interface
- 3D document visualization
- Gesture-controlled interface
- Voice-controlled legal research
- AI avatar for interactive guidance
- Immersive document exploration

## Architecture

```
├── app.py                 # Main Streamlit application
├── backend/
│   ├── app/
│   │   ├── ai/           # AI and ML components
│   │   ├── middleware/   # Security and logging middleware
│   │   ├── utils/        # Utilities and helpers
│   │   └── schemas.py    # Data validation schemas
├── tests/                 # Test suite
├── docs/                  # Documentation
└── docker/               # Docker configuration
```

## Setup

### Prerequisites
- Python 3.9+
- Virtual environment (recommended)
- Required system packages for OCR

### Installation

1. Clone the repository:
```bash
git clone https://github.com/yourusername/legal-doc-analyzer.git
cd legal-doc-analyzer
```

2. Create and activate virtual environment:
```bash
python -m venv venv
source venv/bin/activate  # Linux/Mac
venv\Scripts\activate     # Windows
```

3. Install dependencies:
```bash
pip install -r requirements.txt
```

### Configuration

1. Copy example environment file:
```bash
cp .env.example .env
```

2. Configure environment variables in `.env`:
```env
DEBUG=False
MAX_UPLOAD_SIZE=10000000
RATE_LIMIT_REQUESTS=100
RATE_LIMIT_PERIOD=3600
OPENAI_API_KEY=YOUR_OPENAI_API_KEY
MONGODB_URI=YOUR_MONGODB_URI
REDIS_URL=YOUR_REDIS_URL
JWT_SECRET=YOUR_JWT_SECRET
LOG_LEVEL=INFO
```

## Running Tests

```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=backend

# Run specific test file
pytest tests/test_document_analyzer.py
```

## Development

### Code Style
- Black for code formatting
- isort for import sorting
- flake8 for linting
- mypy for type checking

### Pre-commit Hooks
```bash
pre-commit install
pre-commit run --all-files
```

## Monitoring

### Logging
- Structured JSON logging
- Log rotation
- Error tracking with Sentry
- Analytics events tracking

### Metrics
- Request latency
- Error rates
- Document processing time
- Cache hit rates

## Deployment

### Docker
```bash
# Build image
docker build -t legal-doc-analyzer .

# Run container
docker run -p 8501:8501 legal-doc-analyzer
```

### Production Considerations
- Use gunicorn for WSGI server
- Set up load balancing
- Configure Redis for caching
- Enable Sentry for error tracking
- Set up automated backups

## CI/CD Configuration

This project uses GitHub Actions for continuous integration and deployment. The pipeline includes automated testing, linting, and deployment to a production environment.

### Required Configuration

#### GitHub Actions Variables (Settings > Environments > production > Variables)

These are environment-specific variables that can be viewed in logs:

- `DEPLOY_URL`: The URL where your application is deployed (e.g., `https://pdf-chat.example.com`)
- `DEPLOY_HOST`: The hostname/IP of your deployment server (e.g., `deploy@example.com`)
- `DOCKER_NAMESPACE`: Your Docker Hub username/organization (e.g., `myorganization`)

#### GitHub Actions Secrets (Settings > Environments > production > Secrets)

These are sensitive values that are masked in logs:

- `DOCKER_TOKEN`: Docker Hub access token with push permissions
- `SSH_PRIVATE_KEY`: SSH private key for deployment server access

### Local Development Setup

1. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

2. Run tests:
   ```bash
   pytest
   ```

3. Run linting:
   ```bash
   black .
   flake8 .
   mypy .
   isort .
   ```

### Deployment

The application is automatically deployed when changes are pushed to the main branch. The deployment process:

1. Builds a Docker image with the latest code
2. Tags the image with git SHA and branch name
3. Pushes the image to Docker Hub
4. Deploys the new image to the production server using Docker Compose

To deploy manually:

1. Configure your environment:
   ```bash
   export DOCKER_NAMESPACE=your-dockerhub-username
   export DOCKER_IMAGE=pdf-chat-reg
   ```

2. Build and push:
   ```bash
   docker build -t $DOCKER_NAMESPACE/$DOCKER_IMAGE:latest .
   docker push $DOCKER_NAMESPACE/$DOCKER_IMAGE:latest
   ```

3. Deploy:
   ```bash
   ssh deploy@your-server "cd /opt/pdf-chat-reg && docker-compose -f docker-compose.prod.yml up -d"
   ```

## Roadmap

### Short-term
- [x] CI/CD pipeline setup
- [ ] Enhanced performance monitoring
- [ ] API documentation with Swagger
- [ ] User authentication system
- [ ] Document version control

### Long-term
- [ ] Load balancing implementation
- [ ] Analytics dashboard
- [ ] Automated backup system
- [ ] Multi-language support

## Contributing

1. Fork the repository
2. Create feature branch
3. Commit changes
4. Push to branch
5. Create Pull Request

## License

This project is licensed under the MIT License - see the LICENSE file for details.

## Support

For support, please open an issue in the GitHub repository or contact the development team.
