package com.changeanalyzer.service;

import com.changeanalyzer.model.Analysis;
import com.changeanalyzer.repository.AnalysisRepository;
import com.fasterxml.jackson.core.JsonProcessingException;
import com.fasterxml.jackson.databind.JsonNode;
import com.fasterxml.jackson.databind.ObjectMapper;
import com.fasterxml.jackson.databind.node.ObjectNode;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.beans.factory.annotation.Value;
import org.springframework.stereotype.Service;
import org.springframework.web.reactive.function.client.WebClient;
import reactor.core.publisher.Mono;

import java.time.Duration;
import java.util.*;

@Service
public class AiServiceClient {

    private static final Logger log = LoggerFactory.getLogger(AiServiceClient.class);

    private final WebClient webClient;
    private final AnalysisRepository analysisRepository;
    private final ObjectMapper objectMapper;

    @Value("${ai-service.url}")
    private String aiServiceUrl;

    @Value("${ai-service.timeout:30000}")
    private int timeout;

    @Autowired
    public AiServiceClient(WebClient webClient, AnalysisRepository analysisRepository, 
                          ObjectMapper objectMapper) {
        this.webClient = webClient;
        this.analysisRepository = analysisRepository;
        this.objectMapper = objectMapper;
    }

    /**
     * Proxy a change impact analysis request to the AI service.
     */
    public JsonNode analyzeChangeImpact(String changeTitle, String changeDescription,
                                         String changeType, List<String> affectedServices,
                                         String priority) {
        try {
            ObjectNode requestBody = objectMapper.createObjectNode();
            requestBody.put("change_title", changeTitle);
            requestBody.put("change_description", changeDescription);
            requestBody.put("change_type", changeType != null ? changeType : "enhancement");
            requestBody.put("priority", priority != null ? priority : "medium");

            if (affectedServices != null && !affectedServices.isEmpty()) {
                var servicesArray = requestBody.putArray("affected_services");
                affectedServices.forEach(servicesArray::add);
            }

            String responseJson = webClient.post()
                    .uri(aiServiceUrl + "/api/v1/change-impact/analyze")
                    .bodyValue(requestBody)
                    .retrieve()
                    .bodyToMono(String.class)
                    .timeout(Duration.ofMillis(timeout))
                    .block();

            JsonNode response = objectMapper.readTree(responseJson);

            // Persist to H2
            persistAnalysis(changeTitle, changeDescription, changeType, response);

            return response;
        } catch (Exception e) {
            log.error("Failed to call AI service: {}", e.getMessage());
            return createErrorResponse("AI Service unavailable: " + e.getMessage());
        }
    }

    /**
     * Proxy a chat request to the AI service.
     */
    public JsonNode chat(String message, List<Map<String, String>> conversationHistory) {
        try {
            ObjectNode requestBody = objectMapper.createObjectNode();
            requestBody.put("message", message);

            if (conversationHistory != null && !conversationHistory.isEmpty()) {
                var historyArray = requestBody.putArray("conversation_history");
                for (Map<String, String> msg : conversationHistory) {
                    ObjectNode historyItem = objectMapper.createObjectNode();
                    historyItem.put("role", msg.getOrDefault("role", "user"));
                    historyItem.put("content", msg.getOrDefault("content", ""));
                    historyArray.add(historyItem);
                }
            }

            String responseJson = webClient.post()
                    .uri(aiServiceUrl + "/api/v1/chat/general")
                    .bodyValue(requestBody)
                    .retrieve()
                    .bodyToMono(String.class)
                    .timeout(Duration.ofMillis(timeout))
                    .block();

            return objectMapper.readTree(responseJson);
        } catch (Exception e) {
            log.error("Failed to call AI chat service: {}", e.getMessage());
            return createErrorResponse("Chat service unavailable: " + e.getMessage());
        }
    }

    /**
     * Proxy an assistant request to the AI service.
     */
    public JsonNode assistantRespond(String message, List<Map<String, String>> conversationHistory) {
        try {
            ObjectNode requestBody = objectMapper.createObjectNode();
            requestBody.put("message", message);

            if (conversationHistory != null && !conversationHistory.isEmpty()) {
                var historyArray = requestBody.putArray("conversation_history");
                for (Map<String, String> msg : conversationHistory) {
                    ObjectNode historyItem = objectMapper.createObjectNode();
                    historyItem.put("role", msg.getOrDefault("role", "user"));
                    historyItem.put("content", msg.getOrDefault("content", ""));
                    historyArray.add(historyItem);
                }
            }

            String responseJson = webClient.post()
                    .uri(aiServiceUrl + "/api/v1/assistant/respond")
                    .bodyValue(requestBody)
                    .retrieve()
                    .bodyToMono(String.class)
                    .timeout(Duration.ofMillis(timeout))
                    .block();

            return objectMapper.readTree(responseJson);
        } catch (Exception e) {
            log.error("Failed to call AI assistant service: {}", e.getMessage());
            return createErrorResponse("Assistant service unavailable: " + e.getMessage());
        }
    }

    /**
     * Proxy a change impact analyze-prompt request.
     */
    public JsonNode analyzeChangeImpactFromPrompt(Map<String, Object> prompt) {
        try {
            ObjectNode requestBody = objectMapper.valueToTree(prompt);

            String responseJson = webClient.post()
                    .uri(aiServiceUrl + "/api/v1/change-impact/analyze-prompt")
                    .bodyValue(requestBody)
                    .retrieve()
                    .bodyToMono(String.class)
                    .timeout(Duration.ofMillis(timeout))
                    .block();

            JsonNode response = objectMapper.readTree(responseJson);

            // Persist
            String title = (String) prompt.getOrDefault("title", prompt.getOrDefault("change_title", "Prompt Analysis"));
            String description = (String) prompt.getOrDefault("description", prompt.getOrDefault("message", ""));
            String type = (String) prompt.getOrDefault("change_type", prompt.getOrDefault("type", "enhancement"));
            persistAnalysis(title, description, type, response);

            return response;
        } catch (Exception e) {
            log.error("Failed to call AI prompt analysis: {}", e.getMessage());
            return createErrorResponse("Analysis service unavailable: " + e.getMessage());
        }
    }

    /**
     * Get change types from AI service.
     */
    public JsonNode getChangeTypes() {
        try {
            String responseJson = webClient.get()
                    .uri(aiServiceUrl + "/api/v1/change-types")
                    .retrieve()
                    .bodyToMono(String.class)
                    .timeout(Duration.ofMillis(timeout))
                    .block();
            return objectMapper.readTree(responseJson);
        } catch (Exception e) {
            log.error("Failed to get change types: {}", e.getMessage());
            return objectMapper.createArrayNode();
        }
    }

    /**
     * Get components from AI service.
     */
    public JsonNode getComponents() {
        try {
            String responseJson = webClient.get()
                    .uri(aiServiceUrl + "/api/v1/components")
                    .retrieve()
                    .bodyToMono(String.class)
                    .timeout(Duration.ofMillis(timeout))
                    .block();
            return objectMapper.readTree(responseJson);
        } catch (Exception e) {
            log.error("Failed to get components: {}", e.getMessage());
            return objectMapper.createArrayNode();
        }
    }

    /**
     * Get technical details from AI service.
     */
    public JsonNode getTechnicalDetails() {
        try {
            String responseJson = webClient.get()
                    .uri(aiServiceUrl + "/api/v1/system/technical-details")
                    .retrieve()
                    .bodyToMono(String.class)
                    .timeout(Duration.ofMillis(timeout))
                    .block();
            return objectMapper.readTree(responseJson);
        } catch (Exception e) {
            log.error("Failed to get technical details: {}", e.getMessage());
            return createErrorResponse("Technical details unavailable: " + e.getMessage());
        }
    }

    /**
     * Get analysis history (latest 20).
     */
    public List<Analysis> getAnalysisHistory() {
        return analysisRepository.findTop20ByOrderByCreatedAtDesc();
    }

    /**
     * Get a single analysis by ID.
     */
    public Analysis getAnalysisById(String analysisId) {
        return analysisRepository.findByAnalysisId(analysisId);
    }

    /**
     * Persist analysis result to H2 database.
     */
    private void persistAnalysis(String changeTitle, String changeDescription, 
                                  String changeType, JsonNode response) {
        try {
            Analysis analysis = new Analysis();
            analysis.setAnalysisId(response.has("analysisId") ? 
                response.get("analysisId").asText() : UUID.randomUUID().toString().substring(0, 12));
            analysis.setChangeTitle(changeTitle);
            analysis.setChangeDescription(changeDescription);
            analysis.setChangeType(changeType != null ? changeType : "enhancement");
            analysis.setRiskScore(response.has("riskScore") ? response.get("riskScore").asDouble() : 0.0);
            analysis.setRiskLevel(response.has("riskLevel") ? response.get("riskLevel").asText() : "unknown");
            analysis.setConfidence(response.has("confidence") ? response.get("confidence").asDouble() : 0.0);
            analysis.setImpactedServices(response.has("impactedServices") ? 
                response.get("impactedServices").toString() : "[]");
            analysis.setTeamsToNotify(response.has("teamsToNotify") ? 
                response.get("teamsToNotify").toString() : "[]");
            analysis.setPotentialRisks(response.has("potentialRisks") ? 
                response.get("potentialRisks").toString() : "[]");
            analysis.setRecommendedTests(response.has("recommendedTests") ? 
                response.get("recommendedTests").toString() : "[]");
            analysis.setMitigationPlan(response.has("mitigationPlan") ? 
                response.get("mitigationPlan").toString() : "[]");
            analysis.setExecutiveSummary(response.has("executiveSummary") ? 
                response.get("executiveSummary").asText() : "");
            analysis.setFullResponse(response.toString());
            analysis.setMockMode(response.has("mockMode") ? response.get("mockMode").asBoolean() : true);

            analysisRepository.save(analysis);
            log.info("Persisted analysis: {}", analysis.getAnalysisId());
        } catch (Exception e) {
            log.error("Failed to persist analysis: {}", e.getMessage());
        }
    }

    /**
     * Create an error response JSON node.
     */
    private JsonNode createErrorResponse(String errorMessage) {
        ObjectNode error = objectMapper.createObjectNode();
        error.put("error", errorMessage);
        error.put("mockMode", true);
        return error;
    }
}

