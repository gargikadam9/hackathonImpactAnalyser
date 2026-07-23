"""
Dependency Agent - Second agent in the pipeline.
Maps service dependencies and detects cascading impact.
"""

from typing import Dict, Any, List
from app.agents.base_agent import BaseAgent
from app.models import AgentType


class DependencyAgent(BaseAgent):
    """Agent responsible for analyzing service dependencies and cascading impacts."""

    def __init__(self, data_loader, embedding_service=None):
        super().__init__(AgentType.DEPENDENCY, data_loader, embedding_service)

    def process(self, input_data: Dict[str, Any], context: Dict[str, Any]) -> Dict[str, Any]:
        """Map dependencies and identify cascading impact."""
        primary_services = context.get("intake", {}).get("primary_services", [])
        services = self.data_loader.get_services()
        
        # Build dependency graph
        service_map = {s["name"]: s for s in services}
        
        all_impacted = []
        dependency_chain = []
        
        def traverse_dependencies(svc_name: str, visited: set, depth: int = 0):
            """Traverse dependency chain recursively."""
            if svc_name in visited or depth > 5:
                return
            visited.add(svc_name)
            if svc_name in service_map:
                svc = service_map[svc_name]
                all_impacted.append(svc_name)
                
                # Dependents of this service (services that depend on it)
                for dep_name in svc.get("dependents", []):
                    if dep_name not in visited:
                        dependency_chain.append({
                            "from": svc_name,
                            "to": dep_name,
                            "relationship": "depends_on_me",
                            "criticality": svc.get("criticality", "unknown")
                        })
                        traverse_dependencies(dep_name, visited, depth + 1)

        visited_services = set()
        for svc_name in primary_services:
            traverse_dependencies(svc_name, visited_services)

        # Get criticality and team info for impacted services
        impacted_details = []
        for name in all_impacted:
            if name in service_map:
                svc = service_map[name]
                impacted_details.append({
                    "name": name,
                    "criticality": svc.get("criticality", "unknown"),
                    "owner": svc.get("owner", "unknown"),
                    "type": svc.get("type", "unknown")
                })

        # Use LLM for additional analysis
        system_prompt = """You are a dependency analysis agent.
        Analyze the dependency chain and identify high-risk cascading impacts.
        Consider service criticality and dependency depth."""

        user_prompt = f"""
        Primary Services: {primary_services}
        All Impacted Services: {all_impacted}
        Dependency Chain: {dependency_chain}
        """

        llm_analysis = self._call_llm(system_prompt, user_prompt)

        result = {
            "primary_services": primary_services,
            "all_impacted_services": all_impacted,
            "impacted_details": impacted_details,
            "dependency_chain": dependency_chain,
            "cascade_depth": max([len(primary_services) if primary_services else 0, len(all_impacted)]),
            "llm_analysis": llm_analysis,
            "critical_services_impacted": [
                d["name"] for d in impacted_details if d.get("criticality") == "critical"
            ]
        }

        return result

    def _mock_agent_response(self, prompt: str) -> str:
        return """[Mock Dependency Analysis]
        Dependency Graph Analysis Complete:
        - payment-gateway (critical) depends on: database-proxy, auth-service
        - order-service (critical) depends on: payment-gateway, inventory-service
        - checkout-service (critical) depends on: payment-gateway, order-service
        Cascade Impact Level: 2 services directly impacted
        Critical Path: payment-gateway → order-service → checkout-service
        """

