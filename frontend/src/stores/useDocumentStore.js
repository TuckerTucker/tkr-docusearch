/**
 * Document Store - Filter/sort/pagination state
 *
 * Manages document library filters and temporary documents during upload.
 * Persists filters to localStorage, temp documents are in-memory only.
 *
 * Provider: infrastructure-agent (Wave 1)
 * Contract: integration-contracts/stores.contract.md
 */

import { create } from 'zustand';
import { persist } from 'zustand/middleware';

/**
 * Initial filter state
 */
const initialFilters = {
  search: '',
  sortBy: 'newest_first',
  fileTypeGroup: 'all',
  limit: 50,
  offset: 0,
};

/**
 * Document store with filter persistence
 */
export const useDocumentStore = create(
  persist(
    (set, get) => ({
      // State
      filters: { ...initialFilters },
      tempDocuments: new Map(), // Not persisted
      tempDocumentsVersion: 0, // Increment to trigger re-renders

      // Filter actions
      setFilters: (partial) =>
        set((state) => ({
          filters: { ...state.filters, ...partial },
        })),

      resetFilters: () =>
        set({
          filters: { ...initialFilters },
        }),

      setSearch: (search) =>
        set((state) => ({
          filters: { ...state.filters, search, offset: 0 }, // Reset offset on search
        })),

      setSortBy: (sortBy) =>
        set((state) => ({
          filters: { ...state.filters, sortBy, offset: 0 }, // Reset offset on sort change
        })),

      setFileTypeGroup: (fileTypeGroup) =>
        set((state) => ({
          filters: { ...state.filters, fileTypeGroup, offset: 0 }, // Reset offset on filter change
        })),

      setPage: (page) =>
        set((state) => {
          const offset = (page - 1) * state.filters.limit;
          return {
            filters: { ...state.filters, offset },
          };
        }),

      // Temp documents actions (for optimistic UI during upload)
      // tempId is now actually doc_id from server pre-registration
      addTempDocument: (doc_id, filename) =>
        set((state) => {
          const newMap = new Map(state.tempDocuments);
          newMap.set(doc_id, {
            doc_id,  // Store doc_id in the document data
            filename,
            status: 'uploading',
            progress: 0,
          });
          console.log(`[Store] addTempDocument: FULL doc_id=${doc_id}, filename=${filename}, Map size: ${newMap.size}`);
          console.log(`[Store] All temp doc_ids in map:`, Array.from(newMap.keys()));
          return {
            tempDocuments: newMap,
            tempDocumentsVersion: state.tempDocumentsVersion + 1
          };
        }),

      updateTempDocumentProgress: (tempId, progress) =>
        set((state) => {
          const newMap = new Map(state.tempDocuments);
          const doc = newMap.get(tempId);
          if (doc) {
            newMap.set(tempId, { ...doc, progress });
          }
          return {
            tempDocuments: newMap,
            tempDocumentsVersion: state.tempDocumentsVersion + 1
          };
        }),

      setTempDocumentStatus: (doc_id, status, stage) =>
        set((state) => {
          const newMap = new Map(state.tempDocuments);
          const doc = newMap.get(doc_id);
          if (doc) {
            newMap.set(doc_id, {
              ...doc,
              status,
              ...(stage && { stage })
            });
          }
          return {
            tempDocuments: newMap,
            tempDocumentsVersion: state.tempDocumentsVersion + 1
          };
        }),

      updateTempDocument: (doc_id, updates) =>
        set((state) => {
          const newMap = new Map(state.tempDocuments);
          const doc = newMap.get(doc_id);
          if (doc) {
            newMap.set(doc_id, {
              ...doc,
              ...updates,
            });
          }
          return {
            tempDocuments: newMap,
            tempDocumentsVersion: state.tempDocumentsVersion + 1
          };
        }),

      removeTempDocument: (tempId) =>
        set((state) => {
          const newMap = new Map(state.tempDocuments);
          newMap.delete(tempId);
          return {
            tempDocuments: newMap,
            tempDocumentsVersion: state.tempDocumentsVersion + 1
          };
        }),

      clearAllTempDocuments: () =>
        set({
          tempDocuments: new Map(),
          tempDocumentsVersion: 0
        }),
    }),
    {
      name: 'docusearch-filters',
      partialize: (state) => ({
        filters: state.filters,
        // tempDocuments is NOT persisted (in-memory only)
      }),
    }
  )
);
