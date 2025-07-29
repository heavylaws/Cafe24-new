# Cafe24 POS - Deployment Guide

## Overview

This guide covers deploying the Cafe24 POS system to production environments.

## System Requirements

### Minimum Requirements
- **CPU**: 2 cores
- **RAM**: 4GB
- **Storage**: 20GB SSD
- **OS**: Ubuntu 20.04 LTS or CentOS 8+

### Recommended Requirements
- **CPU**: 4 cores
- **RAM**: 8GB
- **Storage**: 50GB SSD
- **OS**: Ubuntu 22.04 LTS

## Dependencies

### System Dependencies
```bash
# Ubuntu/Debian
sudo apt update
sudo apt install python3.9 python3.9-venv python3-pip
sudo apt install postgresql postgresql-contrib
sudo apt install nginx
sudo apt install redis-server
sudo apt install git

# CentOS/RHEL
sudo yum update
sudo yum install python39 python39-pip
sudo yum install postgresql postgresql-server postgresql-contrib
sudo yum install nginx
sudo yum install redis
sudo yum install git
```

### Node.js (for frontend)
```bash
curl -fsSL https://deb.nodesource.com/setup_18.x | sudo -E bash -
sudo apt-get install -y nodejs
```

## Database Setup

### PostgreSQL Configuration
```bash
# Initialize PostgreSQL (CentOS only)
sudo postgresql-setup --initdb
sudo systemctl start postgresql
sudo systemctl enable postgresql

# Create database and user
sudo -u postgres psql
```

```sql
CREATE DATABASE cafe24_pos;
CREATE USER cafe24_user WITH PASSWORD 'secure_password';
GRANT ALL PRIVILEGES ON DATABASE cafe24_pos TO cafe24_user;
\q
```

### Database Connection
Update `.env` file:
```
DATABASE_URL=postgresql://cafe24_user:secure_password@localhost/cafe24_pos
```

## Backend Deployment

### 1. Application Setup
```bash
# Clone repository
git clone <repository-url>
cd Cafe24-new

# Create virtual environment
python3 -m venv venv
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt
pip install gunicorn

# Set up environment variables
cp .env.example .env
```

### 2. Environment Configuration
Create production `.env` file:
```bash
# Flask Configuration
FLASK_ENV=production
FLASK_APP=run.py
SECRET_KEY=your-super-secret-production-key
JWT_SECRET_KEY=your-jwt-secret-production-key

# Database
DATABASE_URL=postgresql://cafe24_user:secure_password@localhost/cafe24_pos

# Currency Settings
USD_TO_LBP_EXCHANGE_RATE=90000.0
PRIMARY_CURRENCY_CODE=LBP
SECONDARY_CURRENCY_CODE=USD
LBP_ROUNDING_FACTOR=5000

# Redis (for caching/sessions)
REDIS_URL=redis://localhost:6379/0
```

### 3. Database Migration
```bash
# Initialize and migrate database
python run.py create-db
python run.py seed-db

# Or use Flask-Migrate
flask db upgrade
```

### 4. Gunicorn Configuration
Create `/etc/systemd/system/cafe24.service`:
```ini
[Unit]
Description=Cafe24 POS Gunicorn server
After=network.target

[Service]
User=www-data
Group=www-data
WorkingDirectory=/var/www/cafe24
Environment="PATH=/var/www/cafe24/venv/bin"
ExecStart=/var/www/cafe24/venv/bin/gunicorn --workers 3 --bind unix:cafe24.sock -m 007 run:app
Restart=always

[Install]
WantedBy=multi-user.target
```

### 5. Start Services
```bash
sudo systemctl daemon-reload
sudo systemctl start cafe24
sudo systemctl enable cafe24
```

## Frontend Deployment

### 1. Build Frontend
```bash
cd pwa_frontend

# Install dependencies
npm install

# Set production API URL
echo "REACT_APP_API_URL=https://your-domain.com" > .env

# Build for production
npm run build
```

### 2. Deploy Static Files
```bash
# Copy build files to web server
sudo cp -r build/* /var/www/html/
sudo chown -R www-data:www-data /var/www/html/
```

## Nginx Configuration

### 1. Backend Proxy
Create `/etc/nginx/sites-available/cafe24`:
```nginx
server {
    listen 80;
    server_name your-domain.com;

    # Frontend static files
    location / {
        root /var/www/html;
        try_files $uri $uri/ /index.html;
        
        # PWA caching headers
        location ~* \.(js|css|png|jpg|jpeg|gif|ico|svg)$ {
            expires 1y;
            add_header Cache-Control "public, immutable";
        }
    }

    # API backend
    location /api/ {
        include proxy_params;
        proxy_pass http://unix:/var/www/cafe24/cafe24.sock;
        
        # CORS headers
        add_header Access-Control-Allow-Origin *;
        add_header Access-Control-Allow-Methods "GET, POST, PUT, DELETE, OPTIONS";
        add_header Access-Control-Allow-Headers "Authorization, Content-Type";
    }

    # Health check
    location /health {
        include proxy_params;
        proxy_pass http://unix:/var/www/cafe24/cafe24.sock;
    }
}
```

### 2. SSL Configuration
```bash
# Install Certbot
sudo apt install certbot python3-certbot-nginx

# Get SSL certificate
sudo certbot --nginx -d your-domain.com

# Auto-renewal
sudo crontab -e
# Add: 0 12 * * * /usr/bin/certbot renew --quiet
```

### 3. Enable Site
```bash
sudo ln -s /etc/nginx/sites-available/cafe24 /etc/nginx/sites-enabled/
sudo nginx -t
sudo systemctl restart nginx
```

## Security Configuration

### 1. Firewall Setup
```bash
# UFW (Ubuntu)
sudo ufw allow ssh
sudo ufw allow 'Nginx Full'
sudo ufw enable

# Firewalld (CentOS)
sudo firewall-cmd --permanent --add-service=ssh
sudo firewall-cmd --permanent --add-service=http
sudo firewall-cmd --permanent --add-service=https
sudo firewall-cmd --reload
```

### 2. PostgreSQL Security
```bash
# Edit postgresql.conf
sudo nano /etc/postgresql/13/main/postgresql.conf
# Set: listen_addresses = 'localhost'

# Edit pg_hba.conf for local connections only
sudo nano /etc/postgresql/13/main/pg_hba.conf
```

### 3. Application Security
- Use strong, unique passwords
- Enable database SSL connections
- Implement rate limiting
- Regular security updates
- Monitor logs for suspicious activity

## Monitoring & Logging

### 1. Application Logs
```bash
# View application logs
sudo journalctl -u cafe24 -f

# Log rotation
sudo nano /etc/logrotate.d/cafe24
```

### 2. Nginx Logs
```bash
# Access logs
tail -f /var/log/nginx/access.log

# Error logs
tail -f /var/log/nginx/error.log
```

### 3. System Monitoring
```bash
# Install htop for system monitoring
sudo apt install htop

# Monitor PostgreSQL
sudo -u postgres psql -c "SELECT * FROM pg_stat_activity;"
```

## Backup Strategy

### 1. Database Backup
```bash
# Create backup script
cat > /home/backup/backup_db.sh << 'EOF'
#!/bin/bash
DATE=$(date +%Y%m%d_%H%M%S)
pg_dump -h localhost -U cafe24_user cafe24_pos > /home/backup/cafe24_${DATE}.sql
# Keep only last 7 days
find /home/backup -name "cafe24_*.sql" -mtime +7 -delete
EOF

chmod +x /home/backup/backup_db.sh

# Schedule daily backups
sudo crontab -e
# Add: 0 2 * * * /home/backup/backup_db.sh
```

### 2. Application Backup
```bash
# Backup application files
tar -czf /home/backup/cafe24_app_$(date +%Y%m%d).tar.gz /var/www/cafe24
```

## Performance Optimization

### 1. Database Optimization
```sql
-- Add indexes for frequently queried columns
CREATE INDEX idx_orders_status ON orders(status);
CREATE INDEX idx_orders_created_at ON orders(created_at);
CREATE INDEX idx_menu_items_category ON menu_items(category_id);
```

### 2. Nginx Optimization
```nginx
# Add to nginx.conf
worker_processes auto;
worker_connections 1024;

# Enable gzip compression
gzip on;
gzip_types text/plain text/css application/json application/javascript;

# Enable caching
location ~* \.(css|js|png|jpg|jpeg|gif|ico)$ {
    expires 1y;
    add_header Cache-Control public;
}
```

### 3. Application Optimization
```python
# Use connection pooling
SQLALCHEMY_ENGINE_OPTIONS = {
    'pool_pre_ping': True,
    'pool_recycle': 300,
    'pool_size': 10,
    'max_overflow': 20
}
```

## Scaling Considerations

### Horizontal Scaling
- Load balancer (HAProxy/Nginx)
- Multiple application servers
- Database replication
- Redis clustering

### Vertical Scaling
- Increase server resources
- Optimize database queries
- Implement caching layers
- CDN for static assets

## Troubleshooting

### Common Issues

**Database Connection Errors**
```bash
# Check PostgreSQL status
sudo systemctl status postgresql

# Check database connectivity
psql -h localhost -U cafe24_user -d cafe24_pos
```

**Application Not Starting**
```bash
# Check application logs
sudo journalctl -u cafe24 -n 50

# Test application manually
cd /var/www/cafe24
source venv/bin/activate
python run.py
```

**Nginx 502 Errors**
```bash
# Check socket file
ls -la /var/www/cafe24/cafe24.sock

# Check Nginx error logs
sudo tail -f /var/log/nginx/error.log
```

### Performance Issues
```bash
# Monitor system resources
htop
iotop
nethogs

# Check database performance
sudo -u postgres psql -c "SELECT * FROM pg_stat_activity;"
```

## Maintenance

### Regular Tasks
- Monitor disk space
- Check application logs
- Update system packages
- Review security logs
- Test backup restoration
- Performance monitoring

### Updates
```bash
# Update application
cd /var/www/cafe24
git pull origin main
source venv/bin/activate
pip install -r requirements.txt
flask db upgrade
sudo systemctl restart cafe24

# Update frontend
cd pwa_frontend
npm install
npm run build
sudo cp -r build/* /var/www/html/
```

## Support

For deployment support:
- Check application logs
- Review configuration files
- Consult the troubleshooting section
- Create an issue in the project repository