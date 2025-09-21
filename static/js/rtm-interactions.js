/**
 * RTM Interactions JavaScript
 * Enhanced interactive functionality for Requirements Traceability Matrix reports
 * US-00002: Enhanced RTM Report UX/UI Design
 *
 * Features:
 * - Collapsible epic sections
 * - Advanced filtering with smooth animations
 * - Keyboard accessibility (WCAG 2.1 AA)
 * - Search functionality
 * - Export capabilities
 * - Real-time filter count updates
 */

(function() {
    'use strict';

    // ===== CONFIGURATION & STATE =====

    const RTM = {
        // Configuration
        config: {
            animationDuration: 300,
            debounceDelay: 300,
            defaultTestFilter: 'all',
            supportedExportFormats: ['csv', 'json'],
        },

        // State management
        state: {
            activeFilters: {
                epic: 'all',
                userStory: 'all',
                test: 'all',
                defect: 'all'
            },
            expandedEpics: new Set(),
            searchTerm: '',
            isInitialized: false
        },

        // DOM element cache
        elements: {
            epicCards: null,
            searchInput: null,
            exportButtons: null,
            filterCounts: null
        }
    };

    // ===== UTILITY FUNCTIONS =====

    /**
     * Debounce function for search input
     */
    function debounce(func, wait) {
        let timeout;
        return function executedFunction(...args) {
            const later = () => {
                clearTimeout(timeout);
                func(...args);
            };
            clearTimeout(timeout);
            timeout = setTimeout(later, wait);
        };
    }

    /**
     * Sanitize string for use in selectors
     */
    function sanitizeSelector(str) {
        return str.replace(/[^a-zA-Z0-9-_]/g, '');
    }

    /**
     * Get epic ID from various element contexts
     */
    function getEpicId(element) {
        const epicCard = element.closest('.epic-card');
        if (!epicCard) return null;

        const titleLink = epicCard.querySelector('.epic-title-link');
        if (titleLink) {
            return titleLink.textContent.trim().split(':')[0];
        }

        return null;
    }

    /**
     * Update filter count display
     */
    function updateFilterCount(epicId, filterType, visible, total) {
        // Map filter types to actual HTML class names
        const classMap = {
            'test': 'test-count-display',
            'userStory': 'us-count-display',
            'defect': 'defect-count-display'
        };

        const className = classMap[filterType];
        if (!className) {
            console.warn(`❌ Unknown filter type: ${filterType}`);
            return;
        }

        const countDisplay = document.querySelector(`#epic-${epicId} .${className}`);
        if (!countDisplay) {
            console.warn(`❌ No count display found for ${filterType} in epic ${epicId}`);
            return;
        }

        const filterName = RTM.state.activeFilters[filterType];
        const displayName = filterType === 'userStory' ? 'user story' : filterType;

        if (total === 0) {
            countDisplay.textContent = `No ${displayName}s available for this epic`;
        } else if (filterName === 'all' || !filterName) {
            countDisplay.textContent = `Showing all ${total} ${displayName}s`;
        } else {
            const filterDisplay = filterName.replace('_', ' ').replace(/\b\w/g, l => l.toUpperCase());
            countDisplay.textContent = `Showing ${visible} ${filterDisplay} ${displayName}s (${total} total)`;
        }

    }

    /**
     * Animate element visibility with smooth transitions
     */
    function animateVisibility(element, show) {
        if (show) {
            element.classList.remove('hidden');
            element.style.opacity = '0';
            element.style.transform = 'translateY(-10px)';

            // Use requestAnimationFrame to avoid forced reflow
            requestAnimationFrame(() => {
                element.style.transition = `opacity ${RTM.config.animationDuration}ms ease, transform ${RTM.config.animationDuration}ms ease`;
                element.style.opacity = '1';
                element.style.transform = 'translateY(0)';
            });
        } else {
            element.style.transition = `opacity ${RTM.config.animationDuration}ms ease, transform ${RTM.config.animationDuration}ms ease`;
            element.style.opacity = '0';
            element.style.transform = 'translateY(-10px)';

            setTimeout(() => {
                element.classList.add('hidden');
                element.style.transition = '';
                element.style.opacity = '';
                element.style.transform = '';
            }, RTM.config.animationDuration);
        }
    }

    // ===== CORE FUNCTIONALITY =====

    /**
     * Toggle epic details with smooth animation and accessibility
     */
    function toggleEpicDetails(epicId) {
        const content = document.getElementById('epic-' + epicId);
        const header = document.querySelector(`[data-epic-id="${epicId}"] .epic-header`);

        if (!content || !header) {
            return;
        }

        // Check current display state (works with inline style="display: none;")
        const isHidden = content.style.display === 'none' || getComputedStyle(content).display === 'none';
        const newState = isHidden; // If hidden, we want to show (expand)

        // Update ARIA attributes
        header.setAttribute('aria-expanded', newState.toString());

        // Update state
        if (newState) {
            RTM.state.expandedEpics.add(epicId);
        } else {
            RTM.state.expandedEpics.delete(epicId);
        }

        // SIMPLIFIED APPROACH: Just show/hide the original element
        // This allows filter selectors to work correctly with #epic-{epicId}
        if (newState) {
            // Show the original epic content - this makes filtering work!
            content.style.display = 'block';

            // Clean up any leftover epic-display elements from previous workaround
            const existingEpicDisplay = document.getElementById('epic-display-' + epicId);
            if (existingEpicDisplay) existingEpicDisplay.remove();

            // Apply default filter when epic is first expanded
            setTimeout(() => {
                filterTestsByType(epicId, RTM.config.defaultTestFilter);
            }, 100); // Small delay to ensure DOM is ready
        } else {
            // Hide the epic content
            content.style.display = 'none';
        }

        // Announce to screen readers
        const announcement = newState ?
            `Epic ${epicId} expanded` :
            `Epic ${epicId} collapsed`;
        announceToScreenReader(announcement);
    }

    /**
     * Filter epics by status with animation
     */
    function filterByStatus(status) {
        RTM.state.activeFilters.epic = status;

        const cards = document.querySelectorAll('.epic-card');
        let visibleCount = 0;

        cards.forEach(card => {
            const cardStatus = card.dataset.status;
            const shouldShow = status === 'all' || cardStatus === status;

            if (shouldShow) {
                visibleCount++;
                animateVisibility(card, true);
            } else {
                animateVisibility(card, false);
            }
        });

        // Update filter button states
        updateFilterButtonStates('epic-status', status);

        // Announce results
        announceToScreenReader(`Showing ${visibleCount} epics with status: ${status}`);
    }

    /**
     * Filter tests by type with enhanced UX
     */
    function filterTestsByType(epicId, testType) {
        RTM.state.activeFilters.test = testType;

        const testTable = document.querySelector(`#epic-${epicId} table[aria-label*="Test Traceability"] tbody`);
        if (!testTable) {
            console.warn(`❌ No test table found for epic ${epicId}`);
            return;
        }

        const testRows = testTable.querySelectorAll('tr.test-row');
        let visibleCount = 0;

        // Update button states
        updateFilterButtonStates(`epic-${epicId}-test`, testType);

        // Filter test rows with animation
        testRows.forEach((row, index) => {
            const testTypeBadge = row.querySelector('.test-type-badge');
            if (!testTypeBadge) {
                return;
            }

            const rowTestType = testTypeBadge.textContent.toLowerCase();
            const shouldShow = testType === 'all' || rowTestType === testType.toLowerCase();

            if (shouldShow) {
                visibleCount++;
                animateVisibility(row, true);
            } else {
                animateVisibility(row, false);
            }
        });



        // Update count display
        updateFilterCount(epicId, 'test', visibleCount, testRows.length);

        // Announce results
        announceToScreenReader(`Filtered tests to show ${visibleCount} ${testType} tests`);
    }

    /**
     * Filter user stories by status
     */
    function filterUserStoriesByStatus(epicId, status) {
        RTM.state.activeFilters.userStory = status;

        const usTable = document.querySelector(`#epic-${epicId} table:first-of-type tbody`);
        if (!usTable) return;

        const usRows = usTable.querySelectorAll('.us-row');
        let visibleCount = 0;

        // Update button states
        updateFilterButtonStates(`epic-${epicId}-us`, status);

        // Filter user story rows
        usRows.forEach(row => {
            const rowStatus = row.dataset.usStatus;
            const shouldShow = status === 'all' || rowStatus === status;

            if (shouldShow) {
                visibleCount++;
                animateVisibility(row, true);
            } else {
                animateVisibility(row, false);
            }
        });

        // Update count display
        updateFilterCount(epicId, 'userStory', visibleCount, usRows.length);
    }

    /**
     * Filter defects with enhanced filtering options
     */
    function filterDefects(epicId, filterType, filterValue) {
        RTM.state.activeFilters.defect = `${filterType}:${filterValue}`;

        const defectTable = document.querySelector(`#epic-${epicId} .defect-filter-section + table tbody`);
        if (!defectTable) {
            console.warn(`❌ No defect table found for epic ${epicId}`);
            return;
        }

        const defectRows = defectTable.querySelectorAll('.defect-row');
        let visibleCount = 0;

        // Update button states
        updateFilterButtonStates(`epic-${epicId}-defect`, `${filterType}:${filterValue}`);

        // Filter defect rows
        defectRows.forEach((row, index) => {
            let shouldShow = false;

            if (filterType === 'all') {
                shouldShow = true;
            } else if (filterType === 'priority') {
                shouldShow = row.dataset.defectPriority === filterValue;
            } else if (filterType === 'status') {
                shouldShow = row.dataset.defectStatus === filterValue;
            }

            if (shouldShow) {
                visibleCount++;
                animateVisibility(row, true);
            } else {
                animateVisibility(row, false);
            }
        });

        // Check after a delay if anything changed
        setTimeout(() => {
            const visibleAfterDelay = defectTable.querySelectorAll('.defect-row:not(.hidden)').length;
        }, 500);

        // Update count display
        updateFilterCount(epicId, 'defect', visibleCount, defectRows.length);
    }

    /**
     * Update filter button states
     */
    function updateFilterButtonStates(filterGroup, activeValue) {
        const buttons = document.querySelectorAll(`[data-filter-group="${filterGroup}"]`);

        buttons.forEach(btn => {
            const btnValue = btn.dataset.filterValue || btn.dataset.testType || btn.dataset.usStatus || btn.dataset.defectFilter;

            if (btnValue === activeValue) {
                btn.classList.add('filter-button--active');
                btn.setAttribute('aria-pressed', 'true');
            } else {
                btn.classList.remove('filter-button--active');
                btn.setAttribute('aria-pressed', 'false');
            }
        });
    }

    // ===== SEARCH FUNCTIONALITY =====

    /**
     * Global search across all RTM content
     */
    function performSearch(searchTerm) {
        RTM.state.searchTerm = searchTerm.toLowerCase();

        if (!searchTerm.trim()) {
            // Show all content when search is empty
            showAllContent();
            return;
        }

        const epicCards = document.querySelectorAll('.epic-card');
        let visibleEpics = 0;

        epicCards.forEach(card => {
            const epicContent = card.textContent.toLowerCase();
            const shouldShow = epicContent.includes(RTM.state.searchTerm);

            if (shouldShow) {
                visibleEpics++;
                animateVisibility(card, true);
                highlightSearchTerms(card, searchTerm);
            } else {
                animateVisibility(card, false);
            }
        });

        // Update search results count
        updateSearchResultsCount(visibleEpics, epicCards.length);
    }

    /**
     * Highlight search terms in content
     */
    function highlightSearchTerms(container, term) {
        if (!term.trim()) return;

        // Remove existing highlights
        const existingHighlights = container.querySelectorAll('.search-highlight');
        existingHighlights.forEach(highlight => {
            highlight.outerHTML = highlight.innerHTML;
        });

        // Add new highlights (simplified for safety)
        const textNodes = getTextNodes(container);
        textNodes.forEach(node => {
            const text = node.textContent;
            const regex = new RegExp(`(${escapeRegExp(term)})`, 'gi');

            if (regex.test(text)) {
                const highlightedHTML = text.replace(regex, '<mark class="search-highlight">$1</mark>');
                const span = document.createElement('span');
                span.innerHTML = highlightedHTML;
                node.parentNode.replaceChild(span, node);
            }
        });
    }

    /**
     * Get all text nodes from an element
     */
    function getTextNodes(element) {
        const textNodes = [];
        const walker = document.createTreeWalker(
            element,
            NodeFilter.SHOW_TEXT,
            {
                acceptNode: function(node) {
                    // Skip script and style elements
                    if (node.parentElement.tagName === 'SCRIPT' ||
                        node.parentElement.tagName === 'STYLE') {
                        return NodeFilter.FILTER_REJECT;
                    }
                    return NodeFilter.FILTER_ACCEPT;
                }
            }
        );

        let node;
        while (node = walker.nextNode()) {
            textNodes.push(node);
        }
        return textNodes;
    }

    /**
     * Escape regular expression special characters
     */
    function escapeRegExp(string) {
        return string.replace(/[.*+?^${}()|[\]\\]/g, '\\$&');
    }

    /**
     * Show all content (clear search)
     */
    function showAllContent() {
        const epicCards = document.querySelectorAll('.epic-card');
        epicCards.forEach(card => {
            animateVisibility(card, true);

            // Remove search highlights
            const highlights = card.querySelectorAll('.search-highlight');
            highlights.forEach(highlight => {
                highlight.outerHTML = highlight.innerHTML;
            });
        });

        updateSearchResultsCount(epicCards.length, epicCards.length);
    }

    /**
     * Update search results count display
     */
    function updateSearchResultsCount(visible, total) {
        const countElement = document.querySelector('.search-results-count');
        if (countElement) {
            if (RTM.state.searchTerm) {
                countElement.textContent = `${visible} of ${total} epics match "${RTM.state.searchTerm}"`;
                countElement.style.display = 'block';
            } else {
                countElement.style.display = 'none';
            }
        }
    }

    // ===== ACCESSIBILITY FUNCTIONS =====

    /**
     * Announce messages to screen readers
     */
    function announceToScreenReader(message) {
        const announcement = document.createElement('div');
        announcement.setAttribute('aria-live', 'polite');
        announcement.setAttribute('aria-atomic', 'true');
        announcement.className = 'sr-only';
        announcement.textContent = message;

        document.body.appendChild(announcement);

        // Remove after announcement
        setTimeout(() => {
            document.body.removeChild(announcement);
        }, 1000);
    }

    /**
     * Setup keyboard navigation for epic headers
     */
    function setupKeyboardNavigation() {
        const epicHeaders = document.querySelectorAll('.epic-header');

        epicHeaders.forEach(header => {
            header.setAttribute('tabindex', '0');
            header.setAttribute('role', 'button');
            header.setAttribute('aria-expanded', 'false');

            // Keyboard event handler
            header.addEventListener('keydown', function(e) {
                if (e.key === 'Enter' || e.key === ' ') {
                    e.preventDefault();
                    const epicId = getEpicId(this);
                    if (epicId) {
                        toggleEpicDetails(epicId);
                    }
                }
            });

            // Click handler
            header.addEventListener('click', function(e) {
                const epicId = getEpicId(this);
                if (epicId) {
                    toggleEpicDetails(epicId);
                }
            });
        });
    }

    /**
     * Setup filter button accessibility
     */
    function setupFilterButtonAccessibility() {
        const filterButtons = document.querySelectorAll('.filter-button');

        filterButtons.forEach(button => {
            button.setAttribute('role', 'button');
            button.setAttribute('aria-pressed', 'false');

            // Add keyboard support
            button.addEventListener('keydown', function(e) {
                if (e.key === 'Enter' || e.key === ' ') {
                    e.preventDefault();
                    this.click();
                }
            });
        });
    }

    // ===== EXPORT FUNCTIONALITY =====

    /**
     * Export RTM data in specified format
     */
    function exportData(format) {
        if (!RTM.config.supportedExportFormats.includes(format)) {
            console.error(`Unsupported export format: ${format}`);
            return;
        }

        const data = collectRTMData();

        switch (format) {
            case 'csv':
                exportToCSV(data);
                break;
            case 'json':
                exportToJSON(data);
                break;
        }
    }

    /**
     * Collect all RTM data for export
     */
    function collectRTMData() {
        const data = {
            metadata: {
                generated: new Date().toISOString(),
                filters: RTM.state.activeFilters,
                searchTerm: RTM.state.searchTerm
            },
            epics: []
        };

        const epicCards = document.querySelectorAll('.epic-card:not(.hidden)');

        epicCards.forEach(card => {
            const epicData = {
                id: card.dataset.epicId,
                status: card.dataset.status,
                title: card.querySelector('.epic-title-link')?.textContent || '',
                userStories: [],
                tests: [],
                defects: []
            };

            // Collect user stories
            const usRows = card.querySelectorAll('.us-row:not(.hidden)');
            usRows.forEach(row => {
                const cells = row.querySelectorAll('td');
                if (cells.length >= 3) {
                    epicData.userStories.push({
                        id: cells[0].textContent.trim(),
                        title: cells[1].textContent.trim(),
                        status: cells[2].textContent.trim()
                    });
                }
            });

            // Collect tests
            const testRows = card.querySelectorAll('.test-row:not(.hidden)');
            testRows.forEach(row => {
                const cells = row.querySelectorAll('td');
                if (cells.length >= 4) {
                    epicData.tests.push({
                        id: cells[0].textContent.trim(),
                        type: cells[1].textContent.trim(),
                        status: cells[2].textContent.trim(),
                        description: cells[3].textContent.trim()
                    });
                }
            });

            // Collect defects
            const defectRows = card.querySelectorAll('.defect-row:not(.hidden)');
            defectRows.forEach(row => {
                const cells = row.querySelectorAll('td');
                if (cells.length >= 4) {
                    epicData.defects.push({
                        id: cells[0].textContent.trim(),
                        priority: cells[1].textContent.trim(),
                        status: cells[2].textContent.trim(),
                        summary: cells[3].textContent.trim()
                    });
                }
            });

            data.epics.push(epicData);
        });

        return data;
    }

    /**
     * Export data to CSV format
     */
    function exportToCSV(data) {
        let csv = 'Epic ID,Epic Status,Epic Title,Item Type,Item ID,Item Title,Item Status\n';

        data.epics.forEach(epic => {
            // User stories
            epic.userStories.forEach(us => {
                csv += `"${epic.id}","${epic.status}","${epic.title}","User Story","${us.id}","${us.title}","${us.status}"\n`;
            });

            // Tests
            epic.tests.forEach(test => {
                csv += `"${epic.id}","${epic.status}","${epic.title}","Test","${test.id}","${test.description}","${test.status}"\n`;
            });

            // Defects
            epic.defects.forEach(defect => {
                csv += `"${epic.id}","${epic.status}","${epic.title}","Defect","${defect.id}","${defect.summary}","${defect.status}"\n`;
            });
        });

        downloadFile(csv, 'rtm-export.csv', 'text/csv');
    }

    /**
     * Export data to JSON format
     */
    function exportToJSON(data) {
        const json = JSON.stringify(data, null, 2);
        downloadFile(json, 'rtm-export.json', 'application/json');
    }

    /**
     * Download file helper
     */
    function downloadFile(content, filename, mimeType) {
        const blob = new Blob([content], { type: mimeType });
        const url = URL.createObjectURL(blob);

        const link = document.createElement('a');
        link.href = url;
        link.download = filename;
        link.style.display = 'none';

        document.body.appendChild(link);
        link.click();
        document.body.removeChild(link);

        URL.revokeObjectURL(url);

        announceToScreenReader(`RTM data exported as ${filename}`);
    }

    // ===== INITIALIZATION =====

    /**
     * Initialize default test filtering
     */
    function initializeTestFiltering() {
        console.log('[DEBUG] initializeTestFiltering called');
        const epics = document.querySelectorAll('.epic-card');

        epics.forEach(epic => {
            const epicId = getEpicId(epic);
            if (epicId) {
                console.log(`[DEBUG] Initializing filters for epic: ${epicId}, filter: ${RTM.config.defaultTestFilter}`);
                // Apply default filter (show all tests)
                filterTestsByType(epicId, RTM.config.defaultTestFilter);
            }
        });
    }

    /**
     * Setup search functionality
     */
    function initializeSearch() {
        const searchInput = document.getElementById('rtm-search');
        if (searchInput) {
            RTM.elements.searchInput = searchInput;

            const debouncedSearch = debounce((e) => {
                performSearch(e.target.value);
            }, RTM.config.debounceDelay);

            searchInput.addEventListener('input', debouncedSearch);

            // Clear search button
            const clearButton = document.getElementById('clear-search');
            if (clearButton) {
                clearButton.addEventListener('click', () => {
                    searchInput.value = '';
                    showAllContent();
                    RTM.state.searchTerm = '';
                });
            }
        }
    }

    /**
     * Setup export functionality
     */
    function initializeExport() {
        const exportButtons = document.querySelectorAll('[data-export-format]');

        exportButtons.forEach(button => {
            button.addEventListener('click', (e) => {
                e.preventDefault();
                const format = button.dataset.exportFormat;
                exportData(format);
            });
        });
    }

    /**
     * Main initialization function
     */
    function initialize() {
        if (RTM.state.isInitialized) return;

        // Cache DOM elements
        RTM.elements.epicCards = document.querySelectorAll('.epic-card');

        // Setup core functionality
        setupKeyboardNavigation();
        setupFilterButtonAccessibility();
        // Note: Test filtering will be applied when epics are expanded (in toggleEpicDetails)
        initializeSearch();
        initializeExport();

        // Mark as initialized
        RTM.state.isInitialized = true;

        // Announce initialization
        announceToScreenReader('RTM interactive features initialized');

    }

    // ===== GLOBAL FUNCTION EXPOSURE =====

    // Expose functions to global scope for HTML onclick handlers
    window.toggleEpicDetails = toggleEpicDetails;
    window.filterByStatus = filterByStatus;
    window.filterTestsByType = filterTestsByType;
    window.filterUserStoriesByStatus = filterUserStoriesByStatus;
    window.filterDefects = filterDefects;

    // ===== EVENT LISTENERS =====

    // Initialize when DOM is ready
    if (document.readyState === 'loading') {
        document.addEventListener('DOMContentLoaded', initialize);
    } else {
        initialize();
    }

    // Re-initialize if new content is added dynamically
    window.addEventListener('rtm:contentUpdated', initialize);

})();