"""
Database models for HermitBench application.
"""
from sqlalchemy import Column, Integer, String, Float, Boolean, DateTime, ForeignKey, JSON, Text
from sqlalchemy.orm import relationship
from datetime import datetime

from app.database import Base

class Model(Base):
    """Model information."""
    __tablename__ = "models"
    
    id = Column(Integer, primary_key=True, index=True)
    model_id = Column(String, unique=True, index=True)
    name = Column(String)
    description = Column(Text, nullable=True)
    context_length = Column(Integer, nullable=True)
    pricing = Column(JSON, nullable=True)
    
    runs = relationship("Run", back_populates="model")
    summaries = relationship("ModelSummary", back_populates="model")

class Run(Base):
    """Results from a single model run."""
    __tablename__ = "runs"
    
    id = Column(Integer, primary_key=True, index=True)
    run_id = Column(String, unique=True, index=True)
    batch_id = Column(String, index=True)
    model_id = Column(String, ForeignKey("models.model_id"))
    timestamp = Column(DateTime, default=datetime.now)
    conversation = Column(JSON)
    compliance_rate = Column(Float, nullable=True)
    failure_count = Column(Integer, nullable=True)
    malformed_braces_count = Column(Integer, nullable=True)
    mirror_test_passed = Column(Boolean, nullable=True)
    autonomy_score = Column(Float, nullable=True)
    turns_count = Column(Integer, default=0)
    topics = Column(JSON, default=list)
    exploration_style = Column(String, nullable=True)
    judge_evaluation = Column(JSON, nullable=True)
    
    model = relationship("Model", back_populates="runs")

class ModelSummary(Base):
    """Summary of results across multiple runs for a model."""
    __tablename__ = "model_summaries"
    
    id = Column(Integer, primary_key=True, index=True)
    batch_id = Column(String, index=True)
    model_id = Column(String, ForeignKey("models.model_id"))
    total_runs = Column(Integer)
    avg_compliance_rate = Column(Float)
    avg_failures = Column(Float)
    avg_malformed_braces = Column(Float)
    mirror_test_pass_rate = Column(Float)
    avg_autonomy_score = Column(Float)
    thematic_synthesis = Column(Text, nullable=True)
    
    model = relationship("Model", back_populates="summaries")

class Batch(Base):
    """Batch run information."""
    __tablename__ = "batches"
    
    id = Column(Integer, primary_key=True, index=True)
    batch_id = Column(String, unique=True, index=True)
    status = Column(String)  # running, completed, error
    total_tasks = Column(Integer)
    completed_tasks = Column(Integer, default=0)
    error = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.now)
    completed_at = Column(DateTime, nullable=True)
    config = Column(JSON)  # Store batch configuration

class Report(Base):
    """Generated reports."""
    __tablename__ = "reports"
    
    id = Column(Integer, primary_key=True, index=True)
    batch_id = Column(String, index=True)
    report_type = Column(String)  # csv_results, csv_summary, detailed_scorecard
    filename = Column(String)
    created_at = Column(DateTime, default=datetime.now)
    file_path = Column(String, nullable=True)  # Path to stored report file, if applicable