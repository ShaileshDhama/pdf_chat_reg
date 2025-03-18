import axios from 'axios';
import { AnalysisResult, Clause, Entity, Document } from '../types';

const API_URL = process.env.REACT_APP_API_URL || 'http://localhost:8000/api';

/**
 * Analyze a document using AI
 */
export async function analyzeDocument(documentId: string): Promise<AnalysisResult> {
  const response = await axios.post(`${API_URL}/documents/${documentId}/analyze`);
  return response.data;
}

/**
 * Extract clauses from a document
 */
export async function extractClauses(documentId: string): Promise<{
  clauses: Clause[];
  entities: Record<string, Entity[]>;
}> {
  const response = await axios.post(`${API_URL}/documents/${documentId}/clauses`);
  return response.data;
}

/**
 * Compare two documents and find similarities/differences
 */
export async function compareDocuments(
  sourceId: string,
  targetId: string
): Promise<{
  similarities: Clause[];
  differences: Clause[];
  riskAssessment: string[];
}> {
  const response = await axios.post(`${API_URL}/documents/compare`, {
    sourceId,
    targetId
  });
  return response.data;
}

/**
 * Generate a summary of a document
 */
export async function generateSummary(documentId: string): Promise<{
  summary: string;
  keyPoints: string[];
}> {
  const response = await axios.post(`${API_URL}/documents/${documentId}/summary`);
  return response.data;
}

/**
 * Ask a question about a document
 */
export async function askQuestion(
  documentId: string,
  question: string
): Promise<{
  answer: string;
  confidence: number;
  relevantClauses: Clause[];
}> {
  const response = await axios.post(`${API_URL}/documents/${documentId}/ask`, {
    question
  });
  return response.data;
}

/**
 * Extract entities from a document
 */
export async function extractEntities(documentId: string): Promise<{
  entities: Record<string, Entity[]>;
  relationships: Array<{
    source: Entity;
    target: Entity;
    type: string;
  }>;
}> {
  const response = await axios.post(`${API_URL}/documents/${documentId}/entities`);
  return response.data;
}

/**
 * Analyze document risks
 */
export async function analyzeRisks(documentId: string): Promise<{
  risks: Array<{
    severity: 'low' | 'medium' | 'high';
    description: string;
    relatedClauses: Clause[];
    recommendations: string[];
  }>;
}> {
  const response = await axios.post(`${API_URL}/documents/${documentId}/risks`);
  return response.data;
}

/**
 * Generate document visualization data
 */
export async function generateVisualization(documentId: string): Promise<{
  sections: Array<{
    id: string;
    title: string;
    content: string;
    position: [number, number, number];
    connections: string[];
  }>;
  metadata: Record<string, any>;
}> {
  const response = await axios.post(`${API_URL}/documents/${documentId}/visualize`);
  return response.data;
}

/**
 * Translate document content
 */
export async function translateDocument(
  documentId: string,
  targetLanguage: string
): Promise<{
  translatedContent: string;
  originalLanguage: string;
  confidence: number;
}> {
  const response = await axios.post(`${API_URL}/documents/${documentId}/translate`, {
    targetLanguage
  });
  return response.data;
}

/**
 * Generate alternative clause suggestions
 */
export async function suggestAlternativeClauses(
  clause: string
): Promise<{
  suggestions: Array<{
    content: string;
    reasoning: string;
    riskLevel: 'lower' | 'similar' | 'higher';
  }>;
}> {
  const response = await axios.post(`${API_URL}/clauses/suggest`, {
    clause
  });
  return response.data;
}

/**
 * Check document compliance with specified regulations
 */
export async function checkCompliance(
  documentId: string,
  regulations: string[]
): Promise<{
  compliant: boolean;
  violations: Array<{
    regulation: string;
    description: string;
    severity: 'low' | 'medium' | 'high';
    suggestedFix: string;
  }>;
}> {
  const response = await axios.post(`${API_URL}/documents/${documentId}/compliance`, {
    regulations
  });
  return response.data;
}
