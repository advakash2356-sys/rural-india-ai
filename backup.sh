#!/bin/bash

# Backup Rural India AI Data
# Called automatically by cron

BACKUP_DIR=~/rural-india-ai/backups
TIMESTAMP=$(date +%Y%m%d_%H%M%S)
BACKUP_FILE="$BACKUP_DIR/rural-india-ai_backup_$TIMESTAMP.tar.gz"

# Create backup directory
mkdir -p $BACKUP_DIR

# Backup critical data
echo "💾 Creating backup: $BACKUP_FILE"
tar -czf $BACKUP_FILE \
    -C ~/rural-india-ai \
    data/vector_db \
    data/metrics \
    requirements.txt \
    --exclude='data/logs' \
    --exclude='__pycache__' \
    --exclude='*.pyc' \
    2>/dev/null

if [ $? -eq 0 ]; then
    # Compress to save space
    du -h "$BACKUP_FILE" | awk '{print "✓ Backup size: " $1}'
    
    # Keep only last 7 backups
    ls -t $BACKUP_DIR/rural-india-ai_backup_*.tar.gz 2>/dev/null | tail -n +8 | xargs -r rm
    
    echo "✅ Backup complete"
else
    echo "❌ Backup failed"
    exit 1
fi
