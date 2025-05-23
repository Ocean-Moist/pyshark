# 5G Callflow Analyzer

A web application for analyzing 5G control plane traffic from PCAP files using AI.

## Features

- Upload PCAP files containing 5G control plane traffic
- AI-powered analysis of NGAP and NAS-5GS messages
- Interactive chat interface for querying call flows
- Persistent analysis state (Jupyter-style kernel)

## Architecture

- **Frontend**: Next.js with TypeScript and Tailwind CSS
- **Backend**: FastAPI with Python
- **AI**: OpenAI o4-mini reasoning model

## Setup

### Prerequisites

- Node.js 18+ and npm
- Python 3.8+
- OpenAI API key (with o4-mini access)

### Backend Setup

1. Navigate to the backend directory:
   ```bash
   cd backend
   ```

2. Create a virtual environment:
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

4. Create a `.env` file:
   ```bash
   cp .env.example .env
   ```
   Edit `.env` and add your OpenAI API key.

5. Run the backend:
   ```bash
   uvicorn main:app --reload
   ```
   The API will be available at http://localhost:8000

### Frontend Setup

1. Navigate to the frontend directory:
   ```bash
   cd frontend
   ```

2. Install dependencies:
   ```bash
   npm install
   ```

3. Set up authentication (optional):
   ```bash
   cp .env.local.example .env.local
   ```
   Edit `.env.local` and set:
   - `SITE_PASSWORD`: Password to access the site (default: "5g-analyzer-2024")
   - `COOKIE_SECRET`: Secret key for signing cookies (generate a random string)

4. Run the development server:
   ```bash
   npm run dev
   ```
   The app will be available at http://localhost:3000

## Usage

1. Open http://localhost:3000 in your browser
2. Enter the password (default: "5g-analyzer-2024" or as configured)
3. Click the upload area to select a PCAP file
4. Once uploaded, you can ask questions about the 5G call flow
5. The AI will analyze the packets and provide insights

## Authentication

The application includes password protection to restrict access. To configure:

- Set `SITE_PASSWORD` environment variable in the frontend
- Default password: "5g-analyzer-2024"
- Users will be prompted to enter the password on first access
- Authentication persists for 7 days via secure cookie

## Example Questions

- "What are the main procedures in this call flow?"
- "Show me the registration procedure"
- "Are there any failed procedures?"
- "Explain the NAS security setup"
- "What is the sequence of NGAP messages?"

## API Endpoints

- `POST /upload` - Upload a PCAP file
- `POST /analyze` - Analyze packets with AI
- `GET /state` - Get current kernel state
- `POST /reset` - Reset the analysis kernel

## OpenAI O4-mini Model Notes

The application uses OpenAI's o4-mini reasoning model, which provides superior analysis capabilities for complex 5G call flows. Key points:

- **o4-mini** is the latest reasoning model from OpenAI
- Uses internal chain-of-thought reasoning for better results
- No need to prompt for "step-by-step" thinking - it does this automatically
- Requires appropriate OpenAI API access
- Check your access at https://platform.openai.com