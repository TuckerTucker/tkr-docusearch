# Changelog

All notable changes to the DocuSearch project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Added
- Comprehensive repository review reports (security, code quality, performance, accessibility, testing, architecture, documentation, commit quality, dependencies)
- Environment variable validation module (src/config/env_validator.py) with placeholder detection and security checks
- Security remediation guide (.context-kit/_ref/SECURITY_REMEDIATION_GUIDE.md) with credential rotation procedures
- Skip navigation links for keyboard users (WCAG 2.4.1 Level A compliance)
- Proper file input label association in FilterBar component (WCAG 3.3.2 Level A compliance)

### Changed
- **SECURITY**: Replaced MD5 with SHA-256 for document ID generation (prevents hash collision attacks)
- **SECURITY**: Removed 6 wildcard CORS headers, now relies on centralized CORS middleware
- **SECURITY**: Redacted exposed API keys from repository history
- Extracted duplicate `convert_path_to_url()` function to shared utility (src/utils/paths.py)
- Updated page title from generic "frontend" to descriptive "DocuSearch - Multimodal Document Search & Research" (WCAG 2.4.2 Level A compliance)
- Updated .env.example with NGROK_AUTHTOKEN placeholder
- Enhanced README.md with comprehensive environment setup instructions

### Fixed
- Security vulnerabilities (3 critical, 5 high-severity issues resolved)
- Architecture DRY violation with inconsistent bug fixes across duplicate functions
- Accessibility violations (WCAG 2.4.1, 2.4.2, 3.3.2 Level A compliance achieved)

### Security
- All dependencies updated to patched versions (jinja2 >= 3.1.4, PyMuPDF >= 1.24.0, torch >= 2.1.0, vite >= 7.1.11)
- Command injection already prevented via proper path validation and subprocess argument lists
- CORS wildcard headers removed, using environment-based whitelist
- Cryptographic algorithms upgraded from MD5 to SHA-256

## [0.11.0] - 2025-10-21

### Added
- React 19 SPA migration complete with 76 components and feature parity with legacy frontend
- Vite 7, React Router 7, React Query 5, Zustand 5 integration
- Research API thumbnail fix: Convert filesystem paths to URL format in hybrid search metadata
- Wave 7 React migration with zero backend changes

### Changed
- Migrated from legacy frontend to production-ready React 19 SPA
- Updated all frontend dependencies to latest stable versions

### Fixed
- Research API metadata path conversion for thumbnail display

## [0.10.0] - 2025-10-15

### Added
- Local LLM preprocessing pipeline with gpt-oss-20B via MLX
- GPT-OSS-20B Harmony optimization for preprocessing (30-50% token reduction)
- Visual necessity detection for intelligent preprocessing
- Automated MLX model setup script
- Preprocessing strategies: compress, filter, synthesize

### Changed
- Preprocessing now uses MLX for local inference (60% cost reduction)
- Improved preprocessing token counting and efficiency
- Enhanced chunk context JSON storage

### Fixed
- MLX dependency and SVG image format issues
- Local inference hallucination problems
- Preprocessing enum comparison bug
- MLX initialization logic

## [0.9.0] - 2025-10-01

### Added
- MLX Whisper integration for ASR (Metal GPU acceleration)
- Audio transcription with word timestamps
- VTT caption generation with configurable duration and character limits
- Cover art extraction for audio files

### Changed
- ASR backend switched to MLX for 10-20x performance improvement
- Improved ASR model selection and configuration

### Fixed
- HuggingFace repo IDs for MLX Whisper models
- MLX Whisper options for MPS device activation
- Worker startup reliability in start-all script

## [0.8.0] - 2025-09-15

### Added
- 2-stage HNSW + MaxSim search (239ms avg, exceeds <300ms target)
- Hybrid Metal GPU + Docker architecture for optimal performance
- Native worker with Metal GPU acceleration (10-20x faster than CPU)
- Comprehensive unified bash scripts for system management
- Research Bot with LiteLLM multi-provider support and inline citations
- Bidirectional highlighting between research responses and source documents

### Changed
- Switched from Docker-only to hybrid architecture
- Unified management scripts for all services
- Enhanced research API with vision support

### Performance
- Search: 239ms average (target: <300ms) ✅
- Research: ~2.5s total (target: <3s) ✅
- Image embedding: 2.3s (2.6x faster than target) ✅
- Text embedding: 0.24s (25x faster than target) ✅

## [0.7.0] - 2025-09-01

### Added
- ColPali ColNomic 7B integration for vision-language retrieval
- ChromaDB vector database with persistent storage
- Real-time processing status updates via WebSocket
- Document deletion with 5-stage cleanup (ChromaDB, images, cover art, markdown, temp)

### Changed
- Switched from mock embeddings to production ColPali engine
- Implemented persistent ChromaDB storage
- Enhanced document processing pipeline

## [0.6.0] - 2025-08-15

### Added
- Multimodal document processing (PDF, DOCX, PPTX, XLSX, HTML, Markdown, CSV, audio, images)
- Page image extraction and thumbnail generation
- Markdown chunking with specialized metadata
- Audio format support (MP3, WAV) with cover art

### Changed
- Expanded supported file formats from 8 to 15
- Enhanced document parsing with Docling

## [0.5.0] - 2025-08-01

### Added
- FastAPI-based processing worker
- Document upload and processing endpoints
- Status API with health checks
- CORS middleware with environment-based whitelist

## [0.4.0] - 2025-07-15

### Added
- React frontend with component-based architecture
- Upload modal with drag-and-drop support
- Document library with filtering and search
- Research interface with source highlighting

## [0.3.0] - 2025-07-01

### Added
- Basic document search functionality
- PDF parsing and text extraction
- Simple embedding generation

## [0.2.0] - 2025-06-15

### Added
- Project structure and configuration
- Docker Compose setup
- Development environment

## [0.1.0] - 2025-06-01

### Added
- Initial project setup
- README and basic documentation
- License (MIT)

---

## Release Notes

### Version 0.11.0 - React 19 SPA Migration
This release completes the Wave 7 React migration, delivering a production-ready single-page application with modern tooling (Vite 7, React Router 7, React Query 5, Zustand 5). The migration achieved complete feature parity with the legacy frontend while maintaining zero backend changes.

### Version 0.10.0 - Local LLM Preprocessing
This release introduces local LLM preprocessing using gpt-oss-20B via MLX, reducing foundation model costs by ~60%. The Harmony optimization format delivers 30-50% additional token reduction and 2x faster inference.

### Version 0.9.0 - MLX Whisper ASR
This release adds audio transcription capabilities using MLX Whisper for Metal GPU acceleration, achieving 10-20x performance improvement over CPU-based inference. Includes VTT caption generation and audio cover art extraction.

### Version 0.8.0 - Production-Ready Search & Research
This release achieves production-ready status with all performance targets exceeded. The hybrid Metal GPU + Docker architecture delivers exceptional search performance (239ms vs 300ms target) and comprehensive research capabilities with inline citations.

### Version 0.7.0 - ColPali & ChromaDB Integration
This release replaces mock implementations with production ColPali and ChromaDB, enabling real vision-language retrieval and persistent vector storage.

---

## Contributors

- Tucker (@tuckertucker) - Project Lead & Primary Developer

## Support

For issues, questions, or contributions, please visit:
- GitHub: https://github.com/TuckerTucker/tkr-docusearch
- Documentation: See README.md

---

## License

This project is licensed under the MIT License - see the LICENSE file for details.
