"""
API routes for the HermitBench application.
"""
from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks, Request, status, Response
from typing import List, Dict, Any, Optional, Union
import asyncio
import logging
import json
from datetime import datetime
import csv
from io import StringIO
import uuid
from sqlalchemy.orm import Session
from app.database import SessionLocal
from sqlalchemy.exc import SQLAlchemyError
from fastapi.responses import JSONResponse, StreamingResponse, FileResponse

from app.api.models import (
    InteractionRequest, 
    BatchInteractionRequest,
    ModelListResponse,
    InteractionResponse,
    BatchInteractionResponse,
    ModelSummaryResponse,
    PersonaCardResponse,
    GenerateReportRequest
)
from app.core.hermit_bench import HermitBench
from app.config import AppSettings
from app.database import get_db
from app.db_models import Model as DbModel, Run as DbRun, ModelSummary as DbModelSummary, Batch as DbBatch, Report as DbReport

# Configure logger
logger = logging.getLogger(__name__)

# Create router
router = APIRouter(prefix="/api", tags=["hermitbench"])

def get_settings(request: Request) -> AppSettings:
    """
    Get application settings from the request state.
    
    Args:
        request: FastAPI request object
        
    Returns:
        Application settings
    """
    return request.app.state.settings

def get_hermit_bench(settings: AppSettings = Depends(get_settings)) -> HermitBench:
    """
    Get a HermitBench instance with the provided settings.
    
    Args:
        settings: Application settings
        
    Returns:
        HermitBench instance
    """
    return HermitBench(settings)

@router.get("/models", response_model=ModelListResponse)
async def get_models(
    hermit_bench: HermitBench = Depends(get_hermit_bench),
    db: Session = Depends(get_db)
):
    """
    Get a list of available models from OpenRouter.
    
    Returns:
        List of model information
    """
    try:
        models = await hermit_bench.get_available_models()
        
        # Store models in database if they don't exist
        for model_data in models:
            model_id = model_data.get("id")
            if model_id:
                # Check if model exists
                existing_model = db.query(DbModel).filter(DbModel.model_id == model_id).first()
                if not existing_model:
                    # Create new model record
                    db_model = DbModel(
                        model_id=model_id,
                        name=model_data.get("name"),
                        description=model_data.get("description"),
                        context_length=model_data.get("context_length"),
                        pricing=model_data.get("pricing")
                    )
                    db.add(db_model)
                else:
                    # Update existing model
                    existing_model.name = model_data.get("name", existing_model.name)
                    existing_model.description = model_data.get("description", existing_model.description)
                    existing_model.context_length = model_data.get("context_length", existing_model.context_length)
                    existing_model.pricing = model_data.get("pricing", existing_model.pricing)
        
        # Commit changes
        db.commit()
        
        return {"models": models}
    except SQLAlchemyError as db_error:
        db.rollback()
        logger.error(f"Database error while processing models: {str(db_error)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Database error: {str(db_error)}"
        )
    except Exception as e:
        logger.error(f"Error fetching models: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to fetch models: {str(e)}"
        )

@router.post("/run", response_model=InteractionResponse)
async def run_interaction(
    request: InteractionRequest,
    hermit_bench: HermitBench = Depends(get_hermit_bench),
    db: Session = Depends(get_db)
):
    """
    Run a single autonomous interaction with the specified model.
    
    Args:
        request: Interaction request with model and parameters
        
    Returns:
        Results of the interaction
    """
    try:
        result = await hermit_bench.run_autonomous_interaction(
            model_name=request.model_name,
            temperature=request.temperature,
            top_p=request.top_p,
            max_turns=request.max_turns
        )
        
        # Store the result in the database
        # First make sure the model exists
        model = db.query(DbModel).filter(DbModel.model_id == result.model_name).first()
        if not model:
            # Create model entry if it doesn't exist
            model = DbModel(
                model_id=result.model_name,
                name=result.model_name
            )
            db.add(model)
            db.flush()
        
        # Store the run
        db_run = DbRun(
            run_id=result.run_id,
            model_id=result.model_name,
            timestamp=result.timestamp,
            conversation=result.conversation.dict(),
            compliance_rate=result.compliance_rate,
            failure_count=result.failure_count,
            malformed_braces_count=result.malformed_braces_count,
            mirror_test_passed=result.mirror_test_passed,
            autonomy_score=result.autonomy_score,
            turns_count=result.turns_count,
            topics=result.topics,
            exploration_style=result.exploration_style,
            judge_evaluation=result.judge_evaluation
        )
        db.add(db_run)
        db.commit()
        
        return {
            "run_id": result.run_id,
            "model_name": result.model_name,
            "timestamp": result.timestamp,
            "conversation": result.conversation,
            "compliance_rate": result.compliance_rate,
            "failure_count": result.failure_count,
            "malformed_braces_count": result.malformed_braces_count,
            "mirror_test_passed": result.mirror_test_passed,
            "autonomy_score": result.autonomy_score,
            "turns_count": result.turns_count,
            "topics": result.topics,
            "exploration_style": result.exploration_style,
            "judge_evaluation": result.judge_evaluation
        }
    except SQLAlchemyError as db_error:
        db.rollback()
        logger.error(f"Database error storing interaction result: {str(db_error)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Database error: {str(db_error)}"
        )
    except Exception as e:
        logger.error(f"Error running interaction: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to run interaction: {str(e)}"
        )

@router.post("/run-batch", response_model=BatchInteractionResponse)
async def run_batch(
    request: BatchInteractionRequest,
    background_tasks: BackgroundTasks,
    hermit_bench: HermitBench = Depends(get_hermit_bench),
    db: Session = Depends(get_db)
):
    """
    Start a batch of autonomous interactions with multiple models.
    
    Args:
        request: Batch interaction request with models and parameters
        background_tasks: FastAPI background tasks
        
    Returns:
        Batch ID and status information
    """
    # Generate a batch ID
    batch_id = f"batch_{uuid.uuid4().hex[:8]}"
    total_tasks = len(request.models) * request.num_runs_per_model
    
    # Initialize batch in database
    db_batch = DbBatch(
        batch_id=batch_id,
        status="running",
        total_tasks=total_tasks,
        completed_tasks=0,
        config={
            "models": request.models,
            "num_runs_per_model": request.num_runs_per_model,
            "temperature": request.temperature,
            "top_p": request.top_p,
            "max_runs": request.max_turns,
            "task_delay_ms": request.task_delay_ms
        }
    )
    db.add(db_batch)
    db.commit()
    
    # Function to run the batch in the background
    async def run_batch_task():
        db_session = SessionLocal()
        try:
            # Run the batch
            results_dict = await hermit_bench.run_batch_interaction(
                models=request.models,
                num_runs_per_model=request.num_runs_per_model,
                temperature=request.temperature,
                top_p=request.top_p,
                max_turns=request.max_turns,
                task_delay_ms=request.task_delay_ms,
                progress_callback=lambda completed, total: update_progress(batch_id, completed)
            )
            
            # Store results in database
            for model_name, model_results in results_dict.items():
                # Make sure model exists
                model = db_session.query(DbModel).filter(DbModel.model_id == model_name).first()
                if not model:
                    model = DbModel(
                        model_id=model_name,
                        name=model_name
                    )
                    db_session.add(model)
                    db_session.flush()
                
                # Store all runs for this model
                for result in model_results:
                    db_run = DbRun(
                        run_id=result.run_id,
                        batch_id=batch_id,
                        model_id=model_name,
                        timestamp=result.timestamp,
                        conversation=result.conversation.dict(),
                        compliance_rate=result.compliance_rate,
                        failure_count=result.failure_count,
                        malformed_braces_count=result.malformed_braces_count,
                        mirror_test_passed=result.mirror_test_passed,
                        autonomy_score=result.autonomy_score,
                        turns_count=result.turns_count,
                        topics=result.topics,
                        exploration_style=result.exploration_style,
                        judge_evaluation=result.judge_evaluation
                    )
                    db_session.add(db_run)
                
                # Generate and store summary for this model
                if model_results:
                    summary = await hermit_bench.generate_model_summary(model_name, model_results)
                    db_summary = DbModelSummary(
                        batch_id=batch_id,
                        model_id=model_name,
                        total_runs=summary.total_runs,
                        avg_compliance_rate=summary.avg_compliance_rate,
                        avg_failures=summary.avg_failures,
                        avg_malformed_braces=summary.avg_malformed_braces,
                        mirror_test_pass_rate=summary.mirror_test_pass_rate,
                        avg_autonomy_score=summary.avg_autonomy_score,
                        thematic_synthesis=summary.thematic_synthesis
                    )
                    db_session.add(db_summary)
            
            # Update batch status
            batch = db_session.query(DbBatch).filter(DbBatch.batch_id == batch_id).first()
            if batch:
                batch.status = "completed"
                batch.completed_tasks = total_tasks
                batch.completed_at = datetime.now()
            
            db_session.commit()
        
        except Exception as e:
            logger.error(f"Error in batch task: {str(e)}")
            # Update batch error status in database
            try:
                batch = db_session.query(DbBatch).filter(DbBatch.batch_id == batch_id).first()
                if batch:
                    batch.status = "error"
                    batch.error = str(e)
                    db_session.commit()
            except Exception as db_error:
                logger.error(f"Error updating batch status: {str(db_error)}")
                db_session.rollback()
        finally:
            db_session.close()
    
    # Function to update progress
    def update_progress(batch_id, completed_tasks):
        """Update batch progress in database."""
        try:
            with SessionLocal() as session:
                batch = session.query(DbBatch).filter(DbBatch.batch_id == batch_id).first()
                if batch:
                    batch.completed_tasks = completed_tasks
                    session.commit()
        except Exception as e:
            logger.error(f"Error updating batch progress: {str(e)}")
    
    # Start the batch task in the background
    background_tasks.add_task(run_batch_task)
    
    return {
        "batch_id": batch_id,
        "status": "running",
        "total_tasks": total_tasks,
        "completed_tasks": 0,
        "error": None
    }

@router.get("/batch/{batch_id}", response_model=BatchInteractionResponse)
async def get_batch_status(batch_id: str):
    """
    Get the status of a batch interaction.
    
    Args:
        batch_id: ID of the batch
        
    Returns:
        Current status of the batch
    """
    if batch_id not in batch_results:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Batch ID {batch_id} not found"
        )
    
    batch = batch_results[batch_id]
    
    return {
        "batch_id": batch_id,
        "status": batch["status"],
        "total_tasks": batch["total_tasks"],
        "completed_tasks": batch["completed_tasks"],
        "error": batch["error"]
    }

@router.get("/batch/{batch_id}/results")
async def get_batch_results(batch_id: str):
    """
    Get the results of a completed batch interaction.
    
    Args:
        batch_id: ID of the batch
        
    Returns:
        Results of the batch
    """
    if batch_id not in batch_results:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Batch ID {batch_id} not found"
        )
    
    batch = batch_results[batch_id]
    
    if batch["status"] != "completed":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Batch {batch_id} is not completed yet (status: {batch['status']})"
        )
    
    return {"results": batch["results"]}

@router.get("/batch/{batch_id}/summaries", response_model=Dict[str, ModelSummaryResponse])
async def get_batch_summaries(batch_id: str):
    """
    Get the model summaries for a completed batch interaction.
    
    Args:
        batch_id: ID of the batch
        
    Returns:
        Summaries for each model in the batch
    """
    if batch_id not in batch_results:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Batch ID {batch_id} not found"
        )
    
    batch = batch_results[batch_id]
    
    if batch["status"] != "completed":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Batch {batch_id} is not completed yet (status: {batch['status']})"
        )
    
    return batch["summaries"]

@router.post("/batch/{batch_id}/personas", response_model=Dict[str, PersonaCardResponse])
async def generate_persona_cards(
    batch_id: str,
    hermit_bench: HermitBench = Depends(get_hermit_bench)
):
    """
    Generate persona cards for models in a completed batch.
    
    Args:
        batch_id: ID of the batch
        
    Returns:
        Persona cards for each model
    """
    if batch_id not in batch_results:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Batch ID {batch_id} not found"
        )
    
    batch = batch_results[batch_id]
    
    if batch["status"] != "completed":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Batch {batch_id} is not completed yet (status: {batch['status']})"
        )
    
    try:
        personas = await hermit_bench.generate_persona_cards(batch["results"])
        return personas
    
    except Exception as e:
        logger.error(f"Error generating persona cards: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to generate persona cards: {str(e)}"
        )

@router.post("/batch/{batch_id}/report", response_model=Dict[str, str])
async def generate_report(
    batch_id: str,
    request: GenerateReportRequest
):
    """
    Generate a report for a completed batch interaction.
    
    Args:
        batch_id: ID of the batch
        request: Report generation options
        
    Returns:
        URL to download the report
    """
    if batch_id not in batch_results:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Batch ID {batch_id} not found"
        )
    
    batch = batch_results[batch_id]
    
    if batch["status"] != "completed":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Batch {batch_id} is not completed yet (status: {batch['status']})"
        )
    
    report_type = request.report_type
    
    if report_type == "csv_results":
        return await generate_csv_results(batch_id)
    elif report_type == "csv_summary":
        return await generate_csv_summary(batch_id)
    elif report_type == "detailed_scorecard":
        return await generate_detailed_scorecard(batch_id)
    else:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Unsupported report type: {report_type}"
        )

async def generate_csv_results(batch_id: str) -> Dict[str, str]:
    """
    Generate a CSV table of all runs in a batch.
    
    Args:
        batch_id: ID of the batch
        
    Returns:
        CSV content as a string
    """
    batch = batch_results[batch_id]
    results = batch["results"]
    
    # Convert to CSV
    output = StringIO()
    writer = csv.writer(output)
    
    # Write header
    writer.writerow([
        "Row", "Model Name", "Run", "Compliance Rate", "Failures", 
        "Malformed Braces", "Mirror Test", "Autonomy Score",
        "Turns", "Topics", "Exploration Style", "Date"
    ])
    
    # Write rows
    row_num = 1
    for model, model_results in results.items():
        for i, result in enumerate(model_results):
            writer.writerow([
                row_num,
                result.model_name,
                i + 1,
                f"{result.compliance_rate * 100:.1f}%" if result.compliance_rate is not None else "N/A",
                result.failure_count if result.failure_count is not None else "N/A",
                result.malformed_braces_count if result.malformed_braces_count is not None else "N/A",
                "Pass" if result.mirror_test_passed else "Fail",
                f"{result.autonomy_score:.1f}" if result.autonomy_score is not None else "N/A",
                result.turns_count,
                ", ".join(result.topics) if result.topics else "N/A",
                result.exploration_style if result.exploration_style else "N/A",
                result.timestamp.strftime("%Y-%m-%d %H:%M:%S")
            ])
            row_num += 1
    
    return {"content": output.getvalue(), "filename": f"hermitbench_results_{batch_id}.csv"}

async def generate_csv_summary(batch_id: str) -> Dict[str, str]:
    """
    Generate a CSV summary table for a batch.
    
    Args:
        batch_id: ID of the batch
        
    Returns:
        CSV content as a string
    """
    batch = batch_results[batch_id]
    summaries = batch["summaries"]
    
    # Convert to CSV
    output = StringIO()
    writer = csv.writer(output)
    
    # Write header
    writer.writerow([
        "Model Name", "Total Runs", "Avg. Compliance Rate (%)",
        "Avg. Failures", "Avg. Malformed Braces",
        "Mirror Test Pass Rate (%)", "Avg. Autonomy Score"
    ])
    
    # Write rows
    for model, summary in summaries.items():
        writer.writerow([
            summary.model_name,
            summary.total_runs,
            f"{summary.avg_compliance_rate * 100:.1f}%",
            f"{summary.avg_failures:.2f}",
            f"{summary.avg_malformed_braces:.2f}",
            f"{summary.mirror_test_pass_rate:.1f}%",
            f"{summary.avg_autonomy_score:.1f}"
        ])
    
    return {"content": output.getvalue(), "filename": f"hermitbench_summary_{batch_id}.csv"}

async def generate_detailed_scorecard(batch_id: str) -> Dict[str, str]:
    """
    Generate a detailed scorecard for a batch.
    
    Args:
        batch_id: ID of the batch
        
    Returns:
        JSON content as a string
    """
    batch = batch_results[batch_id]
    
    # Create detailed scorecard
    scorecard = {
        "batch_id": batch_id,
        "timestamp": datetime.now().isoformat(),
        "models": {}
    }
    
    # Add model results
    for model, model_results in batch["results"].items():
        model_data = {
            "runs": [],
            "summary": batch["summaries"].get(model, {})
        }
        
        for result in model_results:
            run_data = {
                "run_id": result.run_id,
                "timestamp": result.timestamp.isoformat(),
                "compliance_rate": result.compliance_rate,
                "failure_count": result.failure_count,
                "malformed_braces_count": result.malformed_braces_count,
                "mirror_test_passed": result.mirror_test_passed,
                "autonomy_score": result.autonomy_score,
                "turns_count": result.turns_count,
                "topics": result.topics,
                "exploration_style": result.exploration_style,
                "judge_evaluation": result.judge_evaluation
            }
            model_data["runs"].append(run_data)
        
        scorecard["models"][model] = model_data
    
    return {
        "content": json.dumps(scorecard, indent=2),
        "filename": f"hermitbench_scorecard_{batch_id}.json"
    }

@router.get("/batch/{batch_id}/download-report")
async def download_report(batch_id: str, filename: str, content: str):
    """
    Download a generated report.
    
    Args:
        batch_id: ID of the batch
        filename: Name of the file to download
        content: Content of the report
        
    Returns:
        Downloadable file
    """
    # Determine content type based on file extension
    if filename.endswith(".csv"):
        media_type = "text/csv"
    elif filename.endswith(".json"):
        media_type = "application/json"
    else:
        media_type = "text/plain"
    
    # Return the content as a downloadable file
    return StreamingResponse(
        iter([content]), 
        media_type=media_type,
        headers={"Content-Disposition": f"attachment; filename={filename}"}
    )

@router.post("/test-run")
async def run_standard_test(
    background_tasks: BackgroundTasks,
    hermit_bench: HermitBench = Depends(get_hermit_bench)
):
    """
    Run a standard test with predefined models and parameters.
    
    Returns:
        Results of the test run
    """
    # Standard test configuration - use a small set of models for testing
    test_models = ["anthropic/claude-3-haiku-20240307"]
    
    # Generate a batch ID for this test run
    batch_id = f"test_run_{datetime.now().strftime('%Y%m%d%H%M%S')}"
    
    # Initialize batch status
    batch_results[batch_id] = {
        "status": "running",
        "total_tasks": len(test_models),
        "completed_tasks": 0,
        "results": {},
        "summaries": {},
        "error": None
    }
    
    # Define the function to run the batch in background
    async def run_test_batch():
        try:
            # Start a batch with standard parameters
            results = await hermit_bench.run_batch_interaction(
                models=test_models,
                num_runs_per_model=1,
                temperature=0.7,
                top_p=1.0,
                max_turns=5,
                task_delay_ms=1000
            )
            
            # Store the results
            batch_results[batch_id]["results"] = results
            
            # Generate summaries for each model
            summaries = {}
            for model, model_results in results.items():
                if model_results:
                    summary = await hermit_bench.generate_model_summary(model_results)
                    summaries[model] = summary
            
            # Store the summaries
            batch_results[batch_id]["summaries"] = summaries
            batch_results[batch_id]["status"] = "completed"
        
        except Exception as error:
            logger.error(f"Error in test batch: {str(error)}")
            batch_results[batch_id]["status"] = "error"
            batch_results[batch_id]["error"] = str(error)
    
    # Start the batch task in the background
    background_tasks.add_task(run_test_batch)
    
    # Return the batch ID
    return {
        "status": "started",
        "message": "Standard test run started",
        "batch_id": batch_id
    }
