#!/bin/bash

# Script to recursively find all .aig and .aag files and run ABC solver on each
# with a timeout of 3600 seconds (1 hour)

# Create a directory to store logs
LOG_DIR="solver_logs"
mkdir -p "$LOG_DIR"

# Find all .aig and .aag files recursively
echo "Finding all AIGER files (.aig and .aag)..."
AIGER_FILES=$(find . -name "*.aig" -o -name "*.aag")
TOTAL_FILES=$(echo "$AIGER_FILES" | wc -l)
echo "Found $TOTAL_FILES AIGER files."

# Counter for processed files
COUNTER=0

# Process each file
for FILE in $AIGER_FILES; do
    COUNTER=$((COUNTER + 1))
    
    # Extract filename without path and extension for log naming
    FILENAME=$(basename "$FILE")
    LOG_FILE="$LOG_DIR/${FILENAME%.*}_log.txt"
    
    echo "[$COUNTER/$TOTAL_FILES] Processing: $FILE"
    echo "Log will be saved to: $LOG_FILE"
    
    # Run ABC solver with timeout
    {
        echo "File: $FILE"
        echo "Command: ~/coding_env/abc/abc -c \"&r $FILE; &put; fold; pdr -v\""
        echo "Started at: $(date)"
        echo "----------------------------------------"
        
        # Run the solver with timeout and capture output
        timeout 3600 ~/coding_env/abc/abc -c "&r $FILE; &put; fold; pdr -v" 2>&1
        
        # Check if the command timed out
        if [ $? -eq 124 ]; then
            echo "----------------------------------------"
            echo "STATUS: TIMEOUT (exceeded 3600 seconds)"
        else
            echo "----------------------------------------"
            echo "STATUS: COMPLETED"
        fi
        
        echo "Finished at: $(date)"
        echo "========================================"
    } > "$LOG_FILE"
    
    # Print progress
    echo "Completed $COUNTER of $TOTAL_FILES files."
    echo "----------------------------------------"
done

echo "All files processed. Logs are stored in the $LOG_DIR directory."