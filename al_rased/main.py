import logging

# Load environment variables FIRST before any imports
from dotenv import load_dotenv
load_dotenv()

# Now import the rest
from core.bot import create_app

# Configure logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)

def main():
    try:
        app = create_app()
        app.run_polling()
    except Exception as e:
        logging.error(f"Failed to start bot: {e}")

if __name__ == '__main__':
    main()
