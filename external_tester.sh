#!/bin/bash

# run with 
### BASE_URL="{your_url_for_fastapi" && chmod +x external_tester.sh && ./external_tester.sh

# Exit immediately if a command exits with a non-zero status.
set -e
# Treat unset variables as an error when substituting.
# set -u # Commented out as REPORT_PATH_SUFFIX might be empty if API changes
# Cause a pipeline to return the exit status of the last command in the pipe
# that returned a non-zero return value.
set -o pipefail


# --- Configuration ---
# YOU HAVE TO PUT BASE URL IN THE COMMAND SEE LINE 4
# BASE_URL=""
POLL_INTERVAL_SECONDS=10 # How often to check batch status

echo "🧪 Starting HermitBench Test Workflow..."
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
echo "----------------------------------------"

# --- Step 2 & 3: Check batch status and get results when completed ---
echo "🔄 Step 2 & 3: Monitoring batch status (ID: ${BATCH_ID})..."
while true; do
  STATUS_RESPONSE=$(curl -s -X GET "${BASE_URL}/api/batch/${BATCH_ID}")
  CURRENT_STATUS=$(echo "${STATUS_RESPONSE}" | jq -r .status)
  NUM_COMPLETED=$(echo "${STATUS_RESPONSE}" | jq -r .completed_tasks)
  NUM_TOTAL=$(echo "${STATUS_RESPONSE}" | jq -r .total_tasks)

  echo "Current status: ${CURRENT_STATUS} (${NUM_COMPLETED}/${NUM_TOTAL} runs completed)"

  if [[ "${CURRENT_STATUS}" == "completed" ]]; then
    echo "✅ Batch completed!"
    echo "Fetching results..."
    RESULTS_RESPONSE=$(curl -s -X GET "${BASE_URL}/api/batch/${BATCH_ID}/results")
    
    echo "Results fetched. Processing data..."
    
    # Check if response is an array or an object with items property
    if echo "${RESULTS_RESPONSE}" | jq -e 'type == "array"' >/dev/null; then
      # It's an array
      RESULTS_ARRAY="${RESULTS_RESPONSE}"
    elif echo "${RESULTS_RESPONSE}" | jq -e 'has("items")' >/dev/null; then
      # It's an object with items array
      RESULTS_ARRAY=$(echo "${RESULTS_RESPONSE}" | jq -r '.items')
    else
      # Unknown format, show raw data
      echo "Response format unexpected. Raw data:"
      echo "${RESULTS_RESPONSE}" | jq '.'
      break
    fi
    
    # Get count of results
    RESULT_COUNT=$(echo "${RESULTS_ARRAY}" | jq -r 'length')
    echo "Found ${RESULT_COUNT} result(s)."
    
    echo "Result summary:"
    echo "${RESULTS_ARRAY}" | jq -c '.[]' | while read -r result; do
      MODEL=$(echo "${result}" | jq -r '.model_name // "Unknown model"')
      COMPLIANCE=$(echo "${result}" | jq -r '.compliance_rate // "N/A"')
      AUTONOMY=$(echo "${result}" | jq -r '.autonomy_score // "N/A"')
      TURNS=$(echo "${result}" | jq -r '.turns_count // 0')
      
      echo "  - Model: ${MODEL}"
      echo "    Compliance Rate: ${COMPLIANCE}"
      echo "    Autonomy Score: ${AUTONOMY}"
      echo "    Turns: ${TURNS}"
      echo ""
    done
    
    break
  elif [[ "${CURRENT_STATUS}" == "failed" || "${CURRENT_STATUS}" == "error" ]]; then
    echo "❌ Error: Batch run failed or errored."
    echo "Status Response: ${STATUS_RESPONSE}"
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
  exit 1
fi
echo "✅ CSV summary report generation initiated."
echo "Download URL Suffix: ${DOWNLOAD_URL_SUFFIX}"
echo "Response: ${REPORT_URL_RESPONSE}"
echo "----------------------------------------"

# --- Step 5: Download the generated report ---
DOWNLOAD_FILENAME="hermitbench_summary_${BATCH_ID}.csv"
FULL_DOWNLOAD_URL="${BASE_URL}${DOWNLOAD_URL_SUFFIX}" # The download_url is already a full path from root

echo "📥 Step 5: Downloading the report from ${FULL_DOWNLOAD_URL} to ${DOWNLOAD_FILENAME}..."
curl -s -X GET "${FULL_DOWNLOAD_URL}" -o "${DOWNLOAD_FILENAME}"

if [[ -f "${DOWNLOAD_FILENAME}" && -s "${DOWNLOAD_FILENAME}" ]]; then
  echo "✅ Report downloaded successfully as ${DOWNLOAD_FILENAME}."
else
  echo "❌ Error: Failed to download or the downloaded file is empty."
  # Attempt to show error if the server returned one instead of a file
  # This assumes the server might return a JSON error if the GET fails for the file
  cat "${DOWNLOAD_FILENAME}"
  exit 1
fi
echo "----------------------------------------"

# --- Step 6 (Optional): Generate persona cards ---
echo "🎭 Step 6: Generating persona cards for BATCH_ID: ${BATCH_ID} (Optional)..."
PERSONA_RESPONSE=$(curl -s -X POST "${BASE_URL}/api/batch/${BATCH_ID}/personas")

# Extract model names from persona response
MODEL_NAMES=$(echo "${PERSONA_RESPONSE}" | jq -r 'keys[]' 2>/dev/null)

if [[ -n "$MODEL_NAMES" ]]; then
  echo "✅ Persona cards successfully generated for models:"
  for MODEL in ${MODEL_NAMES}; do
    echo "  - ${MODEL}"
    PERSONA_DESCRIPTION=$(echo "${PERSONA_RESPONSE}" | jq -r ".[\"${MODEL}\"].personality_description")
    if [[ -n "$PERSONA_DESCRIPTION" && "$PERSONA_DESCRIPTION" != "null" ]]; then
      echo "    Personality: ${PERSONA_DESCRIPTION:0:100}..."
    fi
  done
else
  echo "⚠️ Persona generation may not have returned expected format."
  echo "Response: ${PERSONA_RESPONSE}"
fi
echo "----------------------------------------"

# --- Step 7 (Optional): Generate a detailed scorecard ---
echo "📈 Step 7: Generating detailed scorecard for BATCH_ID: ${BATCH_ID} (Optional)..."
SCORECARD_PAYLOAD='{"report_type": "detailed_scorecard"}'

SCORECARD_RESPONSE=$(curl -s -X POST "${BASE_URL}/api/batch/${BATCH_ID}/report" \
  -H "Content-Type: application/json" \
  -d "${SCORECARD_PAYLOAD}")

DETAILED_SCORECARD_URL_SUFFIX=$(echo "${SCORECARD_RESPONSE}" | jq -r .download_url)
if [[ -n "$DETAILED_SCORECARD_URL_SUFFIX" && "$DETAILED_SCORECARD_URL_SUFFIX" != "null" ]]; then
  FULL_DETAILED_SCORECARD_URL="${BASE_URL}${DETAILED_SCORECARD_URL_SUFFIX}"
  DETAILED_SCORECARD_FILENAME="detailed_scorecard_${BATCH_ID}.json"
  echo "Downloading detailed scorecard from ${FULL_DETAILED_SCORECARD_URL} to ${DETAILED_SCORECARD_FILENAME}..."
  curl -s -X GET "${FULL_DETAILED_SCORECARD_URL}" -o "${DETAILED_SCORECARD_FILENAME}"
  echo "✅ Detailed scorecard downloaded as ${DETAILED_SCORECARD_FILENAME}."
else
  echo "ℹ️ No direct download URL for detailed scorecard in response, or an issue occurred."
  echo "Response: ${SCORECARD_RESPONSE}"
fi

echo "----------------------------------------"
echo "🎉 HermitBench Test Workflow Completed!"