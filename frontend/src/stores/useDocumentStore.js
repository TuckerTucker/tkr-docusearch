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
      addTempDocument: (tempId, filename) =>
        set((state) => {
          const newMap = new Map(state.tempDocuments);
          newMap.set(tempId, {
            filename,
            status: 'uploading',
            progress: 0,
          });
          return { tempDocuments: newMap };
        }),

      updateTempDocumentProgress: (tempId, progress) =>
        set((state) => {
          const newMap = new Map(state.tempDocuments);
          const doc = newMap.get(tempId);
          if (doc) {
            newMap.set(tempId, { ...doc, progress });
          }
          return { tempDocuments: newMap };
        }),

      setTempDocumentStatus: (tempId, status) =>
        set((state) => {
          const newMap = new Map(state.tempDocuments);
          const doc = newMap.get(tempId);
          if (doc) {
            newMap.set(tempId, { ...doc, status });
          }
          return { tempDocuments: newMap };
        }),

      removeTempDocument: (tempId) =>
        set((state) => {
          const newMap = new Map(state.tempDocuments);
          newMap.delete(tempId);
          return { tempDocuments: newMap };
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
