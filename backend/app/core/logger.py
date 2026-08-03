import logging

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)-8s | %(name)s | %(message)s",
    datefmt="%d-%m-%Y %I:%M:%S %p",
)

logger = logging.getLogger("Wave Notebook")
