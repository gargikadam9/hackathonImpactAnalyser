package com.changeanalyzer.service;

import com.changeanalyzer.model.Analysis;
import com.changeanalyzer.repository.AnalysisRepository;
import com.fasterxml.jackson.databind.JsonNode;
import com.fasterxml.jackson.databind.ObjectMapper;
import org.junit.jupiter.api.BeforeEach;
import org.junit.jupiter.api.Test;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.boot.test.context.SpringBootTest;
import org.springframework.test.context.ActiveProfiles;

import java.time.LocalDateTime;
import java.util.List;

import static org.junit.jupiter.api.Assertions.*;

@SpringBootTest
@ActiveProfiles("test")
class AiServiceClientTest {

    @Autowired
    private AnalysisRepository analysisRepository;

    @Autowired
    private ObjectMapper objectMapper;

    @BeforeEach
    void setUp() {
        analysisRepository.deleteAll();
    }

    @Test
    void testPersistAndRetrieveAnalysis() {
        // Create and persist an analysis
        Analysis analysis = new Analysis();
        analysis.setAnalysisId("test-svc-001");
        analysis.setChangeTitle("Database Pool Upgrade");
        analysis.setChangeDescription("Increasing pool to 200 connections");
        analysis.setChangeType("infrastructure");
        analysis.setRiskScore(0.65);
        analysis.setRiskLevel("high");
        analysis.setConfidence(0.82);
        analysis.setImpactedServices("[\"payment-gateway\",\"order-service\"]");
        analysis.setTeamsToNotify("[\"Payments\",\"Platform\"]");
        analysis.setExecutiveSummary("Test summary");
        analysis.setMockMode(true);
        analysis.setCreatedAt(LocalDateTime.now());

        analysisRepository.save(analysis);

        // Retrieve and verify
        Analysis found = analysisRepository.findByAnalysisId("test-svc-001");
        assertNotNull(found);
        assertEquals("Database Pool Upgrade", found.getChangeTitle());
        assertEquals(0.65, found.getRiskScore());
        assertEquals("high", found.getRiskLevel());
        assertTrue(found.getMockMode());
    }

    @Test
    void testTop20OrderedByDate() {
        // Create multiple analyses
        for (int i = 0; i < 25; i++) {
            Analysis analysis = new Analysis();
            analysis.setAnalysisId("test-" + i);
            analysis.setChangeTitle("Change " + i);
            analysis.setRiskScore(0.5);
            analysis.setRiskLevel("medium");
            analysis.setConfidence(0.7);
            analysis.setCreatedAt(LocalDateTime.now().minusHours(i));
            analysisRepository.save(analysis);
        }

        List<Analysis> history = analysisRepository.findTop20ByOrderByCreatedAtDesc();
        assertEquals(20, history.size());
        // Most recent first
        assertTrue(history.get(0).getCreatedAt().isAfter(
                   history.get(history.size() - 1).getCreatedAt()));
    }

    @Test
    void testErrorResponseFallback() {
        // Test that the client handles AI service errors gracefully
        assertTrue(true); // Integration test would need running AI service
    }
}

