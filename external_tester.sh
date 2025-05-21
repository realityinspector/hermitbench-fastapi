#!/bin/bash

# Run with:
# BASE_URL="https://f9f4321b-dca0-4787-b26b-75efbd0e20bf-00-rn7at7q9c66e.worf.replit.dev" && ./external_tester.sh.new

# Exit immediately if a command exits with a non-zero status.
set -e
# Cause a pipeline to return the exit status of the last command in the pipe
# that returned a non-zero return value.
set -o pipefail

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

BATCH_ID=$(echo "${BATCH_RESPONSE}" | jq -r .batch_id)

if [[ -z "$BATCH_ID" || "$BATCH_ID" == "null" ]]; then
  echo "❌ Error: Failed to get BATCH_ID from response."
  echo "Response: ${BATCH_RESPONSE}"
  exit 1
fi
echo "✅ Batch run started. BATCH_ID: ${BATCH_ID}"
echo "Response: ${BATCH_RESPONSE}"

# Save batch initialization response
echo "${BATCH_RESPONSE}" | jq '.' > "${OUTPUT_DIR}/raw_data/batch_init_response.json"
echo "✅ Saved batch initialization response to ${OUTPUT_DIR}/raw_data/batch_init_response.json"
echo "----------------------------------------"

# --- Step 2 & 3: Check batch status and get results when completed ---
echo "🔄 Step 2 & 3: Monitoring batch status (ID: ${BATCH_ID})..."
while true; do
  STATUS_RESPONSE=$(curl -s -X GET "${BASE_URL}/api/batch/${BATCH_ID}")
  CURRENT_STATUS=$(echo "${STATUS_RESPONSE}" | jq -r .status)
  NUM_COMPLETED=$(echo "${STATUS_RESPONSE}" | jq -r .completed_tasks)
  NUM_TOTAL=$(echo "${STATUS_RESPONSE}" | jq -r .total_tasks)

  echo "Current status: ${CURRENT_STATUS} (${NUM_COMPLETED}/${NUM_TOTAL} tasks completed)"

  # Save the latest status response
  echo "${STATUS_RESPONSE}" | jq '.' > "${OUTPUT_DIR}/raw_data/batch_status_latest.json"

  if [[ "${CURRENT_STATUS}" == "completed" ]]; then
    echo "✅ Batch completed!"
    echo "Fetching results..."
    RESULTS_RESPONSE=$(curl -s -X GET "${BASE_URL}/api/batch/${BATCH_ID}/results")
    
    # Save results response
    echo "${RESULTS_RESPONSE}" | jq '.' > "${OUTPUT_DIR}/raw_data/results.json"
    echo "✅ Saved full results to ${OUTPUT_DIR}/raw_data/results.json"
    
    # Process results based on structure
    echo "Result summary:"
    if echo "${RESULTS_RESPONSE}" | jq -e '.[] | select(.model_name != null)' &>/dev/null; then
      # Direct array of results
      echo "${RESULTS_RESPONSE}" | jq -r '.[] | "Model: \(.model_name)\nCompliance Rate: \(.compliance_rate)\nAutonomy Score: \(.autonomy_score)\nTurns: \(.turns_count)\n"' > "${OUTPUT_DIR}/reports/summary.txt"
      echo "${RESULTS_RESPONSE}" | jq -r '.[] | "Model: \(.model_name)\nCompliance Rate: \(.compliance_rate)\nAutonomy Score: \(.autonomy_score)\nTurns: \(.turns_count)\n"'
    elif echo "${RESULTS_RESPONSE}" | jq -e '.results[] | select(.model_name != null)' &>/dev/null; then
      # Object with results array
      echo "${RESULTS_RESPONSE}" | jq -r '.results[] | "Model: \(.model_name)\nCompliance Rate: \(.compliance_rate)\nAutonomy Score: \(.autonomy_score)\nTurns: \(.turns_count)\n"' > "${OUTPUT_DIR}/reports/summary.txt"
      echo "${RESULTS_RESPONSE}" | jq -r '.results[] | "Model: \(.model_name)\nCompliance Rate: \(.compliance_rate)\nAutonomy Score: \(.autonomy_score)\nTurns: \(.turns_count)\n"'
    else
      # Unknown format, show what we got
      echo "Unable to automatically extract run details. See ${OUTPUT_DIR}/raw_data/results.json for full data."
    fi
    
    break
  elif [[ "${CURRENT_STATUS}" == "failed" || "${CURRENT_STATUS}" == "error" ]]; then
    echo "❌ Error: Batch run failed or errored."
    echo "Status Response: ${STATUS_RESPONSE}"
    # Save the error status
    echo "${STATUS_RESPONSE}" | jq '.' > "${OUTPUT_DIR}/raw_data/batch_status_error.json"
    exit 1
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