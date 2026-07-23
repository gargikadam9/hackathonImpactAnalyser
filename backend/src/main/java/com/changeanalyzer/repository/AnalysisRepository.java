package com.changeanalyzer.repository;

import com.changeanalyzer.model.Analysis;
import org.springframework.data.jpa.repository.JpaRepository;
import org.springframework.stereotype.Repository;

import java.util.List;

@Repository
public interface AnalysisRepository extends JpaRepository<Analysis, Long> {

    List<Analysis> findTop20ByOrderByCreatedAtDesc();

    Analysis findByAnalysisId(String analysisId);
}

