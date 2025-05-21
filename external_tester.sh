#!/bin/bash

# Run with:
# BASE_URL="https://your-replit-url.replit.dev" && chmod +x external_tester.sh && ./external_tester.sh

# We're making this script more fault-tolerant, so we're not exiting on first error
# Instead we'll handle errors more gracefully with proper error messages
# set -e
# set -o pipefail

# Function for logging errors
log_error() {
  echo "❌ ERROR: $1" >&2
}

# Function for logging warnings
log_warning() {
  echo "⚠️ WARNING: $1" >&2
}

# Function for logging info
log_info() {
  echo "ℹ️ INFO: $1"
}

# Function for logging success
log_success() {
  echo "✅ SUCCESS: $1"
}

# --- Configuration ---
if [ -z "$BASE_URL" ]; then
  BASE_URL="https://f9f4321b-dca0-4787-b26b-75efbd0e20bf-00-rn7at7q9c66e.worf.replit.dev"
fi
POLL_INTERVAL_SECONDS=5 # How often to check batch status

# Generate unique test run ID with timestamp
TEST_RUN_ID=$(date +"%Y%m%d_%H%M%S")
OUTPUT_DIR="test_outputs/${TEST_RUN_ID}"

# Create directory structure
mkdir -p "${OUTPUT_DIR}/raw_data"
mkdir -p "${OUTPUT_DIR}/reports"
mkdir -p "${OUTPUT_DIR}/personas"
mkdir -p "${OUTPUT_DIR}/scorecards"

echo "🧪 Starting HermitBench Test Workflow..."
echo "----------------------------------------"
echo "Using API URL: ${BASE_URL}"
echo "Test Run ID: ${TEST_RUN_ID}"
echo "Output Directory: ${OUTPUT_DIR}"
echo "----------------------------------------"

# --- Step 1: Start a batch run ---
echo "🚀 Step 1: Starting a batch run..."
BATCH_RUN_PAYLOAD='{
  "models": ["openai/gpt-3.5-turbo", "openai/gpt-4"],
  "num_runs_per_model": 1,
  "temperature": 0.7,
  "top_p": 1.0,
  "max_turns": 5,
  "task_delay_ms": 3000
}'

BATCH_RESPONSE=$(curl -s -X POST "${BASE_URL}/api/run-batch" \
  -H "Content-Type: application/json" \
  -d "${BATCH_RUN_PAYLOAD}")

# Validate JSON response
if ! echo "${BATCH_RESPONSE}" | jq -e . >/dev/null 2>&1; then
  log_error "Invalid JSON response received from batch initialization:"
  echo "${BATCH_RESPONSE}"
  echo "${BATCH_RESPONSE}" > "${OUTPUT_DIR}/raw_data/batch_init_response.raw"
  echo "{\"error\": \"Invalid JSON response\", \"raw_response\": \"${BATCH_RESPONSE}\"}" > "${OUTPUT_DIR}/raw_data/batch_init_response.json"
  
  # Ask user if they want to retry or abort
  echo
  read -p "Would you like to retry batch initialization? (y/n): " retry_choice
  if [[ "$retry_choice" =~ ^[Yy]$ ]]; then
    log_info "Retrying batch initialization..."
    # Wait a bit before retrying
    sleep 5
    BATCH_RESPONSE=$(curl -s -X POST "${BASE_URL}/api/run-batch" \
      -H "Content-Type: application/json" \
      -d "${BATCH_RUN_PAYLOAD}")
  else
    log_error "Aborting test run due to initialization failure."
    exit 1
  fi
fi

# Try to extract batch ID, with additional error handling
BATCH_ID=$(echo "${BATCH_RESPONSE}" | jq -r '.batch_id // empty')

if [[ -z "$BATCH_ID" ]]; then
  log_error "Failed to get BATCH_ID from response."
  echo "Response: ${BATCH_RESPONSE}"
  echo "${BATCH_RESPONSE}" > "${OUTPUT_DIR}/raw_data/batch_init_response.raw"
  
  # Save as JSON if possible, otherwise create an error JSON
  if echo "${BATCH_RESPONSE}" | jq -e . >/dev/null 2>&1; then
    echo "${BATCH_RESPONSE}" | jq '.' > "${OUTPUT_DIR}/raw_data/batch_init_response.json"
  else
    echo "{\"error\": \"Missing batch_id\", \"raw_response\": \"${BATCH_RESPONSE}\"}" > "${OUTPUT_DIR}/raw_data/batch_init_response.json"
  fi
  
  exit 1
fi

log_success "Batch run started. BATCH_ID: ${BATCH_ID}"
echo "Response: ${BATCH_RESPONSE}"

# Save batch initialization response (safely)
echo "${BATCH_RESPONSE}" > "${OUTPUT_DIR}/raw_data/batch_init_response.raw"
if echo "${BATCH_RESPONSE}" | jq -e . >/dev/null 2>&1; then
  echo "${BATCH_RESPONSE}" | jq '.' > "${OUTPUT_DIR}/raw_data/batch_init_response.json"
  log_success "Saved batch initialization response to ${OUTPUT_DIR}/raw_data/batch_init_response.json"
else
  echo "{\"error\": \"Invalid JSON but batch_id extracted\", \"batch_id\": \"${BATCH_ID}\", \"raw_response\": \"${BATCH_RESPONSE}\"}" > "${OUTPUT_DIR}/raw_data/batch_init_response.json"
  log_warning "Response wasn't valid JSON. Saved raw response and extracted batch_id."
fi
echo "----------------------------------------"

# --- Step 2 & 3: Check batch status and get results when completed ---
echo "🔄 Step 2 & 3: Monitoring batch status (ID: ${BATCH_ID})..."
while true; do
  STATUS_RESPONSE=$(curl -s -X GET "${BASE_URL}/api/batch/${BATCH_ID}")
  
  # Validate JSON response before parsing
  if ! echo "${STATUS_RESPONSE}" | jq -e . >/dev/null 2>&1; then
    echo "⚠️ Warning: Invalid JSON response received:"
    echo "${STATUS_RESPONSE}"
    echo "Waiting to retry..."
    sleep "${POLL_INTERVAL_SECONDS}"
    continue
  fi
  
  # Safely extract values with fallbacks
  CURRENT_STATUS=$(echo "${STATUS_RESPONSE}" | jq -r '.status // "unknown"')
  NUM_COMPLETED=$(echo "${STATUS_RESPONSE}" | jq -r '.completed_tasks // 0')
  NUM_TOTAL=$(echo "${STATUS_RESPONSE}" | jq -r '.total_tasks // 0')

  echo "Current status: ${CURRENT_STATUS} (${NUM_COMPLETED}/${NUM_TOTAL} tasks completed)"

  # Save the latest status response (only if valid JSON)
  echo "${STATUS_RESPONSE}" > "${OUTPUT_DIR}/raw_data/batch_status_latest.raw"
  echo "${STATUS_RESPONSE}" | jq -e '.' > "${OUTPUT_DIR}/raw_data/batch_status_latest.json" 2>/dev/null || 
    echo "{\"error\": \"Invalid JSON response\", \"raw_response\": \"${STATUS_RESPONSE}\"}" > "${OUTPUT_DIR}/raw_data/batch_status_latest.json"

  if [[ "${CURRENT_STATUS}" == "completed" ]]; then
    log_success "Batch completed!"
    echo "Fetching results..."
    RESULTS_RESPONSE=$(curl -s -X GET "${BASE_URL}/api/batch/${BATCH_ID}/results")
    
    # Store raw results regardless of format
    echo "${RESULTS_RESPONSE}" > "${OUTPUT_DIR}/raw_data/results.raw"
    
    # Validate JSON response
    if ! echo "${RESULTS_RESPONSE}" | jq -e . >/dev/null 2>&1; then
      log_error "Invalid JSON response when fetching results:"
      echo "${RESULTS_RESPONSE}"
      echo "{\"error\": \"Invalid JSON response\", \"raw_response\": \"${RESULTS_RESPONSE}\"}" > "${OUTPUT_DIR}/raw_data/results.json"
      echo "⚠️ Batch completed but results could not be parsed as JSON. See raw file for details."
      
      # Ask user if they want to retry fetching results
      read -p "Would you like to retry fetching results? (y/n): " retry_choice
      if [[ "$retry_choice" =~ ^[Yy]$ ]]; then
        log_info "Retrying results fetch..."
        sleep 3
        RESULTS_RESPONSE=$(curl -s -X GET "${BASE_URL}/api/batch/${BATCH_ID}/results")
        
        # Check again
        if ! echo "${RESULTS_RESPONSE}" | jq -e . >/dev/null 2>&1; then
          log_error "Still received invalid JSON response. Continuing with other steps."
          break
        else
          log_success "Retry successful, processing results..."
        fi
      else
        log_info "Continuing with other steps..."
        break
      fi
    fi
    
    # Save results response as proper JSON
    echo "${RESULTS_RESPONSE}" | jq '.' > "${OUTPUT_DIR}/raw_data/results.json"
    log_success "Saved full results to ${OUTPUT_DIR}/raw_data/results.json"
    
    # Process results based on structure
    echo "Result summary:"
    if echo "${RESULTS_RESPONSE}" | jq -e '.[] | select(.model_name != null)' &>/dev/null 2>&1; then
      # Direct array of results
      echo "${RESULTS_RESPONSE}" | jq -r '.[] | "Model: \(.model_name // "unknown")\nCompliance Rate: \(.compliance_rate // "N/A")\nAutonomy Score: \(.autonomy_score // "N/A")\nTurns: \(.turns_count // "N/A")\n"' > "${OUTPUT_DIR}/reports/summary.txt"
      echo "${RESULTS_RESPONSE}" | jq -r '.[] | "Model: \(.model_name // "unknown")\nCompliance Rate: \(.compliance_rate // "N/A")\nAutonomy Score: \(.autonomy_score // "N/A")\nTurns: \(.turns_count // "N/A")\n"'
    elif echo "${RESULTS_RESPONSE}" | jq -e '.results[] | select(.model_name != null)' &>/dev/null 2>&1; then
      # Object with results array
      echo "${RESULTS_RESPONSE}" | jq -r '.results[] | "Model: \(.model_name // "unknown")\nCompliance Rate: \(.compliance_rate // "N/A")\nAutonomy Score: \(.autonomy_score // "N/A")\nTurns: \(.turns_count // "N/A")\n"' > "${OUTPUT_DIR}/reports/summary.txt"
      echo "${RESULTS_RESPONSE}" | jq -r '.results[] | "Model: \(.model_name // "unknown")\nCompliance Rate: \(.compliance_rate // "N/A")\nAutonomy Score: \(.autonomy_score // "N/A")\nTurns: \(.turns_count // "N/A")\n"'
    elif echo "${RESULTS_RESPONSE}" | jq -e '.runs[] | select(.model_name != null)' &>/dev/null 2>&1; then
      # Object with runs array (another possible format)
      echo "${RESULTS_RESPONSE}" | jq -r '.runs[] | "Model: \(.model_name // "unknown")\nCompliance Rate: \(.compliance_rate // "N/A")\nAutonomy Score: \(.autonomy_score // "N/A")\nTurns: \(.turns_count // "N/A")\n"' > "${OUTPUT_DIR}/reports/summary.txt"
      echo "${RESULTS_RESPONSE}" | jq -r '.runs[] | "Model: \(.model_name // "unknown")\nCompliance Rate: \(.compliance_rate // "N/A")\nAutonomy Score: \(.autonomy_score // "N/A")\nTurns: \(.turns_count // "N/A")\n"'
    else
      # Unknown format, show what we got
      log_warning "Unable to automatically extract run details. See ${OUTPUT_DIR}/raw_data/results.json for full data."
      # At least save the raw JSON as our summary
      echo "Results received but in unexpected format:" > "${OUTPUT_DIR}/reports/summary.txt"
      echo "${RESULTS_RESPONSE}" | jq '.' >> "${OUTPUT_DIR}/reports/summary.txt"
    fi
    
    break
  elif [[ "${CURRENT_STATUS}" == "failed" || "${CURRENT_STATUS}" == "error" ]]; then
    log_error "Batch run failed or errored."
    echo "Status Response: ${STATUS_RESPONSE}"
    
    # Save the raw response first
    echo "${STATUS_RESPONSE}" > "${OUTPUT_DIR}/raw_data/batch_status_error.raw"
    
    # Save structured error data if possible
    if echo "${STATUS_RESPONSE}" | jq -e . >/dev/null 2>&1; then
      echo "${STATUS_RESPONSE}" | jq '.' > "${OUTPUT_DIR}/raw_data/batch_status_error.json"
    else
      echo "{\"error\": \"Batch failed but response was not valid JSON\", \"raw_response\": \"${STATUS_RESPONSE}\"}" > "${OUTPUT_DIR}/raw_data/batch_status_error.json"
    fi
    
    # Extract error message if present
    ERROR_MSG=$(echo "${STATUS_RESPONSE}" | jq -r '.error // "Unknown error"' 2>/dev/null)
    log_error "Error details: ${ERROR_MSG}"
    
    # Ask if user wants to continue with other steps or abort
    echo
    read -p "Would you like to continue with report generation anyway? (y/n): " continue_choice
    if [[ "$continue_choice" =~ ^[Yy]$ ]]; then
      log_warning "Continuing with report generation despite batch failure."
      break
    else
      log_error "Aborting test run due to batch failure."
      exit 1
    fi
  fi
  sleep "${POLL_INTERVAL_SECONDS}"
done
echo "----------------------------------------"

# --- Step 4: Generate a CSV summary report ---
echo "📊 Step 4: Generating CSV summary report for BATCH_ID: ${BATCH_ID}..."
REPORT_GEN_PAYLOAD='{"report_type": "csv_summary"}'

REPORT_URL_RESPONSE=$(curl -s -X POST "${BASE_URL}/api/batch/${BATCH_ID}/report" \
  -H "Content-Type: application/json" \
  -d "${REPORT_GEN_PAYLOAD}")

DOWNLOAD_URL_SUFFIX=$(echo "${REPORT_URL_RESPONSE}" | jq -r .download_url)

if [[ -z "$DOWNLOAD_URL_SUFFIX" || "$DOWNLOAD_URL_SUFFIX" == "null" ]]; then
  echo "❌ Error: Failed to get download_url for CSV summary from response."
  echo "Response: ${REPORT_URL_RESPONSE}"
  # Save error response
  echo "${REPORT_URL_RESPONSE}" | jq '.' > "${OUTPUT_DIR}/raw_data/csv_report_error.json"
  exit 1
fi
echo "✅ CSV summary report generation initiated."
echo "Download URL Suffix: ${DOWNLOAD_URL_SUFFIX}"

# Save report URL response
echo "${REPORT_URL_RESPONSE}" | jq '.' > "${OUTPUT_DIR}/raw_data/csv_report_response.json"
echo "----------------------------------------"

# --- Step 5: Download the generated report ---
DOWNLOAD_FILENAME="${OUTPUT_DIR}/reports/hermitbench_summary.csv"
FULL_DOWNLOAD_URL="${BASE_URL}${DOWNLOAD_URL_SUFFIX}" # The download_url is already a full path from root

echo "📥 Step 5: Downloading the report from ${FULL_DOWNLOAD_URL} to ${DOWNLOAD_FILENAME}..."
curl -s -X GET "${FULL_DOWNLOAD_URL}" -o "${DOWNLOAD_FILENAME}"

if [[ -f "${DOWNLOAD_FILENAME}" && -s "${DOWNLOAD_FILENAME}" ]]; then
  echo "✅ Report downloaded successfully as ${DOWNLOAD_FILENAME}."
  echo "Report preview (first 5 lines):"
  head -n 5 "${DOWNLOAD_FILENAME}"
else
  echo "❌ Error: Failed to download or the downloaded file is empty."
  # Attempt to show error if the server returned one instead of a file
  cat "${DOWNLOAD_FILENAME}" || echo "No error message available"
  exit 1
fi
echo "----------------------------------------"

# --- Step 6: Generate persona cards ---
echo "🎭 Step 6: Generating persona cards for BATCH_ID: ${BATCH_ID}..."
PERSONA_RESPONSE=$(curl -s -X POST "${BASE_URL}/api/batch/${BATCH_ID}/personas")

# Save full response for reference
echo "${PERSONA_RESPONSE}" | jq '.' > "${OUTPUT_DIR}/personas/persona_cards.json"
echo "✅ Saved full persona data to ${OUTPUT_DIR}/personas/persona_cards.json"

# Try to extract useful information
if echo "${PERSONA_RESPONSE}" | jq -e 'keys' &>/dev/null; then
  echo "✅ Persona cards generated for models:"
  PERSONA_SUMMARY="${OUTPUT_DIR}/personas/summary.txt"
  touch "${PERSONA_SUMMARY}"
  
  echo "${PERSONA_RESPONSE}" | jq -r 'keys[]' | while read -r model; do
    echo "  - ${model}"
    DESCRIPTION=$(echo "${PERSONA_RESPONSE}" | jq -r --arg model "$model" '.[$model].personality_description // "N/A"')
    echo "    Description: ${DESCRIPTION:0:100}..."
    
    # Write to summary file
    echo "Model: ${model}" >> "${PERSONA_SUMMARY}"
    echo "Description: ${DESCRIPTION:0:100}..." >> "${PERSONA_SUMMARY}"
    echo "----------------------------------------" >> "${PERSONA_SUMMARY}"
    
    # Save individual model persona to separate file
    echo "${PERSONA_RESPONSE}" | jq -r --arg model "$model" '.[$model]' > "${OUTPUT_DIR}/personas/${model//\//_}_persona.json"
  done
else
  echo "⚠️ Persona data not in expected format. See ${OUTPUT_DIR}/personas/persona_cards.json for details."
fi
echo "----------------------------------------"

# --- Step 7: Generate a detailed scorecard ---
echo "📈 Step 7: Generating detailed scorecard for BATCH_ID: ${BATCH_ID}..."
SCORECARD_PAYLOAD='{"report_type": "detailed_scorecard"}'

SCORECARD_RESPONSE=$(curl -s -X POST "${BASE_URL}/api/batch/${BATCH_ID}/report" \
  -H "Content-Type: application/json" \
  -d "${SCORECARD_PAYLOAD}")

# Save scorecard generation response
echo "${SCORECARD_RESPONSE}" | jq '.' > "${OUTPUT_DIR}/raw_data/scorecard_response.json"

DETAILED_SCORECARD_URL_SUFFIX=$(echo "${SCORECARD_RESPONSE}" | jq -r .download_url)
if [[ -n "$DETAILED_SCORECARD_URL_SUFFIX" && "$DETAILED_SCORECARD_URL_SUFFIX" != "null" ]]; then
  FULL_DETAILED_SCORECARD_URL="${BASE_URL}${DETAILED_SCORECARD_URL_SUFFIX}"
  DETAILED_SCORECARD_FILENAME="${OUTPUT_DIR}/scorecards/detailed_scorecard.json"
  echo "Downloading detailed scorecard from ${FULL_DETAILED_SCORECARD_URL} to ${DETAILED_SCORECARD_FILENAME}..."
  curl -s -X GET "${FULL_DETAILED_SCORECARD_URL}" -o "${DETAILED_SCORECARD_FILENAME}"
  echo "✅ Detailed scorecard downloaded as ${DETAILED_SCORECARD_FILENAME}."
  
  # Extract and save model-specific scorecards if possible
  if jq -e '.models' "${DETAILED_SCORECARD_FILENAME}" &>/dev/null; then
    echo "Extracting model-specific scorecards..."
    jq -r '.models | keys[]' "${DETAILED_SCORECARD_FILENAME}" 2>/dev/null | while read -r model; do
      model_safe=$(echo "${model}" | tr '/' '_')
      jq --arg model "${model}" '.models[$model]' "${DETAILED_SCORECARD_FILENAME}" > "${OUTPUT_DIR}/scorecards/${model_safe}_scorecard.json"
      echo "✅ Extracted scorecard for ${model} to ${OUTPUT_DIR}/scorecards/${model_safe}_scorecard.json"
    done
  fi
else
  echo "⚠️ No download URL received for detailed scorecard."
  echo "Response: ${SCORECARD_RESPONSE}"
fi

echo "----------------------------------------"
echo "🏁 Test Run Summary"
echo "----------------------------------------"
echo "🆔 Test Run ID: ${TEST_RUN_ID}"
echo "🆔 Batch ID: ${BATCH_ID}"
echo "📂 Output Directory: ${OUTPUT_DIR}"
echo ""
echo "📁 Files generated:"
find "${OUTPUT_DIR}" -type f | sort

echo ""
echo "🎉 HermitBench Test Workflow Completed!"
echo "----------------------------------------"

# Generate a metadata file with test run information
cat > "${OUTPUT_DIR}/metadata.json" << EOF
{
  "test_run_id": "${TEST_RUN_ID}",
  "batch_id": "${BATCH_ID}",
  "timestamp": "$(date -u +"%Y-%m-%dT%H:%M:%SZ")",
  "base_url": "${BASE_URL}",
  "models_tested": $(echo "${BATCH_RUN_PAYLOAD}" | jq '.models')
}
EOF
echo "✅ Generated metadata file at ${OUTPUT_DIR}/metadata.json"