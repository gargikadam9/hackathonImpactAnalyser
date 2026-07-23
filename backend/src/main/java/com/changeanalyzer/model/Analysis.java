package com.changeanalyzer.model;

import jakarta.persistence.*;
import java.time.LocalDateTime;

@Entity
@Table(name = "analyses")
public class Analysis {

    @Id
    @GeneratedValue(strategy = GenerationType.IDENTITY)
    private Long id;

    @Column(name = "analysis_id", unique = true, nullable = false)
    private String analysisId;

    @Column(name = "change_title", nullable = false)
    private String changeTitle;

    @Column(name = "change_description", columnDefinition = "TEXT")
    private String changeDescription;

    @Column(name = "change_type")
    private String changeType;

    @Column(name = "risk_score")
    private Double riskScore;

    @Column(name = "risk_level")
    private String riskLevel;

    @Column(name = "confidence")
    private Double confidence;

    @Column(name = "impacted_services", columnDefinition = "TEXT")
    private String impactedServices;

    @Column(name = "teams_to_notify", columnDefinition = "TEXT")
    private String teamsToNotify;

    @Column(name = "potential_risks", columnDefinition = "TEXT")
    private String potentialRisks;

    @Column(name = "recommended_tests", columnDefinition = "TEXT")
    private String recommendedTests;

    @Column(name = "mitigation_plan", columnDefinition = "TEXT")
    private String mitigationPlan;

    @Column(name = "executive_summary", columnDefinition = "TEXT")
    private String executiveSummary;

    @Column(name = "full_response", columnDefinition = "TEXT")
    private String fullResponse;

    @Column(name = "mock_mode")
    private Boolean mockMode;

    @Column(name = "created_at", nullable = false)
    private LocalDateTime createdAt;

    @PrePersist
    protected void onCreate() {
        createdAt = LocalDateTime.now();
    }

    // Getters and Setters
    public Long getId() { return id; }
    public void setId(Long id) { this.id = id; }

    public String getAnalysisId() { return analysisId; }
    public void setAnalysisId(String analysisId) { this.analysisId = analysisId; }

    public String getChangeTitle() { return changeTitle; }
    public void setChangeTitle(String changeTitle) { this.changeTitle = changeTitle; }

    public String getChangeDescription() { return changeDescription; }
    public void setChangeDescription(String changeDescription) { this.changeDescription = changeDescription; }

    public String getChangeType() { return changeType; }
    public void setChangeType(String changeType) { this.changeType = changeType; }

    public Double getRiskScore() { return riskScore; }
    public void setRiskScore(Double riskScore) { this.riskScore = riskScore; }

    public String getRiskLevel() { return riskLevel; }
    public void setRiskLevel(String riskLevel) { this.riskLevel = riskLevel; }

    public Double getConfidence() { return confidence; }
    public void setConfidence(Double confidence) { this.confidence = confidence; }

    public String getImpactedServices() { return impactedServices; }
    public void setImpactedServices(String impactedServices) { this.impactedServices = impactedServices; }

    public String getTeamsToNotify() { return teamsToNotify; }
    public void setTeamsToNotify(String teamsToNotify) { this.teamsToNotify = teamsToNotify; }

    public String getPotentialRisks() { return potentialRisks; }
    public void setPotentialRisks(String potentialRisks) { this.potentialRisks = potentialRisks; }

    public String getRecommendedTests() { return recommendedTests; }
    public void setRecommendedTests(String recommendedTests) { this.recommendedTests = recommendedTests; }

    public String getMitigationPlan() { return mitigationPlan; }
    public void setMitigationPlan(String mitigationPlan) { this.mitigationPlan = mitigationPlan; }

    public String getExecutiveSummary() { return executiveSummary; }
    public void setExecutiveSummary(String executiveSummary) { this.executiveSummary = executiveSummary; }

    public String getFullResponse() { return fullResponse; }
    public void setFullResponse(String fullResponse) { this.fullResponse = fullResponse; }

    public Boolean getMockMode() { return mockMode; }
    public void setMockMode(Boolean mockMode) { this.mockMode = mockMode; }

    public LocalDateTime getCreatedAt() { return createdAt; }
    public void setCreatedAt(LocalDateTime createdAt) { this.createdAt = createdAt; }
}

