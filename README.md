# Al Rased (الراصد)

Al Rased is an advanced Telegram bot designed for smart detection, monitoring, and automated moderation. It leverages machine learning to identify and filter unwanted content, with a continuous learning loop to improve its accuracy over time.

## 📁 Project Structure

- **`al_rased/`**: Contains the core application code.
  - `core/`: Main bot logic and database connection.
  - `features/`: Bot features (detection, admin tools, etc.).
  - `services/`: External services (Monitoring, Telethon).
- **`scripts/`**: A collection of scripts for dataset management, model training, and optimization.
- **`data/`**: Stores datasets, database files, and model artifacts.

## 🚀 Getting Started

### Prerequisites

- Python 3.9+
- A Telegram Bot Token
- API ID and Hash (for Telethon features)

### Installation

1. Clone the repository.
2. Install dependencies:
   ```bash
   make install
   ```

### Running the Bot

To start the main bot:
```bash
make run
```

To start the Telethon monitor:
```bash
make monitor
```

## 🛠 Scripts Guide

The `scripts/` directory contains powerful tools for maintaining the AI model:

- **`aggressive_learning.py`**: Rapidly learns from new data.
- **`enhance_and_review.py`**: Reviews and enhances the dataset quality.
- **`autonomous_optimization.py`**: Runs optimization cycles automatically.
- **`generate_report.py`**: Generates performance reports.

## 🧪 Testing

Run the test suite with:
```bash
make test
```

## 🤝 Contribution

1. Fork the project.
2. Create your feature branch (`git checkout -b feature/AmazingFeature`).
3. Commit your changes (`git commit -m 'Add some AmazingFeature'`).
4. Push to the branch (`git push origin feature/AmazingFeature`).
5. Open a Pull Request.

## 📝 License

Distributed under the MIT License.
