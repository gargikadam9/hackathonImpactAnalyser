package com.changeanalyzer.controller;

import com.changeanalyzer.model.Analysis;
import com.changeanalyzer.service.AiServiceClient;
import com.fasterxml.jackson.databind.JsonNode;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.http.ResponseEntity;
import org.springframework.web.bind.annotation.*;

import java.util.List;
import java.util.Map;

/**
 * REST controller that proxies API requests to the AI service
 * and persists analysis history.
 */
@RestController
@RequestMapping("/api/v1")
public class ApiProxyController {

    private final AiServiceClient aiServiceClient;

    @Autowired
    public ApiProxyController(AiServiceClient aiServiceClient) {
        this.aiServiceClient = aiServiceClient;
    }

    /**
     * POST /api/v1/change-impact/analyze
     * Analyze change impact by proxying to AI service.
     */
    @PostMapping("/change-impact/analyze")
    public ResponseEntity<JsonNode> analyzeChangeImpact(@RequestBody Map<String, Object> request) {
        String changeTitle = (String) request.getOrDefault("change_title", "Unspecified Change");
        String changeDescription = (String) request.getOrDefault("change_description", "");
        String changeType = (String) request.getOrDefault("change_type", "enhancement");
        String priority = (String) request.getOrDefault("priority", "medium");
        @SuppressWarnings("unchecked")
        List<String> affectedServices = (List<String>) request.getOrDefault("affected_services", List.of());

        JsonNode result = aiServiceClient.analyzeChangeImpact(
                changeTitle, changeDescription, changeType, affectedServices, priority);
        return ResponseEntity.ok(result);
    }

    /**
     * POST /api/v1/change-impact/analyze-prompt
     * Analyze change impact from a natural language prompt.
     */
    @PostMapping("/change-impact/analyze-prompt")
    public ResponseEntity<JsonNode> analyzeChangeImpactFromPrompt(@RequestBody Map<String, Object> prompt) {
        JsonNode result = aiServiceClient.analyzeChangeImpactFromPrompt(prompt);
        return ResponseEntity.ok(result);
    }

    /**
     * POST /api/v1/chat/general
     * Proxy general chat to AI service.
     */
    @PostMapping("/chat/general")
    public ResponseEntity<JsonNode> generalChat(@RequestBody Map<String, Object> request) {
        String message = (String) request.getOrDefault("message", "");
        @SuppressWarnings("unchecked")
        List<Map<String, String>> history = (List<Map<String, String>>) request.getOrDefault("conversation_history", List.of());

        JsonNode result = aiServiceClient.chat(message, history);
        return ResponseEntity.ok(result);
    }

    /**
     * POST /api/v1/assistant/respond
     * Unified assistant route.
     */
    @PostMapping("/assistant/respond")
    public ResponseEntity<JsonNode> assistantRespond(@RequestBody Map<String, Object> request) {
        String message = (String) request.getOrDefault("message", "");
        @SuppressWarnings("unchecked")
        List<Map<String, String>> history = (List<Map<String, String>>) request.getOrDefault("conversation_history", List.of());

        JsonNode result = aiServiceClient.assistantRespond(message, history);
        return ResponseEntity.ok(result);
    }

    /**
     * GET /api/v1/change-types
     * Get available change types.
     */
    @GetMapping("/change-types")
    public ResponseEntity<JsonNode> getChangeTypes() {
        JsonNode result = aiServiceClient.getChangeTypes();
        return ResponseEntity.ok(result);
    }

    /**
     * GET /api/v1/components
     * Get all tracked system components.
     */
    @GetMapping("/components")
    public ResponseEntity<JsonNode> getComponents() {
        JsonNode result = aiServiceClient.getComponents();
        return ResponseEntity.ok(result);
    }

    /**
     * GET /api/v1/system/technical-details
     * Get system technical details.
     */
    @GetMapping("/system/technical-details")
    public ResponseEntity<JsonNode> getTechnicalDetails() {
        JsonNode result = aiServiceClient.getTechnicalDetails();
        return ResponseEntity.ok(result);
    }

    /**
     * MODULE 8 — POST /api/v1/feedback/capture
     * Human-in-the-loop feedback: thumbs up/down and/or a manual risk-score
     * override for a given analysisId, persisted by the AI service.
     */
    @PostMapping("/feedback/capture")
    public ResponseEntity<JsonNode> captureFeedback(@RequestBody Map<String, Object> request) {
        JsonNode result = aiServiceClient.captureFeedback(request);
        return ResponseEntity.ok(result);
    }

    /**
     * MODULE 8 — GET /api/v1/feedback/{analysisId}
     * Retrieve all feedback captured so far for a given analysis.
     */
    @GetMapping("/feedback/{analysisId}")
    public ResponseEntity<JsonNode> getFeedbackForAnalysis(@PathVariable String analysisId) {
        JsonNode result = aiServiceClient.getFeedbackForAnalysis(analysisId);
        return ResponseEntity.ok(result);
    }

    /**
     * GET /api/v1/analyses/history
     * Get analysis history (latest 20).
     */
    @GetMapping("/analyses/history")
    public ResponseEntity<List<Analysis>> getAnalysisHistory() {
        List<Analysis> history = aiServiceClient.getAnalysisHistory();
        return ResponseEntity.ok(history);
    }

    /**
     * GET /api/v1/analyses/{analysisId}
     * Get a single analysis by ID.
     */
    @GetMapping("/analyses/{analysisId}")
    public ResponseEntity<Analysis> getAnalysisById(@PathVariable String analysisId) {
        Analysis analysis = aiServiceClient.getAnalysisById(analysisId);
        if (analysis == null) {
            return ResponseEntity.notFound().build();
        }
        return ResponseEntity.ok(analysis);
    }
}

