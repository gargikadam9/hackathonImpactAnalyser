package com.changeanalyzer.controller;

import com.changeanalyzer.model.Analysis;
import com.changeanalyzer.repository.AnalysisRepository;
import com.fasterxml.jackson.databind.ObjectMapper;
import com.fasterxml.jackson.databind.node.ObjectNode;
import org.junit.jupiter.api.BeforeEach;
import org.junit.jupiter.api.Test;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.boot.test.autoconfigure.web.servlet.AutoConfigureMockMvc;
import org.springframework.boot.test.context.SpringBootTest;
import org.springframework.http.MediaType;
import org.springframework.test.context.ActiveProfiles;
import org.springframework.test.web.servlet.MockMvc;

import java.time.LocalDateTime;

import static org.springframework.test.web.servlet.request.MockMvcRequestBuilders.*;
import static org.springframework.test.web.servlet.result.MockMvcResultMatchers.*;

@SpringBootTest
@AutoConfigureMockMvc
@ActiveProfiles("test")
class ApiProxyControllerTest {

    @Autowired
    private MockMvc mockMvc;

    @Autowired
    private ObjectMapper objectMapper;

    @Autowired
    private AnalysisRepository analysisRepository;

    @BeforeEach
    void setUp() {
        analysisRepository.deleteAll();
    }

    @Test
    void testGetChangeTypes() throws Exception {
        mockMvc.perform(get("/api/v1/change-types"))
                .andExpect(status().isOk())
                .andExpect(content().contentType(MediaType.APPLICATION_JSON));
    }

    @Test
    void testGetComponents() throws Exception {
        mockMvc.perform(get("/api/v1/components"))
                .andExpect(status().isOk())
                .andExpect(content().contentType(MediaType.APPLICATION_JSON));
    }

    @Test
    void testGetTechnicalDetails() throws Exception {
        mockMvc.perform(get("/api/v1/system/technical-details"))
                .andExpect(status().isOk())
                .andExpect(content().contentType(MediaType.APPLICATION_JSON));
    }

    @Test
    void testAnalyzeChangeImpact() throws Exception {
        ObjectNode request = objectMapper.createObjectNode();
        request.put("change_title", "Test Database Pool Upgrade");
        request.put("change_description", "Increasing connection pool from 50 to 200");
        request.put("change_type", "infrastructure");
        request.put("priority", "high");

        mockMvc.perform(post("/api/v1/change-impact/analyze")
                        .contentType(MediaType.APPLICATION_JSON)
                        .content(objectMapper.writeValueAsString(request)))
                .andExpect(status().isOk())
                .andExpect(content().contentType(MediaType.APPLICATION_JSON));
    }

    @Test
    void testGetHistory() throws Exception {
        // Create a test analysis entry
        Analysis analysis = new Analysis();
        analysis.setAnalysisId("test-123");
        analysis.setChangeTitle("Test Change");
        analysis.setRiskScore(0.65);
        analysis.setRiskLevel("high");
        analysis.setConfidence(0.82);
        analysis.setCreatedAt(LocalDateTime.now());
        analysisRepository.save(analysis);

        mockMvc.perform(get("/api/v1/analyses/history"))
                .andExpect(status().isOk())
                .andExpect(content().contentType(MediaType.APPLICATION_JSON))
                .andExpect(jsonPath("$").isArray())
                .andExpect(jsonPath("$[0].changeTitle").value("Test Change"));
    }

    @Test
    void testGetAnalysisById() throws Exception {
        Analysis analysis = new Analysis();
        analysis.setAnalysisId("test-456");
        analysis.setChangeTitle("Specific Change");
        analysis.setRiskScore(0.5);
        analysis.setRiskLevel("medium");
        analysis.setConfidence(0.7);
        analysis.setCreatedAt(LocalDateTime.now());
        analysisRepository.save(analysis);

        mockMvc.perform(get("/api/v1/analyses/test-456"))
                .andExpect(status().isOk())
                .andExpect(content().contentType(MediaType.APPLICATION_JSON))
                .andExpect(jsonPath("$.analysisId").value("test-456"))
                .andExpect(jsonPath("$.changeTitle").value("Specific Change"));
    }

    @Test
    void testGetAnalysisByIdNotFound() throws Exception {
        mockMvc.perform(get("/api/v1/analyses/nonexistent"))
                .andExpect(status().isNotFound());
    }

    @Test
    void testGeneralChat() throws Exception {
        ObjectNode request = objectMapper.createObjectNode();
        request.put("message", "Hello, how are you?");

        mockMvc.perform(post("/api/v1/chat/general")
                        .contentType(MediaType.APPLICATION_JSON)
                        .content(objectMapper.writeValueAsString(request)))
                .andExpect(status().isOk())
                .andExpect(content().contentType(MediaType.APPLICATION_JSON));
    }

    @Test
    void testAssistantRespond() throws Exception {
        ObjectNode request = objectMapper.createObjectNode();
        request.put("message", "Analyze the impact of upgrading payment gateway");

        mockMvc.perform(post("/api/v1/assistant/respond")
                        .contentType(MediaType.APPLICATION_JSON)
                        .content(objectMapper.writeValueAsString(request)))
                .andExpect(status().isOk())
                .andExpect(content().contentType(MediaType.APPLICATION_JSON));
    }
}

