#!/bin/bash

# Get the absolute path to the script directory
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PYTHON_PATH="$(which python3)"
DAILY_SCRIPT="${SCRIPT_DIR}/daily_paper_job.py"

# Make the daily script executable
chmod +x "${DAILY_SCRIPT}"

# Create a temporary file for the crontab
TEMP_CRON=$(mktemp)

# Export current crontab to the temporary file
crontab -l > "${TEMP_CRON}" 2>/dev/null || echo "# New crontab" > "${TEMP_CRON}"

# Check if the job already exists
if ! grep -q "${DAILY_SCRIPT}" "${TEMP_CRON}"; then
    # Add the job to run at 8:00 AM every day
    echo "0 10 * * * cd ${SCRIPT_DIR} && ${PYTHON_PATH} ${DAILY_SCRIPT} >> ${SCRIPT_DIR}/cron_output.log 2>&1" >> "${TEMP_CRON}"
    
    # Install the new crontab
    crontab "${TEMP_CRON}"
    echo "Cron job installed successfully. It will run daily at 8:00 AM."
else
    echo "Cron job already exists. No changes made."
fi

# Clean up
rm "${TEMP_CRON}"

echo "You can check your crontab with: crontab -l"