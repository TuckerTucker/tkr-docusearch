# Integration Contracts - Enhanced Mode Bidirectional Highlighting

**Last Updated**: 2025-10-17
**Status**: COMPLETE - IMPLEMENTATION READY
**Agent**: Agent 3 (API Contract Designer)

---

## 📋 Overview

This directory contains the complete API contract specifications for the bidirectional highlighting feature, including HTTP endpoint definitions, data schemas, coordinate system specifications, and sample responses.

**Purpose**: Provide authoritative contracts for backend (Wave 2) and frontend (Wave 3) agents to implement against, ensuring seamless integration without ambiguities.

---

## 📁 Directory Structure

```
integration-contracts/
├── README.md                          # This file
├── API_CONTRACT_REVIEW.md             # Complete review report (START HERE)
├── api-contracts.md                   # Endpoint specifications (v1.1)
├── sample-api-responses.json          # Realistic API response examples
├── coordinate-system-spec.md          # Mathematical coordinate system spec
├── openapi-spec.yaml                  # OpenAPI 3.0 specification
├── chromadb-metadata-schema.md        # ChromaDB metadata format
├── sample-metadata-text.json          # Text embedding metadata example
└── sample-metadata-visual.json        # Visual embedding metadata example
```

---

## 🎯 Quick Start

### For New Agents

**Read these in order**:

1. **`API_CONTRACT_REVIEW.md`** - Start here for complete overview and findings
2. **`api-contracts.md`** - Detailed endpoint specifications
3. **`sample-api-responses.json`** - Realistic examples for testing
4. **`coordinate-system-spec.md`** - Critical for bbox rendering

### For Backend Agents (Wave 2)

**Implementation Priority**:

1. **Agent 4**: Read `api-contracts.md` → Structure Metadata Endpoint
2. **Agent 5**: Read `api-contracts.md` → Chunk Metadata Endpoint
3. **Agent 6**: Read `api-contracts.md` → Research API Extension
4. **Agent 7**: Read `api-contracts.md` → Markdown Enhancement

**Reference**:
- `sample-api-responses.json` - Test against these examples
- `chromadb-metadata-schema.md` - Understand stored metadata format
- `openapi-spec.yaml` - Optional for API tooling

### For Frontend Agents (Wave 3)

**Implementation Priority**:

1. **Agent 8**: Read `coordinate-system-spec.md` → Critical for bbox rendering
2. **Agent 9**: Read `api-contracts.md` → URL parameters and navigation
3. **Agent 10**: Read `api-contracts.md` → Research navigation integration

**Reference**:
- `sample-api-responses.json` - Mock data for frontend development
- `coordinate-system-spec.md` - Scaling formulas and validation

---

## 📄 File Descriptions

### Core Specifications

#### `api-contracts.md` (11 KB)
**Version**: 1.1
**Purpose**: Complete HTTP API specifications

**Contents**:
- 5 endpoint specifications (3 new, 2 enhanced)
- Request/response schemas
- Error handling
- URL parameter contracts
- Implementation status matrix
- Integration testing checklist

**Consumers**: All backend and frontend agents

---

#### `sample-api-responses.json` (13 KB)
**Purpose**: Realistic API response examples

**Contents**:
- Structure endpoint (with/without structure, errors)
- Chunk endpoint (text, audio, errors)
- Enhanced markdown sample
- Research API full response
- URL parameter examples with behavior

**Usage**:
- Backend: Test implementation against these
- Frontend: Use as mock data during development

---

#### `coordinate-system-spec.md` (12 KB)
**Purpose**: Mathematical coordinate system definition

**Contents**:
- Origin and axes definition
- Bounding box format
- Units and scale factors
- Responsive scaling formulas
- Validation rules
- Edge case handling
- Complete testing checklist
- Visual diagrams

**Critical for**: Agent 8 (BoundingBox Overlay)

---

### Supporting Documents

#### `API_CONTRACT_REVIEW.md` (15 KB)
**Purpose**: Complete design review and implementation guidance

**Contents**:
- Executive summary
- Detailed review findings for each endpoint
- Implementation status matrix
- Risk assessment
- Recommendations for all agents
- Next steps and dependencies

**Read this first** for context and overview.

---

#### `openapi-spec.yaml` (23 KB)
**Purpose**: Machine-readable OpenAPI 3.0 specification

**Contents**:
- Complete API definitions
- Request/response schemas
- Examples for all endpoints
- Error responses
- Data model definitions

**Usage**:
- Generate API documentation (Swagger UI)
- Generate client libraries
- API testing tools (Postman, Insomnia)
- Schema validation

**Optional** but recommended for tooling.

---

#### `chromadb-metadata-schema.md` (28 KB)
**Purpose**: ChromaDB metadata structure documentation

**Contents**:
- Visual embedding metadata schema
- Text embedding metadata schema
- Structure metadata format
- Chunk context format
- Field mappings and transformations

**Usage**: Backend agents understand stored data format

---

#### `sample-metadata-text.json` (7 KB)
#### `sample-metadata-visual.json` (5 KB)
**Purpose**: Example ChromaDB metadata records

**Usage**: Backend agents see actual data structure

---

## 🔗 Endpoint Summary

| Endpoint | Method | Purpose | Status | Agent |
|----------|--------|---------|--------|-------|
| `/documents/{id}/pages/{page}/structure` | GET | Retrieve page structure metadata | New | 4 |
| `/documents/{id}/chunks/{chunk_id}` | GET | Retrieve chunk metadata | New | 5 |
| `/documents/{id}/markdown` | GET | Enhanced markdown with chunk markers | Enhanced | 7 |
| `/api/research/ask` | POST | Research with chunk references | Enhanced | 6 |

---

## ✅ Validation Checklist

### Backend Implementation

- [ ] All endpoints return correct status codes
- [ ] Response schemas match specifications
- [ ] Bbox coordinates validated before returning
- [ ] Chunk ID format: `{doc_id}-chunk{NNNN}` (zero-padded)
- [ ] Error responses follow standard format
- [ ] Null handling for optional fields
- [ ] ChromaDB metadata correctly transformed

### Frontend Implementation

- [ ] Bbox scaling formulas implemented correctly
- [ ] URL parameters parsed and handled
- [ ] Null bbox handled gracefully
- [ ] Responsive resize updates overlays
- [ ] Invalid chunk IDs show user-friendly error
- [ ] Deep links work correctly
- [ ] Mobile responsive breakpoints scale correctly

---

## 🚀 Implementation Workflow

### Phase 1: Backend (Wave 2)

**Week 1**: Structure & Chunk APIs
- Agent 4: Implement Structure Metadata endpoint
- Agent 5: Implement Chunk Metadata endpoint
- Test against sample responses

**Week 2**: Enhancements
- Agent 6: Add chunk_id to Research API
- Agent 7: Add chunk markers to markdown
- Integration testing

### Phase 2: Frontend (Wave 3)

**Week 3**: Core Rendering
- Agent 8: Implement bbox overlay system
- Test scaling with coordinate system spec
- Responsive design validation

**Week 4**: Navigation
- Agent 9: Implement details page controller
- Agent 10: Integrate research navigation
- End-to-end testing

---

## 📊 Dependencies

### Backend → Frontend

Frontend agents **depend on** backend APIs being implemented:

```
Agent 4, 5, 6, 7 (Backend)
    ↓
    ↓ APIs deployed
    ↓
Agent 8, 9, 10 (Frontend)
```

**Timeline**: Frontend can start design/prototyping but requires backend for integration.

### Internal Dependencies

```
Agent 4 (Structure API)  ─┐
Agent 5 (Chunk API)      ─┼─→ Agent 8 (Bbox Overlay)
Agent 6 (Research chunk) ─┘      ↓
                                 ↓
Agent 7 (Markdown)       ─────→ Agent 9 (Details Page)
                                 ↓
Agent 6 (Research chunk) ─────→ Agent 10 (Navigation)
```

---

## 🧪 Testing Strategy

### Unit Testing

**Backend**:
- Test each endpoint independently
- Validate against sample responses
- Test error cases (404, 400, etc.)

**Frontend**:
- Test bbox scaling with different image sizes
- Test coordinate transformation formulas
- Test edge cases (null, minimum size, etc.)

### Integration Testing

**After Backend Complete**:
- Test actual API calls with real data
- Verify response format matches contracts
- Test bbox alignment with page images

**After Frontend Complete**:
- Test end-to-end navigation flows
- Test research → details page linking
- Test responsive scaling on different devices

---

## 📞 Support

### Questions About Contracts

- Refer to `API_CONTRACT_REVIEW.md` for design decisions
- Check `sample-api-responses.json` for concrete examples
- Review `coordinate-system-spec.md` for bbox questions

### Issues or Ambiguities

If you find any ambiguities or issues:

1. Check the review report first
2. Review relevant sample responses
3. Consult the OpenAPI spec for schema details
4. Raise with orchestrator if still unclear

---

## 📈 Version History

**v1.1** (2025-10-17):
- Added OpenAPI specification
- Enhanced API contracts with implementation status
- Added comprehensive review report
- All contracts finalized and ready

**v1.0** (2025-10-17):
- Initial contract specifications
- Sample responses created
- Coordinate system defined
- ChromaDB metadata documented

---

## ✨ Status

**Current Status**: ✅ **COMPLETE - IMPLEMENTATION READY**

All contracts are finalized, reviewed, and validated against existing codebase. No ambiguities or blockers remain. Backend agents (Wave 2) can begin implementation immediately.

**Next**: Wave 2 backend implementation → Wave 3 frontend integration → Testing & deployment

---

**Agent 3 (API Contract Designer) - Task Complete** ✅
