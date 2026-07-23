"""
Multi-agent pipeline orchestrator.
Executes agents in order: intake -> dependency -> knowledge -> incident -> risk -> notification -> summary.
"""

import time
from typing import Dict, Any, Optional
from datetime import datetime

from app.models import ChangeImpactRequest, ChangeImpactResponse, AgentTrace
from app.rag.data_loader import DataLoader
from app.rag.embeddings import EmbeddingService
from app.agents.intake_agent import IntakeAgent
from app.agents.dependency_agent import DependencyAgent
from app.agents.knowledge_agent import KnowledgeAgent
from app.agents.incident_agent import IncidentAgent
from app.agents.risk_agent import RiskAgent
from app.agents.notification_agent import NotificationAgent
from app.agents.summary_agent import SummaryAgent


class AgentPipeline:
    """Orchestrates the multi-agent analysis pipeline."""

    def __init__(self, data_loader: Optional[DataLoader] = None,
                 embedding_service: Optional[EmbeddingService] = None):
        self.data_loader = data_loader or DataLoader()
        self.embeddings = embedding_service or EmbeddingService()

        # Initialize agents
        self.agents = {
            "intake": IntakeAgent(self.data_loader, self.embeddings),
            "dependency": DependencyAgent(self.data_loader, self.embeddings),
            "knowledge": KnowledgeAgent(self.data_loader, self.embeddings),
            "incident": IncidentAgent(self.data_loader, self.embeddings),
            "risk": RiskAgent(self.data_loader, self.embeddings),
            "notification": NotificationAgent(self.data_loader, self.embeddings),
            "summary": SummaryAgent(self.data_loader, self.embeddings)
        }

        self.pipeline_order = [
            "intake",
            "dependency",
            "knowledge",
            "incident",
            "risk",
            "notification",
            "summary"
        ]

    def analyze(self, request: ChangeImpactRequest) -> ChangeImpactResponse:
        """
        Execute the full multi-agent pipeline.
        
        Pipeline:
        1. Intake Agent - Analyze change request
        2. Dependency Agent - Map service dependencies
        3. Knowledge Agent - Retrieve relevant knowledge
        4. Incident Agent - Find similar incidents
        5. Risk Agent - Assess risk & mitigation
        6. Notification Agent - Determine notification targets
        7. Summary Agent - Generate final report
        """
        start_time = time.time()

        # Prepare input data
        input_data = {
            "change_title": request.change_title,
            "change_description": request.change_description,
            "change_type": request.change_type,
            "affected_services": request.affected_services,
            "priority": request.priority,
            "proposed_by": request.proposed_by,
            "environment": request.environment
        }

        # Shared context for pipeline execution
        context = {
            "start_time": start_time,
            "agent_traces": []
        }

        # Execute pipeline sequentially
        for agent_name in self.pipeline_order:
            agent = self.agents[agent_name]

            # Execute agent
            trace = agent.execute(input_data, context)
            context["agent_traces"].append(trace)

            # Store output in context for subsequent agents
            if trace.status == "completed":
                try:
                    import json
                    context[agent_name] = json.loads(trace.output) if trace.output else {}
                except (json.JSONDecodeError, TypeError):
                    context[agent_name] = {"output": trace.output}
            else:
                context[agent_name] = {"error": trace.error}

        # Get final summary from the context
        final_result = context.get("summary", {})
        agent_traces = context.get("agent_traces", [])

        # Build the response
        # Find summary agent output for the report
        summary_output = final_result

        response = ChangeImpactResponse(
            analysisId=summary_output.get("analysis_id", f"analysis-{hash(str(start_time)) % 1000000:06d}"),
            riskScore=summary_output.get("risk_score", 0.5),
            riskLevel=summary_output.get("risk_level", "medium"),
            confidence=summary_output.get("confidence", 0.7),
            impactedServices=summary_output.get("impacted_services", []),
            teamsToNotify=summary_output.get("teams_to_notify", ["Operations"]),
            potentialRisks=summary_output.get("potential_risks", ["Unknown risks"]),
            recommendedTests=summary_output.get("recommended_tests", ["Standard testing"]),
            similarIncidents=summary_output.get("similar_incidents", []),
            mitigationPlan=summary_output.get("mitigation_plan", ["Standard mitigation"]),
            executiveSummary=summary_output.get("executive_summary", "Analysis complete."),
            agentTraces=[t.dict() if hasattr(t, 'dict') else t for t in agent_traces],
            interpretedIntent=summary_output.get("interpreted_intent", input_data.get("change_title", "")),
            retrievedEvidence=summary_output.get("retrieved_evidence", []),
            dataSourcesUsed=summary_output.get("data_sources_used", ["cmdb.json"]),
            processingTimeMs=int((time.time() - start_time) * 1000),
            mockMode=self.embeddings.provider == "mock"
        )

        return response

    def classify_and_respond(self, message: str, conversation_history: list = None) -> dict:
        """
        Unified assistant route.
        Classifies input as conversation or change-analysis and responds accordingly.
        """
        # Simple classification logic
        change_keywords = [
            "change", "deploy", "impact", "risk", "migration", "upgrade",
            "release", "rollout", "modify", "update", "config", "database",
            "migrate", "incident", "analysis"
        ]
        
        message_lower = message.lower()
        is_change_analysis = any(kw in message_lower for kw in change_keywords)
        
        if is_change_analysis or len(message.split()) > 10:
            # Likely a change analysis request
            classification = "change-analysis"
            
            # Extract basic intent
            intent = {
                "type": "change_analysis",
                "requires_full_pipeline": True
            }
            
            reply = (
                "I've identified this as a change impact analysis request. "
                "I'll analyze the potential risks and impacts. "
                "Please provide more details about the proposed change."
            )
            
            suggested_actions = [
                "Run full impact analysis",
                "View similar past incidents",
                "Check service dependencies"
            ]
        else:
            # General conversation
            classification = "conversation"
            intent = {"type": "general_chat"}
            reply = self._generate_chat_response(message, conversation_history)
            suggested_actions = [
                "Ask about architecture",
                "Query past incidents",
                "Check change history"
            ]
        
        return {
            "classification": classification,
            "reply": reply,
            "extracted_intent": intent,
            "suggested_actions": suggested_actions
        }

    def _generate_chat_response(self, message: str, history: list = None) -> str:
        """Generate a conversational response."""
        message_lower = message.lower()
        
        # Simple rule-based chat responses
        if "hello" in message_lower or "hi" in message_lower:
            return "Hello! I'm the AI Change Impact Analyzer. I can help analyze the impact of proposed changes, review past incidents, or answer questions about the system architecture."
        elif "help" in message_lower:
            return "I can help with:\n1. **Change Impact Analysis** - Describe a proposed change, and I'll analyze risks\n2. **Incident Lookup** - Search past incidents\n3. **Architecture Questions** - Answer questions about the system"
        elif "architecture" in message_lower:
            return "The system consists of 19 microservices organized by domain: Commerce, Order, Platform, Data & ML, Security. Key components include payment-gateway, order-service, user-service, and api-gateway."
        elif "incident" in message_lower:
            return "I have access to 50+ historical incidents. The most common issues involve database connection problems, Kafka consumer lag, and configuration changes."
        elif "thank" in message_lower:
            return "You're welcome! Feel free to ask if you need any further analysis or have more questions."
        else:
            return "I understand your message. Would you like me to perform a change impact analysis, look up information about the system, or help with something else?"

    def get_change_types(self) -> list:
        """Get available change types."""
        return [
            {"id": "infrastructure", "name": "Infrastructure", "description": "Infrastructure changes (DB, network, k8s)", "risk_default": "high"},
            {"id": "enhancement", "name": "Enhancement", "description": "Feature enhancements and improvements", "risk_default": "medium"},
            {"id": "bugfix", "name": "Bug Fix", "description": "Bug fixes and patches", "risk_default": "low"},
            {"id": "security", "name": "Security", "description": "Security patches and configuration", "risk_default": "high"},
            {"id": "rollback", "name": "Rollback", "description": "Rollback to previous version", "risk_default": "medium"},
            {"id": "data", "name": "Data Update", "description": "Data updates and migrations", "risk_default": "medium"},
            {"id": "policy", "name": "Policy Change", "description": "Policy or process changes", "risk_default": "low"},
            {"id": "research", "name": "Research", "description": "Research and evaluation", "risk_default": "low"}
        ]

    def get_components(self) -> list:
        """Get all tracked components."""
        services = self.data_loader.get_services()
        return [
            {
                "id": svc["id"],
                "name": svc["name"],
                "type": svc.get("type", "unknown"),
                "criticality": svc.get("criticality", "unknown"),
                "owner": svc.get("owner", "unknown"),
                "dependencies": svc.get("dependencies", [])
            }
            for svc in services
        ]

    def get_technical_details(self) -> dict:
        """Get system technical details."""
        arch = self.data_loader.get_architecture()
        services = self.data_loader.get_services()
        
        # Count by type
        type_counts = {}
        for svc in services:
            svc_type = svc.get("type", "unknown")
            type_counts[svc_type] = type_counts.get(svc_type, 0) + 1

        return {
            "total_services": len(services),
            "service_types": type_counts,
            "architecture_overview": arch.get("content", "")[:1000] if arch.get("content") else "",
            "technologies": ["Java", "Python", "Go", "Node.js", "Rust", "C#"],
            "databases": ["PostgreSQL", "MySQL", "MongoDB", "Redis", "Elasticsearch", "TimescaleDB", "ClickHouse"],
            "message_queues": ["Kafka", "RabbitMQ"],
            "deployment": "Kubernetes"
        }

