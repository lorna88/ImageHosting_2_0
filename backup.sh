#!/bin/bash

BACKUP_DIR=${BACKUP_DIR:='backups'}
PG_USER=${PG_USER:='postgres'}
DB_NAME=${DB_NAME:='images_db'}
NOW=$(date '+%Y-%m-%d %H:%M:%S')
FILE_NAME=backup_${NOW//:/}.sql
LOG_FILE='logs/app.log'

mkdir -p "$BACKUP_DIR"

echo "Creating backup..."
RESULT=$(docker exec -t db pg_dump -U $PG_USER $DB_NAME > "$BACKUP_DIR/$FILE_NAME" && echo "Backup created" || echo "Backup failed")
echo $RESULT
echo "[$NOW] INFO: $RESULT: $BACKUP_DIR/$FILE_NAME" >> $LOG_FILE
