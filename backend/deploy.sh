set -e

echo "================================"
echo "Wave Notebook API Deployment"
echo "================================"

echo "==> Python version"
python --version

echo "==> Installing dependencies"
pip install -r requirements.txt

echo "==> Running Alembic migrations"
alembic upgrade head

echo "==> Checking migration status"
alembic current

echo "================================"
echo "Deployment preparation complete"
echo "================================"
