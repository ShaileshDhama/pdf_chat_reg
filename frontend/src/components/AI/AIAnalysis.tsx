import React, { useState, useEffect } from 'react';
import { useQuery, useMutation } from 'react-query';
import { motion, AnimatePresence } from 'framer-motion';

import { Document, AnalysisResult } from '../../types';
import { analyzeDocument, extractClauses, compareDocuments } from '../../services/ai';

interface AIAnalysisProps {
  document: Document | null;
  onComplete: (result: AnalysisResult) => void;
}

function AIAnalysis({ document, onComplete }: AIAnalysisProps) {
  const [activeStep, setActiveStep] = useState(0);
  const [analysisResults, setAnalysisResults] = useState<AnalysisResult | null>(null);

  // Analysis pipeline steps
  const analysisSteps = [
    { id: 'text-extraction', name: 'Text Extraction', icon: '📄' },
    { id: 'clause-analysis', name: 'Clause Analysis', icon: '🔍' },
    { id: 'risk-assessment', name: 'Risk Assessment', icon: '⚠️' },
    { id: 'summary', name: 'Summary Generation', icon: '📝' }
  ];

  // Query for document analysis
  const { data: analysisData, isLoading: isAnalyzing } = useQuery(
    ['analyze', document?.id],
    () => analyzeDocument(document!.id),
    {
      enabled: !!document,
      onSuccess: (data) => {
        setAnalysisResults((prev) => ({
          ...prev,
          ...data,
          textExtraction: data.extractedText
        }));
        setActiveStep(1);
      }
    }
  );

  // Mutation for clause extraction
  const clausesMutation = useMutation(
    (docId: string) => extractClauses(docId),
    {
      onSuccess: (data) => {
        setAnalysisResults((prev) => ({
          ...prev,
          clauses: data.clauses,
          entities: data.entities
        }));
        setActiveStep(2);
      }
    }
  );

  // Effect to trigger clause analysis after text extraction
  useEffect(() => {
    if (analysisData && document) {
      clausesMutation.mutate(document.id);
    }
  }, [analysisData, document]);

  // Effect to complete analysis
  useEffect(() => {
    if (activeStep === analysisSteps.length && analysisResults) {
      onComplete(analysisResults);
    }
  }, [activeStep, analysisResults, onComplete]);

  if (!document) {
    return (
      <div className="flex items-center justify-center h-full">
        <p className="text-lg text-gray-500">No document selected for analysis</p>
      </div>
    );
  }

  return (
    <div className="p-6 max-w-4xl mx-auto">
      <header className="mb-8">
        <h2 className="text-2xl font-bold mb-2">AI Document Analysis</h2>
        <p className="text-gray-600">
          Analyzing: {document.name}
        </p>
      </header>

      {/* Progress Steps */}
      <div className="mb-8">
        <div className="flex justify-between items-center">
          {analysisSteps.map((step, index) => (
            <div
              key={step.id}
              className={`flex items-center ${
                index < activeStep ? 'text-green-500' : 
                index === activeStep ? 'text-blue-500' : 'text-gray-400'
              }`}
            >
              <motion.div
                initial={{ scale: 0.8 }}
                animate={{ scale: index === activeStep ? 1.1 : 1 }}
                className="flex flex-col items-center"
              >
                <span className="text-2xl mb-2">{step.icon}</span>
                <span className="text-sm">{step.name}</span>
              </motion.div>
              {index < analysisSteps.length - 1 && (
                <div className="w-16 h-0.5 mx-4 bg-gray-200" />
              )}
            </div>
          ))}
        </div>
      </div>

      {/* Analysis Results */}
      <AnimatePresence mode="wait">
        {isAnalyzing ? (
          <motion.div
            key="analyzing"
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            exit={{ opacity: 0 }}
            className="text-center py-12"
          >
            <div className="inline-block animate-spin rounded-full h-12 w-12 border-4 border-blue-500 border-t-transparent" />
            <p className="mt-4 text-gray-600">
              Analyzing document... {analysisSteps[activeStep]?.name}
            </p>
          </motion.div>
        ) : (
          <motion.div
            key="results"
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            exit={{ opacity: 0, y: -20 }}
            className="space-y-6"
          >
            {analysisResults && (
              <>
                {/* Text Extraction */}
                {analysisResults.textExtraction && (
                  <section className="bg-white rounded-lg shadow p-6">
                    <h3 className="text-lg font-semibold mb-4">
                      Extracted Text
                    </h3>
                    <pre className="whitespace-pre-wrap text-sm text-gray-700">
                      {analysisResults.textExtraction}
                    </pre>
                  </section>
                )}

                {/* Clauses */}
                {analysisResults.clauses && (
                  <section className="bg-white rounded-lg shadow p-6">
                    <h3 className="text-lg font-semibold mb-4">
                      Important Clauses
                    </h3>
                    <div className="space-y-4">
                      {analysisResults.clauses.map((clause, index) => (
                        <div
                          key={index}
                          className="p-4 border rounded-lg hover:bg-gray-50"
                        >
                          <h4 className="font-medium text-blue-600 mb-2">
                            {clause.type}
                          </h4>
                          <p className="text-gray-700">{clause.content}</p>
                          {clause.risk && (
                            <div className="mt-2 flex items-center">
                              <span className="text-red-500 mr-2">⚠️</span>
                              <span className="text-sm text-red-600">
                                {clause.risk}
                              </span>
                            </div>
                          )}
                        </div>
                      ))}
                    </div>
                  </section>
                )}

                {/* Entities */}
                {analysisResults.entities && (
                  <section className="bg-white rounded-lg shadow p-6">
                    <h3 className="text-lg font-semibold mb-4">
                      Identified Entities
                    </h3>
                    <div className="grid grid-cols-2 gap-4">
                      {Object.entries(analysisResults.entities).map(([type, entities]) => (
                        <div key={type} className="p-4 border rounded-lg">
                          <h4 className="font-medium text-gray-700 mb-2">
                            {type}
                          </h4>
                          <ul className="list-disc list-inside text-sm text-gray-600">
                            {entities.map((entity, index) => (
                              <li key={index}>{entity}</li>
                            ))}
                          </ul>
                        </div>
                      ))}
                    </div>
                  </section>
                )}

                {/* Summary */}
                {analysisResults.summary && (
                  <section className="bg-white rounded-lg shadow p-6">
                    <h3 className="text-lg font-semibold mb-4">
                      Document Summary
                    </h3>
                    <div className="prose max-w-none">
                      {analysisResults.summary}
                    </div>
                  </section>
                )}
              </>
            )}
          </motion.div>
        )}
      </AnimatePresence>
    </div>
  );
}

export default AIAnalysis;
