/**
 * Mock Structure API Client
 *
 * Agent 6: Document Structure Hook Builder
 * Wave 1 - BBox Overlay React Implementation
 *
 * Provides mock data for testing and offline development.
 * Uses MSW (Mock Service Worker) patterns for realistic API simulation.
 */

import type { PageStructure } from '../../types/structure';

/**
 * Mock page structure with realistic data
 */
export const mockPageStructure: PageStructure = {
  doc_id: 'test-doc-123',
  page: 1,
  has_structure: true,
  headings: [
    {
      text: 'Introduction',
      level: 'SECTION_HEADER',
      page: 1,
      section_path: '1. Introduction',
      bbox: {
        left: 72.0,
        bottom: 650.0,
        right: 540.0,
        top: 720.0,
      },
    },
    {
      text: 'Background',
      level: 'SECTION_HEADER',
      page: 1,
      section_path: '1. Introduction > 1.1 Background',
      bbox: {
        left: 72.0,
        bottom: 550.0,
        right: 540.0,
        top: 600.0,
      },
    },
  ],
  tables: [
    {
      page: 1,
      caption: 'Sample Data Table',
      rows: 5,
      cols: 3,
      has_header: true,
      table_id: 'table-001',
      bbox: {
        left: 100.0,
        bottom: 300.0,
        right: 500.0,
        top: 450.0,
      },
    },
  ],
  pictures: [
    {
      page: 1,
      type: 'chart',
      caption: 'Figure 1: Sample Chart',
      confidence: 0.95,
      picture_id: 'pic-001',
      bbox: {
        left: 150.0,
        bottom: 100.0,
        right: 450.0,
        top: 250.0,
      },
    },
  ],
  code_blocks: [
    {
      page: 1,
      language: 'python',
      lines: 10,
      bbox: {
        left: 80.0,
        bottom: 200.0,
        right: 520.0,
        top: 280.0,
      },
    },
  ],
  formulas: [
    {
      page: 1,
      latex: 'E = mc^2',
      bbox: {
        left: 200.0,
        bottom: 400.0,
        right: 400.0,
        top: 430.0,
      },
    },
  ],
  summary: {
    total_sections: 5,
    max_depth: 3,
    has_toc: true,
  },
  coordinate_system: {
    format: '[left, bottom, right, top]',
    origin: 'bottom-left',
    units: 'points',
    reference: 'integration-contracts/docling-structure-spec.md',
  },
  image_dimensions: {
    width: 1700,
    height: 2200,
  },
};

/**
 * Mock empty structure response (no structure available)
 */
export const mockEmptyStructure: PageStructure = {
  doc_id: 'test-doc-456',
  page: 1,
  has_structure: false,
  headings: [],
  tables: [],
  pictures: [],
  code_blocks: [],
  formulas: [],
  summary: null,
  coordinate_system: {
    format: '[left, bottom, right, top]',
    origin: 'bottom-left',
    units: 'points',
    reference: 'integration-contracts/docling-structure-spec.md',
  },
};

/**
 * Mock API client for testing
 */
export const structureApi = {
  /**
   * Mock fetchPageStructure implementation
   */
  fetchPageStructure: async (docId: string, page: number): Promise<PageStructure> => {
    // Simulate network delay
    await new Promise((resolve) => setTimeout(resolve, 100));

    // Simulate different responses based on input
    if (docId === 'not-found-doc') {
      throw new Error('Page not found');
    }

    if (docId === 'no-structure-doc') {
      return mockEmptyStructure;
    }

    if (docId === 'error-doc') {
      throw new Error('Internal server error');
    }

    // Return mock structure with correct doc_id and page
    return {
      ...mockPageStructure,
      doc_id: docId,
      page,
    };
  },
};

/**
 * Export mock handlers for MSW
 */
export { mockPageStructure as default };
