import React, { createContext, useContext, useState, useEffect } from 'react';
import { QueryResponse, RetrievalMode, LLMProvider } from '../api/types';

export interface ChatTurn {
  id: string;
  query: string;
  response: QueryResponse;
  timestamp: string;
}

interface ChatContextType {
  chatHistory: ChatTurn[];
  addTurn: (query: string, response: QueryResponse) => void;
  clearHistory: () => void;
  retrievalMode: RetrievalMode;
  setRetrievalMode: (mode: RetrievalMode) => void;
  topK: number;
  setTopK: (k: number) => void;
  llmProvider: LLMProvider;
  setLlmProvider: (provider: LLMProvider) => void;
  categoryFocus: string;
  setCategoryFocus: (cat: string) => void;
}

const ChatContext = createContext<ChatContextType | undefined>(undefined);

export const ChatProvider: React.FC<{ children: React.ReactNode }> = ({ children }) => {
  const [chatHistory, setChatHistory] = useState<ChatTurn[]>(() => {
    try {
      const saved = sessionStorage.getItem('apexprint-chat-history');
      return saved ? JSON.parse(saved) : [];
    } catch {
      return [];
    }
  });

  const [retrievalMode, setRetrievalMode] = useState<RetrievalMode>('multi_context');
  const [topK, setTopK] = useState<number>(5);
  const [llmProvider, setLlmProvider] = useState<LLMProvider>('auto');
  const [categoryFocus, setCategoryFocus] = useState<string>('all');

  useEffect(() => {
    try {
      sessionStorage.setItem('apexprint-chat-history', JSON.stringify(chatHistory));
    } catch {
      // Ignore quota exceeded errors
    }
  }, [chatHistory]);

  const addTurn = (query: string, response: QueryResponse) => {
    const newTurn: ChatTurn = {
      id: `turn_${Date.now()}_${Math.random().toString(36).substring(2, 7)}`,
      query,
      response,
      timestamp: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit', second: '2-digit' }),
    };
    setChatHistory((prev) => [...prev, newTurn]);
  };

  const clearHistory = () => {
    setChatHistory([]);
    sessionStorage.removeItem('apexprint-chat-history');
  };

  return (
    <ChatContext.Provider
      value={{
        chatHistory,
        addTurn,
        clearHistory,
        retrievalMode,
        setRetrievalMode,
        topK,
        setTopK,
        llmProvider,
        setLlmProvider,
        categoryFocus,
        setCategoryFocus,
      }}
    >
      {children}
    </ChatContext.Provider>
  );
};

export const useChat = () => {
  const context = useContext(ChatContext);
  if (!context) {
    throw new Error('useChat must be used within a ChatProvider');
  }
  return context;
};
